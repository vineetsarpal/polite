from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, List
from src.database import get_db
from src import schemas, models, utils, config
from fastapi import Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError
# from fastapi_auth0 import Auth0
from jose import jwt, JWTError
import os
import httpx

# === Auth0 ===
# auth0 = Auth0(
#     domain=config.AUTH0_DOMAIN,
#     api_audience=config.AUTH0_AUDIENCE,
#     scopes={'read:messages': ''}
# )

bearer_scheme = HTTPBearer()

async def get_jwk():
    async with httpx.AsyncClient() as client:
        url = f"https://{config.AUTH0_DOMAIN}/.well-known/jwks.json"
        res = await client.get(url)
        res.raise_for_status()
        return res.json()

async def get_current_user_auth0(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    token = credentials.credentials
    if not credentials:
        return None # No bearer token provided, so Auth0 can't authenticate.
    try:
        jwks = await get_jwk()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
            )
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=config.AUTH0_ALGORITHM,
            audience=config.AUTH0_AUDIENCE,
            issuer=f"https://{config.AUTH0_DOMAIN}/",
        )
        # payload now contains all user claims, including 'sub'
        return payload
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e


# === Basic Auth ===
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/v1/auth/login')

def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    if not utils.verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[Optional[str], Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    if not token:
        return None # No token provided for Basic Auth
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract username, organization, permissions from JWT
        username = payload.get("sub")
        organization_id: int | None = payload.get("organization_id")
        permissions: List[str] = payload.get("permissions", [])

        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username, permissions=permissions, organization_id=organization_id)

    except InvalidTokenError:
        raise credentials_exception
    except Exception as e:
        print(f"Basic Auth validation error: {e}") 
        raise credentials_exception from e
    
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    
    # Attach permissions and organization to user object
    user.permissions = permissions
    user.organization_id = organization_id
    
    return user

async def get_current_active_user(current_user: schemas.UserPublic = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


# === Check Permission ===
async def check_permission(permission_to_check: str, user_permissions: List[str]):
    if permission_to_check not in user_permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
    return True

# === Future: Common func to try both auth0 and basic auth and return user ===
