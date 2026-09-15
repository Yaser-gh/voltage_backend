"""Payment ORM model representing a single payment/installment on a project."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.file import FileAsset
    from app.models.project import Project


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A single payment/receipt recorded against a project."""
    __tablename__ = "payments"

    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    receipt_created_at: Mapped[date] = mapped_column(Date, nullable=False)
    paid_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    project: Mapped["Project"] = relationship(back_populates="payments")
    files: Mapped[list["FileAsset"]] = relationship(back_populates="payment", cascade="all, delete-orphan")
