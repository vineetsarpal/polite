# Polite API

A modular FastAPI backend for managing insurance policies.

## Features

- **Policy Management:** Issue, update, and view policies.
- **Dynamic Covers & Rates:** Configure product-specific and rates with effective dates.
- **Authentication:** Secure endpoints with JWT-based authentication.
- **Role-Based Access:** Restrict actions by user roles (admin, agent, customer). *(Coming Soon)*
- **Audit Trail:** Track changes to policies. *(Coming Soon)*

## Getting Started

1. **Clone the repository**
    ```
    git clone https://github.com/vineetsarpal/polite-server.git
    cd polite-server
    ```

2. **Create and activate a virtual environment**
    ```
    python -m venv venv
    # On Linux/macOS
    source venv/bin/activate

    # On Windows
    venv\Scripts\activate
    ```

3. **Install dependencies**
    ```
    pip install -r requirements.txt
    ```

4. **Configure environment variables**
    - Copy `.env.example` to `.env` and update values.

5. **Start the FastAPI server**
    ```
    fastapi dev main.py
    ```

6. **API Overview**  
    Access the interactive docs:
    Open [http://localhost:8000/docs](http://localhost:8000/docs)


## Project Structure

- `src/routers` – API route definitions
- `src/models.py` – SQLAlchemy ORM models
- `src/schemas.py` – Pydantic schemas
- `src/database.py` – Database connection and session management

## Frontend
Repo for the React frontend
- [polite-client-web](https://github.com/vineetsarpal/polite-client-web)
