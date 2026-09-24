from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from app.models.inventory import InventoryUnit, UnitStatus, BloodComponent, BloodGroup

def calculate_current_inventory(units: List[InventoryUnit]) -> int:
    """Calculates the total number of available units."""
    return sum(1 for unit in units if unit.status == UnitStatus.AVAILABLE)

def identify_expiring_units(units: List[InventoryUnit], days_threshold: int = 3) -> List[InventoryUnit]:
    """Identifies units expiring within the given threshold (default 3 days)."""
    now = datetime.now(timezone.utc)
    threshold_date = now + timedelta(days=days_threshold)
    return [
        unit for unit in units 
        if unit.status == UnitStatus.AVAILABLE and unit.expiration_date <= threshold_date
    ]

def calculate_projected_inventory(
    current_inventory: int,
    incoming_transfers: int,
    confirmed_demand: int,
    expected_demand: int,
    expired_units_projection: int
) -> int:
    """
    Projected Inventory = Current + Incoming - Confirmed Demand - Expected Demand - Expired Units
    """
    return current_inventory + incoming_transfers - confirmed_demand - expected_demand - expired_units_projection

def calculate_inventory_health_score(
    current_inventory: int,
    projected_inventory: int,
    minimum_reserve: int,
    expiring_count: int,
    total_capacity: int
) -> int:
    """
    Calculates a health score from 0 to 100 for a facility's inventory.
    """
    if total_capacity <= 0:
        return 0
        
    score = 100
    
    # Penalty for dipping below minimum reserve
    if projected_inventory < minimum_reserve:
        deficit = minimum_reserve - projected_inventory
        score -= min(50, deficit * 2)  # Heavy penalty for deficit
        
    # Penalty for excess expiring units
    if current_inventory > 0:
        expiring_ratio = expiring_count / current_inventory
        score -= min(30, int(expiring_ratio * 100))
        
    # Penalty for overcapacity
    if current_inventory > total_capacity:
        score -= 20
        
    # Reward for stable projection
    if projected_inventory >= minimum_reserve and projected_inventory <= total_capacity * 0.8:
        score = min(100, score + 10)
        
    return max(0, score)

def get_inventory_summary_by_group(units: List[InventoryUnit]) -> Dict[BloodGroup, int]:
    """Summarizes available inventory by blood group."""
    summary = {bg: 0 for bg in BloodGroup}
    for unit in units:
        if unit.status == UnitStatus.AVAILABLE:
            summary[unit.blood_group] += 1
    return summary
