import uuid
from app.models.organizations import Organization, OrganizationType
from app.models.users import User, UserRole, UserStatus
from app.security.auth import get_password_hash

def seed_demo_data(db_session):
    org = Organization(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Org",
        type=OrganizationType.REGIONAL_CENTER,
    )
    db_session.add(org)
    db_session.flush()

    admin = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        organization_id=org.id,
        name="Test Admin",
        email="admin@bloodflow.local",
        password_hash=get_password_hash("BloodFlow2026!"),
        role=UserRole.ORG_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(admin)
    db_session.commit()

def test_login_success(client, db_session):
    seed_demo_data(db_session)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@bloodflow.local", "password": "BloodFlow2026!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure(client, db_session):
    seed_demo_data(db_session)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@bloodflow.local", "password": "wrongpassword!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

def test_auth_me(client, db_session):
    seed_demo_data(db_session)
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@bloodflow.local", "password": "BloodFlow2026!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_resp.json()["access_token"]

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "admin@bloodflow.local"
