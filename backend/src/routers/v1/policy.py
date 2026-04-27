from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src import models, schemas
from src.database import get_tenant_db
from src.security import get_current_active_user, require_permission

v1_router = APIRouter(prefix="/v1/policies", tags=["policies"])


@v1_router.get(
    "/",
    response_model=List[schemas.PolicyPublic],
    dependencies=[Depends(require_permission("org:policies:read"))],
)
def list_policies(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    return (
        db.query(models.Policy)
        .filter(models.Policy.organization_id == current_user.organization_id)
        .order_by(models.Policy.id.desc())
        .all()
    )


@v1_router.get(
    "/{policy_id}",
    response_model=schemas.PolicyPublic,
    dependencies=[Depends(require_permission("org:policies:read"))],
)
def get_policy(
    policy_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    p = (
        db.query(models.Policy)
        .filter(
            models.Policy.id == policy_id,
            models.Policy.organization_id == current_user.organization_id,
        )
        .one_or_none()
    )
    if p is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return p


@v1_router.post(
    "/",
    response_model=schemas.PolicyPublic,
    status_code=201,
    dependencies=[Depends(require_permission("org:policies:create"))],
)
def create_policy(
    payload: schemas.PolicyCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    data = payload.model_dump()
    data["organization_id"] = current_user.organization_id
    if data.get("policyholder_id") is not None:
        contact = (
            db.query(models.Contact)
            .filter(
                models.Contact.id == data["policyholder_id"],
                models.Contact.organization_id == current_user.organization_id,
            )
            .one_or_none()
        )
        if contact is None:
            raise HTTPException(
                status_code=400, detail="policyholder_id does not belong to this organization"
            )
    obj = models.Policy(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@v1_router.put(
    "/{policy_id}",
    response_model=schemas.PolicyPublic,
    dependencies=[Depends(require_permission("org:policies:update"))],
)
def update_policy(
    policy_id: int,
    payload: schemas.PolicyCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    p = (
        db.query(models.Policy)
        .filter(
            models.Policy.id == policy_id,
            models.Policy.organization_id == current_user.organization_id,
        )
        .one_or_none()
    )
    if p is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@v1_router.delete(
    "/{policy_id}",
    status_code=204,
    dependencies=[Depends(require_permission("org:policies:delete"))],
)
def delete_policy(
    policy_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    p = (
        db.query(models.Policy)
        .filter(
            models.Policy.id == policy_id,
            models.Policy.organization_id == current_user.organization_id,
        )
        .one_or_none()
    )
    if p is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(p)
    db.commit()
    return None
