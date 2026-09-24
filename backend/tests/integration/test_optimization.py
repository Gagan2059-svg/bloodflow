from app.optimization.transfer import optimize_transfers
import uuid

def test_optimize_transfers_resolves_deficits():
    fac_a = uuid.uuid4()
    fac_b = uuid.uuid4()

    # Facility A has surplus 50 units. Facility B has deficit 20 units.
    facility_surplus_deficit = {
        fac_a: 50,
        fac_b: -20
    }

    # Cost is 5 to move from A to B
    distances = {
        (fac_a, fac_b): 5.0
    }

    transfers = optimize_transfers(facility_surplus_deficit, distances)

    # Should move exactly 20 units to fulfill B's deficit
    assert len(transfers) == 1
    assert transfers[0].source_facility_id == fac_a
    assert transfers[0].destination_facility_id == fac_b
    assert transfers[0].units_to_transfer == 20

def test_optimize_transfers_insufficient_supply():
    fac_a = uuid.uuid4()
    fac_b = uuid.uuid4()

    # A has 10 surplus. B has 20 deficit.
    facility_surplus_deficit = {
        fac_a: 10,
        fac_b: -20
    }

    distances = {
        (fac_a, fac_b): 5.0
    }

    transfers = optimize_transfers(facility_surplus_deficit, distances)

    # Should move maximum 10 units
    assert len(transfers) == 1
    assert transfers[0].units_to_transfer == 10
