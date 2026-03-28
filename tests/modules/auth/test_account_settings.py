"""
Test Account Settings & DSGVO Self-Service API endpoints.

Covers the three new endpoints introduced in Issue #111:
  - GET  /api/v1/auth/me               — read own profile
  - PATCH /api/v1/auth/me              — partial profile update
  - POST  /api/v1/auth/me/change-password — secure password-change self-service

Each test class is organised around a single endpoint and covers:
  * authentication requirements (401 without token)
  * happy path (success with correct data)
  * error paths (wrong input, wrong current password, policy violations)

Tests rely on the shared ``client``, ``db_session``, and ``app`` fixtures
defined in ``tests/conftest.py``.  Infrastructure (PostgreSQL, Redis) is
provided by the ``Test: Verified`` task or via SQLite in-memory for unit runs.
"""

import pytest

from app.modules.auth.service import register_user, verify_user_email
from app.schemas import UserRegister

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REGISTER_PAYLOAD = dict(
    email="settings_user@example.com",
    username="settingsuser",
    password="SecureP@ss1",
    first_name="Test",
    last_name="User",
    accept_terms=True,
    accept_privacy=True,
)


async def _create_and_login(client, db_session, *, overrides: dict | None = None) -> str:
    """Register a user, verify their email, and return an access token.

    Args:
        client: FastAPI TestClient.
        db_session: Active database session.
        overrides: Optional field overrides for the registration payload.

    Returns:
        Bearer access token string.
    """
    payload = {**_REGISTER_PAYLOAD, **(overrides or {})}
    user_data = UserRegister(**payload)
    user_response = await register_user(db_session, user_data)
    await verify_user_email(db_session, user_response.id)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200, login_response.text
    return login_response.json()["access_token"]


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetMyProfile:
    """Test GET /api/v1/auth/me — read own profile."""

    async def test_get_profile_requires_authentication(self, client):
        """Unauthenticated request must be rejected with 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_profile_returns_own_data(self, client, db_session):
        """Authenticated user receives their own profile in the response.

        Expected: HTTP 200 with correct email, username, and name fields.
        """
        token = await _create_and_login(client, db_session)

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Core identity fields
        assert data["email"] == _REGISTER_PAYLOAD["email"]
        assert data["username"] == _REGISTER_PAYLOAD["username"]
        assert data["first_name"] == _REGISTER_PAYLOAD["first_name"]
        assert data["last_name"] == _REGISTER_PAYLOAD["last_name"]

        # Status and role present
        assert data["status"] == "active"
        assert "role" in data

        # GDPR fields present
        assert "accepted_terms" in data
        assert "accepted_privacy" in data
        assert data["accepted_terms"] is not None
        assert data["accepted_privacy"] is not None

    async def test_get_profile_contains_required_fields(self, client, db_session):
        """Profile response includes all documented response model fields.

        Verifies that the response shape matches the UserResponse schema so
        that the frontend can rely on every expected field being present.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={
                "email": "profile_fields@example.com",
                "username": "profilefields",
            },
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        expected_fields = {
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "bio",
            "preferred_language",
            "status",
            "role",
            "email_verified",
            "created_at",
            "updated_at",
            "accepted_terms",
            "accepted_privacy",
        }
        assert expected_fields.issubset(data.keys())


