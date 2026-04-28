"""Database engines and FastAPI session dependencies.

Three connection roles, two engines:

- `engine_app` (DATABASE_URL, role `polite_app`, pooler endpoint):
    Used by request handlers via `get_tenant_db`. RLS applies.
    Each session sets `app.current_org_id` via `SET LOCAL` inside an
    explicit transaction.
- `engine_admin` (DATABASE_URL_ADMIN, role `polite_admin`, direct endpoint):
    Used by webhook handler, scripts, and `get_current_user`'s sync-on-demand
    path. Has BYPASSRLS — no GUC needed.
- Alembic uses DATABASE_URL_MIGRATIONS directly (project owner); not exposed
    as an engine in application code.
"""
from contextvars import ContextVar
from typing import Optional
from urllib.parse import urlparse, urlunparse

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src import config


def _derive_urls() -> tuple[str, str, str]:
    """
    Resolve the three Postgres URLs (app/admin/migrations) from config.

    In prod and local-dev, all three are set explicitly and returned as-is.
    In Render PR previews, only `DATABASE_URL` is auto-injected by the
    Render+Neon integration; the other two are constructed from it by:
      - stripping the `-pooler` hostname suffix to get the direct endpoint
      - substituting role + password from POLITE_ADMIN_DB_PASSWORD /
        OWNER_DB_USER+OWNER_DB_PASSWORD env vars (which are inherited from
        the parent branch on copy-on-write).
    """
    app_url = config.DATABASE_URL
    admin_url = config.DATABASE_URL_ADMIN
    migrations_url = config.DATABASE_URL_MIGRATIONS

    if admin_url and migrations_url:
        return app_url, admin_url, migrations_url

    parsed = urlparse(app_url)
    direct_host = parsed.hostname.replace("-pooler", "") if parsed.hostname else parsed.hostname
    port = f":{parsed.port}" if parsed.port else ""
    netloc_admin = f"polite_admin:{config.POLITE_ADMIN_DB_PASSWORD}@{direct_host}{port}"
    netloc_owner = f"{config.OWNER_DB_USER}:{config.OWNER_DB_PASSWORD}@{direct_host}{port}"

    derived_admin = urlunparse(parsed._replace(netloc=netloc_admin))
    derived_migrations = urlunparse(parsed._replace(netloc=netloc_owner))

    return app_url, admin_url or derived_admin, migrations_url or derived_migrations


APP_URL, ADMIN_URL, MIGRATIONS_URL = _derive_urls()

engine_app = create_engine(APP_URL, pool_pre_ping=True)
engine_admin = create_engine(ADMIN_URL, pool_pre_ping=True)

def _assert_engine_role(engine, expected_role: str) -> None:
    """
    Verify the engine connects as the expected Postgres role.
    Runs once at import time; surfaces misconfigured envs at boot,
    not at first request.
    """
    with engine.connect() as conn:
        actual_role = conn.exec_driver_sql("SELECT current_user").scalar_one()
        if actual_role != expected_role:
            raise RuntimeError(
                f"Engine connected as {actual_role!r} but expected {expected_role!r}. "
                f"Check DATABASE_URL / DATABASE_URL_ADMIN / role-password env vars."
            )


_assert_engine_role(engine_app, "polite_app")
_assert_engine_role(engine_admin, "polite_admin")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_app)
AdminSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_admin)

Base = declarative_base()


# Per-request org id, populated by `get_current_user` (security.py) after JWT validation.
current_org_id_var: ContextVar[Optional[str]] = ContextVar("current_org_id", default=None)


def get_db() -> Session:
    """Plain app-engine session. Reserved for cases where neither auth nor
    admin makes sense (rare; almost no caller should use this directly).
    Does not set `app.current_org_id` — RLS will fail-closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_admin_db() -> Session:
    """BYPASSRLS session for cross-tenant work (webhooks, scripts, sync-on-demand)."""
    db = AdminSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_tenant_db() -> Session:
    """Tenant-scoped session for request handlers.

    Wraps the session in an explicit transaction and issues `SET LOCAL
    app.current_org_id = <jwt org_id>` so RLS policies on org-scoped tables
    filter correctly. Reads the org id from `current_org_id_var`, which
    `get_current_user` sets after JWT validation.

    `SET LOCAL` is transaction-scoped and safe under transaction-mode
    pgbouncer — the GUC dies when the transaction commits/rolls back, so
    pooled connections cannot leak it across requests.
    """
    db = SessionLocal()
    try:
        org_id = current_org_id_var.get()
        if org_id is not None:
            db.execute(text("SET LOCAL app.current_org_id = :oid"), {"oid": org_id})
        # If org_id is None, fail-closed: RLS policies see NULL and return zero rows.
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
