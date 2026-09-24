from typing import List, Dict, Tuple
from pydantic import BaseModel
import uuid

try:
    from ortools.linear_solver import pywraplp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

class TransferRecommendation(BaseModel):
    source_facility_id: uuid.UUID
    destination_facility_id: uuid.UUID
    units_to_transfer: int
    expected_impact_score: float

def optimize_transfers(
    facility_surplus_deficit: Dict[uuid.UUID, int], 
    distances: Dict[Tuple[uuid.UUID, uuid.UUID], float]
) -> List[TransferRecommendation]:
    """
    Uses Google OR-Tools to optimize inventory transfers between facilities.
    Maximizes deficit fulfillment while penalizing transportation cost.

    facility_surplus_deficit: dict mapping facility_id to int. >0 means surplus, <0 means deficit.
    distances: dict mapping (source_id, dest_id) to transport cost/distance.
    """
    if not ORTOOLS_AVAILABLE:
        return []

    sources = [f for f, val in facility_surplus_deficit.items() if val > 0]
    destinations = [f for f, val in facility_surplus_deficit.items() if val < 0]

    if not sources or not destinations:
        return []

    # Use GLOP (LP relaxation) for speed; round to int afterwards
    solver = pywraplp.Solver.CreateSolver('GLOP')
    if not solver:
        # Fallback to SCIP
        solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return []

    # Large reward coefficient: fulfilling 1 unit of deficit is worth much more than any transport cost
    FULFILLMENT_REWARD = 10000.0

    # Decision variables: x[i, j] = units transferred from i to j
    x = {}
    for src in sources:
        for dst in destinations:
            max_transfer = min(facility_surplus_deficit[src], abs(facility_surplus_deficit[dst]))
            x[src, dst] = solver.NumVar(0, float(max_transfer), f'x_{src}_{dst}')

    # Slack variable for unmet deficit at each destination
    slack = {}
    for dst in destinations:
        deficit_amount = abs(facility_surplus_deficit[dst])
        slack[dst] = solver.NumVar(0, float(deficit_amount), f'slack_{dst}')

    # Constraint: Cannot transfer more than surplus at each source
    for src in sources:
        solver.Add(sum(x[src, dst] for dst in destinations) <= facility_surplus_deficit[src])

    # Constraint: Transfers + slack = deficit (fulfillment balance)
    for dst in destinations:
        deficit_amount = abs(facility_surplus_deficit[dst])
        solver.Add(sum(x[src, dst] for src in sources) + slack[dst] == deficit_amount)

    # Objective: Maximize fulfillment (minimize slack) while minimizing transport cost
    objective = solver.Objective()
    for src in sources:
        for dst in destinations:
            cost = distances.get((src, dst), 10.0)
            # Net coefficient: huge reward for fulfilling deficit, minus small transport cost
            objective.SetCoefficient(x[src, dst], FULFILLMENT_REWARD - cost)
    for dst in destinations:
        # Penalize unmet deficit
        objective.SetCoefficient(slack[dst], -FULFILLMENT_REWARD)
    objective.SetMaximization()

    status = solver.Solve()

    recommendations = []
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        for src in sources:
            for dst in destinations:
                transferred = round(x[src, dst].solution_value())
                if transferred > 0:
                    recommendations.append(TransferRecommendation(
                        source_facility_id=src,
                        destination_facility_id=dst,
                        units_to_transfer=transferred,
                        expected_impact_score=round(
                            FULFILLMENT_REWARD * transferred - distances.get((src, dst), 10.0) * transferred, 2
                        )
                    ))

    return recommendations
