"""
Tests for upload service layer.

This module tests the business logic for creating Nano records.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import UploadFile

from app.models import Nano, NanoStatus
from app.modules.upload.service import create_draft_nano, get_nano_by_id


class TestCreateDraftNano:
    """
    Test suite for the create_draft_nano service function.

    Tests Nano record creation with various scenarios.
    """

    @pytest.mark.asyncio
    async def test_create_nano_with_explicit_title(self, db_session):
        """Test creating a Nano with an explicitly provided title."""
        creator_id = uuid.uuid4()
        title = "My Custom Learning Module"

        file = MagicMock(spec=UploadFile)
        file.filename = "uploaded.zip"

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            title=title,
        )

        assert nano.id is not None
        assert nano.creator_id == creator_id
        assert nano.title == title
        assert nano.status == NanoStatus.DRAFT
        assert nano.file_storage_path is None  # Not set yet (MinIO integration pending)
        assert nano.description is None
        assert nano.duration_minutes is None
        assert nano.uploaded_at is not None

    @pytest.mark.asyncio
    async def test_create_nano_with_generated_title(self, db_session):
        """Test creating a Nano with title auto-generated from filename."""
        creator_id = uuid.uuid4()

        file = MagicMock(spec=UploadFile)
        file.filename = "my-learning-module.zip"

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
        )

        assert nano.title == "my-learning-module"
        assert nano.status == NanoStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_nano_strips_zip_extension(self, db_session):
        """Test that .zip extension is removed when generating title."""
        creator_id = uuid.uuid4()

        file = MagicMock(spec=UploadFile)
        file.filename = "Python_Basics.zip"

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
        )

        assert nano.title == "Python_Basics"

    @pytest.mark.asyncio
    async def test_create_nano_handles_no_filename(self, db_session):
        """Test that a default title is used when filename is not provided."""
        creator_id = uuid.uuid4()

        file = MagicMock(spec=UploadFile)
        file.filename = None

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
        )

        assert nano.title == "untitled"
        assert nano.status == NanoStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_nano_truncates_long_title(self, db_session):
        """Test that titles longer than 200 chars are truncated."""
        creator_id = uuid.uuid4()
        long_title = "A" * 250  # 250 characters

        file = MagicMock(spec=UploadFile)
        file.filename = "test.zip"

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            title=long_title,
        )

        assert len(nano.title) == 200
        assert nano.title == long_title[:200]

    @pytest.mark.asyncio
    async def test_nano_persisted_to_database(self, db_session):
        """Test that created Nano is actually persisted to the database."""
        creator_id = uuid.uuid4()

        file = MagicMock(spec=UploadFile)
        file.filename = "test.zip"

        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            title="Test Nano",
        )

        # Verify we can retrieve it
        retrieved_nano = await get_nano_by_id(db_session, nano.id)
        assert retrieved_nano is not None
        assert retrieved_nano.id == nano.id
        assert retrieved_nano.title == "Test Nano"


class TestGetNanoById:
    """
    Test suite for the get_nano_by_id service function.

    Tests Nano record retrieval.
    """

    @pytest.mark.asyncio
    async def test_get_existing_nano(self, db_session):
        """Test retrieving an existing Nano by ID."""
        creator_id = uuid.uuid4()

        file = MagicMock(spec=UploadFile)
        file.filename = "test.zip"

        # Create a Nano
        nano = await create_draft_nano(
            db=db_session,
            creator_id=creator_id,
            file=file,
            title="Retrievable Nano",
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
