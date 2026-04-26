import os
from dotenv import load_dotenv

load_dotenv()

# Existing app settings
SECRET_KEY = os.getenv("SECRET_KEY")  # legacy; will be removed once login route is deleted
ALGORITHM = os.getenv("ALGORITHM")
DATABASE_URL = os.getenv("DATABASE_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Auth0 (dormant — will be removed in a later task)
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
AUTH0_ALGORITHM = os.getenv("AUTH0_ALGORITHM")

# Clerk
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")
