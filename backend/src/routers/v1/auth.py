from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from src import schemas, models, security
from src.database import get_db
from datetime import timedelta
import os

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

v1_router = APIRouter(
    prefix='/v1/auth',
    tags=['Auth']
)

@v1_router.post("/login")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)) -> schemas.Token:
    user = security.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get all unique permissions associated with the user's roles
    permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.name)
    user_permissions = list(permissions)

    # Add organization id to token
    organization_id = None
    if user.organization:
        organization_id = user.organization_id

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    tokenData = {
        "sub": user.username,
        "permissions": user_permissions,
        "organization_id": organization_id
    }
    access_token = security.create_access_token(data=tokenData, expires_delta=access_token_expires)
    return schemas.Token(access_token=access_token, token_type="bearer")

@v1_router.get("/users/me/", response_model=schemas.UserPublic)
async def read_users_me(current_user: Annotated[schemas.UserPublic, Depends(security.get_current_active_user)],):
    return current_user


# @router.post('/login', response_model=schemas.Token)
# def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

#     user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

#     if not utils.verify_password(user_credentials.password, user.password):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

#     # Create a token
#     access_token = security.create_access_token(data={"user_id": user.id})

#     # Return a Token
#     return {"access_token": access_token, "token_type": "bearer"}`