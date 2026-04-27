import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from src.routers.v1 import contact, policy, user
from src.routers.webhooks import clerk as clerk_webhook

load_dotenv()

app = FastAPI(title="Polite API")

API_BASE_PREFIX = "/api"

# Prometheus
Instrumentator().instrument(app).expose(app)

# Static
current_dir = os.path.dirname(__file__)
public_dir = os.path.abspath(os.path.join(current_dir, "..", "public", "images"))
app.mount("/static", StaticFiles(directory=public_dir), name="static")

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join(public_dir, "favicon.ico"))


@app.get("/")
async def root():
    return {"message": "Hello World!"}


# Routers
app.include_router(user.v1_router, prefix=API_BASE_PREFIX)
app.include_router(contact.v1_router, prefix=API_BASE_PREFIX)
app.include_router(policy.v1_router, prefix=API_BASE_PREFIX)
app.include_router(clerk_webhook.v1_router, prefix=API_BASE_PREFIX)
