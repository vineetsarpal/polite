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

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src import config


engine_app = create_engine(config.DATABASE_URL, pool_pre_ping=True)
engine_admin = create_engine(config.DATABASE_URL_ADMIN, pool_pre_ping=True)

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
