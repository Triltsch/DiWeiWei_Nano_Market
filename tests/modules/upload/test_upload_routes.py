"""
Tests for upload API routes.

This module tests the complete upload workflow through API endpoints.
"""

import io
import zipfile

import pytest

from app.models import NanoStatus


class TestUploadNanoEndpoint:
    """
    Test suite for POST /api/v1/upload/nano endpoint.

    Tests the complete upload workflow including authentication,
    validation, and Nano record creation.
    """

    @pytest.mark.asyncio
    async def test_upload_nano_success(self, async_client, verified_user_id, db_session):
        """Test successful Nano upload with valid ZIP file."""
        # Create a valid ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("module.pdf", "Learning content")
            zf.writestr("exercises/exercise1.txt", "Exercise content")

        zip_buffer.seek(0)

        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Upload the file
        response = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("learning_module.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201
        data = response.json()
        assert "nano_id" in data
        assert data["status"] == "draft"
        assert data["title"] == "learning_module"
        assert "uploaded_at" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_upload_nano_requires_authentication(self, async_client):
        """Test that upload endpoint requires authentication."""
        # Create a valid ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test.txt", "Content")

        zip_buffer.seek(0)

        # Try to upload without authentication
        response = await async_client.post(
            "/api/v1/upload/nano",
            files={"file": ("test.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_nano_rejects_invalid_token(self, async_client):
        """Test that upload endpoint rejects invalid authentication tokens."""
        # Create a valid ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test.txt", "Content")

        zip_buffer.seek(0)

        # Try to upload with invalid token
        response = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": "Bearer invalid_token_12345"},
            files={"file": ("test.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_nano_rejects_non_zip_file(self, async_client, verified_user_id):
        """Test that non-ZIP files are rejected."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Create a non-ZIP file
        pdf_content = b"%PDF-1.4\nFake PDF content"
        pdf_buffer = io.BytesIO(pdf_content)

        # Try to upload
        response = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("document.pdf", pdf_buffer, "application/pdf")},
        )

        assert response.status_code == 400
        assert "zip" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_nano_rejects_empty_zip(self, async_client, verified_user_id):
        """Test that empty ZIP files are rejected."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Create an empty ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            pass  # Don't add any files

        zip_buffer.seek(0)

        # Try to upload
        response = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("empty.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_nano_rejects_corrupt_zip(self, async_client, verified_user_id):
        """Test that corrupt ZIP files are rejected."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Create corrupt ZIP content
        corrupt_buffer = io.BytesIO(b"This is not a valid ZIP file")

        # Try to upload
        response = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("corrupt.zip", corrupt_buffer, "application/zip")},
        )

        assert response.status_code == 400
        assert (
            "invalid" in response.json()["detail"].lower()
            or "corrupt" in response.json()["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_upload_nano_creates_draft_record(
        self, async_client, verified_user_id, db_session
    ):
        """Test that upload creates a Nano record with draft status."""
        from uuid import UUID

        from sqlalchemy import select

        from app.models import Nano

        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Create a valid ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.txt", "Learning material")

        zip_buffer.seek(0)

        # Upload
        response = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test_module.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201
        nano_id = UUID(response.json()["nano_id"])

        # Verify database record
        query = select(Nano).where(Nano.id == nano_id)
        result = await db_session.execute(query)
        nano = result.scalar_one()

        assert nano.creator_id == verified_user_id
        assert nano.status == NanoStatus.DRAFT
        assert nano.title == "test_module"
        assert nano.file_storage_path is None  # Not set yet (MinIO integration pending)

    @pytest.mark.asyncio
    async def test_upload_nano_rejects_filename_without_zip_extension(
        self, async_client, verified_user_id
    ):
        """Test that files without .zip extension are rejected even with correct MIME type."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Create a valid ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.txt", "Learning material")

        zip_buffer.seek(0)

        # Upload with filename without .zip extension
        response = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("noextension", zip_buffer, "application/zip")},
        )

        assert response.status_code == 400
        assert "zip" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_nano_multiple_uploads_create_separate_records(
        self, async_client, verified_user_id, db_session
    ):
        """Test that multiple uploads by the same user create separate Nano records."""
        from sqlalchemy import select

        from app.models import Nano

        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Upload first file
        zip_buffer1 = io.BytesIO()
        with zipfile.ZipFile(zip_buffer1, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("module1.txt", "Content 1")
        zip_buffer1.seek(0)

        response1 = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("module1.zip", zip_buffer1, "application/zip")},
        )
        assert response1.status_code == 201
        nano_id1 = response1.json()["nano_id"]

        # Upload second file
        zip_buffer2 = io.BytesIO()
        with zipfile.ZipFile(zip_buffer2, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("module2.txt", "Content 2")
        zip_buffer2.seek(0)

        response2 = await async_client.post(
            "/api/v1/upload/nano",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("module2.zip", zip_buffer2, "application/zip")},
        )
        assert response2.status_code == 201
        nano_id2 = response2.json()["nano_id"]

        # Verify both records exist and are different
        assert nano_id1 != nano_id2

        query = select(Nano).where(Nano.creator_id == verified_user_id)
        result = await db_session.execute(query)
        nanos = result.scalars().all()

        assert len(nanos) == 2
        assert all(nano.status == NanoStatus.DRAFT for nano in nanos)
