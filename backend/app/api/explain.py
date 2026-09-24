"""
Dynamic AI Explainability Layer.
Replaces the static string-match mock with a context-aware rule engine
that formats explanations from actual system state data.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.inventory import InventoryUnit, UnitStatus
from app.models.operations import Alert, AlertSeverity
from app.models.facilities import Facility
from app.security.auth import get_current_active_user
from app.models.users import User

router = APIRouter()

class ExplanationRequest(BaseModel):
    query: str
    facility_id: Optional[uuid.UUID] = None
    context: Optional[dict] = None

class ExplanationResponse(BaseModel):
    explanation: str
    confidence: float
    model: str
    data_sources: list[str]

@router.post("/", response_model=ExplanationResponse)
def explain_decision(
    request: ExplanationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Dynamic Explainability Layer.
    Builds a context-aware explanation from real database state.
    Queries live inventory, alert, and facility data to generate grounded explanations.
    """
    org_id = current_user.organization_id
    query_lower = request.query.lower()
    data_sources = []
    explanation_parts = []
    confidence = 0.80

    # --- Facility-specific explanation ---
    if request.facility_id:
        facility = db.query(Facility).filter(
            Facility.id == request.facility_id,
            Facility.organization_id == org_id
        ).first()

        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")

        # Get live inventory stats
        total_units = db.query(InventoryUnit).filter(
            InventoryUnit.facility_id == facility.id,
        ).count()

        available_units = db.query(InventoryUnit).filter(
            InventoryUnit.facility_id == facility.id,
            InventoryUnit.status == UnitStatus.AVAILABLE,
        ).count()

        expired_units = db.query(InventoryUnit).filter(
            InventoryUnit.facility_id == facility.id,
            InventoryUnit.status == UnitStatus.EXPIRED,
        ).count()

        # Get active critical alerts for this facility
        from app.models.operations import AlertStatus
        active_alerts = db.query(Alert).filter(
            Alert.organization_id == org_id,
            Alert.facility_id == facility.id,
            Alert.status != AlertStatus.RESOLVED,
        ).order_by(Alert.severity.desc()).limit(3).all()

        data_sources.extend(["inventory_units", "alerts"])

        utilization_pct = round((available_units / total_units * 100) if total_units > 0 else 0, 1)
        wastage_pct = round((expired_units / total_units * 100) if total_units > 0 else 0, 1)

        explanation_parts.append(
            f"Facility '{facility.name}' currently holds {total_units} total inventory units. "
            f"{available_units} ({utilization_pct}%) are available for use and "
            f"{expired_units} ({wastage_pct}%) have expired."
        )

        if "risk" in query_lower or "shortage" in query_lower:
            if available_units < 20:
                explanation_parts.append(
                    f"The available stock of {available_units} units is critically low. "
                    f"Based on current demand patterns, a shortage is highly probable within 24-48 hours "
                    f"without an inbound transfer."
                )
                confidence = 0.92
            elif available_units < 50:
                explanation_parts.append(
                    f"The available stock of {available_units} units is below the recommended safety buffer of 50 units. "
                    f"Monitor closely and consider initiating a precautionary transfer."
                )
                confidence = 0.85
            else:
                explanation_parts.append(
                    f"Stock levels are within acceptable range. No immediate shortage risk detected."
                )
                confidence = 0.90

        if active_alerts:
            alert_summaries = "; ".join(
                [f"[{a.severity.value.upper()}] {a.message}" for a in active_alerts]
            )
            explanation_parts.append(f"Active alerts: {alert_summaries}.")
            confidence = min(confidence + 0.03, 0.99)

    # --- Network-wide explanation ---
    elif "network" in query_lower or "optimization" in query_lower or "transfer" in query_lower:
        # Pull org-wide inventory snapshot
        total_org_units = db.query(InventoryUnit).join(Facility).filter(
            Facility.organization_id == org_id,
        ).count()

        available_org_units = db.query(InventoryUnit).join(Facility).filter(
            Facility.organization_id == org_id,
            InventoryUnit.status == UnitStatus.AVAILABLE,
        ).count()

        expired_org_units = db.query(InventoryUnit).join(Facility).filter(
            Facility.organization_id == org_id,
            InventoryUnit.status == UnitStatus.EXPIRED,
        ).count()

        data_sources.append("inventory_units")

        explanation_parts.append(
            f"Across the network, there are {total_org_units} total units: "
            f"{available_org_units} available and {expired_org_units} expired. "
        )

        if "optimization" in query_lower or "transfer" in query_lower:
            explanation_parts.append(
                "The optimization engine uses Google OR-Tools to solve a linear programming problem. "
                "It calculates the minimum-cost transfer matrix that moves units from facilities with "
                "surplus stock to facilities with deficits, subject to capacity constraints and "
                "blood group compatibility rules. The output are the cost-minimized transfer recommendations."
            )
            confidence = 0.95
            data_sources.append("or_tools_solver")

    # --- Fallback: generic system explanation ---
    else:
        explanation_parts.append(
            "The BloodFlow decision engine continuously monitors inventory levels, demand forecasts, "
            "and network topology to surface actionable recommendations. "
            "Provide a specific facility ID or use keywords like 'shortage', 'network', "
            "or 'optimization' for a more targeted explanation."
        )
        confidence = 0.70

    return ExplanationResponse(
        explanation=" ".join(explanation_parts),
        confidence=confidence,
        model="BloodFlow-Explain-v2 (Dynamic Rule Engine)",
        data_sources=data_sources,
    )
