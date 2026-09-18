"""Generic repository base class implementing the Repository Pattern.

All database access is isolated behind repository classes so that services
(and therefore routes) never construct SQL/ORM queries directly. This keeps
persistence concerns swappable and testable via mocking.

NOTE: Per project scope, concrete query bodies are intentionally left as
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, func

from app.database.base import Base
from app.utils.datetime_utils import utcnow

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base class providing the standard CRUD contract for a single ORM model."""

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: UUID) -> ModelType | None:
        """Fetch a single row by primary key, or None if not found / soft-deleted."""
        stmt = select(self.model).where(self.model.u_id == entity_id, self.model.deleted_at.is_(None))
        resp = await self.session.execute(stmt)
        return resp.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        sort_by: str | None = None,
        sort_order: str = "desc",
        search: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelType], int]:
        """Fetch a paginated, sorted, filtered, searchable list plus total count.

        TODO: implement using SQLAlchemy `select()` + `func.count()`, applying
        `filters` as `.where(...)` clauses and `search` as `.ilike()` across
        relevant text columns.
        """
        raise NotImplementedError

    async def create(self, **kwargs: Any) -> ModelType:
        """Instantiate and persist a new row."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, entity_id: UUID, **kwargs: Any) -> ModelType | None:
        """Update an existing row's fields by id."""
        instance = await self.get_by_id(entity_id)
        (
        setattr(instance, key, value) for key, value in kwargs.items() if hasattr(instance, key)
        )
        await self.session.flush()
        return instance

    async def soft_delete(self, entity_id: UUID) -> bool:
        """Soft-delete a row by setting `deleted_at. """
        instance = await self.get_by_id(entity_id)
        if not instance:
            return False

        instance.deleted_at = utcnow()
        await self.session.flush()
        return True

    async def hard_delete(self, entity_id: UUID) -> bool:
        """Permanently remove a row. Use sparingly — prefer soft_delete."""
        instance = await self.get_by_id(entity_id)
        if not instance:
            return False

        await self.session.delete(instance=instance)
        await self.session.flush()
        return True

    async def exists(self, **filters: Any) -> bool:
        """Check whether any row matching the given filters exists."""
        conditions = [
            getattr(self.model, key) == value
            for key, value in filters.items()
        ]
        stmt = select(exists().where(*conditions))
        return bool(await self.session.scalar(stmt))

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count rows matching optional filters."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .filter_by(**filters)
        )
        return await self.session.scalar(stmt) or 0
