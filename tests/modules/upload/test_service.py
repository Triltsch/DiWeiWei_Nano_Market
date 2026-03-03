"""
Tests for upload service layer.

This module tests the business logic for creating Nano records.
"""

import time
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.models import Nano, NanoStatus
from app.modules.upload.service import create_draft_nano, get_nano_by_id
from app.modules.upload.storage import StorageError


class TestCreateDraftNano:
    """
    Test suite for the create_draft_nano service function.

    Tests Nano record creation with various scenarios.
    """

    def _create_mock_file(self, filename: str = "test.zip") -> MagicMock:
        """
        Helper to create a properly mocked UploadFile.

        Returns mock with read() method returning bytes.
        """
        file = MagicMock(spec=UploadFile)
        file.filename = filename
        file.content_type = "application/zip"
        # Mock async read() to return bytes
        file.read = AsyncMock(return_value=b"fake zip content")
        return file

    def _create_mock_storage(self) -> MagicMock:
        """
        Helper to create a mocked MinIOStorageAdapter.

        Returns mock with upload_file() returning deterministic storage key.
        """
        storage = MagicMock()

        def mock_upload_file(nano_id, file_content, filename, content_type=None):
            return f"nanos/{nano_id}/content/{filename}"

        storage.upload_file = mock_upload_file
        return storage

    @pytest.mark.asyncio
    async def test_create_nano_with_explicit_title(self, db_session):
        """Test creating a Nano with an explicitly provided title."""
        creator_id = uuid.uuid4()
        title = "My Custom Learning Module"

        file = self._create_mock_file("uploaded.zip")
        storage = self._create_mock_storage()

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            title=title,
            storage_adapter=storage,
        )

        assert nano.id is not None
        assert nano.creator_id == creator_id
        assert nano.title == title
        assert nano.status == NanoStatus.DRAFT
        # file_storage_path is now populated by MinIO integration
        assert nano.file_storage_path is not None
        assert nano.file_storage_path.startswith("nanos/")
        assert nano.description is None
        assert nano.duration_minutes is None
        assert nano.uploaded_at is not None

    @pytest.mark.asyncio
    async def test_create_nano_with_generated_title(self, db_session):
        """Test creating a Nano with title auto-generated from filename."""
        creator_id = uuid.uuid4()

        file = self._create_mock_file("my-learning-module.zip")
        storage = self._create_mock_storage()

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            storage_adapter=storage,
        )

        assert nano.title == "my-learning-module"
        assert nano.status == NanoStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_nano_strips_zip_extension(self, db_session):
        """Test that .zip extension is removed when generating title."""
        creator_id = uuid.uuid4()

        file = self._create_mock_file("Python_Basics.zip")
        storage = self._create_mock_storage()

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            storage_adapter=storage,
        )

        assert nano.title == "Python_Basics"

    @pytest.mark.asyncio
    async def test_create_nano_handles_no_filename(self, db_session):
        """Test that a default title is used when filename is not provided."""
        creator_id = uuid.uuid4()

        file = self._create_mock_file(None)
        storage = self._create_mock_storage()

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            storage_adapter=storage,
        )

        assert nano.title == "untitled"
        assert nano.status == NanoStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_nano_truncates_long_title(self, db_session):
        """Test that titles longer than 200 chars are truncated."""
        creator_id = uuid.uuid4()
        long_title = "A" * 250  # 250 characters

        file = self._create_mock_file("test.zip")
        storage = self._create_mock_storage()

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            title=long_title,
            storage_adapter=storage,
        )

        assert len(nano.title) == 200
        assert nano.title == long_title[:200]

    @pytest.mark.asyncio
    async def test_nano_persisted_to_database(self, db_session):
        """Test that created Nano is actually persisted to the database."""
        creator_id = uuid.uuid4()

        file = self._create_mock_file("test.zip")
        storage = self._create_mock_storage()

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            title="Test Nano",
            storage_adapter=storage,
        )

        # Verify we can retrieve it
        retrieved_nano = await get_nano_by_id(db_session, nano.id)
        assert retrieved_nano is not None
        assert retrieved_nano.id == nano.id
        assert retrieved_nano.title == "Test Nano"

    @pytest.mark.asyncio
    async def test_create_nano_upload_timeout_raises_storage_error(self, db_session):
        """Test that upload operation timeout is surfaced as StorageError.

        Uses deterministic mocking to simulate timeout without real delays.
        """
        from unittest.mock import patch

        creator_id = uuid.uuid4()
        file = self._create_mock_file("timeout.zip")

        storage = MagicMock()
        storage.timeout = 1

        with patch("asyncio.wait_for") as mock_wait_for:
            # Simulate asyncio.wait_for raising TimeoutError
            mock_wait_for.side_effect = TimeoutError("Upload operation exceeded timeout")

            with pytest.raises(StorageError) as exc_info:
                await create_draft_nano(
                    db=db_session,
                    creator_id=creator_id,
                    file=file,
                    storage_adapter=storage,
                )

            assert "timeout" in str(exc_info.value).lower()
            assert exc_info.value.is_retryable is True


class TestGetNanoById:
    """
    Test suite for the get_nano_by_id service function.

    Tests Nano record retrieval.
    """

    def _create_mock_file(self, filename: str = "test.zip") -> MagicMock:
        """
        Helper to create a properly mocked UploadFile.

        Returns mock with read() method returning bytes.
        """
        file = MagicMock(spec=UploadFile)
        file.filename = filename
        file.content_type = "application/zip"
        # Mock async read() to return bytes
        file.read = AsyncMock(return_value=b"fake zip content")
        return file

    def _create_mock_storage(self) -> MagicMock:
        """
        Helper to create a mocked MinIOStorageAdapter.

        Returns mock with upload_file() returning deterministic storage key.
        """
        storage = MagicMock()

        def mock_upload_file(nano_id, file_content, filename, content_type=None):
            return f"nanos/{nano_id}/content/{filename}"

        storage.upload_file = mock_upload_file
        return storage

    @pytest.mark.asyncio
    async def test_get_existing_nano(self, db_session):
        """Test retrieving an existing Nano by ID."""
        creator_id = uuid.uuid4()

        file = self._create_mock_file("test.zip")
        storage = self._create_mock_storage()

        # Create a Nano
        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            title="Retrievable Nano",
            storage_adapter=storage,
        )

        # Retrieve it
        retrieved = await get_nano_by_id(db_session, nano.id)
        assert retrieved is not None
        assert retrieved.id == nano.id
        assert retrieved.title == "Retrievable Nano"

    @pytest.mark.asyncio
    async def test_get_nonexistent_nano_returns_none(self, db_session):
        """Test that retrieving a non-existent Nano returns None."""
        nonexistent_id = uuid.uuid4()
        result = await get_nano_by_id(db_session, nonexistent_id)
        assert result is None
