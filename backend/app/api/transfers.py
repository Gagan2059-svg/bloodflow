"""
Transfers API — multi-tenant enforced, inventory reservation on creation.
Publishes domain events to the EventBus for real-time SSE streaming.
Enforces RBAC and writes immutable audit logs for all mutations.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.operations import Transfer, TransferStatus, AuditLog
from app.models.inventory import InventoryUnit, UnitStatus
from app.security.auth import get_current_active_user
from app.security.rbac import require_logistics
from app.models.users import User
from app.events.bus import DomainEvent, EventType

router = APIRouter()

class TransferCreate(BaseModel):
    source_facility_id: uuid.UUID
    dest_facility_id: uuid.UUID
    blood_group: str
    component: str
    quantity: int
    priority: Optional[str] = "ROUTINE"

class TransferResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    source_facility_id: uuid.UUID
    dest_facility_id: uuid.UUID
    blood_group: str
    component: str
    quantity: int
    status: TransferStatus
    created_at: datetime

    class Config:
        from_attributes = True


def _write_audit(db: Session, user: User, action: str, entity_type: str, entity_id: str, metadata: dict = None):
    """Write an immutable audit record."""
    log = AuditLog(
        id=uuid.uuid4(),
        organization_id=user.organization_id,
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=f"{user.email} performed {action} on {entity_type} {entity_id}",
        metadata_json=metadata or {},
    )
    db.add(log)


@router.get("/", response_model=List[TransferResponse])
def list_transfers(
    facility_id: Optional[str] = None,
    status: Optional[TransferStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = db.query(Transfer).filter(Transfer.organization_id == current_user.organization_id)
    if facility_id:
        q = q.filter(
            (Transfer.source_facility_id == facility_id) |
            (Transfer.dest_facility_id == facility_id)
        )
    if status:
        q = q.filter(Transfer.status == status)
    return q.order_by(Transfer.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.post("/", response_model=TransferResponse, status_code=201)
def create_transfer(
    payload: TransferCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_logistics),  # RBAC enforced
):
    # Validate available inventory at source (pessimistic lock)
    available_units = (
        db.query(InventoryUnit)
        .filter(
            InventoryUnit.facility_id == payload.source_facility_id,
            InventoryUnit.blood_group == payload.blood_group,
            InventoryUnit.component == payload.component,
            InventoryUnit.status == UnitStatus.AVAILABLE,
        )
        .limit(payload.quantity)
        .with_for_update()
        .all()
    )
    if len(available_units) < payload.quantity:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient inventory: only {len(available_units)} units available, {payload.quantity} requested"
        )

    # Reserve inventory units
    for unit in available_units:
        unit.status = UnitStatus.IN_TRANSIT

    transfer = Transfer(
        organization_id=current_user.organization_id,
        source_facility_id=payload.source_facility_id,
        dest_facility_id=payload.dest_facility_id,
        blood_group=payload.blood_group,
        component=payload.component,
        quantity=payload.quantity,
        status=TransferStatus.PENDING,
        initiated_by=current_user.id,
    )
    db.add(transfer)

    # Audit log
    _write_audit(db, current_user, "CREATE_TRANSFER", "Transfer", "pending",
                 metadata={
                     "source": str(payload.source_facility_id),
                     "dest": str(payload.dest_facility_id),
                     "blood_group": payload.blood_group,
                     "component": payload.component,
                     "quantity": payload.quantity,
                     "priority": payload.priority,
                 })

    db.commit()
    db.refresh(transfer)

    # Update audit log with real transfer ID
    _write_audit(db, current_user, "CREATE_TRANSFER_CONFIRMED", "Transfer", str(transfer.id),
                 metadata={"transfer_id": str(transfer.id)})
    db.commit()

    # Publish SSE event
    try:
        bus = getattr(request.app.state, "event_bus", None)
        if bus:
            bus.publish(DomainEvent(
                event_type=EventType.TRANSFER_CREATED,
                organization_id=str(current_user.organization_id),
                facility_id=str(payload.source_facility_id),
                payload={
                    "transfer_id": str(transfer.id),
                    "blood_group": transfer.blood_group,
                    "quantity": transfer.quantity,
                    "source": str(payload.source_facility_id),
                    "dest": str(payload.dest_facility_id),
                }
            ))
    except Exception:
        pass

    return transfer


@router.post("/{transfer_id}/complete", response_model=TransferResponse)
def complete_transfer(
    transfer_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_logistics),  # RBAC enforced
):
    """Complete a transfer: move IN_TRANSIT units to the destination facility."""
    t = db.query(Transfer).filter(
        Transfer.id == transfer_id, Transfer.organization_id == current_user.organization_id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if t.status == TransferStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Transfer already completed (idempotent: no-op)")

    in_transit_units = (
        db.query(InventoryUnit)
        .filter(
            InventoryUnit.facility_id == t.source_facility_id,
            InventoryUnit.blood_group == t.blood_group,
            InventoryUnit.component == t.component,
            InventoryUnit.status == UnitStatus.IN_TRANSIT,
        )
        .limit(t.quantity)
        .with_for_update()
        .all()
    )
    for unit in in_transit_units:
        unit.facility_id = t.dest_facility_id
        unit.status = UnitStatus.AVAILABLE

    t.status = TransferStatus.COMPLETED
    t.completed_at = datetime.utcnow()
    t.approved_by = current_user.id

    # Audit log
    _write_audit(db, current_user, "COMPLETE_TRANSFER", "Transfer", str(transfer_id),
                 metadata={
                     "units_moved": len(in_transit_units),
                     "dest_facility": str(t.dest_facility_id),
                 })

    db.commit()
    db.refresh(t)

    # Publish SSE completion event
    try:
        bus = getattr(request.app.state, "event_bus", None)
        if bus:
            bus.publish(DomainEvent(
                event_type=EventType.TRANSFER_CREATED,
                organization_id=str(current_user.organization_id),
                facility_id=str(t.dest_facility_id),
                payload={"transfer_id": str(transfer_id), "status": "COMPLETED"}
            ))
    except Exception:
        pass

    return t


@router.delete("/{transfer_id}", status_code=204)
def cancel_transfer(
    transfer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_logistics),  # RBAC enforced
):
    """Cancel a pending transfer and release reserved inventory."""
    t = db.query(Transfer).filter(
        Transfer.id == transfer_id,
        Transfer.organization_id == current_user.organization_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if t.status == TransferStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed transfer")

    # Release IN_TRANSIT units back to AVAILABLE
    in_transit_units = (
        db.query(InventoryUnit)
        .filter(
            InventoryUnit.facility_id == t.source_facility_id,
            InventoryUnit.blood_group == t.blood_group,
            InventoryUnit.component == t.component,
            InventoryUnit.status == UnitStatus.IN_TRANSIT,
        )
        .limit(t.quantity)
        .with_for_update()
        .all()
    )
    for unit in in_transit_units:
        unit.status = UnitStatus.AVAILABLE

    t.status = TransferStatus.CANCELLED
    _write_audit(db, current_user, "CANCEL_TRANSFER", "Transfer", str(transfer_id),
                 metadata={"units_released": len(in_transit_units)})
    db.commit()

