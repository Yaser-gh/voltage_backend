"""Project ORM model representing an electrical installation/service project."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ProjectStatus
from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.file import FileAsset
    from app.models.payment import Payment
    from app.models.user import User


class Project(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """An electrical project owned by a user (customer)."""
    __tablename__ = "projects"

    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    contract_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    base_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_paid: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)

    status: Mapped[ProjectStatus] = mapped_column(
        String(20), nullable=False, default=ProjectStatus.ACTIVE, index=True
    )

    owner: Mapped["User"] = relationship(back_populates="projects")
    payments: Mapped[list["Payment"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    files: Mapped[list["FileAsset"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        primaryjoin="and_(Project.u_id==FileAsset.project_id, FileAsset.payment_id==None)",
        foreign_keys="FileAsset.project_id"
    )
