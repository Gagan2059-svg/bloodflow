from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid
from app.models.facilities import FacilityType, OperatingStatus

class FacilityBase(BaseModel):
    name: str
    facility_type: FacilityType
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    capacity: int = 0
    operating_status: OperatingStatus = OperatingStatus.OPERATIONAL
    contact_info: Optional[str] = None

class FacilityCreate(FacilityBase):
    organization_id: uuid.UUID

class FacilityResponse(FacilityBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
