from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import BaseModel

class OrganizationType(str, enum.Enum):
    HOSPITAL_NETWORK = "HOSPITAL_NETWORK"
    BLOOD_BANK = "BLOOD_BANK"
    REGIONAL_CENTER = "REGIONAL_CENTER"

class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[OrganizationType] = mapped_column(SQLEnum(OrganizationType))

    # Relationships
    users = relationship("User", back_populates="organization")
    facilities = relationship("Facility", back_populates="organization")
