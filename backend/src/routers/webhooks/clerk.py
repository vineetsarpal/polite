"""Clerk webhook ingress.

POST /api/webhooks/clerk
Headers: svix-id, svix-timestamp, svix-signature
Body: JSON event payload from Clerk

Each handler is idempotent and order-tolerant (compares event timestamp to
clerk_synced_at; skips stale).
"""
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from svix.webhooks import Webhook, WebhookVerificationError

from src import config, models
from src.database import get_db


v1_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify(request: Request, raw_body: bytes) -> dict[str, Any]:
    if not config.CLERK_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    try:
        wh = Webhook(config.CLERK_WEBHOOK_SECRET)
        return wh.verify(raw_body, dict(request.headers))
    except WebhookVerificationError as e:
        raise HTTPException(status_code=401, detail=f"Invalid signature: {e}") from e


def _event_ts(event: dict[str, Any]) -> datetime:
    """Clerk event timestamps are unix-ms ints in `timestamp`."""
    ts_ms = event.get("timestamp")
    if ts_ms is None:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)


def _is_stale(event_ts: datetime, synced_at: datetime | None) -> bool:
    if synced_at is None:
        return False
    if synced_at.tzinfo is None:
        synced_at = synced_at.replace(tzinfo=timezone.utc)
    return event_ts < synced_at


@v1_router.post("/clerk")
async def clerk_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    event = _verify(request, raw)
    event_type = event.get("type")
    data = event.get("data", {})
    event_ts = _event_ts(event)

    try:
        if event_type == "user.created":
            _handle_user_upsert(db, data, event_ts)
        elif event_type == "user.updated":
            _handle_user_upsert(db, data, event_ts)
        elif event_type == "user.deleted":
            _handle_user_deleted(db, data, event_ts)
        elif event_type == "organization.created":
            _handle_org_upsert(db, data, event_ts)
        elif event_type == "organization.updated":
            _handle_org_upsert(db, data, event_ts)
        elif event_type == "organization.deleted":
            _handle_org_deleted(db, data, event_ts)
        elif event_type == "organizationMembership.created":
            _handle_membership_upsert(db, data, event_ts)
        elif event_type == "organizationMembership.updated":
            _handle_membership_upsert(db, data, event_ts)
        elif event_type == "organizationMembership.deleted":
            _handle_membership_deleted(db, data)
        else:
            return {"status": "ignored", "type": event_type}
        return {"status": "ok", "type": event_type}
    except Exception:
        db.rollback()
        raise


def _handle_user_upsert(db: Session, data: dict, event_ts: datetime) -> None:
    user_id = data.get("id")
    if not user_id:
        return
    existing = db.get(models.User, user_id)
    if existing and _is_stale(event_ts, existing.clerk_synced_at):
        return

    primary_id = data.get("primary_email_address_id")
    email = None
    for ea in data.get("email_addresses", []) or []:
        if ea.get("id") == primary_id:
            email = ea.get("email_address")
            break

    full_name = " ".join(filter(None, [data.get("first_name"), data.get("last_name")])) or None
    is_active = not (data.get("banned", False) or data.get("locked", False))

    if existing is None:
        existing = models.User(
            id=user_id,
            email=email or f"{user_id}@unknown.local",
            full_name=full_name,
            is_active=is_active,
            clerk_synced_at=event_ts,
        )
        db.add(existing)
    else:
        if email:
            existing.email = email
        existing.full_name = full_name
        existing.is_active = is_active
        existing.clerk_synced_at = event_ts
    db.commit()


def _handle_user_deleted(db: Session, data: dict, event_ts: datetime) -> None:
    user_id = data.get("id")
    if not user_id:
        return
    existing = db.get(models.User, user_id)
    if existing and existing.deleted_at is None:
        existing.deleted_at = event_ts
        existing.clerk_synced_at = event_ts
        db.commit()


def _handle_org_upsert(db: Session, data: dict, event_ts: datetime) -> None:
    org_id = data.get("id")
    if not org_id:
        return
    existing = db.get(models.Organization, org_id)
    if existing and _is_stale(event_ts, existing.clerk_synced_at):
        return
    if existing is None:
        existing = models.Organization(
            id=org_id,
            name=data.get("name") or org_id,
            slug=data.get("slug"),
            clerk_synced_at=event_ts,
        )
        db.add(existing)
    else:
        existing.name = data.get("name") or existing.name
        existing.slug = data.get("slug")
        existing.clerk_synced_at = event_ts
    db.commit()


def _handle_org_deleted(db: Session, data: dict, event_ts: datetime) -> None:
    org_id = data.get("id")
    if not org_id:
        return
    existing = db.get(models.Organization, org_id)
    if existing and existing.deleted_at is None:
        existing.deleted_at = event_ts
        existing.clerk_synced_at = event_ts
        db.commit()


def _handle_membership_upsert(db: Session, data: dict, event_ts: datetime) -> None:
    membership_id = data.get("id")
    org = data.get("organization") or {}
    pub = data.get("public_user_data") or {}
    org_id = org.get("id")
    user_id = pub.get("user_id") or data.get("user_id")
    if not (membership_id and org_id and user_id):
        return
    existing = db.get(models.Membership, membership_id)
    if existing and _is_stale(event_ts, existing.clerk_synced_at):
        return
    if existing is None:
        existing = models.Membership(
            id=membership_id,
            user_id=user_id,
            organization_id=org_id,
            clerk_synced_at=event_ts,
        )
        db.add(existing)
    else:
        existing.clerk_synced_at = event_ts
    db.commit()


def _handle_membership_deleted(db: Session, data: dict) -> None:
    membership_id = data.get("id")
    if not membership_id:
        return
    existing = db.get(models.Membership, membership_id)
    if existing:
        db.delete(existing)
        db.commit()
