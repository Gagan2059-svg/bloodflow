from sqlalchemy import String, Integer, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
import uuid

from app.models.base import BaseModel

class BloodGroup(str, enum.Enum):
    O_POS = "O+"
    O_NEG = "O-"
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"

class BloodComponent(str, enum.Enum):
    WHOLE_BLOOD = "WHOLE_BLOOD"
    RBC = "RBC"
    PLASMA = "PLASMA"
    PLATELETS = "PLATELETS"
    CRYOPRECIPITATE = "CRYOPRECIPITATE"

class UnitStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    IN_TRANSIT = "IN_TRANSIT"
    USED = "USED"
    EXPIRED = "EXPIRED"
    DISCARDED = "DISCARDED"

class InventoryUnit(BaseModel):
    __tablename__ = "inventory_units"

    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"))
    blood_group: Mapped[BloodGroup] = mapped_column(SQLEnum(BloodGroup))
    component: Mapped[BloodComponent] = mapped_column(SQLEnum(BloodComponent))
    collection_date: Mapped[datetime] = mapped_column(DateTime)
    expiration_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[UnitStatus] = mapped_column(SQLEnum(UnitStatus), default=UnitStatus.AVAILABLE, index=True)
    storage_location: Mapped[str] = mapped_column(String, nullable=True)
    quantity_ml: Mapped[int] = mapped_column(Integer, default=250)
    source: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    facility = relationship("Facility", back_populates="inventory_units")
