"""
Simulation Engine - Digital Twin What-If Analysis.

Simulates the impact of scenarios on the blood supply network without
modifying any actual inventory. All calculations are performed in-memory
against a snapshot of current state.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import math


class ScenarioType(str, Enum):
    FACILITY_OUTAGE = "FACILITY_OUTAGE"
    DEMAND_SURGE = "DEMAND_SURGE"
    TRANSPORT_DELAY = "TRANSPORT_DELAY"
    SUPPLY_REDUCTION = "SUPPLY_REDUCTION"
    CUSTOM = "CUSTOM"


@dataclass
class FacilitySnapshot:
    """Lightweight snapshot of a facility's state for simulation."""
    id: str
    name: str
    inventory: int          # available units
    capacity: int
    daily_demand: float     # average daily demand
    is_online: bool = True


@dataclass
class SimulationScenario:
    """Defines the what-if scenario parameters."""
    scenario_type: ScenarioType
    description: str
    affected_facility_ids: List[str] = field(default_factory=list)
    demand_multiplier: float = 1.0          # 1.4 = +40% demand
    transport_delay_multiplier: float = 1.0  # 1.3 = +30% travel time
    supply_reduction_pct: float = 0.0       # 0.8 = lose 80% of inventory
    facility_offline: bool = False
    horizon_hours: int = 72


@dataclass
class FacilityImpact:
    facility_id: str
    facility_name: str
    baseline_inventory: int
    simulated_inventory: int
    baseline_shortage_risk_pct: float
    simulated_shortage_risk_pct: float
    baseline_wastage_units: int
    simulated_wastage_units: int
    is_critical: bool = False


@dataclass
class SimulationResult:
    scenario_id: str
    scenario_description: str
    horizon_hours: int
    generated_at: datetime

    # Network-level summary
    baseline_shortage_risk_pct: float
    simulated_shortage_risk_pct: float
    baseline_wastage_units: int
    simulated_wastage_units: int
    baseline_service_level_pct: float
    simulated_service_level_pct: float

    # Facility-level breakdown
    facility_impacts: List[FacilityImpact]

    # Derived metrics
    affected_facilities_count: int = 0
    critical_facilities: List[str] = field(default_factory=list)
    recommended_mitigations: List[str] = field(default_factory=list)

    @property
    def shortage_delta_pct(self) -> float:
        return round(self.simulated_shortage_risk_pct - self.baseline_shortage_risk_pct, 1)

    @property
    def service_level_delta_pct(self) -> float:
        return round(self.simulated_service_level_pct - self.baseline_service_level_pct, 1)


