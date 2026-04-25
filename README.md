# Polite

A modern, lightweight insurance policy management platform.

This monorepo contains both the API server and the web client:

- [`backend/`](./backend) — FastAPI + SQLAlchemy + PostgreSQL
- [`frontend/`](./frontend) — React 19 + Vite + TypeScript (TanStack Router/Query, Chakra UI v3)

**Live demo:** [https://polite-client-web.pages.dev](https://polite-client-web.pages.dev)

---

## Features

- Policy lifecycle: issue, view, update, and delete insurance policies
- Contact (policyholder) management — individuals and companies
- JWT-based authentication with bcrypt password hashing
- Role-based access control: users → roles → permissions (many-to-many)
- Multi-tenant data isolation via `organization_id` scoped from the JWT
- "Continue as guest" demo login for trying the app without signup
- Prometheus metrics endpoint and an optional Grafana/Alertmanager monitoring stack
- Auth0 integration scaffolded (currently commented out) alongside the built-in auth

## Tech stack

| Layer       | Tools                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------- |
| API         | FastAPI, SQLAlchemy 2, PostgreSQL (psycopg2), Pydantic v2, python-jose, passlib (bcrypt)     |
| Web         | React 19, Vite 6, TypeScript, TanStack Router, TanStack Query, Chakra UI v3, react-hook-form |
| Tooling     | `openapi-typescript` (typed API client from OpenAPI), ESLint, Gunicorn, Uvicorn              |
| Ops         | Prometheus, Grafana, Alertmanager (Docker Compose), GitHub Actions, Cloudflare Pages         |

## Repository layout

```
polite/
├── backend/         # FastAPI service (subtree of polite-server)
│   ├── src/
│   │   ├── main.py          # app + router wiring + CORS + metrics
│   │   ├── models.py        # SQLAlchemy ORM
│   │   ├── schemas.py       # Pydantic models
│   │   ├── security.py      # JWT, password hashing, RBAC helpers
│   │   ├── database.py      # engine + SessionLocal
│   │   └── routers/v1/      # auth, user, role, permission, contact, policy
│   ├── scripts/seed_db.py   # drops, recreates, and seeds demo data
│   ├── config/              # Prometheus / Alertmanager configs
│   ├── nginx/               # reverse-proxy reference config
│   ├── docker-compose.yml   # monitoring stack (NOT the API)
│   ├── gunicorn.service     # systemd unit for production
│   ├── pyproject.toml       # uv-managed deps
│   └── uv.lock
├── frontend/        # React SPA (subtree of polite-client-web)
│   ├── src/
│   │   ├── main.tsx
│   │   ├── routes/          # TanStack Router file-based routes
│   │   ├── components/      # Chakra-based UI
│   │   ├── context/         # AuthContext (token in localStorage)
│   │   ├── services/        # auth + user fetch helpers
│   │   ├── types/openapi.ts # generated from backend OpenAPI
│   │   ├── config/config.ts
│   │   └── routeTree.gen.ts # AUTO-GENERATED, do not edit
│   ├── vite.config.ts
│   ├── package.json
│   └── .env.sample
└── CLAUDE.md        # guidance for AI assistants working in this repo
```

## Architecture overview

### Auth & multi-tenancy

1. The user logs in via `POST /api/v1/auth/login` (OAuth2 password flow).
2. The server signs a JWT containing `sub` (username), `permissions`, and `organization_id`.
3. The frontend stores the token in `localStorage` (`AuthContext`) and sends it as `Authorization: Bearer <token>` on every request.
4. On the server, `get_current_active_user` decodes the JWT and attaches `permissions` and `organization_id` onto the user object.
5. **Every org-scoped query filters by `organization_id` from the token** (never from the request body), so users can only see/modify resources within their own organization.
6. Permission strings follow `action:resource` (e.g. `create:policies`, `delete:roles`); write endpoints check membership against `current_user.permissions`.

### RBAC model

```
User ──< user_roles >── Role ──< role_permissions >── Permission
```

Permissions are aggregated across all of a user's roles at login time and embedded in the JWT.

### Frontend ↔ backend type safety

The frontend imports request/response types directly from the backend's OpenAPI schema:

```ts
import { paths } from '@/types/openapi'
type Policy = paths['/api/v1/policies/{policy_id}']['get']['responses']['200']['content']['application/json']
```

Regenerate `src/types/openapi.ts` whenever the API schema changes (see commands below).

---

## Getting started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+ and npm
- PostgreSQL 14+ running locally (or a connection URL to a remote instance)

### 1. Clone

```bash
git clone https://github.com/vineetsarpal/polite.git
cd polite
```

### 2. Backend

```bash
cd backend
uv sync                                   # creates .venv/ and installs from uv.lock
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/polite
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
FRONTEND_URL=http://localhost:5173

# Optional, only needed if you re-enable the Auth0 path
AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_ALGORITHM=RS256
```

Seed the database with demo data (admin + guest users, sample contacts and policies):

```bash
uv run python scripts/seed_db.py
```

> ⚠️ `seed_db.py` **drops and recreates all tables**. There are no Alembic migrations — the schema is created on app startup via `Base.metadata.create_all`.

Run the API:

```bash
uv run fastapi dev src/main.py
```

The API is now at [http://localhost:8000](http://localhost:8000), interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs), and Prometheus metrics at [http://localhost:8000/metrics](http://localhost:8000/metrics).

### 3. Frontend

```bash
cd ../frontend
npm install
cp .env.sample .env                       # then edit values
```

Default `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_SERVER_URL=http://localhost:8000
# VITE_AUTH0_* values only needed if you enable Auth0
```

Run the web client:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Use the seeded credentials below or click **Continue as guest**.

### Demo credentials

| Username | Password | Organization | Permissions                                 |
| -------- | -------- | ------------ | ------------------------------------------- |
| `admin`  | `admin`  | `org_polite` | All `create/update/delete` on every resource |
| `guest`  | `guest`  | `org_guest`  | Create/update contacts and policies only     |

---

## Common commands

### Backend (`cd backend`)

| Command                              | What it does                                               |
| ------------------------------------ | ---------------------------------------------------------- |
| `uv sync`                            | Install/update dependencies from `uv.lock` into `.venv/`   |
| `uv add <pkg>` / `uv remove <pkg>`   | Add or remove a dependency (updates `pyproject.toml` + lock) |
| `uv run fastapi dev src/main.py`     | Run the API with hot reload                                |
| `uv run python scripts/seed_db.py`   | Drop, recreate, and seed all tables                        |
| `docker compose up -d`               | Start Prometheus + Grafana + Alertmanager (monitoring only) |
| `uv run gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000` | Production server (also defined in `gunicorn.service`) |

### Frontend (`cd frontend`)

| Command                                                                      | What it does                                |
| ---------------------------------------------------------------------------- | ------------------------------------------- |
| `npm run dev`                                                                | Vite dev server                             |
| `npm run build`                                                              | Type-check + production build               |
| `npm run lint`                                                               | ESLint                                      |
| `npm run preview`                                                            | Preview the production build locally        |
| `npx openapi-typescript http://localhost:8000/openapi.json -o src/types/openapi.ts` | Regenerate API types from the running backend |

---

## API surface

All endpoints are mounted under `/api` and versioned under `/v1`:

| Resource      | Path prefix             |
| ------------- | ----------------------- |
| Auth          | `/api/v1/auth`          |
| Users         | `/api/v1/users`         |
| Roles         | `/api/v1/roles`         |
| Permissions   | `/api/v1/permissions`   |
| Contacts      | `/api/v1/contacts`      |
| Policies      | `/api/v1/policies`      |

Full interactive documentation lives at `/docs` (Swagger UI) and `/redoc` when the server is running.

---

## Deployment

- **Backend** — Pushes to `main` trigger `.github/workflows/deploy.yml`, which SSHes to the production host, runs `git pull`, syncs dependencies via `uv sync --frozen`, and restarts the `api` systemd service plus the monitoring `docker compose` stack. The systemd unit is in `backend/gunicorn.service`; an Nginx reverse-proxy reference is in `backend/nginx/nginx.conf`.
- **Frontend** — Deployed to Cloudflare Pages at [polite-client-web.pages.dev](https://polite-client-web.pages.dev).

---

## Development notes

- **Schema changes** require dropping the database (or re-running `scripts/seed_db.py`) — there are no migrations yet.
- **`routeTree.gen.ts` is generated** by `@tanstack/router-plugin/vite`. Add files under `frontend/src/routes/` and the dev server will regenerate it; do not hand-edit.
- **Path alias**: `@/*` → `frontend/src/*` (configured in `tsconfig.app.json` + `vite-tsconfig-paths`).
- **Auth0 is scaffolded but disabled**. To enable it, uncomment the `Auth0Provider` in `frontend/src/main.tsx`, the `auth0` block in `backend/src/security.py`, and the related route dependencies — then provide the Auth0 env vars on both sides.
- **Roadmap** (from the original backend README): role-based access UI polish, full audit trail of policy changes.

## License

[MIT](./backend/LICENSE)
