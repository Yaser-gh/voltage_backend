"""Project management business logic, including status-transition rules."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import FileOwnerType, ProjectStatus
from app.core.logging import get_logger
from app.dependencies.pagination import PaginationParams
from app.exceptions.custom import BusinessRuleViolationException, NotFoundException
from app.repositories.file_repository import FileRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest
from app.services.file_service import FileService

logger = get_logger("project_service")

# Allowed status transitions — prevents e.g. resurrecting a "bad" project directly to "finished".
_ALLOWED_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.ACTIVE: {ProjectStatus.STOPPED, ProjectStatus.FINISHED, ProjectStatus.BAD},
    ProjectStatus.STOPPED: {ProjectStatus.ACTIVE, ProjectStatus.BAD, ProjectStatus.FINISHED},
    ProjectStatus.BAD: {ProjectStatus.ACTIVE},  # "restore"
    ProjectStatus.FINISHED: set(),  # terminal state
}


class ProjectService:
    """Business logic for managing electrical projects and their lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.file_repo = FileRepository(session)
        self.file_service = FileService(session)

    async def create_project(self, payload: ProjectCreateRequest) -> object:
        project = await self.project_repo.create(  # TODO
            owner_id=payload.owner_id, name=payload.name, address=payload.address,
            description=payload.description, contract_date=payload.contract_date,
            contract_end_date=payload.contract_end_date, base_price=payload.base_price,
            status=ProjectStatus.ACTIVE, total_paid=0,
        )
        logger.info("project_created", project_id=str(getattr(project, "id", None)))
        return project

    async def get_project(self, project_id: UUID) -> object:
        project = await self.project_repo.get_by_id(project_id)  # TODO
        if project is None:
            raise NotFoundException("Project not found")
        return project

    async def list_projects(self, pagination: PaginationParams, *, status: ProjectStatus | None = None, owner_id: UUID | None = None):
        return await self.project_repo.search(  # TODO
            query=pagination.search, status=status, owner_id=owner_id,
            offset=pagination.offset, limit=pagination.limit,
            sort_by=pagination.sort_by, sort_order=pagination.sort_order,
        )

    async def update_project(self, project_id: UUID, payload: ProjectUpdateRequest) -> object:
        await self.get_project(project_id)
        update_data = payload.model_dump(exclude_unset=True)
        project = await self.project_repo.update(project_id, **update_data)  # TODO
        logger.info("project_updated", project_id=str(project_id))
        return project

    async def delete_project(self, project_id: UUID) -> None:
        await self.get_project(project_id)
        await self.project_repo.soft_delete(project_id)  # TODO
        logger.info("project_deleted", project_id=str(project_id))

    async def _transition_status(self, project_id: UUID, new_status: ProjectStatus, reason: str | None) -> object:
        """Shared status-transition logic enforcing the allowed-transition matrix."""
        project = await self.get_project(project_id)
        current_status = ProjectStatus(project.status)
        if new_status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
            raise BusinessRuleViolationException(
                f"Cannot transition project from '{current_status.value}' to '{new_status.value}'"
            )
        updated = await self.project_repo.update_status(project_id, new_status, reason)  # TODO
        logger.info("project_status_changed", project_id=str(project_id), status=new_status.value)
        return updated

    async def start_project(self, project_id: UUID, reason: str | None = None) -> object:
        return await self._transition_status(project_id, ProjectStatus.ACTIVE, reason)

    async def stop_project(self, project_id: UUID, reason: str | None = None) -> object:
        return await self._transition_status(project_id, ProjectStatus.STOPPED, reason)

    async def finish_project(self, project_id: UUID, reason: str | None = None) -> object:
        return await self._transition_status(project_id, ProjectStatus.FINISHED, reason)

    async def mark_bad_project(self, project_id: UUID, reason: str | None = None) -> object:
        return await self._transition_status(project_id, ProjectStatus.BAD, reason)

    async def restore_project(self, project_id: UUID, reason: str | None = None) -> object:
        return await self._transition_status(project_id, ProjectStatus.ACTIVE, reason)

    async def upload_file(self, project_id: UUID, file, uploaded_by_id: UUID) -> object:
        await self.get_project(project_id)
        return await self.file_service.upload(
            file, owner_type=FileOwnerType.PROJECT, project_id=project_id, payment_id=None,
            uploaded_by_id=uploaded_by_id, max_size_mb=None,
        )

    async def delete_file(self, project_id: UUID, file_id: UUID) -> None:
        await self.get_project(project_id)
        await self.file_service.delete(file_id)

    async def list_files(self, project_id: UUID) -> list:
        await self.get_project(project_id)
        return await self.file_repo.get_by_project(project_id)  # TODO
