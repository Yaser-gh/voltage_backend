"""Generic file endpoints: download, preview, metadata, rename (works for any file id)."""
# from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db_session
from app.permissions.checker import RequirePermission
from app.permissions.roles import Permission
from app.responses.envelope import ErrorResponse, SuccessResponse
from app.schemas.file import FileAssetResponse, FileRenameRequest
from app.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["Files"])


@router.get(
    "/{file_id}/metadata",
    response_model=SuccessResponse[FileAssetResponse],
    summary="Get file metadata",
    responses={404: {"model": ErrorResponse, "description": "File not found"}},
    dependencies=[Depends(RequirePermission(Permission.FILE_READ))],
)
async def get_file_metadata(file_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[FileAssetResponse]:
    service = FileService(session)
    file_asset = await service.get_file(file_id)
    return SuccessResponse(data=file_asset)


@router.get(
    "/{file_id}/download",
    summary="Download a file",
    description="Streams the file's original bytes with `Content-Disposition: attachment`, "
                "using its original filename. Path is resolved safely against traversal.",
    responses={404: {"model": ErrorResponse, "description": "File not found"}},
    dependencies=[Depends(RequirePermission(Permission.FILE_READ))],
)
async def download_file(file_id: UUID, session: AsyncSession = Depends(get_db_session)) -> FileResponse:
    service = FileService(session)
    path, file_asset = await service.get_download_path(file_id)
    return FileResponse(
        path=path, filename=file_asset.original_filename, media_type=file_asset.mime_type,
        content_disposition_type="attachment",
    )


@router.get(
    "/{file_id}/preview",
    summary="Preview a file inline (images/PDF)",
    description="Same as download, but serves with `Content-Disposition: inline` so "
                "browsers render supported types (images, PDF) directly instead of downloading.",
    responses={404: {"model": ErrorResponse, "description": "File not found"}},
    dependencies=[Depends(RequirePermission(Permission.FILE_READ))],
)
async def preview_file(file_id: UUID, session: AsyncSession = Depends(get_db_session)) -> FileResponse:
    service = FileService(session)
    path, file_asset = await service.get_download_path(file_id)
    return FileResponse(
        path=path, filename=file_asset.original_filename, media_type=file_asset.mime_type,
        content_disposition_type="inline",
    )


@router.patch(
    "/{file_id}/rename",
    response_model=SuccessResponse[FileAssetResponse],
    summary="Rename a file's display name",
    description="Renames only the display (`original_filename`); the on-disk UUID name is unchanged.",
    responses={404: {"model": ErrorResponse, "description": "File not found"}},
    dependencies=[Depends(RequirePermission(Permission.FILE_UPLOAD))],
)
async def rename_file(file_id: UUID, payload: FileRenameRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[FileAssetResponse]:
    service = FileService(session)
    file_asset = await service.rename(file_id, payload.new_filename)
    return SuccessResponse(message="File renamed", data=file_asset)
