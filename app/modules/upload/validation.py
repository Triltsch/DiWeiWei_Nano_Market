"""
ZIP file validation service for Nano uploads.

This module provides utilities for validating uploaded ZIP files:
- File type verification
- Size checking
- ZIP structure validation
"""

import logging
import zipfile
from pathlib import PurePosixPath
from typing import Final

from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

# Constants
MAX_UPLOAD_SIZE: Final[int] = 100 * 1024 * 1024  # 100 MB in bytes
ALLOWED_MIME_TYPES: Final[set[str]] = {
    "application/zip",
    "application/x-zip-compressed",
    "application/x-zip",
}
SUPPORTED_CONTENT_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".pdf", ".jpg", ".png", ".mp4", ".webm"}
)


async def validate_file_type(file: UploadFile) -> None:
    """
    Validate that the uploaded file is a ZIP file.

    Args:
        file: Uploaded file object

    Raises:
        HTTPException: If file type is not ZIP (400 Bad Request)
    """
    # Check MIME type if provided
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Only ZIP files are accepted.",
        )

    # Check file extension
    if file.filename and not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Only .zip files are accepted.",
        )


async def validate_file_size(file: UploadFile) -> None:
    """
    Validate that the uploaded file does not exceed the maximum size.

    Args:
        file: Uploaded file object

    Raises:
        HTTPException: If file size exceeds limit (413 Payload Too Large)
    """
    # Read file in chunks to check size without loading entire file into memory
    total_size = 0
    chunk_size = 1024 * 1024  # 1 MB chunks

    # Reset file position
    await file.seek(0)

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
            )

    # Reset file position for subsequent operations
    await file.seek(0)


async def validate_zip_structure(file: UploadFile) -> None:
    """
    Validate that the ZIP file has valid structure and contains at least one file.

    Args:
        file: Uploaded file object

    Raises:
        HTTPException: If ZIP is corrupt or empty (400 Bad Request)
    """
    # Reset file position
    await file.seek(0)

    try:
        # Attempt to open as ZIP from underlying file object to avoid full buffering in memory
        with zipfile.ZipFile(file.file, "r") as zip_file:
            # Test ZIP integrity
            if zip_file.testzip() is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file is corrupt or contains invalid entries.",
                )

            # Check if ZIP contains at least one file
            file_list = zip_file.namelist()
            if not file_list:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file is empty. At least one file is required.",
                )

            # Filter out directories (entries ending with /)
            actual_files = [name for name in file_list if not name.endswith("/")]
            if not actual_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file contains only directories. At least one file is required.",
                )

            # Ensure ZIP contains at least one supported content file
            supported_files = [
                name
                for name in actual_files
                if PurePosixPath(name).suffix.lower() in SUPPORTED_CONTENT_EXTENSIONS
            ]
            if not supported_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "ZIP file does not contain supported content files. "
                        "Supported file types: .pdf, .jpg, .png, .mp4, .webm."
                    ),
                )

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ZIP file format. The file may be corrupt.",
        )
    except HTTPException:
        # Re-raise our own exceptions
        raise
    except Exception:
        logger.exception("Unexpected error while validating ZIP structure")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to process ZIP file. Ensure the file is a valid ZIP archive.",
        )
    finally:
        # Reset file position for subsequent operations
        await file.seek(0)


async def validate_upload(file: UploadFile) -> None:
    """
    Perform all validation checks on uploaded file.

    This is the main validation entry point that runs all validation checks:
    1. File type validation
    2. File size validation
    3. ZIP structure validation

    Args:
        file: Uploaded file object

    Raises:
        HTTPException: If any validation fails
    """
    await validate_file_type(file)
    await validate_file_size(file)
    await validate_zip_structure(file)
