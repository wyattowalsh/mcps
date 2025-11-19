"""Supabase Storage integration for file uploads.

This module provides helper classes and functions for managing files in Supabase Storage,
including upload, download, delete, and list operations.
"""

import mimetypes
from typing import BinaryIO, Optional

from loguru import logger

from packages.harvester.settings import settings
from packages.harvester.supabase import is_supabase_configured, supabase, supabase_admin


class SupabaseStorage:
    """Helper class for Supabase Storage operations.

    This class provides methods for uploading, downloading, deleting, and listing
    files in Supabase Storage buckets.
    """

    def __init__(self, use_admin: bool = False):
        """Initialize Supabase Storage helper.

        Args:
            use_admin: Use service role key (bypasses RLS) for storage operations
        """
        if not is_supabase_configured():
            raise ValueError(
                "Supabase not configured. Set SUPABASE_URL and keys in environment."
            )

        self.client = supabase_admin() if use_admin else supabase()
        self.bucket = settings.supabase_storage_bucket
        self.use_admin = use_admin

    async def upload_file(
        self,
        file_path: str,
        file_data: BinaryIO,
        content_type: Optional[str] = None,
        upsert: bool = False,
    ) -> str:
        """Upload file to Supabase Storage.

        Args:
            file_path: Destination path in storage bucket (e.g., "avatars/user123.jpg")
            file_data: File-like object containing the file data
            content_type: MIME type of the file (auto-detected if not provided)
            upsert: Whether to overwrite existing files

        Returns:
            Public URL of the uploaded file

        Raises:
            Exception: If upload fails
        """
        if not content_type:
            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        try:
            # Read file data
            file_bytes = file_data.read()

            # Upload to Supabase Storage
            self.client.storage.from_(self.bucket).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": str(upsert).lower()},
            )

            # Get public URL
            public_url = self.client.storage.from_(self.bucket).get_public_url(file_path)
            logger.info(f"Uploaded file to Supabase Storage: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Failed to upload file to Supabase Storage: {e}")
            raise

    async def download_file(self, file_path: str) -> bytes:
        """Download file from Supabase Storage.

        Args:
            file_path: Path to file in storage bucket

        Returns:
            File contents as bytes

        Raises:
            Exception: If download fails
        """
        try:
            result = self.client.storage.from_(self.bucket).download(file_path)
            logger.info(f"Downloaded file from Supabase Storage: {file_path}")
            return result

        except Exception as e:
            logger.error(f"Failed to download file from Supabase Storage: {e}")
            raise

    async def delete_file(self, file_path: str) -> None:
        """Delete file from Supabase Storage.

        Args:
            file_path: Path to file in storage bucket

        Raises:
            Exception: If deletion fails
        """
        try:
            self.client.storage.from_(self.bucket).remove([file_path])
            logger.info(f"Deleted file from Supabase Storage: {file_path}")

        except Exception as e:
            logger.error(f"Failed to delete file from Supabase Storage: {e}")
            raise

    async def list_files(self, path: str = "", limit: int = 100, offset: int = 0) -> list:
        """List files in Supabase Storage bucket.

        Args:
            path: Directory path to list (empty string for root)
            limit: Maximum number of files to return
            offset: Number of files to skip (pagination)

        Returns:
            List of file metadata dictionaries

        Raises:
            Exception: If listing fails
        """
        try:
            result = self.client.storage.from_(self.bucket).list(
                path=path,
                options={"limit": limit, "offset": offset},
            )
            logger.info(f"Listed {len(result)} files from Supabase Storage: {path}")
            return result

        except Exception as e:
            logger.error(f"Failed to list files from Supabase Storage: {e}")
            raise

    async def get_public_url(self, file_path: str) -> str:
        """Get public URL for a file.

        Args:
            file_path: Path to file in storage bucket

        Returns:
            Public URL of the file
        """
        public_url = self.client.storage.from_(self.bucket).get_public_url(file_path)
        return public_url

    async def create_signed_url(
        self, file_path: str, expires_in: int = 3600
    ) -> dict[str, str]:
        """Create a signed URL for temporary access to a private file.

        Args:
            file_path: Path to file in storage bucket
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Dictionary with 'signedURL' and 'path' keys

        Raises:
            Exception: If signed URL creation fails
        """
        try:
            result = self.client.storage.from_(self.bucket).create_signed_url(
                file_path, expires_in
            )
            logger.info(f"Created signed URL for: {file_path} (expires in {expires_in}s)")
            return result

        except Exception as e:
            logger.error(f"Failed to create signed URL: {e}")
            raise

    async def move_file(self, from_path: str, to_path: str) -> None:
        """Move/rename a file within the storage bucket.

        Args:
            from_path: Current file path
            to_path: New file path

        Raises:
            Exception: If move fails
        """
        try:
            self.client.storage.from_(self.bucket).move(from_path, to_path)
            logger.info(f"Moved file from {from_path} to {to_path}")

        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            raise

    async def copy_file(self, from_path: str, to_path: str) -> None:
        """Copy a file within the storage bucket.

        Args:
            from_path: Source file path
            to_path: Destination file path

        Raises:
            Exception: If copy fails
        """
        try:
            self.client.storage.from_(self.bucket).copy(from_path, to_path)
            logger.info(f"Copied file from {from_path} to {to_path}")

        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            raise


# Convenience functions
async def upload_file(
    file_path: str,
    file_data: BinaryIO,
    content_type: Optional[str] = None,
    use_admin: bool = False,
) -> str:
    """Upload file to Supabase Storage (convenience function).

    Args:
        file_path: Destination path in storage bucket
        file_data: File-like object containing the file data
        content_type: MIME type of the file (auto-detected if not provided)
        use_admin: Use service role key (bypasses RLS)

    Returns:
        Public URL of the uploaded file
    """
    storage = SupabaseStorage(use_admin=use_admin)
    return await storage.upload_file(file_path, file_data, content_type)


async def download_file(file_path: str, use_admin: bool = False) -> bytes:
    """Download file from Supabase Storage (convenience function).

    Args:
        file_path: Path to file in storage bucket
        use_admin: Use service role key (bypasses RLS)

    Returns:
        File contents as bytes
    """
    storage = SupabaseStorage(use_admin=use_admin)
    return await storage.download_file(file_path)


async def delete_file(file_path: str, use_admin: bool = True) -> None:
    """Delete file from Supabase Storage (convenience function).

    Args:
        file_path: Path to file in storage bucket
        use_admin: Use service role key (bypasses RLS, default True for deletions)
    """
    storage = SupabaseStorage(use_admin=use_admin)
    await storage.delete_file(file_path)
