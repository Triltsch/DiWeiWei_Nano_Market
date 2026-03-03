"""MinIO storage adapter for persistent object storage.

This module provides a typed interface to MinIO for uploading and managing
learning content files with deterministic key naming and private access control.
"""

import io
import time
from typing import Optional
from uuid import UUID

from minio import Minio
from urllib3 import PoolManager, Timeout

from app.config import get_settings


class StorageError(Exception):
    """Raised when storage operations fail"""

    pass


class MinIOStorageAdapter:
    """MinIO storage adapter for Nano content persistence.

    Provides methods for uploading files to MinIO with deterministic key
    naming and private access control. Supports retry logic and error handling.
    """

    def __init__(self) -> None:
        """Initialize MinIO client with configuration."""
        settings = get_settings()
        self.timeout = settings.UPLOAD_TIMEOUT_SECONDS
        timeout_config = Timeout(
            total=self.timeout,
            connect=min(10, self.timeout),
            read=self.timeout,
        )

        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            region=settings.MINIO_REGION,
            http_client=PoolManager(timeout=timeout_config, retries=False),
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.max_retries = settings.UPLOAD_MAX_RETRIES

    def upload_file(
        self,
        nano_id: UUID,
        file_content: bytes,
        filename: str,
        content_type: str = "application/zip",
    ) -> str:
        """Upload file to MinIO and return storage key.

        Args:
            nano_id: UUID of the Nano entity
            file_content: Binary file content
            filename: Original filename (for reference only)
            content_type: MIME type of the file

        Returns:
            Storage key path relative to bucket (e.g., "nanos/uuid/filename.zip")

        Raises:
            StorageError: If upload fails after retries
        """
        # Generate deterministic object key
        object_key = self._generate_object_key(nano_id, filename)

        # Create file object from bytes
        file_data = io.BytesIO(file_content)
        file_size = len(file_content)

        try:
            # Upload with retry logic
            for attempt in range(self.max_retries):
                try:
                    # Reset file position for retry
                    file_data.seek(0)

                    # Upload to MinIO with private access
                    self.client.put_object(
                        bucket_name=self.bucket_name,
                        object_name=object_key,
                        data=file_data,
                        length=file_size,
                        content_type=content_type,
                        metadata={"nano-id": str(nano_id), "original-filename": filename},
                    )

                    # Verify upload succeeded
                    stat = self.client.stat_object(self.bucket_name, object_key)
                    if stat.size == file_size:
                        return object_key

                    raise StorageError(f"Upload verification failed: size mismatch")

                except Exception as e:
                    if not self._is_transient_error(e):
                        raise StorageError(f"Non-retryable storage failure: {str(e)}") from e

                    if attempt == self.max_retries - 1:
                        # Last attempt failed, raise error
                        raise StorageError(
                            f"Failed to upload file after {self.max_retries} attempts: {str(e)}"
                        ) from e

                    # Retry on next iteration with bounded backoff
                    time.sleep(self._retry_backoff_seconds(attempt))

        finally:
            file_data.close()

    def delete_file(self, object_key: str) -> None:
        """Delete file from MinIO.

        Args:
            object_key: Storage key of the object to delete

        Raises:
            StorageError: If deletion fails
        """
        try:
            self.client.remove_object(self.bucket_name, object_key)
        except Exception as e:
            raise StorageError(f"Failed to delete object {object_key}: {str(e)}") from e

    def get_file_url(self, object_key: str, expires_in_days: int = 7) -> str:
        """Generate presigned URL for file download.

        Args:
            object_key: Storage key of the object
            expires_in_days: Number of days until URL expiration

        Returns:
            Presigned URL for downloading the file

        Raises:
            StorageError: If URL generation fails
        """
        try:
            from datetime import timedelta

            url = self.client.get_presigned_download_url(
                bucket_name=self.bucket_name,
                object_name=object_key,
                expires=timedelta(days=expires_in_days),
            )
            return url
        except Exception as e:
            raise StorageError(
                f"Failed to generate presigned URL for {object_key}: {str(e)}"
            ) from e

    def object_exists(self, object_key: str) -> bool:
        """Check if object exists in MinIO.

        Args:
            object_key: Storage key to check

        Returns:
            True if object exists, False otherwise
        """
        try:
            self.client.stat_object(self.bucket_name, object_key)
            return True
        except Exception:
            return False

    def _generate_object_key(self, nano_id: UUID, filename: str) -> str:
        """Generate deterministic object key for storage.

        Uses structure: nanos/{nano_id}/content/{original_filename}
        This ensures:
        - Clear namespace separation (nanos/ prefix)
        - Unique per Nano (UUID subdirectory)
        - Human-readable original filename preserved
        - Deterministic - same inputs always produce same key

        Args:
            nano_id: UUID of the Nano
            filename: Original filename

        Returns:
            Object key relative to bucket root
        """
        return f"nanos/{str(nano_id)}/content/{filename}"

    def _is_transient_error(self, error: Exception) -> bool:
        """Best-effort classification for transient storage failures.

        Args:
            error: Exception raised during storage operation

        Returns:
            True when the failure appears transient and retry is appropriate.
        """
        transient_indicators = (
            "timeout",
            "timed out",
            "connection",
            "temporarily unavailable",
            "service unavailable",
            "reset",
            "dns",
            "503",
            "429",
        )
        message = str(error).lower()
        return any(indicator in message for indicator in transient_indicators)

    def _retry_backoff_seconds(self, attempt: int) -> float:
        """Calculate bounded exponential backoff in seconds for upload retries."""
        return min(2.0, 0.25 * (2**attempt))


def get_storage_adapter() -> MinIOStorageAdapter:
    """Factory function to get MinIO storage adapter instance.

    Returns:
        Initialized MinIOStorageAdapter instance
    """
    return MinIOStorageAdapter()
