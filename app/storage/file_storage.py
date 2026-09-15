"""
Local filesystem storage backend for uploaded files.

Abstracted behind a small interface so it can later be swapped for S3 /
object storage without touching service-layer code.
"""
from __future__ import annotations

import os
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config.settings import settings
from app.core.constants import FileOwnerType
from app.exceptions.custom import PathTraversalException
from app.utils.file_utils import generate_stored_filename, sha256_of_bytes

_BASE_UPLOAD_DIR = Path(settings.UPLOAD_DIR).resolve()


class FileStorage:
    """Handles physical persistence/removal of uploaded files on local disk."""

    def __init__(self, base_dir: Path = _BASE_UPLOAD_DIR) -> None:
        self.base_dir = base_dir

    def _resolve_subdir(self, owner_type: FileOwnerType) -> Path:
        subdir = self.base_dir / owner_type.value
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    def _safe_resolve(self, relative_path: str) -> Path:
        """Resolve a stored relative path and guarantee it stays within base_dir."""
        resolved = (self.base_dir / relative_path).resolve()
        if self.base_dir not in resolved.parents and resolved != self.base_dir:
            raise PathTraversalException("Resolved file path escapes the storage root")
        return resolved

    async def save(self, file: UploadFile, extension: str, owner_type: FileOwnerType) -> dict:
        """Persist an UploadFile to disk under a random UUID-based name.

        Returns metadata: stored_filename, storage_path (relative), size_bytes, checksum.
        TODO: swap for chunked streaming to disk + object-storage upload in production
        at very large file sizes; current implementation buffers to compute checksum.
        """
        subdir = self._resolve_subdir(owner_type)
        stored_filename = generate_stored_filename(extension)
        destination = subdir / stored_filename

        hasher_bytes = bytearray()
        async with aiofiles.open(destination, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):
                hasher_bytes.extend(chunk)
                await out_file.write(chunk)
        await file.seek(0)

        relative_path = str(destination.relative_to(self.base_dir))
        return {
            "stored_filename": stored_filename,
            "storage_path": relative_path,
            "size_bytes": len(hasher_bytes),
            "checksum_sha256": sha256_of_bytes(bytes(hasher_bytes)),
        }

    async def delete(self, relative_path: str) -> None:
        """Delete a previously stored file. Silently no-ops if already missing."""
        target = self._safe_resolve(relative_path)
        try:
            os.remove(target)
        except FileNotFoundError:
            pass

    def absolute_path(self, relative_path: str) -> Path:
        """Resolve a stored relative path to an absolute path, safe against traversal."""
        return self._safe_resolve(relative_path)


file_storage = FileStorage()
