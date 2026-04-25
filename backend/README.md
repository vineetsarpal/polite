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

1. **Create and activate a virtual environment**
    ```bash
    cd backend
    python -m venv venv
    # On Linux/macOS
    source venv/bin/activate
    # On Windows
    venv\Scripts\activate
    ```

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure environment variables**
    - Create `.env` with `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_URL`. See the [root README](../README.md#2-backend) for a full example.

4. **Seed the database** (drops and recreates all tables, then loads demo data)
    ```bash
    python scripts/seed_db.py
    ```

5. **Start the FastAPI server**
    ```bash
    fastapi dev src/main.py
    ```

6. **API Overview**
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
