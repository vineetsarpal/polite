# Polite — Web Client

The React + Vite + TypeScript frontend for Polite, a modern, lightweight Insurance Policy Management platform.

> This directory is part of the [Polite monorepo](../README.md). It was originally the standalone [`polite-client-web`](https://github.com/vineetsarpal/polite-client-web) repo and was folded in via `git subtree`. See the [root README](../README.md) for the full architecture, demo credentials, and deployment notes.

## Features

- User authentication (JWT, stored in `localStorage` via `AuthContext`)
- Continue as a guest user
- Create, view, and edit policies and contacts
- Multi-tenant: data is scoped to the logged-in user's organization
- Type-safe API calls via types generated from the backend's OpenAPI schema
- Responsive, Chakra UI–based interface

## Live Demo

**[https://polite-client-web.pages.dev](https://polite-client-web.pages.dev)**

## Backend API

This client talks to the FastAPI backend in [`../backend`](../backend) (same repo). The API base URL is configured via `VITE_API_BASE_URL` and defaults to `http://localhost:8000/api`.

## Getting Started

From the monorepo root:

1. **Install dependencies**
    ```bash
    cd frontend
    npm install
    ```

2. **Configure environment**
    ```bash
    cp .env.sample .env
    ```
    Set `VITE_API_BASE_URL` (e.g. `http://localhost:8000/api`).

3. **Run the app**
    ```bash
    npm run dev
    ```

4. **Access the app**
    - Open [http://localhost:5173](http://localhost:5173).

5. **Regenerate API types from the running backend**
    Keep `src/types/openapi.ts` in sync after backend schema changes:
    ```bash
    npx openapi-typescript http://localhost:8000/openapi.json -o src/types/openapi.ts
    ```

## Project Notes

- **Routing:** TanStack Router with file-based routes in `src/routes/`. `src/routeTree.gen.ts` is **auto-generated** — never hand-edit it.
- **Data fetching:** TanStack Query, plus inline `fetch()` calls in route components that read the bearer token from `useAuth()`.
- **UI:** Chakra UI v3, forms via `react-hook-form`.
- **Path alias:** `@/*` → `src/*`.
