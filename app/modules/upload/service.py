"""
Service layer for Nano upload operations.

This module handles business logic for creating Nano records in the database
and managing file persistence to MinIO object storage.
"""

import asyncio
import uuid
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Nano, NanoStatus
from app.modules.upload.storage import MinIOStorageAdapter, StorageError


async def create_draft_nano(
    db: AsyncSession,
    creator_id: UUID,
    file: UploadFile,
    title: Optional[str] = None,
    storage_adapter: Optional[MinIOStorageAdapter] = None,
) -> Nano:
    """
    Create a new Nano record in draft status and persist file to MinIO.

    Workflow:
    1. Read and validate file content
    2. Upload file to MinIO with deterministic key
    3. Create Nano record in database linked to storage object
    4. Return created Nano with file_storage_path set

    Args:
        db: Database session
        creator_id: UUID of the user creating the Nano
        file: Uploaded file (for generating title if not provided)
        title: Optional title for the Nano (defaults to filename)
        storage_adapter: MinIO adapter instance (defaults to new instance)

    Returns:
        Created Nano instance with file_storage_path populated

    Raises:
        StorageError: If file upload to MinIO fails
        Exception: If database operation fails
    """
    # Initialize storage adapter if not provided
    if storage_adapter is None:
        storage_adapter = MinIOStorageAdapter()

    # Generate title from filename if not provided
    if title is None:
        # Remove .zip extension and clean up filename
        filename = file.filename or "untitled"
        title = filename.rsplit(".", 1)[0] if "." in filename else filename

    # Limit title length to 200 chars
    title = title[:200]

    # Create nano_id early for storage key generation
    nano_id = uuid.uuid4()
    timeout_seconds = max(1, int(getattr(storage_adapter, "timeout", 600)))

    try:
        # Read file content
        file_content = await asyncio.wait_for(file.read(), timeout=timeout_seconds)

        # Upload to MinIO and get storage key
        storage_key = await asyncio.wait_for(
            asyncio.to_thread(
                storage_adapter.upload_file,
                nano_id=nano_id,
                file_content=file_content,
                filename=file.filename or "untitled.zip",
                content_type=file.content_type or "application/zip",
            ),
            timeout=timeout_seconds,
        )
    except TimeoutError as e:
        raise StorageError(
            f"Upload operation exceeded timeout of {timeout_seconds} seconds.",
            is_retryable=True,
        ) from e
    except StorageError:
        # Re-raise the original StorageError to preserve retryability metadata
        raise

    # Create new Nano record with storage reference
    nano = Nano(
        id=nano_id,
        creator_id=creator_id,
        title=title,
        status=NanoStatus.DRAFT,
        # MinIO integration: file_storage_path now populated
        file_storage_path=storage_key,
        description=None,
        duration_minutes=None,
        thumbnail_url=None,
    )

    # Add to database
    db.add(nano)
    await db.commit()
    await db.refresh(nano)

    return nano


async def get_nano_by_id(db: AsyncSession, nano_id: UUID) -> Optional[Nano]:
    """
    Retrieve a Nano by ID.

    Args:
        db: Database session
        nano_id: UUID of the Nano to retrieve

    Returns:
        Nano instance if found, None otherwise
    """
    result = await db.execute(select(Nano).where(Nano.id == nano_id))
    return result.scalar_one_or_none()
