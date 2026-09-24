"""
Facilities API — multi-tenant enforced.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.facilities import Facility, FacilityType, OperatingStatus
from app.security.auth import get_current_active_user
from app.models.users import User

router = APIRouter()

class FacilityCreate(BaseModel):
    name: str
    facility_type: FacilityType
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    capacity: int = 0
    operating_status: OperatingStatus = OperatingStatus.OPERATIONAL
    contact_info: Optional[str] = None

class FacilityResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    facility_type: FacilityType
    latitude: Optional[float]
    longitude: Optional[float]
    region: Optional[str]
    capacity: int
    operating_status: OperatingStatus
    contact_info: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[FacilityResponse])
def read_facilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Multi-tenancy: filter by authenticated user's org
    facilities = (
        db.query(Facility)
        .filter(Facility.organization_id == current_user.organization_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return facilities

@router.post("/", response_model=FacilityResponse, status_code=201)
def create_facility(
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    facility = Facility(**payload.dict(), organization_id=current_user.organization_id)
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility

@router.get("/{facility_id}", response_model=FacilityResponse)
def get_facility(
    facility_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    facility = (
        db.query(Facility)
        .filter(Facility.id == facility_id, Facility.organization_id == current_user.organization_id)
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility

@router.patch("/{facility_id}", response_model=FacilityResponse)
def update_facility(
    facility_id: uuid.UUID,
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    facility = (
        db.query(Facility)
        .filter(Facility.id == facility_id, Facility.organization_id == current_user.organization_id)
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(facility, k, v)
    db.commit()
    db.refresh(facility)
    return facility
