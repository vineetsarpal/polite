# Polite — Web Client

The React + Vite + TypeScript frontend for Polite, a modern, lightweight Insurance Policy Management platform.

> This directory is part of the [Polite monorepo](../README.md). It was originally the standalone [`polite-client-web`](https://github.com/vineetsarpal/polite-client-web) repo and was folded in via `git subtree`. See the [root README](../README.md) for the full architecture, demo credentials, and deployment notes.

## Features

- User authentication via Clerk (`@clerk/clerk-react`)
- Create, view, and edit policies and contacts
- Multi-tenant: data is scoped to the logged-in user's Clerk organization
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
    Set `VITE_API_BASE_URL` (e.g. `http://localhost:8000/api`) and `VITE_CLERK_PUBLISHABLE_KEY` (see below).

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

## Authentication (Clerk)

Set in `frontend/.env`:

```
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

(Same value as the backend's `CLERK_PUBLISHABLE_KEY` — get it from Clerk dashboard → Configure → API Keys.)

The app uses `@clerk/clerk-react` for sign-in/sign-up, organization management, and `<Protect>` for permission-gated UI. Backend tokens are injected automatically via the `useApiClient` hook (`src/lib/apiClient.ts`).

## Project Notes

- **Routing:** TanStack Router with file-based routes in `src/routes/`. `src/routeTree.gen.ts` is **auto-generated** — never hand-edit it. Sign-in and sign-up live at `/sign-in` and `/sign-up`.
- **Data fetching:** TanStack Query, using the `useApiClient` hook for authenticated requests.
- **UI:** Chakra UI v3, forms via `react-hook-form`.
- **Path alias:** `@/*` → `src/*`.
