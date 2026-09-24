"""
Alerts API — multi-tenant enforced.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.operations import Alert, AlertStatus, AlertSeverity
from app.security.auth import get_current_active_user
from app.models.users import User

router = APIRouter()

class AlertResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID]
    alert_type: str
    severity: AlertSeverity
    title: str
    description: str
    status: AlertStatus
    blood_group: Optional[str]
    component: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    facility_id: Optional[str] = None,
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = db.query(Alert).filter(Alert.organization_id == current_user.organization_id)
    if facility_id:
        q = q.filter(Alert.facility_id == facility_id)
    if status:
        q = q.filter(Alert.status == status)
    if severity:
        q = q.filter(Alert.severity == severity)
    items = q.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.organization_id == current_user.organization_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.id
    db.commit()
    return {"status": "success"}

@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.organization_id == current_user.organization_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.utcnow()
    db.commit()
    return {"status": "success"}
