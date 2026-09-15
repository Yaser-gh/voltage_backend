"""Project management endpoints, including lifecycle status transitions and files."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.constants import ProjectStatus
from app.dependencies.db import get_db_session
from app.dependencies.pagination import PaginationParams, pagination_params
from app.permissions.checker import RequirePermission
from app.permissions.roles import Permission
from app.responses.envelope import ErrorResponse, MessageResponse, PaginatedResponse, SuccessResponse, build_pagination_meta
from app.schemas.auth import CurrentUser
from app.schemas.file import FileAssetResponse
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListItemResponse,
    ProjectResponse,
    ProjectStatusUpdateRequest,
    ProjectUpdateRequest,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=SuccessResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    responses={404: {"model": ErrorResponse, "description": "Owner user not found"}},
    dependencies=[Depends(RequirePermission(Permission.PROJECT_CREATE))],
)
async def create_project(payload: ProjectCreateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[ProjectResponse]:
    service = ProjectService(session)
    project = await service.create_project(payload)
    return SuccessResponse(status=201, message="Project created", data=project)


@router.get(
    "",
    response_model=PaginatedResponse[ProjectListItemResponse],
    summary="List / search / filter projects",
    description="Supports free-text search (name/address), status filtering, and owner filtering.",
    dependencies=[Depends(RequirePermission(Permission.PROJECT_LIST))],
)
async def list_projects(
    status_filter: ProjectStatus | None = None,
    owner_id: UUID | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[ProjectListItemResponse]:
    service = ProjectService(session)
    items, total = await service.list_projects(pagination, status=status_filter, owner_id=owner_id)
    return PaginatedResponse(data=items, meta=build_pagination_meta(pagination.page, pagination.limit, total))


@router.get(
    "/{project_id}",
    response_model=SuccessResponse[ProjectResponse],
    summary="Get project details",
    responses={404: {"model": ErrorResponse, "description": "Project not found"}},
    dependencies=[Depends(RequirePermission(Permission.PROJECT_READ))],
)
async def get_project(project_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[ProjectResponse]:
    service = ProjectService(session)
    project = await service.get_project(project_id)
    return SuccessResponse(data=project)


@router.patch(
    "/{project_id}",
    response_model=SuccessResponse[ProjectResponse],
    summary="Update a project",
    responses={404: {"model": ErrorResponse, "description": "Project not found"}},
    dependencies=[Depends(RequirePermission(Permission.PROJECT_UPDATE))],
)
async def update_project(project_id: UUID, payload: ProjectUpdateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[ProjectResponse]:
    service = ProjectService(session)
    project = await service.update_project(project_id, payload)
    return SuccessResponse(message="Project updated", data=project)


@router.delete(
    "/{project_id}",
    response_model=SuccessResponse[MessageResponse],
    summary="Delete a project",
    responses={404: {"model": ErrorResponse, "description": "Project not found"}},
    dependencies=[Depends(RequirePermission(Permission.PROJECT_DELETE))],
)
async def delete_project(project_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[MessageResponse]:
    service = ProjectService(session)
    await service.delete_project(project_id)
    return SuccessResponse(message="Project deleted", data=MessageResponse(message="Project deleted"))


def _status_endpoint_docs(action: str) -> dict:
    return {
        "response_model": SuccessResponse[ProjectResponse],
        "summary": f"{action.capitalize()} a project",
        "responses": {
            404: {"model": ErrorResponse, "description": "Project not found"},
            422: {"model": ErrorResponse, "description": "Invalid status transition"},
        },
        "dependencies": [Depends(RequirePermission(Permission.PROJECT_CHANGE_STATUS))],
    }


@router.post("/{project_id}/start", **_status_endpoint_docs("start"))
async def start_project(project_id: UUID, payload: ProjectStatusUpdateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[ProjectResponse]:
    service = ProjectService(session)
    project = await service.start_project(project_id, payload.reason)
    return SuccessResponse(message="Project started", data=project)


@router.post("/{project_id}/stop", **_status_endpoint_docs("stop"))
async def stop_project(project_id: UUID, payload: ProjectStatusUpdateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[ProjectResponse]:
    service = ProjectService(session)
    project = await service.stop_project(project_id, payload.reason)
    return SuccessResponse(message="Project stopped", data=project)


@router.post("/{project_id}/finish", **_status_endpoint_docs("finish"))
async def finish_project(project_id: UUID, payload: ProjectStatusUpdateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[ProjectResponse]:
    service = ProjectService(session)
    project = await service.finish_project(project_id, payload.reason)
    return SuccessResponse(message="Project finished", data=project)


@router.post("/{project_id}/mark-bad", **_status_endpoint_docs("mark as bad"))
async def mark_bad_project(project_id: UUID, payload: ProjectStatusUpdateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[ProjectResponse]:
    service = ProjectService(session)
    project = await service.mark_bad_project(project_id, payload.reason)
    return SuccessResponse(message="Project marked as bad", data=project)


@router.post("/{project_id}/restore", **_status_endpoint_docs("restore"))
async def restore_project(project_id: UUID, payload: ProjectStatusUpdateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[ProjectResponse]:
    service = ProjectService(session)
    project = await service.restore_project(project_id, payload.reason)
    return SuccessResponse(message="Project restored", data=project)


@router.post(
    "/{project_id}/files",
    response_model=SuccessResponse[FileAssetResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file to a project",
    description="Accepts images, PDF, Word, Excel, ZIP, and video files, with full "
                "extension/MIME/size validation and UUID-based storage naming.",
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
    },
    dependencies=[Depends(RequirePermission(Permission.FILE_UPLOAD))],
)
async def upload_project_file(
    project_id: UUID, file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[FileAssetResponse]:
    service = ProjectService(session)
    file_asset = await service.upload_file(project_id, file, current_user.id)
    return SuccessResponse(status=201, message="File uploaded", data=file_asset)


@router.get(
    "/{project_id}/files",
    response_model=SuccessResponse[list[FileAssetResponse]],
    summary="List files attached to a project",
    dependencies=[Depends(RequirePermission(Permission.FILE_READ))],
)
async def list_project_files(project_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[list[FileAssetResponse]]:
    service = ProjectService(session)
    files = await service.list_files(project_id)
    return SuccessResponse(data=files)


@router.delete(
    "/{project_id}/files/{file_id}",
    response_model=SuccessResponse[MessageResponse],
    summary="Delete a file from a project",
    dependencies=[Depends(RequirePermission(Permission.FILE_DELETE))],
)
async def delete_project_file(project_id: UUID, file_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[MessageResponse]:
    service = ProjectService(session)
    await service.delete_file(project_id, file_id)
    return SuccessResponse(message="File deleted", data=MessageResponse(message="File deleted"))
