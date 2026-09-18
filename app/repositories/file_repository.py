"""File asset persistence repository — full implementation."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from app.core.constants import FileOwnerType
from app.models.file import FileAsset
from app.repositories.base import BaseRepository


class FileRepository(BaseRepository[FileAsset]):
    """Data-access methods for the FileAsset aggregate."""

    model = FileAsset

    async def get_by_project(self, project_id: UUID) -> list[FileAsset]:
        """List all files attached directly to a project (excludes payment-scoped files)."""
        stmt = (
            select(FileAsset)
            .where(
                FileAsset.project_id == project_id,
                FileAsset.payment_id.is_(None),
                FileAsset.deleted_at.is_(None),
            )
            .order_by(FileAsset.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_payment(self, payment_id: UUID) -> list[FileAsset]:
        """List all files attached to a specific payment (receipts, etc.)."""
        stmt = (
            select(FileAsset)
            .where(FileAsset.payment_id == payment_id, FileAsset.deleted_at.is_(None))
            .order_by(FileAsset.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def rename(self, file_id: UUID, new_filename: str) -> FileAsset | None:
        """Rename a file's display name (original_filename), not its on-disk stored name."""
        return await self.update(file_id, original_filename=new_filename)

    async def count_by_owner_type(self, owner_type: FileOwnerType) -> int:
        """Count non-deleted files of a given owner type (project/payment/avatar)."""
        stmt = select(func.count()).select_from(FileAsset).where(
            FileAsset.owner_type == owner_type, FileAsset.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_total_size_bytes(self, *, project_id: UUID | None = None) -> int:
        """Sum stored file sizes, optionally scoped to one project. Handy for a
        per-project storage-usage indicator."""
        stmt = select(func.coalesce(func.sum(FileAsset.size_bytes), 0)).where(FileAsset.deleted_at.is_(None))
        if project_id is not None:
            stmt = stmt.where(FileAsset.project_id == project_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
