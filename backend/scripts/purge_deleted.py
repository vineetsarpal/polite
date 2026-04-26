"""Hard-delete soft-deleted rows past the grace period.

Default grace: 30 days. Override with PURGE_GRACE_DAYS env var.

Real cron wiring lands in sub-project #3 (hosting). For now, this script is
runnable on demand and via whatever scheduler is in place.

Cascades:
- organizations.deleted_at past grace → DELETE org → cascades to contacts, policies, memberships
- users.deleted_at past grace          → DELETE user → cascades to memberships
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import models  # noqa: E402
from src.database import SessionLocal  # noqa: E402


def main():
    grace_days = int(os.getenv("PURGE_GRACE_DAYS", "30"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=grace_days)
    print(f"Hard-deleting rows with deleted_at < {cutoff.isoformat()} (grace={grace_days}d)")

    db = SessionLocal()
    try:
        org_q = (
            db.query(models.Organization)
            .filter(
                models.Organization.deleted_at.isnot(None),
                models.Organization.deleted_at < cutoff,
            )
        )
        orgs_to_delete = org_q.all()
        for org in orgs_to_delete:
            print(f"  purging org {org.id} ({org.name}) deleted_at={org.deleted_at.isoformat()}")
            db.delete(org)

        user_q = (
            db.query(models.User)
            .filter(models.User.deleted_at.isnot(None), models.User.deleted_at < cutoff)
        )
        users_to_delete = user_q.all()
        for u in users_to_delete:
            print(f"  purging user {u.id} ({u.email}) deleted_at={u.deleted_at.isoformat()}")
            db.delete(u)

        db.commit()
        print(f"Done. Purged {len(orgs_to_delete)} orgs and {len(users_to_delete)} users.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
