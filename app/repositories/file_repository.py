"""File asset persistence repository. Query bodies are TODO per project scope."""
from __future__ import annotations

from uuid import UUID

from app.core.constants import FileOwnerType
from app.models.file import FileAsset
from app.repositories.base import BaseRepository


class FileRepository(BaseRepository[FileAsset]):
    """Data-access methods for the FileAsset aggregate."""

    model = FileAsset

    async def get_by_project(self, project_id: UUID) -> list[FileAsset]:
        """List all files attached directly to a project (excludes payment-scoped files).

        TODO: implement with `select(FileAsset).where(FileAsset.project_id == project_id,
        FileAsset.payment_id.is_(None), FileAsset.deleted_at.is_(None))`.
        """
        raise NotImplementedError

    async def get_by_payment(self, payment_id: UUID) -> list[FileAsset]:
        """List all files attached to a specific payment (receipts, etc.).

        TODO: implement with `select(FileAsset).where(FileAsset.payment_id == payment_id,
        FileAsset.deleted_at.is_(None))`.
        """
        raise NotImplementedError

    async def rename(self, file_id: UUID, new_filename: str) -> FileAsset | None:
        """Rename a file's display name (original_filename), not its on-disk stored name.

        TODO: implement as a targeted UPDATE statement on FileAsset.original_filename.
        """
        raise NotImplementedError

    async def count_by_owner_type(self, owner_type: FileOwnerType) -> int:
        """Count files of a given owner type (project/payment/avatar).

        TODO: implement via `select(func.count()).where(FileAsset.owner_type == owner_type)`.
        """
        raise NotImplementedError
