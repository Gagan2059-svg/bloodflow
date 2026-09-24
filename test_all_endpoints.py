import requests
import time
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def print_result(name, res, expected_status=200):
    if res.status_code == expected_status:
        print(f"PASS: {name} (Status {res.status_code})")
    else:
        print(f"FAIL: {name} - Expected {expected_status}, got {res.status_code}")
        try:
            print("Response:", res.json())
        except:
            print("Response:", res.text)

print("Starting Comprehensive API Tests for BloodFlow...\n")

# --- 1. System Health ---
res = requests.get("http://localhost:8000/health")
print_result("System Health", res)

res = requests.get("http://localhost:8000/ready")
print_result("System Ready", res)

# --- 2. Auth (Mock) ---
res = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "password"})
print_result("Auth Login (Expected Failure due to mock)", res, 401)

# --- 3. Facilities ---
res = requests.get(f"{BASE_URL}/facilities/")
print_result("List Facilities", res)
facilities = res.json()
if isinstance(facilities, dict) and "items" in facilities:
    facilities = facilities["items"]
if not facilities:
    print("No facilities found. Creating one for tests...")
    test_org_id = str(uuid.uuid4())
    fac_payload = {
        "organization_id": test_org_id,
        "name": "Test Hospital Alpha",
        "facility_type": "HOSPITAL",
        "latitude": 34.05,
        "longitude": -118.24,
        "region": "West",
        "capacity": 500,
        "operating_status": "OPERATIONAL"
    }
    res = requests.post(f"{BASE_URL}/facilities/", json=fac_payload)
    print_result("Create Facility", res)
    fac_id = res.json().get("id")
else:
    fac_id = facilities[0]["id"]
    test_org_id = facilities[0]["organization_id"]

if fac_id:
    res = requests.get(f"{BASE_URL}/facilities/{fac_id}")
    print_result("Get Facility by ID", res)

# --- 4. Inventory ---
res = requests.get(f"{BASE_URL}/inventory/")
print_result("List Inventory", res)

res = requests.get(f"{BASE_URL}/inventory/summary")
print_result("Inventory Summary", res)

res = requests.get(f"{BASE_URL}/inventory/export/csv")
print_result("Export Inventory CSV", res)

# --- 5. Alerts ---
res = requests.get(f"{BASE_URL}/alerts/")
print_result("List Alerts", res)
alerts = res.json()
if isinstance(alerts, dict) and "items" in alerts:
    alerts = alerts["items"]
if alerts:
    alert_id = alerts[0]["id"]
    res = requests.post(f"{BASE_URL}/alerts/{alert_id}/acknowledge")
    print_result("Acknowledge Alert", res)
    res = requests.post(f"{BASE_URL}/alerts/{alert_id}/resolve")
    print_result("Resolve Alert", res)

# --- 6. Recommendations ---
res = requests.get(f"{BASE_URL}/recommendations/")
print_result("List Recommendations", res)
recs = res.json()
if isinstance(recs, dict) and "items" in recs:
    recs = recs["items"]
if recs:
    rec_id = recs[0]["id"]
    res = requests.post(f"{BASE_URL}/recommendations/{rec_id}/approve")
    print_result("Approve Recommendation", res)

# --- 7. Transfers ---
res = requests.get(f"{BASE_URL}/transfers/")
print_result("List Transfers", res)

transfer_payload = {
    "organization_id": test_org_id,
    "source_facility_id": fac_id,
    "dest_facility_id": fac_id,
    "blood_group": "O+",
    "component": "RBC",
    "quantity": 10
}
res = requests.post(f"{BASE_URL}/transfers/", json=transfer_payload)
print_result("Create Transfer", res)
if res.status_code == 200:
    transfer_id = res.json()["id"]
    res = requests.post(f"{BASE_URL}/transfers/{transfer_id}/status?status=COMPLETED")
    print_result("Complete Transfer", res)

# --- 8. Demand ---
res = requests.get(f"{BASE_URL}/demand/")
print_result("List Demand", res)

demand_payload = {
    "organization_id": test_org_id,
    "facility_id": fac_id,
    "blood_group": "A-",
    "component": "PLASMA",
    "requested_quantity": 25,
    "is_emergency": True
}
res = requests.post(f"{BASE_URL}/demand/", json=demand_payload)
print_result("Create Demand Record", res)

# --- 9. Anomalies ---
anomaly_payload = {
    "facility_id": fac_id,
    "blood_group": "AB+",
    "component": "PLATELETS",
    "observed_demand": 50.5,
    "historical_demand": [10, 12, 11, 10, 12, 11, 48, 55]
}
res = requests.post(f"{BASE_URL}/anomalies/detect", json=anomaly_payload)
print_result("Detect Anomaly", res)

# --- 10. Explainability ---
explain_payload = {
    "query": "Why did the system recommend transferring O+ blood from Hub A to Hospital B?",
    "context": {"recommendation_id": "REC-123", "hub_inventory": 500, "hospital_inventory": 10}
}
res = requests.post(f"{BASE_URL}/explain/", json=explain_payload)
print_result("Explain AI Decision", res)

print("\nComprehensive Test Suite Completed!")

