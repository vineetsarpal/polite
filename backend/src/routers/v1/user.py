from fastapi import status, HTTPException, Depends, APIRouter
from src import models, schemas, utils, security
from sqlalchemy.orm import Session
from src.database import get_db
from typing import List

v1_router = APIRouter(
    prefix="/v1/users",
    tags=["Users"]
)

# Get All Users
@v1_router.get("/")
async def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    users = db.query(models.User).filter(models.User.organization_id == current_user.organization_id).offset(skip).limit(limit).all()
    return users

# Create User
@v1_router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserPublic)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # hash the password
    hashed_password = utils.hash_password(user.password)
    user.password = hashed_password

    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Get User with id
@v1_router.get("/{user_id}", response_model=schemas.UserPublic)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id: {user_id} not found")
    return user
    
# Update User with id
@v1_router.put("/{user_id}", response_model=schemas.UserPublic)
def update_user(user_id: int, updated_user: schemas.UserCreate, db: Session = Depends(get_db), current_user = Depends(security.get_current_user)):
    user_query = db.query(models.User).filter(models.User.id == user_id)
    user = user_query.first()
    if user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} does not exist")
    user_query.update(updated_user.model_dump(), synchronize_session=False)
    db.commit()
    return user_query.first()

# === User Roles ===
# # Add Role to User
# @v1_router.post("/{user_id}/roles/{role_id}")
# def add_role_to_user(user_id: int, role_id: int, db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} not found")
#     role = db.query(models.Role).filter(models.Role.id == role_id).first()
#     if not role:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} not found")
#     if role not in user.roles:
#         user.roles.append(role)
#         db.commit()
#         return {"message": f"Role '{role.name}' assigned to user '{user.id}'"}
#     else:
#         return {"message": f"Role '{role.name}' already assigned to user '{user.id}'"}

# Get all Roles for a User
@v1_router.get("/{user_id}/roles", response_model=List[schemas.RoleWithAssignment])
def get_user_roles(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} not found")
    
    # Fetch all roles and check if assigned to current user
    all_roles = db.query(models.Role).all()
    assigned_role_ids = { role.id for role in user.roles }

    roles_with_assignment: List[schemas.RoleWithAssignment] = []

    for role in all_roles:
        is_assigned = role.id in assigned_role_ids
        roles_with_assignment.append(schemas.RoleWithAssignment(id=role.id, name=role.name, assigned=is_assigned))
    
    return roles_with_assignment

# Assign/Remove Roles for a User in batch
@v1_router.post("/{user_id}/roles")
def update_user_roles(user_id: int, role_ids: List[int], db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_roles = db.query(models.Role).filter(models.Role.id.in_(role_ids)).all()
    user.roles = new_roles  # Replaces all existing roles
    db.commit()
    return {"message": "Roles updated successfully"}