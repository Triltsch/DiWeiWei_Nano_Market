"""Tests for authentication API routes"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.modules.auth.service import verify_user_email
from app.schemas import UserRegister


@pytest.mark.asyncio
async def test_register_endpoint_success(client: TestClient, test_user_data: dict):
    """Test /auth/register endpoint with valid data"""
    response = client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"].lower()
    assert data["username"] == test_user_data["username"]
    assert not data["email_verified"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_register_endpoint_missing_required_field(client: TestClient, test_user_data: dict):
    """Test /auth/register with missing required field"""
    del test_user_data["password"]
    response = client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_endpoint_invalid_email(client: TestClient, test_user_data: dict):
    """Test /auth/register with invalid email"""
    test_user_data["email"] = "invalid-email"
    response = client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_endpoint_weak_password(client: TestClient, test_user_data: dict):
    """Test /auth/register with weak password"""
    test_user_data["password"] = "weak"
    response = client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code in (400, 422)
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_register_endpoint_duplicate_email(
    client: TestClient, db_session, test_user_data: dict
):
    """Test /auth/register with duplicate email"""
    # Register first user
    response1 = client.post("/api/v1/auth/register", json=test_user_data)
    assert response1.status_code == 201

    # Try to register with same email
    test_user_data["username"] = "different_user"
    response2 = client.post("/api/v1/auth/register", json=test_user_data)

    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_endpoint_duplicate_username(client: TestClient, test_user_data: dict):
    """Test /auth/register with duplicate username"""
    # Register first user
    response1 = client.post("/api/v1/auth/register", json=test_user_data)
    assert response1.status_code == 201

    # Try to register with same username
    test_user_data["email"] = "different@example.com"
    response2 = client.post("/api/v1/auth/register", json=test_user_data)

    assert response2.status_code == 409
    assert "already taken" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_endpoint_db_unavailable_returns_503(
    client: TestClient, test_user_data: dict, monkeypatch: pytest.MonkeyPatch
):
    """Test /auth/register returns 503 when database is unavailable"""

    async def mock_register_user(*args, **kwargs):
        raise OperationalError(
            statement="SELECT 1",
            params={},
            orig=OSError("Connect call failed"),
        )

    monkeypatch.setattr("app.modules.auth.router.register_user", mock_register_user)

    response = client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code == 503
    assert response.json()["detail"] == "Service temporarily unavailable. Please try again later."


@pytest.mark.asyncio
async def test_login_endpoint_not_verified(client: TestClient, test_user_data: dict):
    """Test /auth/login fails if email not verified"""
    # Register user
    client.post("/api/v1/auth/register", json=test_user_data)

    # Try to login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 403
    assert "verified" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_endpoint_invalid_password(
    client: TestClient, db_session, test_user_data: dict
):
    """Test /auth/login with invalid password"""
    # Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Verify user email
    from uuid import UUID

    await verify_user_email(db_session, UUID(user_id))

    # Try to login with wrong password
    login_data = {
        "email": test_user_data["email"],
        "password": "WrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_endpoint_invalid_email(client: TestClient):
    """Test /auth/login with invalid email"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "SomePassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_endpoint_success(client: TestClient, db_session, test_user_data: dict):
    """Test successful /auth/login"""
    # Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Verify user
    from uuid import UUID

    await verify_user_email(db_session, UUID(user_id))

    # Login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 15 * 60


@pytest.mark.asyncio
async def test_login_endpoint_locked_account(client: TestClient, db_session, test_user_data: dict):
    """Test login fails for locked account - tested via service layer"""
    from uuid import UUID

    import pytest

    from app.modules.auth.service import AccountLockedError, authenticate_user, record_failed_login

    # Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Verify email to allow login
    from app.modules.auth.service import verify_user_email

    await verify_user_email(db_session, UUID(user_id))

    # Lock account at service level
    for _ in range(3):
        await record_failed_login(db_session, test_user_data["email"])

    # Try to login - should fail with AccountLockedError
    with pytest.raises(AccountLockedError):
        await authenticate_user(db_session, test_user_data["email"], test_user_data["password"])


@pytest.mark.asyncio
async def test_refresh_token_endpoint_success(client: TestClient, db_session, test_user_data: dict):
    """Test successful token refresh"""
    # Register and verify user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    from uuid import UUID

    await verify_user_email(db_session, UUID(user_id))

    # Login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    # Refresh
    response = client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_endpoint_invalid_token(client: TestClient):
    """Test refresh with invalid token"""
    response = client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": "invalid_token"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_endpoint_missing_token(client: TestClient):
    """Test refresh with missing token in body"""
    response = client.post(
        "/api/v1/auth/refresh-token",
        json={},
    )

    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_health_check_endpoint(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: TestClient):
    """Test root endpoint"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data
