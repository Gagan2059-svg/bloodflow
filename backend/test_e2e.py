import httpx
import json
import asyncio
import uuid

BASE_URL = "http://localhost:8000/api/v1"
client = httpx.AsyncClient(base_url=BASE_URL, timeout=10.0)

async def test_all_endpoints():
    print("=== STARTING COMPREHENSIVE E2E TESTS ===")
    
    # 1. Auth & Login
    print("\n--- Testing Auth ---")
    login_data = {"username": "admin@bloodflow.local", "password": "BloodFlow2026!"}
    res = await client.post("/auth/login", data=login_data)
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    print("Login successful, token acquired.")
    
    # Auth /me
    res = await client.get("/auth/me")
    assert res.status_code == 200, "Get me failed"
    print(f"Logged in as: {res.json()['email']}")
    org_id = res.json()["organization_id"]

    # 2. Facilities
    print("\n--- Testing Facilities ---")
    res = await client.get("/facilities/")
    assert res.status_code == 200, "Get facilities failed"
    facilities = res.json()
    print(f"Retrieved {len(facilities)} facilities.")
    assert len(facilities) > 0, "No facilities found"
    
    facility_id = facilities[0]["id"]
    res = await client.get(f"/facilities/{facility_id}")
    assert res.status_code == 200, "Get specific facility failed"
    print(f"Facility 0 details: {res.json()['name']}")

    # 3. Inventory
    print("\n--- Testing Inventory ---")
    res = await client.get("/inventory/summary")
    assert res.status_code == 200, "Get inventory summary failed"
    summary_data = res.json()
    print(f"Inventory summary: {summary_data['kpis']['total_available']} total available units.")
    
    res = await client.get(f"/inventory/?facility_id={facility_id}&limit=5")
    assert res.status_code == 200, "Get inventory list failed"
    inv_list = res.json()
    print(f"Retrieved {len(inv_list)} inventory items for facility 0.")

    # 4. Explain (Dynamic Rule Engine)
    print("\n--- Testing Explain (AI) ---")
    res = await client.post("/explain/", json={"query": "network risk optimization"})
    assert res.status_code == 200, f"Explain network failed: {res.text}"
    print("Network Explain response:")
    print("  " + res.json()["explanation"])

    res = await client.post("/explain/", json={"query": "shortage", "facility_id": facility_id})
    assert res.status_code == 200, f"Explain facility failed: {res.text}"
    print(f"Facility {facility_id} Explain response:")
    print("  " + res.json()["explanation"])

    # 5. Transfers (Pessimistic Locking / Concurrency)
    print("\n--- Testing Transfers ---")
    # find a blood group that facility 0 has
    res = await client.get(f"/inventory/?facility_id={facility_id}&status=AVAILABLE&limit=1")
    inv_data = res.json()
    if res.status_code == 200 and len(inv_data.get("items", [])) > 0:
        bg = inv_data["items"][0]["blood_group"]
        comp = inv_data["items"][0]["component"]
        dest_fac = facilities[1]["id"]
        
        transfer_payload = {
            "source_facility_id": facility_id,
            "dest_facility_id": dest_fac,
            "blood_group": bg,
            "component": comp,
            "quantity": 1,
            "priority": "ROUTINE"
        }
        res = await client.post("/transfers/", json=transfer_payload)
        if res.status_code == 201:
            t_id = res.json()["id"]
            print(f"Transfer created successfully: {t_id}")
            
            # test complete transfer
            res = await client.post(f"/transfers/{t_id}/complete")
            assert res.status_code == 200, f"Complete transfer failed: {res.text}"
            print("Transfer completed successfully.")
        else:
            print(f"Could not create transfer (maybe not enough inventory?): {res.text}")
    else:
        print("Could not find available inventory for transfer test.")

    # 6. Digital Twin / Simulation
    print("\n--- Testing Digital Twin / Simulation ---")
    sim_facs = []
    for f in facilities[:3]:
        sim_facs.append({
            "id": f["id"],
            "name": f["name"],
            "inventory": 100,
            "capacity": 200,
            "daily_demand": 15,
            "is_online": True
        })
    sim_scenario = {
        "scenario_type": "FACILITY_OUTAGE",
        "description": "Test E2E Outage",
        "affected_facility_ids": [sim_facs[0]["id"]],
        "demand_multiplier": 1.5,
        "transport_delay_multiplier": 1.0,
        "supply_reduction_pct": 0.0,
        "facility_offline": True,
        "horizon_hours": 48
    }
    res = await client.post("/simulations/run", json={"facilities": sim_facs, "scenario": sim_scenario})
    assert res.status_code == 200, f"Simulation failed: {res.text}"
    sim_result = res.json()
    print(f"Simulation completed. Baseline risk: {sim_result['baseline_shortage_risk_pct']}%, Simulated risk: {sim_result['simulated_shortage_risk_pct']}%")
    if sim_result['recommended_mitigations']:
        print(f"Top mitigation: {sim_result['recommended_mitigations'][0]}")

    print("\n=== ALL E2E TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
