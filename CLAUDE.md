# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo layout

This is a monorepo for **Polite**, a B2B SaaS for North-American insurance brokers. Two top-level apps:

- `backend/` — FastAPI + SQLAlchemy + PostgreSQL API. Originated from the `polite-server` repo and was added here via `git subtree`.
- `frontend/` — React 19 + Vite + TypeScript SPA. Originated from `polite-client-web`, also subtree-merged.

The two apps communicate at runtime via HTTP; in dev the frontend points at the backend through `VITE_API_BASE_URL` (default `http://localhost:8000/api`).

## Production-grade roadmap

Polite is being moved to a managed, production-grade stack across **8 sub-projects** (each with its own spec → plan → implementation cycle). The full roadmap and architecture rationale live in `docs.local/roadmap.md` (gitignored — a local working document):

1. **Identity & auth migration → Clerk** — *complete (PR #1, tag `v0.2.0-auth-migration`)*
2. **Database migration (managed Postgres on Neon + Alembic + RLS tenant isolation)** — *complete (PR #2, tag `v0.3.0-db-migration`)*
3. Hosting & deploy (Render/Fly + Vercel + GitHub Actions)
4. Object storage (policy document upload)
5. Observability (Sentry + Better Stack; decommission self-hosted Prom)
6. Transactional email (Resend)
7. Billing (Stripe subscriptions tied to organizations)
8. Security hardening (rate limiting, audit log, periodic Clerk reconciliation, etc.)

## Common commands

### Backend (`cd backend`)

```bash
uv sync                                # one-time and after dep changes; creates .venv/

uv run fastapi dev src/main.py         # dev server with reload (http://localhost:8000)
uv run alembic upgrade head            # apply pending migrations (uses DATABASE_URL_MIGRATIONS)
uv run alembic revision --autogenerate -m "<slug>"   # generate a new migration; ALWAYS review by hand before applying
uv run python scripts/seed_db.py       # DROPS public schema, runs alembic upgrade head, seeds demo data via Clerk Backend API
uv run python scripts/purge_deleted.py # hard-delete soft-deleted rows past the grace period (default 30 days)
docker compose up -d                   # spins up Prometheus + Grafana + Alertmanager (NOT the API; legacy, decommissioned in sub-project #5)
```

Dependencies are managed via `pyproject.toml` + `uv.lock` (uv); there is no `requirements.txt`. Add deps with `uv add <pkg>` (don't hand-edit the lock).

Schema is managed by Alembic (`backend/alembic/`). New migrations: `uv run alembic revision --autogenerate -m "<slug>"`, then **review the generated file by hand** before applying. RLS policies, GRANTs, and role definitions are **not autogenerable** — write those by hand inside the generated revision (see `20260427_..._enable_rls_and_fix_policyholder_fk.py` for the pattern).

For local Clerk webhook delivery, run `ngrok http 8000` and register the public URL at Clerk dashboard → Webhooks (events: `user.*`, `organization.*`, `organizationMembership.*`).

Production runs Gunicorn under systemd (`gunicorn.service`); CI deploy is `.github/workflows/deploy.yml` which SSH's to the prod host and restarts the `api` service. (To be replaced in sub-project #3.)

### Frontend (`cd frontend`)

```bash
npm install
npm run dev      # Vite dev server (http://localhost:5173)
npm run build    # tsc -b && vite build
npm run lint     # eslint .

# Regenerate API types from the running backend's OpenAPI schema:
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/openapi.ts
```

There is no automated test suite in either app. This gap is acknowledged and will be addressed incrementally per sub-project.

## Architecture

### Backend

- Entry point `src/main.py` mounts four v1 routers under `/api`: `user`, `contact`, `policy`, plus a webhook ingress at `/api/webhooks/clerk`.
- `src/models.py` — SQLAlchemy ORM. Core entities:
  - **Clerk-mirrored** (string PKs from Clerk IDs): `Organization`, `User`, `Membership`. All have `deleted_at` (soft-delete) and `clerk_synced_at` columns. The mirror exists only for FK integrity; never the primary read path for identity/role/permission.
  - **Domain** (integer PKs, app-owned): `Contact`, `Policy`. Both scoped by `organization_id` FK.
- `src/schemas.py` — Pydantic request/response models. Naming convention: `XBase` / `XCreate` / `XPublic`.
- `src/security.py` — Clerk JWT validation (RS256 via Clerk JWKS) using `clerk-backend-api` v5. Three exports:
  - `get_current_user` — validates session token, syncs user/org/membership on demand if not yet mirrored, attaches JWT-sourced `organization_id`, `org_role`, `permissions` onto the User object.
  - `get_current_active_user` — refuses inactive users or missing org context.
  - `require_permission(perm)` — FastAPI dependency factory. Use as `dependencies=[Depends(require_permission("org:policies:create"))]`.
- `src/routers/webhooks/clerk.py` — Svix-verified ingress at `POST /api/webhooks/clerk`. Idempotent, order-tolerant handlers for `user.*`, `organization.*`, `organizationMembership.*` events.
- `src/database.py` — two SQLAlchemy engines bound to two distinct Postgres roles, plus three FastAPI session dependencies. See **Tenant isolation via RLS** below.
- `src/config.py` — env loading. All Clerk env vars (`CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY`, `CLERK_WEBHOOK_SECRET`, `CLERK_JWT_ISSUER`) plus three Postgres URLs (`DATABASE_URL`, `DATABASE_URL_ADMIN`, `DATABASE_URL_MIGRATIONS`) and `FRONTEND_URL`.
- Observability: `prometheus-fastapi-instrumentator` exposes `/metrics`; `docker-compose.yml` at backend root runs the Prometheus/Grafana/Alertmanager stack independently. (Slated for replacement in sub-project #5.)

### Multi-tenancy and authorization (load-bearing pattern)

**Authorization is claims-only.** The Clerk JWT carries `org_id`, `org_role`, and `org_permissions[]` — `get_current_user` reads them and never queries the DB for role/permission state. Roles and permissions are defined in the Clerk dashboard (Configure → Roles & Permissions); features and permissions follow the `org:<feature>:<action>` convention (e.g., `org:contacts:create`, `org:policies:delete`).

Every request is scoped to the user's `organization_id`, which is **read from the Clerk JWT, not the request body**. When creating resources, handlers explicitly inject it:

```python
data["organization_id"] = current_user.organization_id
```

List/get/update queries always filter by `Model.organization_id == current_user.organization_id`. Preserve this on any new endpoint touching org-scoped tables (`Contact`, `Policy`, `Membership`). The two gates — `require_permission(...)` (what action) and the org_id filter (whose data) — are independent and both required.

When a JWT references a user/org/membership not yet mirrored in the DB (webhook-vs-API race during sign-up), `get_current_user` does a sync-on-demand fetch from the Clerk Backend API and upserts. Webhooks are an *optimization*, not a correctness dependency.

### Tenant isolation via Postgres RLS (defense-in-depth)

The app-layer `WHERE organization_id = current_user.organization_id` filter is one of two enforcement layers; the second is **Postgres Row-Level Security**. `organizations`, `memberships`, `contacts`, `policies` all have `FORCE ROW LEVEL SECURITY` with a `tenant_isolation` policy that compares `organization_id` (or `id` for the `organizations` table) to `current_setting('app.current_org_id', true)`. The GUC is set per-request via `SET LOCAL` inside the request transaction; `current_setting(..., true)` returns NULL when unset, which by predicate evaluation hides every row — **fail-closed**.

Three Postgres roles, two engines, three FastAPI dependencies:

| Role | URL env | Endpoint | RLS | FastAPI dep | Used by |
|---|---|---|---|---|---|
| `polite_app` | `DATABASE_URL` | pooler (`-pooler` host, transaction mode) | applies | `get_tenant_db` | tenant-scoped request handlers |
| `polite_admin` | `DATABASE_URL_ADMIN` | direct | bypasses | `get_admin_db` | webhook handler, scripts, `get_current_user`'s sync-on-demand |
| project owner (e.g., `neondb_owner`) | `DATABASE_URL_MIGRATIONS` | direct | bypasses (table owner) | — (Alembic only) | migrations |

**Conventions to preserve:**
- `Depends(get_tenant_db)` for any route handler that touches an org-scoped table. The dependency reads `current_org_id_var` (set by `get_current_user` after JWT validation) and issues `SET LOCAL app.current_org_id = <oid>` in an explicit transaction.
- `Depends(get_admin_db)` only in `routers/webhooks/` and `scripts/`. Never import it into a v1 router.
- In handler signatures, declare `current_user` (or any `Depends(require_permission(...))`) **before** `db: Session = Depends(get_tenant_db)`. FastAPI resolves dependencies in declaration order; auth must run first so the ContextVar is populated before `get_tenant_db` consumes it.
- `get_db()` exists in `database.py` for completeness but is essentially unused — it returns a `polite_app` session with no GUC set, so RLS sees zero rows. Don't use it in new code.

### Soft-delete with grace period

`organizations`, `users`, `memberships` rows have a nullable `deleted_at`. Clerk's deletion webhooks set this column rather than hard-deleting. After the grace period (default 30 days; override with `PURGE_GRACE_DAYS` env var), `scripts/purge_deleted.py` hard-deletes them — cascade FKs clean up dependent rows.

### Frontend

- **Routing**: TanStack Router with file-based routes in `src/routes/`. `src/routeTree.gen.ts` is **auto-generated** by `@tanstack/router-plugin/vite` — never hand-edit it; add files under `src/routes/` and the dev server regenerates it. Dynamic segments use `$param.tsx`; splat (catch-all) segments use `$.tsx` (used for Clerk's path-routed sign-in/sign-up flows).
- **Top-level routes**: `/`, `/about`, `/sign-in` (+ `sign-in.$.tsx` splat), `/sign-up` (+ splat), `/dashboard/*`. The dashboard layout (`dashboard/route.tsx`) gates on Clerk's `useAuth().isSignedIn` and an active organization, redirecting to `<RedirectToSignIn>` or `<RedirectToCreateOrganization>` as appropriate.
- **Data fetching**: TanStack Query (`@tanstack/react-query`). `QueryClient`, `ClerkProvider`, and Chakra `Provider` wrap the app in `src/main.tsx`.
- **Auth**: `@clerk/clerk-react` v5. Use `useAuth()`, `useUser()`, `useOrganization()` from Clerk for identity and org context. Sign-in / sign-up / organization management are rendered via Clerk's `<SignIn>`, `<SignUp>`, `<OrganizationProfile>`, `<OrganizationSwitcher>`, `<UserButton>` components. Permission-gated UI uses `<Protect permission="org:policies:create">…</Protect>` or imperative `useAuth().has({ permission: "..." })`.
- **API client**: `src/lib/apiClient.ts` exports a `useApiClient()` hook with `get`/`post`/`put`/`del` methods that auto-inject the Clerk session token via `getToken()`. Use it everywhere — there is no separate auth service. Convenience helper `v1('/contacts')` returns `/api/v1/contacts`.
- **Types from API**: `src/types/openapi.ts` is generated from the backend's OpenAPI schema. Components import request/response types like:
  ```ts
  type FormData = paths["/api/v1/policies/"]["post"]["requestBody"]["content"]["application/json"]
  ```
  Regenerate `openapi.ts` after backend schema changes.
- **UI**: Chakra UI v3 (`@chakra-ui/react`). Forms use `react-hook-form`. Path alias `@/*` → `src/*` (configured in `tsconfig.app.json` + `vite-tsconfig-paths`).

### Required env vars

Backend (`.env` in `backend/`):
- `DATABASE_URL` — `polite_app` role on the **pooler** endpoint (request handlers)
- `DATABASE_URL_ADMIN` — `polite_admin` role on the **direct** endpoint (webhooks, scripts)
- `DATABASE_URL_MIGRATIONS` — project owner on the **direct** endpoint (Alembic only)
- `POLITE_APP_DB_PASSWORD`, `POLITE_ADMIN_DB_PASSWORD` — read by the RLS migration when (re)applying role passwords
- `FRONTEND_URL`
- `CLERK_SECRET_KEY` (sk_test_...)
- `CLERK_PUBLISHABLE_KEY` (pk_test_..., same value as the frontend's)
- `CLERK_WEBHOOK_SECRET` (whsec_..., from Clerk dashboard → Webhooks after registering an endpoint)
- `CLERK_JWT_ISSUER` (`https://<slug>.clerk.accounts.dev` — the "Frontend API URL" from Clerk dashboard)

Frontend (`.env` in `frontend/`, see `.env.sample`):
- `VITE_API_BASE_URL`
- `VITE_CLERK_PUBLISHABLE_KEY` (pk_test_..., same value as backend's `CLERK_PUBLISHABLE_KEY`)

### Seed data

`scripts/seed_db.py` provisions one demo organization + one demo admin via the Clerk Backend API, then seeds sample contacts and policies. Idempotent (safe to re-run). Drops & recreates the app schema. Dev-only.

Demo creds: `demo-admin+clerk_test@example.com` / `PoliteDemo!2026`. The `+clerk_test` suffix tells Clerk dev mode this is a test user (no real email sent). Public-facing demo experience (e.g., the old "Continue as guest" button) was dropped in sub-project #1; a richer demo flow may land later.

### Clerk dashboard configuration (one-time per environment)

- Personal accounts: **Disabled** (B2B-only)
- Email + password: enabled; email verification required
- MFA: optional (no enforcement at launch)
- Social SSO / SAML: disabled initially
- Organization creation by users: allowed (required for self-serve sign-up)
- Roles: `org:admin` (all 8 perms) and `org:member` (read on both features + create/update on contacts and policies — no deletes)
- Features: `contacts`, `policies`. Permissions per feature: `create`, `read`, `update`, `delete` → keys `org:<feature>:<action>`.