class SimulationEngine:
    """
    BloodFlow Digital Twin Simulation Engine.

    Runs deterministic what-if analysis against a snapshot of network state.
    Never modifies actual inventory records.
    """

    def run(
        self,
        facilities: List[FacilitySnapshot],
        scenario: SimulationScenario,
    ) -> SimulationResult:
        """
        Execute a scenario simulation and return a detailed impact report.
        """
        scenario_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # --- Baseline state ---
        baseline_snapshots = copy.deepcopy(facilities)
        baseline_result = self._evaluate_network(baseline_snapshots, scenario.horizon_hours)

        # --- Apply scenario to a deep copy ---
        simulated_snapshots = copy.deepcopy(facilities)
        simulated_snapshots = self._apply_scenario(simulated_snapshots, scenario)
        simulated_result = self._evaluate_network(simulated_snapshots, scenario.horizon_hours)

        # --- Build per-facility impact ---
        facility_impacts: List[FacilityImpact] = []
        critical = []

        baseline_map = {f.id: f for f in baseline_snapshots}
        simulated_map = {f.id: f for f in simulated_snapshots}

        for fid, base in baseline_map.items():
            sim = simulated_map[fid]
            base_sr = self._facility_shortage_risk(base, scenario.horizon_hours)
            sim_sr = self._facility_shortage_risk(sim, scenario.horizon_hours)
            base_waste = self._facility_wastage(base, scenario.horizon_hours)
            sim_waste = self._facility_wastage(sim, scenario.horizon_hours)
            is_critical = (sim_sr - base_sr) > 20.0

            if is_critical:
                critical.append(base.name)

            facility_impacts.append(FacilityImpact(
                facility_id=fid,
                facility_name=base.name,
                baseline_inventory=base.inventory,
                simulated_inventory=sim.inventory,
                baseline_shortage_risk_pct=base_sr,
                simulated_shortage_risk_pct=sim_sr,
                baseline_wastage_units=base_waste,
                simulated_wastage_units=sim_waste,
                is_critical=is_critical,
            ))

        mitigations = self._generate_mitigations(scenario, facility_impacts)

        return SimulationResult(
            scenario_id=scenario_id,
            scenario_description=scenario.description,
            horizon_hours=scenario.horizon_hours,
            generated_at=now,
            baseline_shortage_risk_pct=baseline_result["shortage_risk"],
            simulated_shortage_risk_pct=simulated_result["shortage_risk"],
            baseline_wastage_units=baseline_result["wastage"],
            simulated_wastage_units=simulated_result["wastage"],
            baseline_service_level_pct=baseline_result["service_level"],
            simulated_service_level_pct=simulated_result["service_level"],
            facility_impacts=facility_impacts,
            affected_facilities_count=len([fi for fi in facility_impacts if fi.is_critical]),
            critical_facilities=critical,
            recommended_mitigations=mitigations,
        )

    # ---- Internal helpers ----

    def _apply_scenario(
        self,
        snapshots: List[FacilitySnapshot],
        scenario: SimulationScenario,
    ) -> List[FacilitySnapshot]:
        for snap in snapshots:
            if snap.id in scenario.affected_facility_ids or not scenario.affected_facility_ids:
                if scenario.facility_offline:
                    snap.is_online = False
                    snap.inventory = 0
                elif scenario.supply_reduction_pct > 0:
                    snap.inventory = int(snap.inventory * (1 - scenario.supply_reduction_pct))
                if scenario.demand_multiplier != 1.0:
                    snap.daily_demand *= scenario.demand_multiplier
        return snapshots

    def _evaluate_network(
        self,
        snapshots: List[FacilitySnapshot],
        horizon_hours: int,
    ) -> Dict[str, Any]:
        online = [s for s in snapshots if s.is_online]
        total_inventory = sum(s.inventory for s in online)
        total_demand = sum(s.daily_demand * (horizon_hours / 24) for s in online)

        shortage_facilities = [s for s in online if self._facility_shortage_risk(s, horizon_hours) > 40]
        shortage_risk = len(shortage_facilities) / max(len(online), 1) * 100
        wastage = sum(self._facility_wastage(s, horizon_hours) for s in snapshots)
        service_level = min(100.0, (total_inventory / max(total_demand, 1)) * 100)

        return {
            "shortage_risk": round(shortage_risk, 1),
            "wastage": wastage,
            "service_level": round(service_level, 1),
        }

    def _facility_shortage_risk(self, snap: FacilitySnapshot, horizon_hours: int) -> float:
        if not snap.is_online:
            return 100.0
        projected_demand = snap.daily_demand * (horizon_hours / 24)
        if projected_demand <= 0:
            return 0.0
        surplus_ratio = snap.inventory / projected_demand
        # Transform to 0-100 risk score: low inventory relative to demand = high risk
        risk = max(0.0, 100.0 - (surplus_ratio * 50.0))
        return round(min(risk, 100.0), 1)

    def _facility_wastage(self, snap: FacilitySnapshot, horizon_hours: int) -> int:
        if not snap.is_online or snap.inventory == 0:
            return 0
        projected_demand = snap.daily_demand * (horizon_hours / 24)
        excess = max(0, snap.inventory - projected_demand)
        # Assume ~15% of excess inventory expires (conservative estimate)
        return int(excess * 0.15)

    def _generate_mitigations(
        self,
        scenario: SimulationScenario,
        impacts: List[FacilityImpact],
    ) -> List[str]:
        mitigations = []
        critical_impacts = [i for i in impacts if i.is_critical]

        if scenario.facility_offline:
            mitigations.append(
                f"Pre-position emergency reserves at the {len(critical_impacts)} most affected facilities "
                "before implementing planned outage."
            )
            mitigations.append(
                "Activate regional mutual-aid agreements with neighbouring blood banks."
            )

        if scenario.demand_multiplier > 1.2:
            mitigations.append(
                f"Accelerate donor drives to compensate for projected {int((scenario.demand_multiplier-1)*100)}% "
                "demand increase."
            )
            mitigations.append(
                "Restrict elective procedure blood reservations to protect emergency supply."
            )

        if scenario.transport_delay_multiplier > 1.1:
            mitigations.append(
                "Dispatch time-critical blood components via air transport to avoid road delays."
            )

        for impact in critical_impacts:
            deficit = impact.baseline_inventory - impact.simulated_inventory
            if deficit > 0:
                mitigations.append(
                    f"Transfer at least {deficit} units to {impact.facility_name} "
                    f"before scenario window (72h shortage risk: {impact.simulated_shortage_risk_pct:.0f}%)."
                )

        if not mitigations:
            mitigations.append(
                "Network resilience sufficient. No immediate mitigation required. "
                "Monitor KPIs and activate if risk escalates."
            )

        return mitigations
