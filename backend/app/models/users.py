from sqlalchemy import String, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
import uuid

from app.models.base import BaseModel

class UserRole(str, enum.Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    ORG_ADMIN = "ORG_ADMIN"
    BLOOD_BANK_MANAGER = "BLOOD_BANK_MANAGER"
    HOSPITAL_MANAGER = "HOSPITAL_MANAGER"
    LOGISTICS_COORDINATOR = "LOGISTICS_COORDINATOR"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class User(BaseModel):
    __tablename__ = "users"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole))
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)

    # Relationships
    organization = relationship("Organization", back_populates="users")
