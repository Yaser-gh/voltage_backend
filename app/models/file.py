"""FileAsset ORM model: unified storage record for project/payment/avatar files."""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import FileOwnerType
from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.project import Project


class FileAsset(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A file stored on disk (or object storage), with metadata for safe serving."""
    __tablename__ = "file_assets"

    owner_type: Mapped[FileOwnerType] = mapped_column(String(20), nullable=False, index=True)

    project_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.u_id", ondelete="CASCADE"), nullable=True, index=True)
    payment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("payments.u_id", ondelete="CASCADE"), nullable=True, index=True)
    uploaded_by_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="SET NULL"), nullable=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # UUID-based name on disk
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="files", foreign_keys=[project_id])
    payment: Mapped["Payment"] = relationship(back_populates="files", foreign_keys=[payment_id])
