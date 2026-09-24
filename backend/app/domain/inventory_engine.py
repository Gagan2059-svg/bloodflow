from typing import List, Dict, Any
from datetime import datetime, timedelta

def calculate_projected_inventory(
    current_inventory: int,
    incoming_transfers: int,
    confirmed_demand: int,
    expected_demand: int,
    expired_units: int
) -> int:
    """
    Calculates projected inventory based on the standard formula.
    """
    return current_inventory + incoming_transfers - confirmed_demand - expected_demand - expired_units

def calculate_shortage_risk(projected_inventory: int, emergency_reserve: int) -> float:
    """
    Returns a probability-like score (0.0 to 1.0) representing shortage risk.
    """
    if projected_inventory < 0:
        return 0.99
    
    # If we are below the emergency reserve, risk increases rapidly
    if projected_inventory < emergency_reserve:
        deficit = emergency_reserve - projected_inventory
        risk = 0.5 + (0.49 * (deficit / emergency_reserve))
        return min(risk, 0.99)
        
    # If we have healthy buffer
    buffer = projected_inventory - emergency_reserve
    if buffer > emergency_reserve * 2:
        return 0.05
        
    # Interpolate risk between 0.05 and 0.5 based on how close we are to dipping into the reserve
    risk = 0.05 + 0.45 * (1 - (buffer / (emergency_reserve * 2)))
    return max(0.05, min(0.5, risk))

def calculate_wastage_risk(expiring_units: int, expected_demand: int) -> float:
    """
    Returns a probability-like score (0.0 to 1.0) representing wastage risk.
    """
    if expiring_units == 0:
        return 0.01
        
    if expiring_units > expected_demand:
        surplus = expiring_units - expected_demand
        risk = 0.5 + (0.49 * min(surplus / expiring_units, 1.0))
        return risk
        
    # We expect to use the expiring units
    risk = 0.01 + 0.49 * (expiring_units / expected_demand)
    return risk

def get_inventory_health_score(
    current_inventory: int,
    shortage_risk: float,
    wastage_risk: float,
    historical_volatility: float
) -> int:
    """
    Calculates an overall inventory health score (0 to 100).
    Higher is better.
    """
    if current_inventory == 0:
        return 0
        
    # Penalty for shortage risk is much higher than wastage risk
    shortage_penalty = shortage_risk * 60
    wastage_penalty = wastage_risk * 30
    volatility_penalty = min(historical_volatility * 10, 10)
    
    score = 100 - (shortage_penalty + wastage_penalty + volatility_penalty)
    return int(max(0, min(100, score)))

def generate_health_report(
    facility_id: str,
    component_type: str,
    blood_group: str,
    current_inventory: int,
    incoming: int,
    confirmed_demand: int,
    expected_demand: int,
    expired_units: int,
    expiring_units: int,
    emergency_reserve: int,
    historical_volatility: float = 0.1
) -> Dict[str, Any]:
    
    projected = calculate_projected_inventory(
        current_inventory, incoming, confirmed_demand, expected_demand, expired_units
    )
    
    shortage_risk = calculate_shortage_risk(projected, emergency_reserve)
    wastage_risk = calculate_wastage_risk(expiring_units, expected_demand)
    
    health_score = get_inventory_health_score(
        current_inventory, shortage_risk, wastage_risk, historical_volatility
    )
    
    status = "Stable"
    if health_score < 40:
        status = "Critical"
    elif health_score < 70:
        status = "Warning"
        
    return {
        "facility_id": facility_id,
        "component": component_type,
        "blood_group": blood_group,
        "health_score": health_score,
        "status": status,
        "current_inventory": current_inventory,
        "projected_inventory": projected,
        "shortage_risk_probability": round(shortage_risk, 2),
        "wastage_risk_probability": round(wastage_risk, 2),
    }
