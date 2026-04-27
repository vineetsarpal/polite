"""User endpoints — read-only mirror of Clerk-managed users.

Lifecycle (create/update/delete) lives in Clerk; we only expose:
- GET /users/me — current user's profile + active org context
- GET /users/    — list members of the active organization (joined from `memberships`)
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src import models, schemas
from src.database import get_tenant_db
from src.security import get_current_active_user, require_permission

v1_router = APIRouter(prefix="/v1/users", tags=["users"])


@v1_router.get("/me", response_model=schemas.UserPublic)
def me(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@v1_router.get("/", response_model=List[schemas.OrgMember])
def list_org_members(
    current_user: models.User = Depends(require_permission("org:contacts:read")),
    db: Session = Depends(get_tenant_db),
):
    """List users in the caller's active organization.

    Requires `org:contacts:read` as a coarse 'can see other org members' gate.
    Adjust to a dedicated permission if/when one is added.
    """
    rows = (
        db.query(models.User, models.Membership)
        .join(models.Membership, models.Membership.user_id == models.User.id)
        .filter(
            models.Membership.organization_id == current_user.organization_id,
            models.User.deleted_at.is_(None),
        )
        .order_by(models.User.email)
        .all()
    )
    return [
        schemas.OrgMember(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            membership_id=m.id,
            membership_created_at=m.created_at,
        )
        for u, m in rows
    ]
