import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date, timezone

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root))

from src.database import Base
from src import models, schemas, utils 
from dotenv import load_dotenv

DATABASE_URL= os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_data():
    db: Session = next(get_db())
    print("Seeding database...")
    try:
        # --- Create Organizations ---
        org1_id = "org_polite"
        org2_id = "org_guest"

        org1 = db.query(models.Organization).filter(models.Organization.id == org1_id).first()
        if not org1:
            org1 = models.Organization(id=org1_id, name="Polite")
            db.add(org1)
            db.commit()
            db.refresh(org1)
        
        org2 = db.query(models.Organization).filter(models.Organization.id == org2_id).first()
        if not org2:
            org2 = models.Organization(id=org2_id, name="Guest")
            db.add(org2)
            db.commit()
            db.refresh(org2)

        # --- Create Users ---
        admin_password_hash = utils.hash_password("admin")
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            admin_user = models.User(
                username="admin",
                password=admin_password_hash,
                email="admin@example.com",
                full_name="Administrator",
                organization_id=org1_id
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
        else:
            print("Admin user already exists")

        guest_password_hash = utils.hash_password("guest")
        guest_user = db.query(models.User).filter(models.User.username == "guest").first()
        if not guest_user:
            guest_user = models.User(
                username="guest",
                password=guest_password_hash,
                email="guest@example.com",
                full_name="Guest",
                organization_id=org2_id
            )
            db.add(guest_user)
            db.commit()
            db.refresh(guest_user)
        else:
            print("Guest user already exists")

        # --- Create Roles ---
        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
        if not admin_role:
            admin_role = models.Role(name="admin", description="Administrator")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print(f"Created role: {admin_role.name}")
        else:
            print(f"Role '{admin_role.name}' already exists.")

        guest_role = db.query(models.Role).filter(models.Role.name == "guest").first()
        if not guest_role:
            guest_role = models.Role(name="guest", description="Guest")
            db.add(guest_role)
            db.commit()
            db.refresh(guest_role)
            print(f"Created role: {guest_role.name}")
        else:
            print(f"Role '{guest_role.name}' already exists.")
        

        # --- Create Permissions ---
        perms_to_create = [
            "create:users", "update:users", "delete:users",
            "create:roles", "update:roles", "delete:roles",
            "create:contacts", "update:contacts", "delete:contacts",
            "create:policies", "update:policies", "delete:policies",
        ]

        created_permissions = {}
        for perm_name in perms_to_create:
            permission = db.query(models.Permission).filter(models.Permission.name == perm_name).first()
            if not permission:
                permission = models.Permission(name=perm_name, description=f"Ability to {perm_name.replace(':', ' ')}")
                db.add(permission)
                db.commit()
                db.refresh(permission)
            else:
                print(f"Permission '{permission.name}' already exists.")
            created_permissions[perm_name] = permission

        # --- Assign Permissions to Roles ---
        admin_role.permissions.extend([p for p in created_permissions.values() if p not in admin_role.permissions])
        guest_role_perms = [
            created_permissions["create:contacts"], created_permissions["update:contacts"], 
            created_permissions["create:policies"], created_permissions["update:policies"], 
        ]
        guest_role.permissions.extend([p for p in guest_role_perms if p not in guest_role.permissions])
        db.commit()

        # --- Assign Roles to Users ---
        if admin_user and admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
        else:
             print(f"'{admin_role.name}' role already assigned to '{admin_user.username}' or user/role missing.")

        if guest_user and guest_role not in guest_user.roles:
            guest_user.roles.append(guest_role)
        else:
            print(f"'{guest_user.name}' role already assigned to '{guest_user.username}' or user/role missing.")
        db.commit()

        # --- Create Contacts ---
        contact1 = models.Contact(type="Individual", first_name="Foo", last_name="Bar", email="foobar@example.com", dob="1970-01-01", organization_id=org1_id)
        contact2 = models.Contact(type="Individual", first_name="John", last_name="Doe", email="johndoe@example.com", dob="1980-01-01", organization_id=org2_id)
        db.add_all([contact1, contact2])
        db.commit()
        db.refresh(contact1)
        db.refresh(contact2)
        print(f"Created contacts")

        # --- Create Policies ---
        policy1 = models.Policy(lob="auto", status="active", base_premium=100, net_premium=750, tax=10, sum_insured=1000000, license_plate="LP1 1VL", vin="123456789", 
                                start_date=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc), 
                                end_date=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc), 
                                policyholder_id=contact1.id,
                                organization_id=org1_id)
        policy2 = models.Policy(lob="auto", status="active", base_premium=50, net_premium=500, tax=5, sum_insured=500000, license_plate="LP2 2VL", vin="987654321", 
                        start_date=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                        end_date=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc), 
                        policyholder_id=contact2.id,
                        organization_id=org2_id)
        db.add_all([policy1, policy2])
        db.commit()
        db.refresh(policy1)
        db.refresh(policy2)
        print(f"Created policies")

        print("\nDatabase seeding complete!")

    except Exception as e:
        db.rollback()
        print(f"\nError during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Drop tables
    print("Dropping tables...")
    Base.metadata.drop_all(bind=engine)

    # Create tables
    print("Recreating tables...")
    Base.metadata.create_all(bind=engine)

    # Seed data
    seed_data()

