"""
Tests for ZIP file validation service.

This module tests the validation logic for uploaded ZIP files including:
- File type validation
- File size validation
- ZIP structure validation
"""

import io
import zipfile
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from app.modules.upload.validation import (
    MAX_UPLOAD_SIZE,
    validate_file_size,
    validate_file_type,
    validate_upload,
    validate_zip_structure,
)


class TestFileTypeValidation:
    """
    Test suite for file type validation.

    Tests that only ZIP files are accepted and other formats are rejected.
    """

    @pytest.mark.asyncio
    async def test_valid_zip_mime_type(self):
        """Test that valid ZIP MIME types are accepted."""
        for mime_type in [
            "application/zip",
            "application/x-zip-compressed",
            "application/x-zip",
        ]:
            file = MagicMock(spec=UploadFile)
            file.content_type = mime_type
            file.filename = "test.zip"

            # Should not raise exception
            await validate_file_type(file)

    @pytest.mark.asyncio
    async def test_invalid_mime_type_rejected(self):
        """Test that non-ZIP MIME types are rejected."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "application/pdf"
        file.filename = "test.pdf"

        with pytest.raises(HTTPException) as exc_info:
            await validate_file_type(file)

        assert exc_info.value.status_code == 400
        assert "Only ZIP files are accepted" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_file_extension_rejected(self):
        """Test that files without .zip extension are rejected."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "application/zip"
        file.filename = "test.pdf"

        with pytest.raises(HTTPException) as exc_info:
            await validate_file_type(file)

        assert exc_info.value.status_code == 400
        assert "Only .zip files are accepted" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_case_insensitive_extension(self):
        """Test that .ZIP extension (uppercase) is accepted."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "application/zip"
        file.filename = "test.ZIP"

        # Should not raise exception
        await validate_file_type(file)


class TestFileSizeValidation:
    """
    Test suite for file size validation.

    Tests that files exceeding 100 MB are rejected.
    """

    @pytest.mark.asyncio
    async def test_file_within_size_limit(self):
        """Test that files under 100 MB are accepted."""
        # Create a file of 50 MB
        size = 50 * 1024 * 1024
        content = b"0" * size

        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(side_effect=[content, b""])
        file.seek = AsyncMock()

        # Should not raise exception
        await validate_file_size(file)
        assert file.seek.call_count == 2

    @pytest.mark.asyncio
    async def test_file_exceeds_size_limit(self):
        """Test that files over 100 MB are rejected."""
        # Create chunks that exceed 100 MB
        chunk_size = 1024 * 1024  # 1 MB
        num_chunks = 101  # 101 MB total

        file = MagicMock(spec=UploadFile)
        chunks = [b"0" * chunk_size for _ in range(num_chunks)] + [b""]
        file.read = AsyncMock(side_effect=chunks)
        file.seek = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await validate_file_size(file)

        assert exc_info.value.status_code == 413
        assert "exceeds maximum allowed size" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_file_exactly_at_size_limit(self):
        """Test that a file exactly at 100 MB is accepted."""
        # Create a file of exactly 100 MB
        size = MAX_UPLOAD_SIZE
        chunk_size = 1024 * 1024  # 1 MB
        num_chunks = size // chunk_size

        file = MagicMock(spec=UploadFile)
        chunks = [b"0" * chunk_size for _ in range(num_chunks)] + [b""]
        file.read = AsyncMock(side_effect=chunks)
        file.seek = AsyncMock()

        # Should not raise exception
        await validate_file_size(file)


class TestZipStructureValidation:
    """
    Test suite for ZIP structure validation.

    Tests that ZIP files are valid and contain at least one file.
    """

    @pytest.mark.asyncio
    async def test_valid_zip_with_files(self):
        """Test that a valid ZIP with files passes validation."""
        # Create a valid ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test.txt", "Hello World")
            zf.writestr("subfolder/file.txt", "Content")

        zip_content = zip_buffer.getvalue()

        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(return_value=zip_content)
        file.seek = AsyncMock()

        # Should not raise exception
        await validate_zip_structure(file)

    @pytest.mark.asyncio
    async def test_empty_zip_rejected(self):
        """Test that an empty ZIP file is rejected."""
        # Create an empty ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            pass  # Don't add any files

        zip_content = zip_buffer.getvalue()

        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(return_value=zip_content)
        file.seek = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await validate_zip_structure(file)

        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_zip_with_only_directories_rejected(self):
        """Test that a ZIP with only directories is rejected."""
        # Create a ZIP with only directories
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("folder1/", "")
            zf.writestr("folder2/", "")

        zip_content = zip_buffer.getvalue()

        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(return_value=zip_content)
        file.seek = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await validate_zip_structure(file)

        assert exc_info.value.status_code == 400
        assert "only directories" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_corrupt_zip_rejected(self):
        """Test that a corrupt ZIP file is rejected."""
        # Create invalid ZIP content
        corrupt_content = b"This is not a valid ZIP file"

        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(return_value=corrupt_content)
        file.seek = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await validate_zip_structure(file)

        assert exc_info.value.status_code == 400
        assert (
            "invalid" in exc_info.value.detail.lower() or "corrupt" in exc_info.value.detail.lower()
        )

    @pytest.mark.asyncio
    async def test_zip_with_files_and_directories(self):
        """Test that a ZIP with both files and directories passes validation."""
        # Create a ZIP with files and directories
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("folder1/", "")
            zf.writestr("folder1/file.txt", "Content")
            zf.writestr("root_file.txt", "Root content")

        zip_content = zip_buffer.getvalue()

        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(return_value=zip_content)
        file.seek = AsyncMock()

        # Should not raise exception
        await validate_zip_structure(file)


class TestCompleteValidation:
    """
    Test suite for the complete validation workflow.

    Tests the validate_upload function that runs all validations.
    """

    @pytest.mark.asyncio
    async def test_complete_validation_success(self):
        """Test that a valid ZIP file passes all validations."""
        # Create a valid ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test.txt", "Hello World")

        zip_content = zip_buffer.getvalue()

        file = MagicMock(spec=UploadFile)
        file.content_type = "application/zip"
        file.filename = "test.zip"
        file.read = AsyncMock(side_effect=[zip_content, b"", zip_content])
        file.seek = AsyncMock()

        # Should not raise exception
        await validate_upload(file)

    @pytest.mark.asyncio
    async def test_complete_validation_fails_on_wrong_type(self):
        """Test that validation fails early on wrong file type."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "application/pdf"
        file.filename = "test.pdf"

        with pytest.raises(HTTPException) as exc_info:
            await validate_upload(file)

        assert exc_info.value.status_code == 400
        # Validation should fail at type check, before size/structure checks

    @pytest.mark.asyncio
    async def test_complete_validation_fails_on_size(self):
        """Test that validation fails on file size even if type is correct."""
        # Create chunks that exceed 100 MB
        chunk_size = 1024 * 1024  # 1 MB
        num_chunks = 101  # 101 MB total

        file = MagicMock(spec=UploadFile)
        file.content_type = "application/zip"
        file.filename = "test.zip"
        chunks = [b"0" * chunk_size for _ in range(num_chunks)] + [b""]
        file.read = AsyncMock(side_effect=chunks)
        file.seek = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await validate_upload(file)

        assert exc_info.value.status_code == 413
