"""Generic repository base class implementing the Repository Pattern."""
from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.database.base import Base
from app.utils.datetime_utils import utcnow

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base class providing the standard CRUD contract for a single ORM model."""

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _apply_filters(self, stmt: Select, filters: dict[str, Any] | None) -> Select:
        """Turn a {field_name: value} dict into equality WHERE clauses.

        Silently skips keys that aren't real columns on the model, so
        callers can pass loosely-built dicts without crashing the query.
        Only supports equality — for ranges/LIKE/IN, add a dedicated
        repository method instead of stretching this helper.
        """
        if not filters:
            return stmt
        for field, value in filters.items():
            column = getattr(self.model, field, None)
            if column is not None and value is not None:
                stmt = stmt.where(column == value)
        return stmt

    async def get_by_id(self, entity_id: UUID, *, include_deleted: bool = False) -> ModelType | None:
        """Fetch a single row by primary key.

        Excludes soft-deleted rows unless `include_deleted=True` — pass that
        when you specifically need a trashed row back (e.g. to restore it).
        """
        stmt = select(self.model).where(self.model.u_id == entity_id)
        if hasattr(self.model, "deleted_at") and not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, entity_ids: list[UUID]) -> list[ModelType]:
        """Fetch multiple rows at once by a list of primary keys, excluding soft-deleted.

        Order is not guaranteed to match `entity_ids` — re-sort at the caller
        if a specific order matters.
        """
        if not entity_ids:
            return []
        stmt = select(self.model).where(self.model.u_id.in_(entity_ids))
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        sort_by: str | None = None,
        sort_order: str = "desc",
        search: str | None = None,
        search_fields: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelType], int]:
        """Fetch a paginated, sorted, filtered, searchable list plus total count.

        `filters` -> equality conditions, e.g. {"is_active": True}.
        `search` + `search_fields` -> ILIKE across the given text columns,
        e.g. search="ali", search_fields=["first_name", "last_name"].
        """
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        stmt = self._apply_filters(stmt, filters)

        if search and search_fields:
            like = f"%{search}%"
            conditions = [getattr(self.model, f).ilike(like) for f in search_fields if hasattr(self.model, f)]
            if conditions:
                stmt = stmt.where(or_(*conditions))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        if sort_by and hasattr(self.model, sort_by):
            column = getattr(self.model, sort_by)
            stmt = stmt.order_by(column.desc() if sort_order == "desc" else column.asc())

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, **kwargs: Any) -> ModelType:
        """Instantiate and persist a new row."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, entity_id: UUID, **kwargs: Any) -> ModelType | None:
        """Update an existing row's fields by id."""
        instance = await self.get_by_id(entity_id)
        if instance is None:
            return None
        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        await self.session.flush()
        return instance

    async def soft_delete(self, entity_id: UUID) -> bool:
        """Soft-delete a row by setting `deleted_at`."""
        instance = await self.get_by_id(entity_id)
        if instance is None or not hasattr(instance, "deleted_at"):
            return False
        instance.deleted_at = utcnow()
        await self.session.flush()
        return True

    async def restore(self, entity_id: UUID) -> ModelType | None:
        """Undo a soft-delete by clearing `deleted_at`. Complement to soft_delete."""
        instance = await self.get_by_id(entity_id, include_deleted=True)
        if instance is None or not hasattr(instance, "deleted_at"):
            return None
        instance.deleted_at = None
        await self.session.flush()
        return instance

    async def hard_delete(self, entity_id: UUID) -> bool:
        """Permanently remove a row. Use sparingly — prefer soft_delete.

        Looks up including soft-deleted rows, so a previously soft-deleted
        row can still be purged for good (e.g. from a cleanup job).
        """
        instance = await self.get_by_id(entity_id, include_deleted=True)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def exists(self, **filters: Any) -> bool:
        """Check whether any non-deleted row matching the given filters exists."""
        stmt = select(self.model.u_id)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count non-deleted rows matching optional filters."""
        stmt = select(func.count()).select_from(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return result.scalar_one()
