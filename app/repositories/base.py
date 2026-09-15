"""Generic repository base class implementing the Repository Pattern.

All database access is isolated behind repository classes so that services
(and therefore routes) never construct SQL/ORM queries directly. This keeps
persistence concerns swappable and testable via mocking.

NOTE: Per project scope, concrete query bodies are intentionally left as
TODO stubs — only the structure, signatures, and contracts are implemented.
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base class providing the standard CRUD contract for a single ORM model."""

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: UUID) -> ModelType | None:
        """Fetch a single row by primary key, or None if not found / soft-deleted.

        TODO: implement with `select(self.model).where(self.model.id == entity_id,
        self.model.deleted_at.is_(None))`.
        """
        raise NotImplementedError

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
        """Instantiate and persist a new row.

        TODO: implement as `instance = self.model(**kwargs); self.session.add(instance);
        await self.session.flush(); return instance`.
        """
        raise NotImplementedError

    async def update(self, entity_id: UUID, **kwargs: Any) -> ModelType | None:
        """Update an existing row's fields by id.

        TODO: fetch via get_by_id, apply setattr for each kwarg, flush, return instance.
        """
        raise NotImplementedError

    async def soft_delete(self, entity_id: UUID) -> bool:
        """Soft-delete a row by setting `deleted_at`.

        TODO: implement using an UPDATE statement setting deleted_at = utcnow().
        """
        raise NotImplementedError

    async def hard_delete(self, entity_id: UUID) -> bool:
        """Permanently remove a row. Use sparingly — prefer soft_delete.

        TODO: implement using DELETE statement or `session.delete(instance)`.
        """
        raise NotImplementedError

    async def exists(self, **filters: Any) -> bool:
        """Check whether any row matching the given filters exists.

        TODO: implement via `select(exists().where(...))`.
        """
        raise NotImplementedError

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count rows matching optional filters.

        TODO: implement via `select(func.count()).select_from(self.model).where(...)`.
        """
        raise NotImplementedError
