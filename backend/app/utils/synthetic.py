import random
from typing import List
from datetime import datetime, timedelta, timezone
import uuid

from app.models.facilities import Facility, FacilityType, OperatingStatus
from app.models.inventory import InventoryUnit, BloodGroup, BloodComponent, UnitStatus

class SyntheticDataGenerator:
    """Generates realistic synthetic data for BloodFlow demos and simulations."""

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def generate_facilities(self, num_facilities: int = 10, org_id: uuid.UUID = uuid.uuid4()) -> List[Facility]:
        facilities = []
        types = [FacilityType.HOSPITAL] * 7 + [FacilityType.BLOOD_BANK] * 2 + [FacilityType.REGIONAL_CENTER] * 1
        regions = ["North", "South", "East", "West", "Central"]

        for i in range(num_facilities):
            f_type = random.choice(types)
            cap = random.randint(1000, 5000) if f_type == FacilityType.REGIONAL_CENTER else random.randint(200, 1000)

            facility = Facility(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=f"Synthetic {f_type.value.replace('_', ' ').title()} {chr(65+i)}",
                facility_type=f_type,
                latitude=round(random.uniform(30.0, 45.0), 4),
                longitude=round(random.uniform(-120.0, -70.0), 4),
                region=random.choice(regions),
                capacity=cap,
                operating_status=OperatingStatus.OPERATIONAL
            )
            facilities.append(facility)
        return facilities

    def generate_inventory(self, facilities: List[Facility], fill_ratio: float = 0.6) -> List[InventoryUnit]:
        units = []
        now = datetime.now(timezone.utc)

        # Approximate distribution of blood groups in general population
        bg_weights = {
            BloodGroup.O_POS: 0.38, BloodGroup.A_POS: 0.34, BloodGroup.B_POS: 0.09, BloodGroup.O_NEG: 0.07,
            BloodGroup.A_NEG: 0.06, BloodGroup.AB_POS: 0.03, BloodGroup.B_NEG: 0.02, BloodGroup.AB_NEG: 0.01
        }
        bgs = list(bg_weights.keys())
        bg_probs = list(bg_weights.values())

        components = [BloodComponent.RBC, BloodComponent.PLASMA, BloodComponent.PLATELETS]

        for facility in facilities:
            target_units = int(facility.capacity * fill_ratio)
            for _ in range(target_units):
                bg = random.choices(bgs, weights=bg_probs, k=1)[0]
                comp = random.choice(components)

                # RBCs last 42 days, Plasma 1 yr, Platelets 5-7 days
                if comp == BloodComponent.PLATELETS:
                    days_to_expire = random.randint(1, 5)
                else:
                    days_to_expire = random.randint(2, 35)

                units.append(InventoryUnit(
                    id=uuid.uuid4(),
                    facility_id=facility.id,
                    blood_group=bg,
                    component=comp,
                    collection_date=now - timedelta(days=5),
                    expiration_date=now + timedelta(days=days_to_expire),
                    status=UnitStatus.AVAILABLE,
                    quantity_ml=250 if comp != BloodComponent.PLASMA else 200
                ))
        return units
