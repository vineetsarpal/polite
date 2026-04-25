from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Table, Date
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from src.database import Base
from typing import Literal

# Association table for many-to-many User <-> Role
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("role_id", Integer, ForeignKey("roles.id")),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=text('now()')),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))
)

# Association table for many-to-many Role <-> Permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id")),
    Column("permission_id", Integer, ForeignKey("permissions.id")),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=text('now()')),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))
)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", back_populates="organization")
    policies = relationship("Policy", back_populates="organization")
    contacts = relationship("Contact", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)

    organization = relationship("Organization", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    description = Column(String(100))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)  # e.g., "create:contact", "delete:user"
    description = Column(String(100))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # individual/company
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    dob = Column(Date) # For Individual = date of birth / for Company = date of inception
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))
    # updated_by = Column(String)

    organization_id = Column(String, ForeignKey("organizations.id"), index=True, nullable=False)
    organization = relationship("Organization", back_populates="contacts")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    lob = Column(String)  # Line of Business = auto / property / liability / marine
    status = Column(String, default="active")

    # Premium
    base_premium = Column(Float)
    net_premium = Column(Float)
    tax = Column(Float)
    sum_insured = Column(Float)

    # Data Capture
    license_plate = Column(String)
    vin = Column(String)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))
    
    policyholder_id = Column(Integer, ForeignKey("contacts.id"))
    organization_id = Column(String, ForeignKey("organizations.id"), index=True, nullable=False)
    organization = relationship("Organization", back_populates="policies")
    