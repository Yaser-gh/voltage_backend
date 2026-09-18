"""SQLAlchemy declarative base and shared model mixins."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""
    pass


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column (`id`) to a model."""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    u_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), default=uuid4, index=True, unique=True)


class TimestampMixin:
    """Adds `created_at` / `updated_at` audit timestamp columns to a model."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )


class SoftDeleteMixin:
    """Adds a `deleted_at` column enabling soft-delete semantics instead of hard deletes."""
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
