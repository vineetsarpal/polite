"""Seed development data.

Provisions one demo organization + one demo admin user via Clerk Backend API,
then seeds sample contacts and policies for that org. Idempotent: safe to re-run.

Required env: CLERK_SECRET_KEY, DATABASE_URL_MIGRATIONS, DATABASE_URL_ADMIN,
POLITE_APP_DB_PASSWORD, POLITE_ADMIN_DB_PASSWORD (the latter two are read by
the RLS migration when it (re)applies role passwords).

WARNING: drops and recreates app schema. Dev only.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone, timedelta

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from clerk_backend_api import Clerk
from clerk_backend_api.models.getuserlistop import GetUserListRequest
from clerk_backend_api.models.createorganizationop import CreateOrganizationRequestBody
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Project root on path so `from src...` resolves when run as `uv run python scripts/seed_db.py`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import config, models  # noqa: E402
from src.database import AdminSessionLocal  # noqa: E402

DEMO_ORG_NAME = "Polite Demo Insurance"
DEMO_ORG_SLUG = "polite-demo"
DEMO_ADMIN_EMAIL = "demo-admin+clerk_test@example.com"
DEMO_ADMIN_PASSWORD = "PoliteDemo!2026"
DEMO_ADMIN_FIRST = "Demo"
DEMO_ADMIN_LAST = "Admin"


def reset_schema():
    """Drop the public schema and re-apply all Alembic migrations.

    Roles created by the RLS migration survive (they live in pg_authid, not
    pg_namespace). The migration's idempotent role block re-applies passwords
    from POLITE_APP_DB_PASSWORD / POLITE_ADMIN_DB_PASSWORD env vars.
    """
    print("Dropping and recreating public schema...")
    owner_engine = create_engine(config.DATABASE_URL_MIGRATIONS)
    with owner_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    print("Applying Alembic migrations...")
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    alembic_cfg = AlembicConfig(os.path.join(repo_root, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(repo_root, "alembic"))
    alembic_command.upgrade(alembic_cfg, "head")


def upsert_clerk_user(clerk: Clerk):
    existing = clerk.users.list(request=GetUserListRequest(email_address=[DEMO_ADMIN_EMAIL]))
    if existing:
        print(f"Found existing demo admin: {existing[0].id}")
        return existing[0]
    print("Creating demo admin user in Clerk...")
    user = clerk.users.create(
        email_address=[DEMO_ADMIN_EMAIL],
        password=DEMO_ADMIN_PASSWORD,
        first_name=DEMO_ADMIN_FIRST,
        last_name=DEMO_ADMIN_LAST,
        skip_password_checks=True,
    )
    print(f"Created Clerk user: {user.id}")
    return user


def upsert_clerk_org(clerk: Clerk, admin_user_id: str):
    listing = clerk.organizations.list(query=DEMO_ORG_NAME)
    for org in (listing.data or []):
        if org.name == DEMO_ORG_NAME:
            print(f"Found existing demo org: {org.id}")
            return org
    print("Creating demo organization in Clerk...")
    org = clerk.organizations.create(
        request=CreateOrganizationRequestBody(
            name=DEMO_ORG_NAME,
            created_by=admin_user_id,
        )
    )
    print(f"Created Clerk org: {org.id}")
    return org


def mirror_into_db(db: Session, clerk_user, clerk_org):
    """Mirror Clerk state into our DB so domain inserts have FK targets.

    Real flow uses webhooks; the seed script does it inline so the script can
    proceed without waiting for webhook delivery.
    """
    primary_email = next(
        (
            ea.email_address
            for ea in (clerk_user.email_addresses or [])
            if ea.id == clerk_user.primary_email_address_id
        ),
        DEMO_ADMIN_EMAIL,
    )
    db_user = models.User(
        id=clerk_user.id,
        email=primary_email,
        full_name=f"{clerk_user.first_name or ''} {clerk_user.last_name or ''}".strip() or None,
        is_active=True,
        clerk_synced_at=datetime.now(timezone.utc),
    )
    db.merge(db_user)

    db_org = models.Organization(
        id=clerk_org.id,
        name=clerk_org.name,
        slug=getattr(clerk_org, "slug", None) or DEMO_ORG_SLUG,
        clerk_synced_at=datetime.now(timezone.utc),
    )
    db.merge(db_org)
    db.commit()


def seed_domain(db: Session, org_id: str):
    print("Seeding sample contacts and policies...")
    contact = models.Contact(
        type="individual",
        first_name="Alice",
        last_name="Underwriter",
        email="alice@example.com",
        organization_id=org_id,
    )
    db.add(contact)
    db.flush()

    today = datetime.now(timezone.utc)
    db.add(
        models.Policy(
            lob="auto",
            status="active",
            base_premium=1200.00,
            net_premium=1100.00,
            tax=100.00,
            sum_insured=20000.00,
            license_plate="DEMO-001",
            vin="1HGCM82633A004352",
            start_date=today,
            end_date=today + timedelta(days=365),
            policyholder_id=contact.id,
            organization_id=org_id,
        )
    )
    db.commit()
    print("Domain seed complete.")


def main():
    if not config.CLERK_SECRET_KEY:
        raise SystemExit("CLERK_SECRET_KEY is required")

    reset_schema()
    clerk = Clerk(bearer_auth=config.CLERK_SECRET_KEY)

    clerk_user = upsert_clerk_user(clerk)
    clerk_org = upsert_clerk_org(clerk, admin_user_id=clerk_user.id)

    db: Session = AdminSessionLocal()
    try:
        mirror_into_db(db, clerk_user, clerk_org)
        seed_domain(db, clerk_org.id)
    finally:
        db.close()

    print("\nDone.")
    print(f"Org: {clerk_org.name} ({clerk_org.id})")
    print(f"Admin: {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
