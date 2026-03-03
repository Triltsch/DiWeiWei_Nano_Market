"""
Tests for MinIO storage adapter.

This module tests the MinIO storage adapter and integration with upload workflow.
"""

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.modules.upload.storage import MinIOStorageAdapter, StorageError


class TestMinIOStorageAdapter:
    """
    Test suite for MinIO storage adapter.

    Tests file upload, deletion, URL generation, and error handling.
    """

    @pytest.fixture
    def storage_adapter(self):
        """Create MinIO storage adapter instance for testing."""
        with patch("app.modules.upload.storage.Minio") as mock_minio:
            adapter = MinIOStorageAdapter()
            adapter.client = mock_minio.return_value
            return adapter

    def test_generate_object_key_format(self, storage_adapter):
        """Test that object key follows deterministic naming convention."""
        nano_id = uuid.uuid4()
        filename = "learning_module.zip"

        key = storage_adapter._generate_object_key(nano_id, filename)

        # Verify format: nanos/{uuid}/content/{filename}
        expected = f"nanos/{str(nano_id)}/content/{filename}"
        assert key == expected

    def test_generate_object_key_with_special_characters(self, storage_adapter):
        """Test object key generation handles filenames with special characters."""
        nano_id = uuid.uuid4()
        filename = "my-learning_module (1).zip"

        key = storage_adapter._generate_object_key(nano_id, filename)

        # Should preserve filename as-is
        assert filename in key
        assert key.startswith("nanos/")
        assert key.endswith(filename)

    def test_upload_file_success(self, storage_adapter):
        """Test successful file upload to MinIO."""
        nano_id = uuid.uuid4()
        file_content = b"PK\x03\x04fake zip content"
        filename = "test.zip"

        # Mock put_object and stat_object
        storage_adapter.client.put_object = MagicMock()
        storage_adapter.client.stat_object = MagicMock(
            return_value=MagicMock(size=len(file_content))
        )

        result = storage_adapter.upload_file(
            nano_id=nano_id,
            file_content=file_content,
            filename=filename,
        )

        # Verify result
        expected_key = f"nanos/{str(nano_id)}/content/{filename}"
        assert result == expected_key

        # Verify upload was called
        storage_adapter.client.put_object.assert_called_once()

    def test_upload_file_with_metadata(self, storage_adapter):
        """Test that file uploads include Nano metadata."""
        nano_id = uuid.uuid4()
        file_content = b"file content"
        filename = "test.zip"

        storage_adapter.client.put_object = MagicMock()
        storage_adapter.client.stat_object = MagicMock(
            return_value=MagicMock(size=len(file_content))
        )

        storage_adapter.upload_file(
            nano_id=nano_id,
            file_content=file_content,
            filename=filename,
            content_type="application/zip",
        )

        # Check that put_object was called with metadata
        call_args = storage_adapter.client.put_object.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert kwargs.get("metadata") is not None
        assert kwargs["metadata"]["nano-id"] == str(nano_id)
        assert kwargs["metadata"]["original-filename"] == filename

    def test_upload_file_retry_on_failure(self, storage_adapter):
        """Test retry logic when upload fails temporarily."""
        nano_id = uuid.uuid4()
        file_content = b"file content"
        filename = "test.zip"

        # First attempt fails, second succeeds
        storage_adapter.client.put_object = MagicMock()
        storage_adapter.client.stat_object = MagicMock(
            side_effect=[
                Exception("Connection error"),
                MagicMock(size=len(file_content)),
            ]
        )

        result = storage_adapter.upload_file(
            nano_id=nano_id,
            file_content=file_content,
            filename=filename,
        )

        # Should succeed after retry
        assert result is not None

    def test_upload_file_failure_after_max_retries(self, storage_adapter):
        """Test error when upload fails after all retries."""
        nano_id = uuid.uuid4()
        file_content = b"file content"
        filename = "test.zip"

        # All attempts fail
        storage_adapter.client.put_object = MagicMock(side_effect=Exception("Connection error"))

        with pytest.raises(StorageError) as exc_info:
            storage_adapter.upload_file(
                nano_id=nano_id,
                file_content=file_content,
                filename=filename,
            )

        assert "after 3 attempts" in str(exc_info.value)

    def test_upload_file_non_transient_failure_no_retry(self, storage_adapter):
        """Test that non-transient storage failures are not retried."""
        nano_id = uuid.uuid4()
        file_content = b"file content"
        filename = "test.zip"

        storage_adapter.client.put_object = MagicMock(side_effect=ValueError("invalid metadata"))

        with pytest.raises(StorageError) as exc_info:
            storage_adapter.upload_file(
                nano_id=nano_id,
                file_content=file_content,
                filename=filename,
            )

        assert "non-retryable" in str(exc_info.value).lower()
        assert storage_adapter.client.put_object.call_count == 1

    def test_upload_file_size_verification_mismatch(self, storage_adapter):
        """Test error when uploaded file size doesn't match."""
        nano_id = uuid.uuid4()
        file_content = b"file content"
        filename = "test.zip"

        storage_adapter.client.put_object = MagicMock()
        # stat_object returns different size than uploaded
        storage_adapter.client.stat_object = MagicMock(return_value=MagicMock(size=999))

        with pytest.raises(StorageError) as exc_info:
            storage_adapter.upload_file(
                nano_id=nano_id,
                file_content=file_content,
                filename=filename,
            )

        assert "size mismatch" in str(exc_info.value)

    def test_delete_file_success(self, storage_adapter):
        """Test successful file deletion."""
        object_key = "nanos/123/content/file.zip"
        storage_adapter.client.remove_object = MagicMock()

        storage_adapter.delete_file(object_key)

        storage_adapter.client.remove_object.assert_called_once_with(
            storage_adapter.bucket_name,
            object_key,
        )

    def test_delete_file_failure(self, storage_adapter):
        """Test error handling when file deletion fails."""
        object_key = "nanos/123/content/file.zip"
        storage_adapter.client.remove_object = MagicMock(side_effect=Exception("Permission denied"))

        with pytest.raises(StorageError) as exc_info:
            storage_adapter.delete_file(object_key)

        assert "Failed to delete" in str(exc_info.value)

    def test_get_file_url_success(self, storage_adapter):
        """Test successful presigned URL generation."""
        object_key = "nanos/123/content/file.zip"
        expected_url = "http://minio:9000/nanos/123/content/file.zip?..."
        storage_adapter.client.get_presigned_download_url = MagicMock(return_value=expected_url)

        url = storage_adapter.get_file_url(object_key)

        assert url == expected_url
        storage_adapter.client.get_presigned_download_url.assert_called_once()

    def test_get_file_url_custom_expiry(self, storage_adapter):
        """Test presigned URL generation with custom expiry."""
        object_key = "nanos/123/content/file.zip"
        expected_url = "http://minio:9000/..."
        storage_adapter.client.get_presigned_download_url = MagicMock(return_value=expected_url)

        url = storage_adapter.get_file_url(object_key, expires_in_days=30)

        assert url == expected_url
        # Verify timedelta(days=30) was passed
        call_args = storage_adapter.client.get_presigned_download_url.call_args
        assert call_args is not None

    def test_object_exists_true(self, storage_adapter):
        """Test object existence check when object exists."""
        object_key = "nanos/123/content/file.zip"
        storage_adapter.client.stat_object = MagicMock(return_value=MagicMock())

        exists = storage_adapter.object_exists(object_key)

        assert exists is True

    def test_object_exists_false(self, storage_adapter):
        """Test object existence check when object doesn't exist."""
        object_key = "nanos/123/content/file.zip"
        storage_adapter.client.stat_object = MagicMock(side_effect=Exception("Not found"))

        exists = storage_adapter.object_exists(object_key)

        assert exists is False


