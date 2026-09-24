from sqlalchemy import String, Float, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
import uuid

from app.models.base import BaseModel

class FacilityType(str, enum.Enum):
    HOSPITAL = "HOSPITAL"
    BLOOD_BANK = "BLOOD_BANK"
    REGIONAL_CENTER = "REGIONAL_CENTER"

class OperatingStatus(str, enum.Enum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"

class Facility(BaseModel):
    __tablename__ = "facilities"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String, index=True)
    facility_type: Mapped[FacilityType] = mapped_column(SQLEnum(FacilityType))
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    region: Mapped[str] = mapped_column(String, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    operating_status: Mapped[OperatingStatus] = mapped_column(SQLEnum(OperatingStatus), default=OperatingStatus.OPERATIONAL)
    contact_info: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="facilities")
    inventory_units = relationship("InventoryUnit", back_populates="facility")
