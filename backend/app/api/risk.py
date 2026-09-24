"""
Risk API — real shortage/wastage predictions using live inventory data.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.models.inventory import InventoryUnit, UnitStatus
from app.models.operations import DemandRecord
from app.models.facilities import Facility
from app.security.auth import get_current_active_user
from app.models.users import User
from app.ml.risk_prediction import RiskPredictor

router = APIRouter()

@router.get("/network-summary")
def network_risk_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return aggregated risk assessment for the entire organization network."""
    facilities = db.query(Facility).filter(Facility.organization_id == current_user.organization_id).all()
    results = []
    now = datetime.utcnow()

    for fac in facilities:
        # Available inventory count
        available = db.query(func.count(InventoryUnit.id)).filter(
            InventoryUnit.facility_id == fac.id,
            InventoryUnit.status == UnitStatus.AVAILABLE,
        ).scalar() or 0

        # Units expiring in 72h
        expiring_soon = db.query(func.count(InventoryUnit.id)).filter(
            InventoryUnit.facility_id == fac.id,
            InventoryUnit.status == UnitStatus.AVAILABLE,
            InventoryUnit.expiration_date <= now + timedelta(days=3),
            InventoryUnit.expiration_date >= now,
        ).scalar() or 0

        # Average daily demand (last 30 days)
        cutoff = now - timedelta(days=30)
        total_demand = db.query(func.sum(DemandRecord.requested_quantity)).filter(
            DemandRecord.facility_id == fac.id,
            DemandRecord.recorded_at >= cutoff,
        ).scalar() or 0
        daily_demand = total_demand / 30.0

        shortage = RiskPredictor.predict_shortage_probability(
            current_inventory=available,
            projected_demand=daily_demand * 7,
            incoming_supply=0,
            emergency_reserve=max(5, int(daily_demand * 2)),
        )
        wastage = RiskPredictor.predict_wastage_probability(
            units_expiring_soon=expiring_soon,
            projected_demand=daily_demand * 3,
        )

        results.append({
            "facility_id": str(fac.id),
            "facility_name": fac.name,
            "region": fac.region,
            "available_units": available,
            "expiring_72h": expiring_soon,
            "daily_demand_avg": round(daily_demand, 2),
            "shortage_risk": shortage,
            "wastage_risk": wastage,
        })

    return {"facilities": results, "generated_at": now.isoformat()}

@router.get("/facility/{facility_id}")
def facility_risk_detail(
    facility_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Detailed risk breakdown for a single facility across all blood groups and components."""
    fac = db.query(Facility).filter(
        Facility.id == facility_id,
        Facility.organization_id == current_user.organization_id
    ).first()
    if not fac:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Facility not found")

    now = datetime.utcnow()
    cutoff = now - timedelta(days=30)

    # Per blood group breakdown
    breakdown = db.query(
        InventoryUnit.blood_group,
        InventoryUnit.component,
        InventoryUnit.status,
        func.count(InventoryUnit.id).label("count"),
    ).filter(
        InventoryUnit.facility_id == facility_id,
    ).group_by(InventoryUnit.blood_group, InventoryUnit.component, InventoryUnit.status).all()

    inventory_map: dict = {}
    for row in breakdown:
        key = f"{row.blood_group.value}|{row.component.value}"
        if key not in inventory_map:
            inventory_map[key] = {"blood_group": row.blood_group.value, "component": row.component.value, "available": 0, "reserved": 0, "expiring_soon": 0}
        if row.status.value == "AVAILABLE":
            inventory_map[key]["available"] = row.count
        elif row.status.value == "RESERVED":
            inventory_map[key]["reserved"] = row.count

    # Expiring soon per type
    expiring_rows = db.query(
        InventoryUnit.blood_group,
        InventoryUnit.component,
        func.count(InventoryUnit.id).label("count"),
    ).filter(
        InventoryUnit.facility_id == facility_id,
        InventoryUnit.status == UnitStatus.AVAILABLE,
        InventoryUnit.expiration_date <= now + timedelta(days=3),
        InventoryUnit.expiration_date >= now,
    ).group_by(InventoryUnit.blood_group, InventoryUnit.component).all()
    for row in expiring_rows:
        key = f"{row.blood_group.value}|{row.component.value}"
        if key in inventory_map:
            inventory_map[key]["expiring_soon"] = row.count

    # Attach risk scores
    results = []
    for key, data in inventory_map.items():
        sr = RiskPredictor.predict_shortage_probability(
            current_inventory=data["available"],
            projected_demand=data["available"] * 0.5,
            incoming_supply=0,
            emergency_reserve=5,
        )
        wr = RiskPredictor.predict_wastage_probability(
            units_expiring_soon=data["expiring_soon"],
            projected_demand=data["available"] * 0.3,
        )
        results.append({**data, "shortage_risk": sr["probability"], "wastage_risk": wr["probability"]})

    return {"facility": {"id": str(fac.id), "name": fac.name}, "breakdown": results, "generated_at": now.isoformat()}