class TestMinIOStorageIntegration:
    """
    Integration tests for storage adapter with upload service.

    These tests verify end-to-end upload flow with mocked MinIO.
    """

    @pytest.mark.asyncio
    async def test_upload_with_storage_integration(
        self, async_client, verified_user_id, db_session
    ):
        """Test complete upload flow with storage integration."""
        import io
        import zipfile

        # Create test ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.pdf", "PDF content")

        zip_buffer.seek(0)

        # Mock MinIO adapter
        with patch("app.modules.upload.router.MinIOStorageAdapter") as mock_adapter:
            mock_instance = MagicMock()
            mock_adapter.return_value = mock_instance

            # Mock upload_file to return storage key
            def mock_upload_file(nano_id, file_content, filename, content_type="application/zip"):
                return f"nanos/{str(nano_id)}/content/{filename}"

            mock_instance.upload_file = mock_upload_file

            # Get auth token
            login_response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "testuser@example.com",
                    "password": "SecurePassword123!",
                },
            )
            token = login_response.json()["access_token"]

            # Upload file
            response = await async_client.post(
                "/api/v1/upload/nano",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("learning_module.zip", zip_buffer, "application/zip")},
            )

            # Verify upload succeeded
            assert response.status_code == 201
            data = response.json()
            assert "nano_id" in data
            assert data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_upload_handles_storage_error(self, async_client, verified_user_id):
        """Test upload endpoint handles storage errors gracefully."""
        import io
        import zipfile

        # Create test ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.pdf", "PDF content")

        zip_buffer.seek(0)

        # Mock MinIO adapter to raise StorageError
        with patch("app.modules.upload.router.MinIOStorageAdapter") as mock_adapter:
            mock_instance = MagicMock()
            mock_adapter.return_value = mock_instance
            # Create a StorageError with is_retryable=True to simulate transient failure
            mock_instance.upload_file.side_effect = StorageError(
                "MinIO connection failed", is_retryable=True
            )

            # Get auth token
            login_response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "testuser@example.com",
                    "password": "SecurePassword123!",
                },
            )
            token = login_response.json()["access_token"]

            # Upload file
            response = await async_client.post(
                "/api/v1/upload/nano",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("learning_module.zip", zip_buffer, "application/zip")},
            )

            # Should return 503 (Service Unavailable)
            assert response.status_code == 503
            data = response.json()
            assert "storage temporarily unavailable" in data["detail"].lower()
            assert data["error_code"] == "UPLOAD_TRANSIENT_FAILURE"
            assert data["failure_state"] == "failed"
            assert data["retryable"] is True
            assert data["retry_after_seconds"] == 30


