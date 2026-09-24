import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.models.users import UserRole
from app.domain.compatibility import BloodGroup, ComponentType

def generate_organizations(count: int = 1) -> List[Dict[str, Any]]:
    orgs = []
    for i in range(count):
        orgs.append({
            "id": uuid.uuid4(),
            "name": f"Regional Health Network {i+1}",
            "type": "HOSPITAL_NETWORK",
            "created_at": datetime.utcnow()
        })
    return orgs

def generate_users(org_id: uuid.UUID, count: int = 5) -> List[Dict[str, Any]]:
    users = []
    roles = [UserRole.ORG_ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.BLOOD_BANK_MANAGER, UserRole.LOGISTICS_COORDINATOR, UserRole.ANALYST]
    for i in range(count):
        users.append({
            "id": uuid.uuid4(),
            "organization_id": org_id,
            "name": f"User {i+1}",
            "email": f"user{i+1}@network.local",
            "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", # "password"
            "role": roles[i % len(roles)],
            "status": "ACTIVE"
        })
    return users

def generate_facilities(org_id: uuid.UUID, count: int = 12) -> List[Dict[str, Any]]:
    facilities = []
    # Mix of hospitals and blood banks
    for i in range(count):
        is_blood_bank = (i % 4 == 0)
        facilities.append({
            "id": uuid.uuid4(),
            "organization_id": org_id,
            "name": f"Regional Blood Center {i+1}" if is_blood_bank else f"General Hospital {i+1}",
            "facility_type": "BLOOD_BANK" if is_blood_bank else "HOSPITAL",
            "latitude": 37.7749 + random.uniform(-0.1, 0.1),
            "longitude": -122.4194 + random.uniform(-0.1, 0.1),
            "region": "West Coast",
            "capacity": random.randint(500, 2000) if is_blood_bank else random.randint(100, 500),
            "operating_status": "NORMAL"
        })
    return facilities

def generate_inventory(facility_id: uuid.UUID, count: int = 100) -> List[Dict[str, Any]]:
    inventory = []
    blood_groups = [
        BloodGroup.O_POS, BloodGroup.A_POS, BloodGroup.B_POS, BloodGroup.O_NEG,
        BloodGroup.A_NEG, BloodGroup.AB_POS, BloodGroup.B_NEG, BloodGroup.AB_NEG
    ]
    # Realistic blood group distribution (US approx)
    bg_weights = [38, 34, 9, 7, 6, 3, 2, 1]

    components = [ComponentType.RBC, ComponentType.PLASMA, ComponentType.PLATELETS]
    comp_weights = [70, 20, 10]

    for _ in range(count):
        bg = random.choices(blood_groups, weights=bg_weights)[0]
        comp = random.choices(components, weights=comp_weights)[0]

        # Shelf life
        if comp == ComponentType.RBC:
            days_to_expire = random.randint(1, 42)
        elif comp == ComponentType.PLATELETS:
            days_to_expire = random.randint(1, 5)
        else:
            days_to_expire = random.randint(10, 365)

        collection_date = datetime.utcnow() - timedelta(days=random.randint(1, 10))
        expiration_date = datetime.utcnow() + timedelta(days=days_to_expire)

        inventory.append({
            "id": uuid.uuid4(),
            "blood_group": bg,
            "component": comp,
            "facility_id": facility_id,
            "collection_date": collection_date,
            "expiration_date": expiration_date,
            "status": "AVAILABLE",
            "quantity": 1,
            "source": "SYNTHETIC"
        })
    return inventory

def generate_demo_dataset() -> Dict[str, Any]:
    """Generates a complete coherent synthetic dataset for one organization."""
    orgs = generate_organizations(1)
    org_id = orgs[0]["id"]

    users = generate_users(org_id, 5)
    facilities = generate_facilities(org_id, 12)

    all_inventory = []
    for fac in facilities:
        # Blood banks have more inventory
        count = random.randint(200, 800) if fac["facility_type"] == "BLOOD_BANK" else random.randint(20, 150)
        inv = generate_inventory(fac["id"], count)
        all_inventory.extend(inv)

    return {
        "organizations": orgs,
        "users": users,
        "facilities": facilities,
        "inventory": all_inventory
    }
