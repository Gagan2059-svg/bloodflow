from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

from app.models.inventory import BloodGroup, BloodComponent, UnitStatus

class InventoryUnitResponse(BaseModel):
    id: uuid.UUID
    facility_id: uuid.UUID
    blood_group: BloodGroup
    component: BloodComponent
    collection_date: datetime
    expiration_date: datetime
    status: UnitStatus
    storage_location: Optional[str]
    quantity_ml: int
    source: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[InventoryUnitResponse]
