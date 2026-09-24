from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.operations import DemandRecord
from pydantic import BaseModel

router = APIRouter()

class DemandCreate(BaseModel):
    organization_id: uuid.UUID
    facility_id: uuid.UUID
    blood_group: str
    component: str
    requested_quantity: int
    is_emergency: bool = False

class DemandResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    facility_id: uuid.UUID
    blood_group: str
    component: str
    requested_quantity: int
    fulfilled_quantity: int
    is_emergency: bool
    recorded_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[DemandResponse])
def list_demand(
    facility_id: Optional[str] = None,
    blood_group: Optional[str] = None,
    is_emergency: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    q = db.query(DemandRecord)
    if facility_id:
        q = q.filter(DemandRecord.facility_id == facility_id)
    if blood_group:
        q = q.filter(DemandRecord.blood_group == blood_group)
    if is_emergency is not None:
        q = q.filter(DemandRecord.is_emergency == is_emergency)
        
    items = q.order_by(DemandRecord.recorded_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items

@router.post("/", response_model=DemandResponse)
def create_demand(payload: DemandCreate, db: Session = Depends(get_db)):
    d = DemandRecord(**payload.dict())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d
