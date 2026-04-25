from fastapi import status, HTTPException, Depends, APIRouter, Response, Security
from typing import Annotated, List
from src import models, schemas, security
from sqlalchemy.orm import Session
from src.database import get_db

v1_router = APIRouter(
    prefix="/v1/contacts",
    tags=["Contacts"]
)

# === Get All Contacts ===
@v1_router.get("/", response_model=List[schemas.ContactPublic])
async def get_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    contacts = db.query(models.Contact).filter(models.Contact.organization_id == current_user.organization_id).offset(skip).limit(limit).all()
    return contacts


# === Create a Contact ===
# Auth0
# @v1_router.post("/", 
#                 status_code=status.HTTP_201_CREATED, 
#                 response_model=schemas.ContactPublic,
#                 dependencies=[Depends(security.auth0.implicit_scheme)])
# async def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user_auth0 = Depends(security.get_current_user_auth0)):
#     # Check Auth0 permissions
#     permissions: List[str] = current_user_auth0["permissions"]
#     if "create:contacts" not in permissions:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
    
#     new_contact = models.Contact(**contact.model_dump(), created_by = current_user_auth0["sub"])
#     db.add(new_contact)
#     db.commit()
#     db.refresh(new_contact)
#     return new_contact

# Basic Auth
@v1_router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ContactPublic)
async def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    # Check permissions
    user_permissions = current_user.permissions
    if "create:contacts" not in user_permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")
    # new_contact = models.Contact(**contact.model_dump(), updated_by=current_user.id)

    # Inject organization_id from token
    contact_data = contact.model_dump()
    contact_data["organization_id"] = current_user.organization_id 

    new_contact = models.Contact(**contact_data)
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact


# === Get Contact with id ===
@v1_router.get("/{contact_id}", response_model=schemas.ContactPublic)
async def get_contact(contact_id: int, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    contact  = db.query(models.Contact).filter(
        models.Contact.organization_id == current_user.organization_id,
        models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact with id: {contact_id} not found")
    return contact


# # === Delete Contact with id ===
# @v1_router.delete("/{contact_id}", dependencies=[Depends(security.auth0.implicit_scheme)])
# def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user_auth0 = Depends(security.get_current_user_auth0)):
#     # Check Auth0 permissions
#     permissions: List[str] = current_user_auth0["permissions"]
#     if "delete:contacts" not in permissions:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")

#     contact_query = db.query(models.Contact).filter(models.Contact.id == contact_id)
#     contact = contact_query.first()
#     if contact == None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact with id: {contact_id} does not exist")
#     contact_query.delete(synchronize_session=False)
#     db.commit()
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


# # === Update Contact with id ===
# Auth0
# @v1_router.put("/{contact_id}", response_model=schemas.ContactPublic)
# def update_contact(contact_id: int, updated_contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user_auth0 = Depends(security.get_current_user_auth0)):
#     # Check Auth0 permissions
#     permissions: List[str] = current_user_auth0["permissions"]
#     if "update:contacts" not in permissions:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")

#     contact_query = db.query(models.Contact).filter(models.Contact.id == contact_id)
#     contact = contact_query.first()
#     if contact == None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact with id: {contact_id} does not exist")
#     update_data = updated_contact.model_dump()
#     update_data["updated_by"] = current_user_auth0["sub"]
#     contact_query.update(update_data, synchronize_session=False)
#     db.commit()
#     return contact_query.first()

@v1_router.put("/{contact_id}", response_model=schemas.ContactPublic)
def update_contact(contact_id: int, updated_contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(security.get_current_active_user)):
    # Check permissions
    permissions = current_user.permissions
    if "update:contacts" not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to perform this action!")

    contact_query = db.query(models.Contact).filter(
        models.Contact.id == contact_id,
        models.Contact.organization_id == current_user.organization_id)
    
    contact = contact_query.first()
    if contact == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact with id: {contact_id} does not exist")
    update_data = updated_contact.model_dump(exclude_unset=True)
    # update_data["updated_by"] = current_user.id
    contact_query.update(update_data, synchronize_session=False)
    db.commit()
    return contact_query.first()
