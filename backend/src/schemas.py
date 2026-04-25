from typing import Annotated, List, Optional, Union
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, date

# === Token Schemas ===
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    organization_id: str | None = None
    permissions: List[str] = []

# === Auth0 ===
class Auth0Payload(BaseModel):
    # This schema defines the expected structure of the Auth0 JWT payload you want to return
    sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    permissions: Optional[List[str]] = None
    # Add other common claims like 'aud', 'iss', 'exp', etc. if you want to use them
    
# Organization Schemas ===
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationPublic(OrganizationBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# === User Schemas ===
class UserBase(BaseModel):
    username: str
    email: EmailStr | None = None
    full_name: str | None = None

class UserCreate(UserBase):
    pass

class UserPublic(UserBase):
    id: int
    is_active: bool | None = True

    created_at: datetime 
    updated_at: datetime
    

    model_config = ConfigDict(from_attributes=True)

class CurrentUser(UserPublic):
    permissions: List[str] = []
    organization_id: str | None = None


# === Permission Schemas ===
class PermissionBase(BaseModel):
    name: str
    description: str | None = None

class PermissionCreate(PermissionBase):
    pass


class PermissionPublic(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

class PermissionWithAssignment(PermissionBase):
    id: int
    assigned: bool


# === Role Schemas ===
class RoleBase(BaseModel):
    name: str
    description: str | None = None

class RoleCreate(RoleBase):
    pass

class RolePublic(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    users: List[UserPublic] = []
    permissions: List[PermissionPublic] = []

    model_config = ConfigDict(from_attributes=True)

class RoleWithAssignment(RoleBase):
    id: int
    assigned: bool | None = None


# === Contact Schemas ===
class ContactBase(BaseModel):
    type: str
    first_name: str
    last_name: str
    email: EmailStr | None = None
    dob: date | None = None

class ContactCreate(ContactBase):
    pass

class ContactPublic(ContactBase):
    id: int
    organization_id: str | None = None
    is_active: bool | None = True

    model_config = ConfigDict(from_attributes=True)


# === Policy Schemas ===
class PolicyBase(BaseModel):
    lob: str
    status: str | None = "active"

    # Premium
    base_premium: float
    net_premium: float
    tax: float  
    sum_insured: float
    
    # Data Capture
    license_plate: str
    vin: str

    start_date: datetime
    end_date: datetime

    policyholder_id: int
    

class PolicyCreate(PolicyBase):
    pass

class PolicyPublic(PolicyBase):
    id: int
    organization_id: str
    
    model_config = ConfigDict(from_attributes=True)