from fastapi import status, HTTPException, Depends, APIRouter, Response
from typing import Annotated, List
from src import models, schemas, security
from sqlalchemy.orm import Session
from src.database import get_db

v1_router = APIRouter(
    prefix="/v1/policies",
    tags=["Policies"]
)

# Get All Policies
@v1_router.get("/", response_model=List[schemas.PolicyPublic])
async def get_policies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    policies = db.query(models.Policy).filter(models.Policy.organization_id == current_user.organization_id).offset(skip).limit(limit).all()
    return policies

# Create a Policy
@v1_router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PolicyPublic)
async def create_policy(policy: schemas.PolicyCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    # Check permissions
    user_permissions = current_user.permissions
    if "create:policies" not in user_permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
    
    # Inject organization_id from token
    policy_data = policy.model_dump()
    policy_data["organization_id"] = current_user.organization_id 

    new_policy = models.Policy(**policy_data)
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return new_policy

# Get Policy with id
@v1_router.get("/{policy_id}", response_model=schemas.PolicyPublic)
async def get_policy(policy_id: int, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    policy  = db.query(models.Policy).filter(models.Policy.organization_id == current_user.organization_id).filter(models.Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy with id:  {policy_id} not found")
    return policy

# Delete Policy with id
@v1_router.delete("/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    # Check permissions
    user_permissions = current_user.permissions
    if "delete:policies" not in user_permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
        
    policy_query = db.query(models.Policy).filter(models.Policy.id == policy_id)
    policy = policy_query.first()
    if policy == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy with id: {policy_id} does not exist")
    if policy.policyholder_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    policy_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Update Policy with id
@v1_router.put("/{policy_id}", response_model=schemas.PolicyPublic)
def update_policy(policy_id: int, updated_policy: schemas.PolicyCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    # Check permissions
    user_permissions = current_user.permissions
    if "update:policies" not in user_permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
    
    policy_query = db.query(models.Policy).filter(models.Policy.organization_id == current_user.organization_id).filter(models.Policy.id == policy_id)
    policy = policy_query.first()
    if policy == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy with id: {policy_id} does not exist")
    if policy.policyholder_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    policy_query.update(updated_policy.model_dump(), synchronize_session=False)
    db.commit()
    return policy_query.first()
