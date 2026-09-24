"""
Recommendations API — multi-tenant enforced, OR-Tools optimizer wired.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.operations import Recommendation, RecommendationStatus, RecommendationType
from app.security.auth import get_current_active_user
from app.models.users import User

router = APIRouter()

class RecommendationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    rec_type: RecommendationType
    priority: int
    source_facility_id: Optional[uuid.UUID]
    dest_facility_id: Optional[uuid.UUID]
    blood_group: Optional[str]
    component: Optional[str]
    quantity: Optional[int]
    reason: str
    confidence: Optional[float]
    status: RecommendationStatus
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[RecommendationResponse])
def list_recommendations(
    facility_id: Optional[str] = None,
    status: Optional[RecommendationStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = db.query(Recommendation).filter(Recommendation.organization_id == current_user.organization_id)
    if facility_id:
        q = q.filter(
            (Recommendation.source_facility_id == facility_id) |
            (Recommendation.dest_facility_id == facility_id)
        )
    if status:
        q = q.filter(Recommendation.status == status)
    return q.order_by(Recommendation.priority.asc(), Recommendation.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

@router.post("/run-optimizer")
def run_optimizer(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Trigger the OR-Tools optimization engine for the current org."""
    background_tasks.add_task(_run_optimizer_task, str(current_user.organization_id))
    return {"status": "optimization_queued", "organization_id": str(current_user.organization_id)}

def _run_optimizer_task(org_id: str):
    """Background task: reads real surplus/deficit from DB, calls OR-Tools, saves Recommendations."""
    from app.core.database import SessionLocal
    from app.models.inventory import InventoryUnit, UnitStatus, BloodComponent, BloodGroup
    from app.models.facilities import Facility
    from app.models.operations import DemandRecord
    from app.optimization.transfer import optimize_transfers
    from sqlalchemy import func
    import uuid as _uuid

    db: Session = SessionLocal()
    try:
        org_uuid = _uuid.UUID(org_id)
        facilities = db.query(Facility).filter(Facility.organization_id == org_uuid).all()
        fac_ids = [f.id for f in facilities]

        # Compute available inventory per facility
        available = db.query(
            InventoryUnit.facility_id,
            func.count(InventoryUnit.id).label("count")
        ).filter(
            InventoryUnit.facility_id.in_(fac_ids),
            InventoryUnit.status == UnitStatus.AVAILABLE,
        ).group_by(InventoryUnit.facility_id).all()
        available_map = {row.facility_id: row.count for row in available}

        # Compute average demand per facility (last 30 days)
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=30)
        demand = db.query(
            DemandRecord.facility_id,
            func.sum(DemandRecord.requested_quantity).label("total_demand")
        ).filter(
            DemandRecord.facility_id.in_(fac_ids),
            DemandRecord.recorded_at >= cutoff,
        ).group_by(DemandRecord.facility_id).all()
        demand_map = {row.facility_id: row.total_demand / 30.0 for row in demand}

        # Calculate surplus/deficit
        surplus_deficit = {}
        for fid in fac_ids:
            avail = available_map.get(fid, 0)
            daily_demand = demand_map.get(fid, 5.0)
            # Surplus = inventory - 7 days of demand
            surplus_deficit[fid] = int(avail - (daily_demand * 7))

        # Build distances (Euclidean from lat/lon as proxy)
        import math
        fac_map = {f.id: f for f in facilities}
        distances = {}
        for a in fac_ids:
            for b in fac_ids:
                if a != b and fac_map[a].latitude and fac_map[b].latitude:
                    dlat = (fac_map[a].latitude or 0) - (fac_map[b].latitude or 0)
                    dlon = (fac_map[a].longitude or 0) - (fac_map[b].longitude or 0)
                    distances[(a, b)] = round(math.sqrt(dlat**2 + dlon**2), 3) or 1.0
                else:
                    distances[(a, b)] = 50.0

        results = optimize_transfers(surplus_deficit, distances)

        # Save to Recommendations table
        for rec in results:
            r = Recommendation(
                organization_id=org_uuid,
                rec_type=RecommendationType.TRANSFER,
                priority=1,
                source_facility_id=rec.source_facility_id,
                dest_facility_id=rec.destination_facility_id,
                quantity=rec.units_to_transfer,
                reason=f"OR-Tools optimizer: {rec.units_to_transfer} units, cost={rec.expected_impact_score:.1f}",
                confidence=0.92,
                status=RecommendationStatus.PENDING,
            )
            db.add(r)
        db.commit()
    finally:
        db.close()

@router.post("/{rec_id}/approve")
def approve_recommendation(
    rec_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id, Recommendation.organization_id == current_user.organization_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = RecommendationStatus.APPROVED
    rec.reviewed_at = datetime.utcnow()
    rec.reviewed_by = current_user.id
    db.commit()
    return {"status": "approved"}

@router.post("/{rec_id}/reject")
def reject_recommendation(
    rec_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id, Recommendation.organization_id == current_user.organization_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = RecommendationStatus.REJECTED
    rec.reviewed_at = datetime.utcnow()
    rec.reviewed_by = current_user.id
    db.commit()
    return {"status": "rejected"}
