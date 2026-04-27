from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src import models, schemas
from src.database import get_tenant_db
from src.security import get_current_active_user, require_permission

v1_router = APIRouter(prefix="/v1/contacts", tags=["contacts"])


@v1_router.get(
    "/",
    response_model=List[schemas.ContactPublic],
    dependencies=[Depends(require_permission("org:contacts:read"))],
)
def list_contacts(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    return (
        db.query(models.Contact)
        .filter(models.Contact.organization_id == current_user.organization_id)
        .order_by(models.Contact.id.desc())
        .all()
    )


@v1_router.get(
    "/{contact_id}",
    response_model=schemas.ContactPublic,
    dependencies=[Depends(require_permission("org:contacts:read"))],
)
def get_contact(
    contact_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    c = (
        db.query(models.Contact)
        .filter(
            models.Contact.id == contact_id,
            models.Contact.organization_id == current_user.organization_id,
        )
        .one_or_none()
    )
    if c is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return c


@v1_router.post(
    "/",
    response_model=schemas.ContactPublic,
    status_code=201,
    dependencies=[Depends(require_permission("org:contacts:create"))],
)
def create_contact(
    payload: schemas.ContactCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    data = payload.model_dump()
    data["organization_id"] = current_user.organization_id
    obj = models.Contact(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@v1_router.put(
    "/{contact_id}",
    response_model=schemas.ContactPublic,
    dependencies=[Depends(require_permission("org:contacts:update"))],
)
def update_contact(
    contact_id: int,
    payload: schemas.ContactCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    c = (
        db.query(models.Contact)
        .filter(
            models.Contact.id == contact_id,
            models.Contact.organization_id == current_user.organization_id,
        )
        .one_or_none()
    )
    if c is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@v1_router.delete(
    "/{contact_id}",
    status_code=204,
    dependencies=[Depends(require_permission("org:contacts:delete"))],
)
def delete_contact(
    contact_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_tenant_db),
):
    c = (
        db.query(models.Contact)
        .filter(
            models.Contact.id == contact_id,
            models.Contact.organization_id == current_user.organization_id,
        )
        .one_or_none()
    )
    if c is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(c)
    db.commit()
    return None