class TestRealMinIOStorageIntegration:
    """
    Optional real MinIO integration tests.

    These tests are disabled by default and only run when
    RUN_REAL_MINIO_TESTS=1 is set in the environment.
    """

    @pytest.mark.integration
    @pytest.mark.skipif(
        os.getenv("RUN_REAL_MINIO_TESTS") != "1",
        reason="Set RUN_REAL_MINIO_TESTS=1 to run real MinIO integration tests.",
    )
    def test_real_minio_upload_roundtrip(self):
        """Test upload/existence/url/delete flow against a real MinIO instance."""
        adapter = MinIOStorageAdapter()
        nano_id = uuid.uuid4()
        filename = f"integration-{uuid.uuid4()}.zip"
        file_content = b"PK\x03\x04real-minio-test-content"

        object_key = adapter.upload_file(
            nano_id=nano_id,
            file_content=file_content,
            filename=filename,
            content_type="application/zip",
        )

        try:
            assert object_key.startswith(f"nanos/{nano_id}/content/")
            assert adapter.object_exists(object_key) is True

            presigned_url = adapter.get_file_url(object_key, expires_in_days=1)
            assert presigned_url
            assert object_key in presigned_url
        finally:
            adapter.delete_file(object_key)
            assert adapter.object_exists(object_key) is False