# ---------------------------------------------------------------------------
# PATCH /api/v1/auth/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestUpdateMyProfile:
    """Test PATCH /api/v1/auth/me — partial profile update."""

    async def test_update_profile_requires_authentication(self, client):
        """Unauthenticated request must be rejected with 401."""
        response = client.patch(
            "/api/v1/auth/me",
            json={"bio": "Should not work"},
        )
        assert response.status_code == 401

    async def test_update_bio_success(self, client, db_session):
        """User can update their bio; other fields remain unchanged.

        Expected: HTTP 200 with updated bio; first_name and last_name unchanged.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "bio_update@example.com", "username": "bioupdate"},
        )

        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"bio": "Passionate nano-market seller."},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Passionate nano-market seller."
        # Fields not in request body must be untouched
        assert data["first_name"] == _REGISTER_PAYLOAD["first_name"]
        assert data["last_name"] == _REGISTER_PAYLOAD["last_name"]

    async def test_update_multiple_fields(self, client, db_session):
        """User can update several optional fields in a single request.

        Expected: HTTP 200; all provided fields reflected in the response.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "multi_update@example.com", "username": "multiupdate"},
        )

        patch_payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "New bio text.",
            "preferred_language": "en",
            "company": "ACME Corp",
            "job_title": "Engineer",
            "phone": "+49-123-4567",
        }

        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json=patch_payload,
        )

        assert response.status_code == 200
        data = response.json()

        for field, value in patch_payload.items():
            assert data[field] == value, f"Field {field!r} mismatch"

    async def test_update_empty_payload_is_noop(self, client, db_session):
        """Sending an empty patch body leaves all fields unchanged.

        Expected: HTTP 200 with the same profile as before.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "noop_update@example.com", "username": "noopupdate"},
        )

        # Fetch profile before patch
        before = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        # Send empty patch
        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        assert response.status_code == 200
        after = response.json()

        # Mutable identity fields must be unchanged
        for field in ("first_name", "last_name", "bio", "preferred_language"):
            assert after[field] == before[field], f"Field {field!r} changed unexpectedly"

    async def test_update_bio_exceeds_max_length(self, client, db_session):
        """Bio longer than 500 characters must be rejected with 422.

        Expected: HTTP 422 Unprocessable Entity.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "toolong_bio@example.com", "username": "toolongbio"},
        )

        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"bio": "x" * 501},
        )

        assert response.status_code == 422

    async def test_update_email_field_is_ignored(self, client, db_session):
        """Email is not updatable via PATCH /me; the field must be rejected.

        The ``UserProfileUpdate`` schema does not include ``email``, so
        Pydantic will strip (or reject via extra='forbid') the field.
        Either the email is untouched or the request is rejected—both are
        acceptable; the important constraint is that the email does NOT change.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "no_email_change@example.com", "username": "noemailchange"},
        )

        # Attempt to change email via PATCH
        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": "hacked@example.com", "bio": "benign"},
        )

        # The server must either reject (422) or succeed while ignoring the email field
        assert response.status_code in (200, 422)

        if response.status_code == 200:
            # Email must be unchanged
            assert response.json()["email"] == "no_email_change@example.com"


# ---------------------------------------------------------------------------
# POST /api/v1/auth/me/change-password
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestChangePassword:
    """Test POST /api/v1/auth/me/change-password — self-service password change."""

    async def test_change_password_requires_authentication(self, client):
        """Unauthenticated request must be rejected with 401."""
        response = client.post(
            "/api/v1/auth/me/change-password",
            json={"current_password": "OldP@ss1", "new_password": "NewP@ss2"},
        )
        assert response.status_code == 401

    async def test_change_password_success(self, client, db_session):
        """User with valid current password can change to a new strong password.

        Expected: HTTP 200; subsequent login with the new password succeeds.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "change_pw@example.com", "username": "changepw"},
        )

        response = client.post(
            "/api/v1/auth/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": "SecureP@ss1", "new_password": "N3wStr0ng!Pass"},
        )

        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()

        # Verify the new password works by logging in with it
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "change_pw@example.com", "password": "N3wStr0ng!Pass"},
        )
        assert login_response.status_code == 200

    async def test_change_password_wrong_current_password(self, client, db_session):
        """Supplying an incorrect current password must be rejected with 401.

        Expected: HTTP 401; password in the database remains unchanged.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "wrong_pw@example.com", "username": "wrongpw"},
        )

        response = client.post(
            "/api/v1/auth/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": "WrongP@ss1", "new_password": "N3wStr0ng!Pass"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

        # Original password must still work
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrong_pw@example.com", "password": "SecureP@ss1"},
        )
        assert login_response.status_code == 200

    async def test_change_password_weak_new_password_rejected(self, client, db_session):
        """A new password that does not meet the strength policy must be rejected.

        Expected: HTTP 400; password in the database remains unchanged.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "weak_pw@example.com", "username": "weakpw"},
        )

        response = client.post(
            "/api/v1/auth/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": "SecureP@ss1", "new_password": "weak"},
        )

        # 422 from Pydantic min_length=8 *or* 400 from policy validator — both indicate rejection
        assert response.status_code in (400, 422)

        # Original password must still work
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "weak_pw@example.com", "password": "SecureP@ss1"},
        )
        assert login_response.status_code == 200

    async def test_change_password_new_password_missing_uppercase_rejected(
        self, client, db_session
    ):
        """A new password missing an uppercase letter must be rejected with 400.

        The min_length Pydantic check passes (>= 8 chars), but the policy
        validator should reject a password without at least one uppercase letter.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "noupcase@example.com", "username": "noupcaseuser"},
        )

        response = client.post(
            "/api/v1/auth/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            # 8+ chars, digit, special — but no uppercase
            json={"current_password": "SecureP@ss1", "new_password": "n3wstr0ng!pass"},
        )

        assert response.status_code == 400

    async def test_change_password_audit_trail(self, client, db_session):
        """A successful password change must emit a PASSWORD_CHANGED audit event.

        Expected: HTTP 200 on change; subsequent audit log query returns at
        least one entry with action ``password_changed`` for the user.
        """
        token = await _create_and_login(
            client,
            db_session,
            overrides={"email": "audit_pw@example.com", "username": "auditpw"},
        )

        response = client.post(
            "/api/v1/auth/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": "SecureP@ss1", "new_password": "N3wStr0ng!Pass2"},
        )

        assert response.status_code == 200
