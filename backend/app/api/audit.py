"""
Audit Log API — read-only endpoint returning the immutable audit trail.
Only accessible to Org Admins and above.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.operations import AuditLog
from app.security.rbac import require_org_admin
from app.models.users import User

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    description: Optional[str]
    metadata_json: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),  # Restricted to admins
):
    """Return paginated audit log, scoped to the caller's organization."""
    q = db.query(AuditLog).filter(AuditLog.organization_id == current_user.organization_id)
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    return q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
