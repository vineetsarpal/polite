from datetime import datetime, date
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, ConfigDict


# === Organization ===
class OrganizationBase(BaseModel):
    id: str
    name: str
    slug: Optional[str] = None


class OrganizationPublic(OrganizationBase):
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# === User ===
class UserBase(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserPublic(UserBase):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Membership ===
class MembershipPublic(BaseModel):
    id: str
    user_id: str
    organization_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrgMember(BaseModel):
    """User listed within their org (joins users + memberships)."""
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    membership_id: str
    membership_created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Contact ===
class ContactBase(BaseModel):
    type: Optional[Literal["individual", "company"]] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    dob: Optional[date] = None
    is_active: bool = True


class ContactCreate(ContactBase):
    pass


class ContactPublic(ContactBase):
    id: int
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Policy ===
class PolicyBase(BaseModel):
    lob: Optional[str] = None
    status: Optional[str] = "active"
    base_premium: Optional[float] = None
    net_premium: Optional[float] = None
    tax: Optional[float] = None
    sum_insured: Optional[float] = None
    license_plate: Optional[str] = None
    vin: Optional[str] = None
    start_date: datetime
    end_date: datetime
    policyholder_id: Optional[int] = None


class PolicyCreate(PolicyBase):
    pass


class PolicyPublic(PolicyBase):
    id: int
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
