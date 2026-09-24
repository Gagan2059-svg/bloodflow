"""
Bootstrap script: creates a demo organization + admin user with hashed password.
Run once: python -m app.utils.seed_users
"""
import uuid
from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.base import Base
from app.models.organizations import Organization, OrganizationType
from app.models.users import User, UserRole, UserStatus
from app.security.auth import get_password_hash

def seed():
    Base.metadata.create_all(bind=engine)
    from app.core.database import SessionLocal
    db: Session = SessionLocal()
    try:
        # Idempotent — skip if already exists
        if db.query(Organization).first():
            print("Seed data already present. Skipping.")
            return

        org = Organization(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="Regional Blood Network",
            type=OrganizationType.REGIONAL_CENTER,
        )
        db.add(org)
        db.flush()

        admin = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            organization_id=org.id,
            name="Platform Admin",
            email="admin@bloodflow.local",
            password_hash=get_password_hash("BloodFlow2026!"),
            role=UserRole.ORG_ADMIN,
            status=UserStatus.ACTIVE,
        )
        db.add(admin)
        db.commit()
        print("Seed complete.")
        print("  Email:    admin@bloodflow.local")
        print("  Password: BloodFlow2026!")
        print("  Org ID:   00000000-0000-0000-0000-000000000001")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
