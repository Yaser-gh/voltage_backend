"""File upload/download/management business logic.

Coordinates validation (app.validators.file_validator), physical storage
(app.storage.file_storage), and metadata persistence (FileRepository).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import FileOwnerType
from app.core.logging import get_logger
from app.exceptions.custom import NotFoundException, UnsupportedMediaTypeException
from app.repositories.file_repository import FileRepository
from app.storage.file_storage import file_storage
from app.utils.file_utils import human_readable_size, sniff_mime_type
from app.validators.file_validator import validate_upload_file

logger = get_logger("file_service")


class FileService:
    """Business logic for uploading, deleting, renaming, and describing files."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.file_repo = FileRepository(session)

    async def upload(
        self, file: UploadFile, *, owner_type: FileOwnerType, project_id: UUID | None,
        payment_id: UUID | None, uploaded_by_id: UUID | None, max_size_mb: int | None,
    ) -> object:
        """Validate and persist an uploaded file, returning its metadata record."""
        extension = await validate_upload_file(file, max_size_mb=max_size_mb)

        # Defense in depth: sniff magic bytes and cross-check against the extension's
        # expected MIME family, independent of the client-declared Content-Type.
        header = await file.read(16)
        await file.seek(0)
        sniffed = sniff_mime_type(header)
        if sniffed and file.content_type and not file.content_type.startswith(sniffed.split("/")[0]):
            raise UnsupportedMediaTypeException("File content does not match its declared type")

        stored = await file_storage.save(file, extension, owner_type)

        file_asset = await self.file_repo.create(  # TODO
            owner_type=owner_type, project_id=project_id, payment_id=payment_id,
            uploaded_by_id=uploaded_by_id, original_filename=file.filename,
            stored_filename=stored["stored_filename"], storage_path=stored["storage_path"],
            extension=extension, mime_type=file.content_type or "application/octet-stream",
            size_bytes=stored["size_bytes"], checksum_sha256=stored["checksum_sha256"],
        )
        logger.info("file_uploaded", owner_type=owner_type.value, size_bytes=stored["size_bytes"])
        return file_asset

    async def get_file(self, file_id: UUID) -> object:
        file_asset = await self.file_repo.get_by_id(file_id)  # TODO
        if file_asset is None:
            raise NotFoundException("File not found")
        return file_asset

    async def delete(self, file_id: UUID) -> None:
        """Delete a file's DB record and its physical bytes on disk."""
        file_asset = await self.get_file(file_id)
        await file_storage.delete(file_asset.storage_path)
        await self.file_repo.soft_delete(file_id)  # TODO
        logger.info("file_deleted", file_id=str(file_id))

    async def rename(self, file_id: UUID, new_filename: str) -> object:
        """Rename a file's display name only; the on-disk UUID name never changes."""
        await self.get_file(file_id)
        return await self.file_repo.rename(file_id, new_filename)  # TODO

    async def get_download_path(self, file_id: UUID):
        """Resolve the absolute, traversal-safe filesystem path for streaming a download."""
        file_asset = await self.get_file(file_id)
        return file_storage.absolute_path(file_asset.storage_path), file_asset

    @staticmethod
    def to_metadata_dict(file_asset) -> dict:
        """Build a human-friendly metadata dict (e.g. for a 'get metadata' endpoint)."""
        return {
            "id": file_asset.id,
            "original_filename": file_asset.original_filename,
            "extension": file_asset.extension,
            "mime_type": file_asset.mime_type,
            "size_bytes": file_asset.size_bytes,
            "size_human": human_readable_size(file_asset.size_bytes),
            "created_at": file_asset.created_at,
        }
