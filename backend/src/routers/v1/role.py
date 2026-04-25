from fastapi import status, HTTPException, Depends, APIRouter, Response
from typing import Annotated
from src import models, schemas, security
from sqlalchemy.orm import Session
from src.database import get_db
from typing import List

v1_router = APIRouter(
    prefix="/v1/roles",
    tags=["Roles"]
)

# Get All Roles
@v1_router.get("/")
async def get_roles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    roles = db.query(models.Role).offset(skip).limit(limit).all()
    return roles

# Create a Role
@v1_router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.RolePublic)
async def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    # Check permissions
    user_permissions = current_user.permissions
    if "create:roles" not in user_permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
    
    new_role = models.Role(**role.model_dump())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

# Get Role with id
@v1_router.get("/{role_id}", response_model=schemas.RolePublic)
async def get_role(role_id: int, db: Session = Depends(get_db)):
    role  = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id:  {role_id} not found")
    return role

# Delete Role with id
@v1_router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    # Check permissions
    user_permissions = current_user.permissions
    if "delete:roles" not in user_permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
    
    role_query = db.query(models.Role).filter(models.Role.id == role_id)
    role = role_query.first()
    if role == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} does not exist")
    role_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Update Role with id
@v1_router.put("/{role_id}", response_model=schemas.RolePublic)
def update_role(role_id: int, updated_role: schemas.RoleCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    # Check permissions
    user_permissions = current_user.permissions
    if "update:roles" not in user_permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
    
    role_query = db.query(models.Role).filter(models.Role.id == role_id)
    role = role_query.first()
    if role == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} does not exist")
    role_query.update(updated_role.model_dump(), synchronize_session=False)
    db.commit()
    return role_query.first()

# === Role Permissions ===
# # Add permission to role
# @v1_router.post("/{role_id}/permissions/{permission_id}")
# def add_permission_to_role(role_id: int, permission_id: int, db: Session = Depends(get_db), current_user = Depends(security.get_current_user)):
#     role = db.query(models.Role).filter(models.Role.id == role_id).first()
#     if not role:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} does not exist")
#     permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
#     if not permission:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Permission with id: {permission_id} does not exist")
#     if permission not in role.permissions:
#         role.permissions.append(permission)
#         db.commit()
#         return {"message": f"Permission '{permission.name}' assigned to role '{role.name}'"}
#     else:
#         return {"message": f"Permission '{permission.name}' already assigned to role '{role.name}'"}

# Get all Permissions for a Role
@v1_router.get("/{role_id}/permissions", response_model=List[schemas.PermissionWithAssignment])
def get_role_permissions(role_id: int, db: Session = Depends(get_db)):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} not found")

    # Fetch all permissions and check if assigned to role
    all_permissions = db.query(models.Permission).all()
    assigned_permission_ids = {permission.id for permission in role.permissions}

    permissions_with_assignment: List[schemas.PermissionWithAssignment] = []

    for permission in all_permissions:
        is_assigned = permission.id in assigned_permission_ids
        permissions_with_assignment.append(schemas.PermissionWithAssignment(id=permission.id, name=permission.name, assigned=is_assigned))
    
    return permissions_with_assignment


# Batch assign/remove permissions for a role
@v1_router.post("/{role_id}/permissions")
def update_role_permissions(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db)
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    new_permissions = db.query(models.Permission).filter(models.Permission.id.in_(permission_ids)).all()
    role.permissions = new_permissions  # Replaces all existing permissions
    db.commit()
    return {"message": "Permissions updated successfully"}