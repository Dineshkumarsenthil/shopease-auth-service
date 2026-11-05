"""Automated version of the 14 mandatory scenarios (uses in-memory SQLite, no MySQL needed)."""
import os

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-1234567890"
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.database.connection import Base, get_db
from app.main import app
from app.models.user_model import User

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

USER = {"full_name": "Dinesh Kumar", "email": "dk@example.com",
        "password": "Strong@123", "confirm_password": "Strong@123"}


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def register(**over):
    return client.post("/api/auth/register", json={**USER, **over})


def login(email=USER["email"], password=USER["password"]):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_01_register_success():
    r = register()
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == USER["email"] and body["is_active"] is True and "user_id" in body
    assert "password" not in body and "password_hash" not in body


def test_02_register_duplicate_email():
    register()
    assert register().status_code == 409


def test_03_register_invalid_email():
    assert register(email="not-an-email").status_code == 422


def test_04_register_password_mismatch():
    assert register(confirm_password="Different@123").status_code == 422


def test_05_login_success():
    register()
    r = login()
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer" and r.json()["access_token"]


def test_06_login_wrong_password():
    register()
    assert login(password="Wrong@12345").status_code == 401


def test_07_login_inactive_user():
    register()
    db = TestingSession()
    db.query(User).update({"is_active": False})
    db.commit()
    db.close()
    assert login().status_code == 403


def test_08_me_with_valid_token():
    register()
    token = login().json()["access_token"]
    r = client.get("/api/auth/me", headers=auth(token))
    assert r.status_code == 200 and r.json()["email"] == USER["email"]


def test_09_protected_without_token():
    assert client.get("/api/auth/me").status_code == 401


def test_10_protected_with_invalid_token():
    assert client.get("/api/auth/me", headers=auth("abc.def.ghi")).status_code == 401


def test_11_protected_with_expired_token():
    register()
    expired = create_access_token(1, "user", expires_minutes=-5)
    r = client.get("/api/auth/me", headers=auth(expired))
    assert r.status_code == 401 and "expired" in r.json()["detail"].lower()


def test_12_change_password_success():
    register()
    token = login().json()["access_token"]
    r = client.post("/api/auth/change-password", headers=auth(token), json={
        "current_password": USER["password"], "new_password": "NewPass@456",
        "confirm_new_password": "NewPass@456"})
    assert r.status_code == 200


def test_13_change_password_wrong_current():
    register()
    token = login().json()["access_token"]
    r = client.post("/api/auth/change-password", headers=auth(token), json={
        "current_password": "Wrong@12345", "new_password": "NewPass@456",
        "confirm_new_password": "NewPass@456"})
    assert r.status_code == 400


def test_14_new_password_works_old_fails():
    register()
    token = login().json()["access_token"]
    client.post("/api/auth/change-password", headers=auth(token), json={
        "current_password": USER["password"], "new_password": "NewPass@456",
        "confirm_new_password": "NewPass@456"})
    assert login(password="NewPass@456").status_code == 200
    assert login().status_code == 401


def test_verify_token_valid_and_invalid():
    register()
    token = login().json()["access_token"]
    ok = client.post("/api/auth/verify-token", json={"token": token})
    assert ok.status_code == 200 and ok.json()["valid"] is True and ok.json()["role"] == "user"
    assert client.post("/api/auth/verify-token", json={"token": "bad"}).status_code == 401
