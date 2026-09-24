"""
Inventory API — multi-tenant enforced, real DB data.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import csv, io, uuid

from app.core.database import get_db
from app.models.inventory import InventoryUnit, BloodGroup, BloodComponent, UnitStatus
from app.security.auth import get_current_active_user
from app.models.users import User

router = APIRouter()

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

    class Config:
        from_attributes = True

class InventoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[InventoryUnitResponse]

def _base_query(db: Session, org_id: uuid.UUID):
    """Base inventory query scoped to the org's facilities."""
    from app.models.facilities import Facility
    return db.query(InventoryUnit).join(Facility).filter(Facility.organization_id == org_id)

@router.get("/", response_model=InventoryListResponse)
def list_inventory(
    facility_id: Optional[str] = None,
    blood_group: Optional[BloodGroup] = None,
    component: Optional[BloodComponent] = None,
    status: Optional[UnitStatus] = None,
    expiring_within_days: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = _base_query(db, current_user.organization_id)
    if facility_id:
        q = q.filter(InventoryUnit.facility_id == uuid.UUID(facility_id))
    if blood_group:
        q = q.filter(InventoryUnit.blood_group == blood_group)
    if component:
        q = q.filter(InventoryUnit.component == component)
    if status:
        q = q.filter(InventoryUnit.status == status)
    if expiring_within_days is not None:
        now = datetime.utcnow()
        window = now + timedelta(days=expiring_within_days)
        q = q.filter(InventoryUnit.expiration_date <= window, InventoryUnit.expiration_date >= now)

    total = q.count()
    items = q.order_by(InventoryUnit.expiration_date).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}

@router.get("/summary")
def inventory_summary(
    facility_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = _base_query(db, current_user.organization_id)
    if facility_id:
        q = q.filter(InventoryUnit.facility_id == uuid.UUID(facility_id))
    rows = q.with_entities(
        InventoryUnit.blood_group,
        InventoryUnit.component,
        InventoryUnit.status,
        func.count(InventoryUnit.id).label("count"),
    ).group_by(InventoryUnit.blood_group, InventoryUnit.component, InventoryUnit.status).all()

    summary: dict = {}
    total_available = 0
    expiring_soon = 0

    for row in rows:
        key = f"{row.blood_group.value}_{row.component.value}"
        if key not in summary:
            summary[key] = {"blood_group": row.blood_group.value, "component": row.component.value, "by_status": {}}
        summary[key]["by_status"][row.status.value] = row.count
        if row.status.value == "AVAILABLE":
            total_available += row.count

    # Expiring within 72h
    now = datetime.utcnow()
    expiring_soon = _base_query(db, current_user.organization_id).filter(
        InventoryUnit.expiration_date <= now + timedelta(days=3),
        InventoryUnit.expiration_date >= now,
        InventoryUnit.status == UnitStatus.AVAILABLE,
    ).count()

    return {
        "summary": list(summary.values()),
        "kpis": {
            "total_available": total_available,
            "expiring_within_72h": expiring_soon,
        }
    }

@router.get("/export/csv")
def export_inventory_csv(
    facility_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = _base_query(db, current_user.organization_id)
    if facility_id:
        q = q.filter(InventoryUnit.facility_id == uuid.UUID(facility_id))
    units = q.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "facility_id", "blood_group", "component", "status", "expiration_date", "quantity_ml"])
    for u in units:
        writer.writerow([str(u.id), str(u.facility_id), u.blood_group.value, u.component.value, u.status.value, u.expiration_date.isoformat(), u.quantity_ml])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=inventory_export.csv"})
