# Polite API

A modular FastAPI backend for managing insurance policies.

> This directory is part of the [Polite monorepo](../README.md). It was originally the standalone [`polite-server`](https://github.com/vineetsarpal/polite-server) repo and was folded in via `git subtree`. See the [root README](../README.md) for the full architecture, RBAC model, deployment notes, and demo credentials.

## Features

- **Policy Management:** Issue, update, and view policies.
- **Dynamic Covers & Rates:** Configure product-specific covers and rates with effective dates.
- **Authentication:** Secure endpoints with JWT-based authentication.
- **Role-Based Access:** Permissions of the form `action:resource`, aggregated from a user's roles into the JWT.
- **Multi-tenancy:** Every request is scoped to the user's `organization_id` from the token.
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
    - Create `.env` with `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_URL`. See the [root README](../README.md#2-backend) for a full example.

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

## Project Structure

- `src/routers/v1/` – API route definitions (`auth`, `user`, `role`, `permission`, `contact`, `policy`)
- `src/models.py` – SQLAlchemy ORM models
- `src/schemas.py` – Pydantic schemas
- `src/security.py` – JWT auth, password hashing, RBAC helpers
- `src/database.py` – Database connection and session management
- `scripts/seed_db.py` – Drops, recreates, and seeds demo data
- `docker-compose.yml` – Prometheus + Grafana + Alertmanager stack (does **not** run the API itself)

## Frontend

The React web client lives in [`../frontend`](../frontend) within this same repo.
