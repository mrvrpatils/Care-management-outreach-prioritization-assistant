import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.models import LoginModel
from app.services.auth_service import hash_password, verify_password


def test_password_hashing_and_verification():
    raw_pass = "SecureClinicalPass2026!"
    hashed = hash_password(raw_pass)
    
    assert hashed.startswith("pbkdf2:sha256:")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


def test_login_page_route():
    with TestClient(app) as client:
        r = client.get("/login")
        assert r.status_code == 200
        assert "CareWise AI" in r.text
        assert "Sign In" in r.text
        assert "Create Account" in r.text


def test_default_seeded_login_users():
    """Verify that default admin & caremanager accounts exist in SQL login table."""
    db = SessionLocal()
    try:
        admin = db.query(LoginModel).filter(LoginModel.username == "admin").first()
        assert admin is not None
        assert admin.role == "Administrator"
        assert verify_password("admin123", admin.password_hash) is True
        
        cm = db.query(LoginModel).filter(LoginModel.username == "caremanager").first()
        assert cm is not None
        assert cm.role == "Lead Care Manager"
        assert verify_password("password123", cm.password_hash) is True
    finally:
        db.close()


def test_login_endpoint_success_and_failure():
    with TestClient(app) as client:
        # Successful login as admin
        r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "Administrator"
        token = data["access_token"]

        # Access /api/auth/me with token
        r_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r_me.status_code == 200
        assert r_me.json()["username"] == "admin"

        # Invalid password
        r_bad = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
        assert r_bad.status_code == 401
        assert "Invalid" in r_bad.json()["detail"]

        # Non-existent user
        r_none = client.post("/api/auth/login", json={"username": "non_existent_user_xyz", "password": "any"})
        assert r_none.status_code == 401


def test_user_registration_and_db_persistence():
    unique_username = f"test_nurse_{SessionLocal().query(LoginModel).count() + 1}"
    with TestClient(app) as client:
        # 1. Register new user
        reg_payload = {
            "username": unique_username,
            "password": "Password@123",
            "full_name": "Nurse Evelyn Wright",
            "email": f"{unique_username}@carewise.health",
            "role": "Care Manager"
        }
        r = client.post("/api/auth/register", json=reg_payload)
        assert r.status_code == 200
        reg_data = r.json()
        assert "access_token" in reg_data
        assert reg_data["user"]["username"] == unique_username
        assert reg_data["user"]["full_name"] == "Nurse Evelyn Wright"
        assert reg_data["user"]["role"] == "Care Manager"

        # 2. Verify directly in the SQL database table
        db = SessionLocal()
        try:
            user_in_db = db.query(LoginModel).filter(LoginModel.username == unique_username).first()
            assert user_in_db is not None
            assert user_in_db.full_name == "Nurse Evelyn Wright"
            assert user_in_db.email == f"{unique_username}@carewise.health"
            assert verify_password("Password@123", user_in_db.password_hash) is True
        finally:
            db.close()

        # 3. Test logging in with newly registered credentials
        login_r = client.post("/api/auth/login", json={"username": unique_username, "password": "Password@123"})
        assert login_r.status_code == 200
        assert login_r.json()["user"]["username"] == unique_username

        # 4. Duplicate registration prevention
        dup_r = client.post("/api/auth/register", json=reg_payload)
        assert dup_r.status_code == 400
        assert "already taken" in dup_r.json()["detail"]


def test_auth_me_unauthorized():
    with TestClient(app) as client:
        r = client.get("/api/auth/me")
        assert r.status_code == 401

        r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.fake.token"})
        assert r.status_code == 401


def test_logout_endpoint():
    with TestClient(app) as client:
        r = client.post("/api/auth/logout")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
