"""
Simulation API endpoints.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from app.simulation.engine import (
    SimulationEngine,
    SimulationScenario,
    FacilitySnapshot,
    ScenarioType,
)

router = APIRouter()
_engine = SimulationEngine()


class FacilitySnapshotIn(BaseModel):
    id: str
    name: str
    inventory: int
    capacity: int
    daily_demand: float
    is_online: bool = True


class ScenarioIn(BaseModel):
    scenario_type: ScenarioType
    description: str
    affected_facility_ids: List[str] = []
    demand_multiplier: float = 1.0
    transport_delay_multiplier: float = 1.0
    supply_reduction_pct: float = 0.0
    facility_offline: bool = False
    horizon_hours: int = 72


class SimulationResultOut(BaseModel):
    scenario_id: str
    scenario_description: str
    horizon_hours: int
    baseline_shortage_risk_pct: float
    simulated_shortage_risk_pct: float
    shortage_delta_pct: float
    baseline_wastage_units: int
    simulated_wastage_units: int
    baseline_service_level_pct: float
    simulated_service_level_pct: float
    service_level_delta_pct: float
    affected_facilities_count: int
    critical_facilities: List[str]
    recommended_mitigations: List[str]


class SimulationRequest(BaseModel):
    """Combined request body wrapping facilities + scenario."""
    facilities: List[FacilitySnapshotIn]
    scenario: ScenarioIn


@router.post("/run", response_model=SimulationResultOut)
def run_simulation(body: SimulationRequest):
    """
    Run a what-if scenario against the provided facility snapshots.
    No real inventory is modified — all calculations are in-memory.

    Accepts a JSON body with `facilities` (list of FacilitySnapshotIn)
    and `scenario` (ScenarioIn) as the simulation parameters.
    """
    snaps = [FacilitySnapshot(**f.model_dump()) for f in body.facilities]
    sc = SimulationScenario(**body.scenario.model_dump())
    result = _engine.run(snaps, sc)

    return SimulationResultOut(
        scenario_id=result.scenario_id,
        scenario_description=result.scenario_description,
        horizon_hours=result.horizon_hours,
        baseline_shortage_risk_pct=result.baseline_shortage_risk_pct,
        simulated_shortage_risk_pct=result.simulated_shortage_risk_pct,
        shortage_delta_pct=result.shortage_delta_pct,
        baseline_wastage_units=result.baseline_wastage_units,
        simulated_wastage_units=result.simulated_wastage_units,
        baseline_service_level_pct=result.baseline_service_level_pct,
        simulated_service_level_pct=result.simulated_service_level_pct,
        service_level_delta_pct=result.service_level_delta_pct,
        affected_facilities_count=result.affected_facilities_count,
        critical_facilities=result.critical_facilities,
        recommended_mitigations=result.recommended_mitigations,
    )
