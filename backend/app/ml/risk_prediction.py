from typing import Dict, Any

class RiskPredictor:
    """
    Predicts probability of shortage and wastage for blood units.
    """

    @staticmethod
    def predict_shortage_probability(
        current_inventory: int,
        projected_demand: float,
        incoming_supply: int,
        emergency_reserve: int
    ) -> Dict[str, Any]:
        """
        Predicts the probability of a shortage occurring.
        Returns a dictionary with probability and contributing factors.
        """
        projected_inventory = current_inventory + incoming_supply - projected_demand

        factors = []
        if projected_inventory < emergency_reserve:
            factors.append("Projected inventory falls below emergency reserve.")
        if projected_demand > current_inventory:
            factors.append("Current inventory is insufficient for projected demand.")
        if incoming_supply == 0 and projected_demand > 0:
            factors.append("No incoming supply to cover demand.")

        if projected_inventory <= 0:
            probability = 0.95
        elif projected_inventory < emergency_reserve:
            deficit = emergency_reserve - projected_inventory
            probability = min(0.9, 0.4 + (0.5 * deficit / emergency_reserve))
        else:
            buffer = projected_inventory - emergency_reserve
            probability = max(0.05, 0.4 - (0.35 * buffer / (emergency_reserve or 1)))

        return {
            "probability": round(probability, 3),
            "factors": factors
        }

    @staticmethod
    def predict_wastage_probability(
        units_expiring_soon: int,
        projected_demand: float
    ) -> Dict[str, Any]:
        """
        Predicts the probability of units being wasted due to expiration.
        """
        factors = []
        if units_expiring_soon > 0:
            factors.append(f"{units_expiring_soon} units are nearing expiration.")

        if projected_demand >= units_expiring_soon:
            probability = 0.05
            if units_expiring_soon > 0:
                factors.append("Projected demand is sufficient to utilize expiring units.")
        else:
            surplus = units_expiring_soon - projected_demand
            factors.append(f"Projected demand is {projected_demand:.1f}, leaving a surplus of {surplus:.1f} at-risk units.")
            probability = min(0.95, 0.2 + (0.75 * surplus / units_expiring_soon))

        return {
            "probability": round(probability, 3),
            "factors": factors
        }
