from sqlalchemy import (
    Column,
    String,
    Float,
    ForeignKey,
    Boolean,
    DateTime,
    Date,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from src.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)  # Clerk org_id
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    clerk_synced_at = Column(TIMESTAMP(timezone=True), nullable=True)

    policies = relationship("Policy", back_populates="organization")
    contacts = relationship("Contact", back_populates="organization")
    memberships = relationship("Membership", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # Clerk user_id
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    clerk_synced_at = Column(TIMESTAMP(timezone=True), nullable=True)

    memberships = relationship("Membership", back_populates="user")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(String, primary_key=True, index=True)  # Clerk membership id
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(
        String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    clerk_synced_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")

    __table_args__ = (UniqueConstraint("user_id", "organization_id", name="uq_membership_user_org"),)


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # individual / company
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    dob = Column(Date)  # individual: DOB; company: date of inception
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )

    organization_id = Column(
        String, ForeignKey("organizations.id"), index=True, nullable=False
    )
    organization = relationship("Organization", back_populates="contacts")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    lob = Column(String)
    status = Column(String, default="active")

    base_premium = Column(Float)
    net_premium = Column(Float)
    tax = Column(Float)
    sum_insured = Column(Float)

    license_plate = Column(String)
    vin = Column(String)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )

    policyholder_id = Column(Integer, ForeignKey("contacts.id"))
    organization_id = Column(
        String, ForeignKey("organizations.id"), index=True, nullable=False
    )
    organization = relationship("Organization", back_populates="policies")
