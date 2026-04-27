"""Clerk-backed authentication and authorization.

The backend never issues tokens. It validates Clerk session tokens (RS256),
reads claims (sub, org_id, org_role, org_permissions), and enforces tenancy
+ permission via FastAPI dependencies.

Authorization is claims-only: never read role/permission state from the DB.
The DB is consulted only to:
1. Mirror Clerk identity for FK integrity.
2. Sync-on-demand if the JWT references an entity not yet mirrored
   (handles webhook-vs-API race during sign-up).
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions

from src import config, models
from src.database import current_org_id_var, get_admin_db


_clerk: Optional[Clerk] = None


def get_clerk() -> Clerk:
    """Lazy singleton Clerk SDK client."""
    global _clerk
    if _clerk is None:
        _clerk = Clerk(bearer_auth=config.CLERK_SECRET_KEY)
    return _clerk


def _authenticate(request: Request) -> dict:
    """Validate Clerk session token and return claims dict.

    Raises 401 on any failure.
    """
    clerk = get_clerk()
    options = AuthenticateRequestOptions(
        secret_key=config.CLERK_SECRET_KEY,
        authorized_parties=None,
        jwt_key=None,
    )
    state = clerk.authenticate_request(request, options)
    if not state.is_signed_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = state.payload or {}
    return payload


def _sync_user_on_demand(db: Session, user_id: str) -> models.User:
    """Fetch user from Clerk and upsert to local DB."""
    clerk = get_clerk()
    clerk_user = clerk.users.get(user_id=user_id)
    primary_email = None
    if clerk_user.email_addresses:
        for ea in clerk_user.email_addresses:
            if ea.id == clerk_user.primary_email_address_id:
                primary_email = ea.email_address
                break
    full_name = " ".join(filter(None, [clerk_user.first_name, clerk_user.last_name])) or None
    is_active = not (getattr(clerk_user, "banned", False) or getattr(clerk_user, "locked", False))

    user = db.get(models.User, user_id)
    if user is None:
        user = models.User(
            id=user_id,
            email=primary_email or f"{user_id}@unknown.local",
            full_name=full_name,
            is_active=is_active,
            clerk_synced_at=datetime.now(timezone.utc),
        )
        db.add(user)
    else:
        if primary_email:
            user.email = primary_email
        user.full_name = full_name
        user.is_active = is_active
        user.clerk_synced_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def _sync_org_on_demand(db: Session, org_id: str) -> models.Organization:
    clerk = get_clerk()
    clerk_org = clerk.organizations.get(organization_id=org_id)
    org = db.get(models.Organization, org_id)
    if org is None:
        org = models.Organization(
            id=org_id,
            name=clerk_org.name,
            slug=clerk_org.slug,
            clerk_synced_at=datetime.now(timezone.utc),
        )
        db.add(org)
    else:
        org.name = clerk_org.name
        org.slug = clerk_org.slug
        org.clerk_synced_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(org)
    return org


def _sync_membership_on_demand(
    db: Session, user_id: str, org_id: str
) -> Optional[models.Membership]:
    clerk = get_clerk()
    memberships_response = clerk.users.get_organization_memberships(user_id=user_id)
    target = None
    for m in (memberships_response.data or []):
        if m.organization.id == org_id:
            target = m
            break
    if target is None:
        return None
    existing = (
        db.query(models.Membership)
        .filter(
            models.Membership.user_id == user_id,
            models.Membership.organization_id == org_id,
        )
        .one_or_none()
    )
    if existing is None:
        existing = models.Membership(
            id=target.id,
            user_id=user_id,
            organization_id=org_id,
            clerk_synced_at=datetime.now(timezone.utc),
        )
        db.add(existing)
    else:
        existing.clerk_synced_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(existing)
    return existing


async def get_current_user(request: Request, db: Session = Depends(get_admin_db)) -> models.User:
    """Validate Clerk JWT, sync on demand, return User with attached claims.

    Attaches: organization_id, org_role, permissions (all from JWT, not DB).
    """
    payload = _authenticate(request)

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    org_role = payload.get("org_role")
    permissions: List[str] = payload.get("org_permissions", []) or []

    # Make org_id visible to get_authed_db so it can SET LOCAL app.current_org_id.
    current_org_id_var.set(org_id)

    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")

    user = db.get(models.User, user_id)
    if user is None:
        user = _sync_user_on_demand(db, user_id)

    if user.deleted_at is not None:
        raise HTTPException(status_code=403, detail="User has been deleted")

    if org_id:
        org = db.get(models.Organization, org_id)
        if org is None:
            org = _sync_org_on_demand(db, org_id)
        if org.deleted_at is not None:
            raise HTTPException(status_code=403, detail="Organization has been deleted")

        membership = (
            db.query(models.Membership)
            .filter(
                models.Membership.user_id == user_id,
                models.Membership.organization_id == org_id,
            )
            .one_or_none()
        )
        if membership is None:
            _sync_membership_on_demand(db, user_id, org_id)

    user.organization_id = org_id  # type: ignore[attr-defined]
    user.org_role = org_role  # type: ignore[attr-defined]
    user.permissions = permissions  # type: ignore[attr-defined]
    return user


async def get_current_active_user(
    user: models.User = Depends(get_current_user),
) -> models.User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    if not getattr(user, "organization_id", None):
        raise HTTPException(
            status_code=403,
            detail="No active organization context. Select or create an organization.",
        )
    return user


def require_permission(perm: str):
    """FastAPI dependency factory: enforces presence of `perm` in JWT claims."""

    async def _check(user: models.User = Depends(get_current_active_user)) -> models.User:
        if perm not in getattr(user, "permissions", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _check
