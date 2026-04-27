# Polite API

A modular FastAPI backend for managing insurance policies.

> This directory is part of the [Polite monorepo](../README.md). It was originally the standalone [`polite-server`](https://github.com/vineetsarpal/polite-server) repo and was folded in via `git subtree`. See the [root README](../README.md) for the full architecture, RBAC model, deployment notes, and demo credentials.

## Features

- **Policy Management:** Issue, update, and view policies.
- **Dynamic Covers & Rates:** Configure product-specific covers and rates with effective dates.
- **Authentication:** Clerk-based identity, sessions, and B2B organizations.
- **Role-Based Access:** Permissions read from Clerk JWT claims; no DB round-trips.
- **Multi-tenancy:** Every request is scoped to the user's organization via the Clerk token.
- **Audit Trail:** Track changes to policies. *(Coming Soon)*

## Getting Started

From the monorepo root:

1. **Install dependencies** (creates `.venv/` and installs from `uv.lock`)
    ```bash
    cd backend
    uv sync
    ```
    Requires [uv](https://docs.astral.sh/uv/). Activate the venv with `source .venv/bin/activate` if you want bare commands, or prefix everything with `uv run`.

2. **Configure environment variables**
    - Create `.env` with `DATABASE_URL`, `FRONTEND_URL`, and the Clerk vars below. See the [root README](../README.md#2-backend) for a full example.

3. **Seed the database** (drops and recreates all tables, then loads demo data)
    ```bash
    uv run python scripts/seed_db.py
    ```

4. **Start the FastAPI server**
    ```bash
    uv run fastapi dev src/main.py
    ```

5. **API Overview**
    Interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs); Prometheus metrics at [http://localhost:8000/metrics](http://localhost:8000/metrics).

## Authentication (Clerk)

Polite uses Clerk for identity, sessions, B2B organizations, and authorization (claims-only — permissions are read from the Clerk JWT, never the DB).

Required env vars in `backend/.env`:

```
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_WEBHOOK_SECRET=whsec_...
CLERK_JWT_ISSUER=https://<slug>.clerk.accounts.dev
```

- `CLERK_SECRET_KEY` / `CLERK_PUBLISHABLE_KEY` — Clerk dashboard → Configure → API Keys.
- `CLERK_JWT_ISSUER` — the "Frontend API URL" from the same page.
- `CLERK_WEBHOOK_SECRET` — set after registering a webhook endpoint (see below).

### Webhook setup (local dev)

1. Run `ngrok http 8000` (or any tunnel) to expose your local backend.
2. In Clerk dashboard → Configure → Webhooks → Add endpoint:
   - URL: `https://<ngrok-url>/api/webhooks/clerk`
   - Subscribe to events: `user.created`, `user.updated`, `user.deleted`, `organization.created`, `organization.updated`, `organization.deleted`, `organizationMembership.created`, `organizationMembership.updated`, `organizationMembership.deleted`.
3. Copy the **Signing Secret** into `CLERK_WEBHOOK_SECRET` and restart the backend.

### Roles & permissions

Defined in Clerk dashboard → Configure → Roles & Permissions:

- Features: `contacts`, `policies`
- Permissions per feature: `create`, `read`, `update`, `delete` → resolved keys: `org:contacts:create`, `org:policies:read`, etc.
- Roles: `org:admin` (all 8) and `org:member` (read on both, plus create/update on contacts and policies).

### Seed data

`scripts/seed_db.py` provisions a demo organization and demo admin via Clerk Backend API, then seeds sample contacts and policies. Idempotent. Drops & recreates the app schema. Dev-only.

```bash
uv run python scripts/seed_db.py
```

Demo creds: `demo-admin+clerk_test@example.com` / `PoliteDemo!2026`.

### Soft-delete grace period

Org/user/membership rows keep a `deleted_at` column. After Clerk fires a deletion webhook, rows are soft-deleted. `scripts/purge_deleted.py` hard-deletes rows past the grace period (default 30 days, override with `PURGE_GRACE_DAYS`).

## Project Structure

- `src/routers/v1/` – API route definitions (`user`, `contact`, `policy`, `webhooks`)
- `src/models.py` – SQLAlchemy ORM models
- `src/schemas.py` – Pydantic schemas
- `src/security.py` – Clerk JWT verification and RBAC helpers
- `src/database.py` – Database connection and session management
- `scripts/seed_db.py` – Drops, recreates, and seeds demo data via Clerk Backend API
- `scripts/purge_deleted.py` – Hard-deletes soft-deleted rows past the grace period
- `docker-compose.yml` – Prometheus + Grafana + Alertmanager stack (does **not** run the API itself)

## Frontend

The React web client lives in [`../frontend`](../frontend) within this same repo.
