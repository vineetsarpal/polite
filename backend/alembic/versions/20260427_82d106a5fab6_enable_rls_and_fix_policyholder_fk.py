"""enable rls and fix policyholder fk

Revision ID: 82d106a5fab6
Revises: b6a266b6228f
Create Date: 2026-04-27 06:39:24.461334

"""
import os
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "82d106a5fab6"
down_revision: Union[str, Sequence[str], None] = "b6a266b6228f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------- helpers ----------

def _pg_quote_literal(s: str) -> str:
    """Quote a string as a PostgreSQL string literal (escape single quotes)."""
    return "'" + s.replace("'", "''") + "'"


_RLS_TABLES_ORG_SCOPED = ("organizations", "memberships", "contacts", "policies")
# `organizations` uses `id`; the others use `organization_id`.
_RLS_PREDICATE_COL = {
    "organizations": "id",
    "memberships": "organization_id",
    "contacts": "organization_id",
    "policies": "organization_id",
}


# ---------- upgrade ----------

def upgrade() -> None:
    app_password = os.environ.get("POLITE_APP_DB_PASSWORD")
    admin_password = os.environ.get("POLITE_ADMIN_DB_PASSWORD")
    if not app_password or not admin_password:
        raise RuntimeError(
            "POLITE_APP_DB_PASSWORD and POLITE_ADMIN_DB_PASSWORD env vars "
            "must be set when running this migration."
        )

    # 1. Roles. Idempotent via DO block.
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'polite_app') THEN
                CREATE ROLE polite_app LOGIN PASSWORD {_pg_quote_literal(app_password)};
            ELSE
                ALTER ROLE polite_app WITH LOGIN PASSWORD {_pg_quote_literal(app_password)};
            END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'polite_admin') THEN
                CREATE ROLE polite_admin LOGIN PASSWORD {_pg_quote_literal(admin_password)} BYPASSRLS;
            ELSE
                ALTER ROLE polite_admin WITH LOGIN PASSWORD {_pg_quote_literal(admin_password)} BYPASSRLS;
            END IF;
        END
        $$;
        """
    )

    # 2. Grants. Re-runnable.
    for role in ("polite_app", "polite_admin"):
        op.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role}"
        )
        op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {role}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {role}"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"GRANT USAGE, SELECT ON SEQUENCES TO {role}"
        )

    # 3. Enable + force RLS, define tenant_isolation policy on each org-scoped table.
    for table in _RLS_TABLES_ORG_SCOPED:
        col = _RLS_PREDICATE_COL[table]
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
                FOR ALL TO polite_app
                USING      ({col} = current_setting('app.current_org_id', true))
                WITH CHECK ({col} = current_setting('app.current_org_id', true));
            """
        )

    # 4. Fix policies.policyholder_id FK to ON DELETE SET NULL.
    op.execute("ALTER TABLE policies DROP CONSTRAINT policies_policyholder_id_fkey")
    op.execute(
        "ALTER TABLE policies "
        "ADD CONSTRAINT policies_policyholder_id_fkey "
        "FOREIGN KEY (policyholder_id) REFERENCES contacts(id) ON DELETE SET NULL"
    )


# ---------- downgrade ----------

def downgrade() -> None:
    # 4. Restore prior FK shape (no ON DELETE).
    op.execute("ALTER TABLE policies DROP CONSTRAINT policies_policyholder_id_fkey")
    op.execute(
        "ALTER TABLE policies "
        "ADD CONSTRAINT policies_policyholder_id_fkey "
        "FOREIGN KEY (policyholder_id) REFERENCES contacts(id)"
    )

    # 3. Drop policies, disable RLS.
    for table in _RLS_TABLES_ORG_SCOPED:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # 2. Revoke grants.
    for role in ("polite_app", "polite_admin"):
        op.execute(
            f"REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM {role}"
        )
        op.execute(
            f"REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public FROM {role}"
        )
        op.execute(f"REVOKE USAGE ON SCHEMA public FROM {role}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM {role}"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"REVOKE USAGE, SELECT ON SEQUENCES FROM {role}"
        )

    # 1. Drop roles.
    op.execute("DROP ROLE IF EXISTS polite_app")
    op.execute("DROP ROLE IF EXISTS polite_admin")
