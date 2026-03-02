"""
Service layer for Nano upload operations.

This module handles business logic for creating Nano records in the database.
"""

import uuid
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Nano, NanoStatus


async def create_draft_nano(
    db: AsyncSession,
    creator_id: UUID,
    file: UploadFile,
    title: Optional[str] = None,
) -> Nano:
    """
    Create a new Nano record in draft status.

    Args:
        db: Database session
        creator_id: UUID of the user creating the Nano
        file: Uploaded file (for generating title if not provided)
        title: Optional title for the Nano (defaults to filename)

    Returns:
        Created Nano instance

    Raises:
        Exception: If database operation fails
    """
    # Generate title from filename if not provided
    if title is None:
        # Remove .zip extension and clean up filename
        filename = file.filename or "untitled"
        title = filename.rsplit(".", 1)[0] if "." in filename else filename

    # Limit title length to 200 chars
    title = title[:200]

    # Create new Nano record
    nano = Nano(
        id=uuid.uuid4(),
        creator_id=creator_id,
        title=title,
        status=NanoStatus.DRAFT,
        # These fields will be updated in future stories when we integrate storage
        file_storage_path=None,  # Will be set when MinIO integration is complete (S2-BE-04)
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
