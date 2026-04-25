# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo layout

This is a monorepo for **Polite**, an insurance policy management app. Two top-level apps:

- `backend/` — FastAPI + SQLAlchemy + PostgreSQL API. Originated from the `polite-server` repo and was added here via `git subtree` (see initial commits).
- `frontend/` — React 19 + Vite + TypeScript SPA. Originated from `polite-client-web`, also subtree-merged.

The two apps communicate at runtime via HTTP; in dev the frontend points at the backend through `VITE_API_BASE_URL` (default `http://localhost:8000/api`).

## Common commands

### Backend (`cd backend`)
```bash
python -m venv venv && source venv/bin/activate  # one-time
pip install -r requirements.txt

fastapi dev src/main.py          # dev server with reload (http://localhost:8000)
python scripts/seed_db.py        # DROPS and recreates all tables, then seeds demo data
docker compose up -d             # spins up Prometheus + Grafana + Alertmanager (NOT the API)
```
Tables are auto-created on app startup via `Base.metadata.create_all` in `src/main.py` — there is no Alembic. Schema changes require dropping the DB or re-running `seed_db.py`.

Production runs Gunicorn under systemd (`gunicorn.service`); CI deploy is `.github/workflows/deploy.yml` which SSH's to the prod host and restarts the `api` service.

### Frontend (`cd frontend`)
```bash
npm install
npm run dev      # Vite dev server (http://localhost:5173)
npm run build    # tsc -b && vite build
npm run lint     # eslint .

# Regenerate API types from the running backend's OpenAPI schema:
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/openapi.ts
```
There is no test suite in either app.

## Architecture

### Backend

- Entry point `src/main.py` mounts six v1 routers under `/api`: `auth`, `user`, `role`, `permission`, `contact`, `policy`. All live in `src/routers/v1/`.
- `src/models.py` — SQLAlchemy ORM. Core entities: `Organization`, `User`, `Role`, `Permission`, `Contact`, `Policy`. `User<->Role` and `Role<->Permission` are many-to-many (`user_roles`, `role_permissions`).
- `src/schemas.py` — Pydantic request/response models. Naming convention: `XBase` / `XCreate` / `XPublic`.
- `src/security.py` — JWT auth (HS256 via `python-jose`), bcrypt via `passlib`. Two parallel auth stacks coexist:
  - **Basic auth** (active): `OAuth2PasswordBearer` at `/api/v1/auth/login`. `get_current_user` decodes the JWT, attaches `permissions` and `organization_id` from the token claims onto the user object.
  - **Auth0** (commented out throughout the codebase, planned): `get_current_user_auth0` validates RS256 tokens against Auth0's JWKS. Frontend has matching commented-out `Auth0Provider` wiring in `src/main.tsx`.
- `src/database.py` — single SQLAlchemy `engine`/`SessionLocal`. `get_db()` is the FastAPI dependency.
- Observability: `prometheus-fastapi-instrumentator` exposes `/metrics`; the `docker-compose.yml` at backend root runs the Prometheus/Grafana/Alertmanager stack independently.

### Multi-tenancy and RBAC (load-bearing pattern)

Every request is scoped to the user's `organization_id`, which is **read from the JWT, not the request body**. When creating resources, handlers explicitly inject it:
```python
data["organization_id"] = current_user.organization_id
```
List/get/update queries always filter by `Model.organization_id == current_user.organization_id`. Preserve this on any new endpoint touching org-scoped tables (`Contact`, `Policy`, `User`).

Permissions are strings of the form `action:resource` (e.g. `create:policies`, `delete:roles`). The login handler in `routers/v1/auth.py` aggregates them from `user.roles[*].permissions` into the `permissions` JWT claim. Most write endpoints currently inline the check:
```python
if "create:policies" not in current_user.permissions:
    raise HTTPException(status_code=403, ...)
```
A `security.check_permission` helper exists but is not consistently used — match the surrounding handler's style when editing.

### Frontend

- **Routing**: TanStack Router with file-based routes in `src/routes/`. `src/routeTree.gen.ts` is **auto-generated** by `@tanstack/router-plugin/vite` — never hand-edit it; add files under `src/routes/` and the dev server regenerates it. Dynamic segments use `$param.tsx` (e.g. `dashboard/policies/$policyId.tsx`).
- **Data fetching**: TanStack Query (`@tanstack/react-query`). `QueryClient`, `AuthProvider`, and Chakra `Provider` wrap the app in `src/main.tsx`.
- **Auth**: `src/context/AuthContext.tsx` stores the bearer token in `localStorage` under `"token"` and exposes `useAuth()`. Most fetches are inline `fetch()` calls in route components that read `token` from `useAuth()` and send `Authorization: Bearer ${token}`. There is no global API client — `src/services/` only contains `authService.ts` and `userService.ts`.
- **Types from API**: `src/types/openapi.ts` is generated from the backend's OpenAPI schema. Components import request/response types like:
  ```ts
  type FormData = paths["/api/v1/policies/"]["post"]["requestBody"]["content"]["application/json"]
  ```
  Regenerate `openapi.ts` after backend schema changes.
- **UI**: Chakra UI v3 (`@chakra-ui/react`). Forms use `react-hook-form`. Path alias `@/*` → `src/*` (configured in `tsconfig.app.json` + `vite-tsconfig-paths`).

### Required env vars

Backend (`.env` in `backend/`): `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_URL`, and (for the dormant Auth0 path) `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `AUTH0_ALGORITHM`.

Frontend (`.env` in `frontend/`, see `.env.sample`): `VITE_API_BASE_URL`, plus `VITE_AUTH0_*` if enabling Auth0.

### Seed credentials

`scripts/seed_db.py` creates two demo users: `admin/admin` (full permissions, org `org_polite`) and `guest/guest` (limited contact/policy create+update, org `org_guest`). The frontend login screen has a "Continue as guest" button that submits these credentials.
