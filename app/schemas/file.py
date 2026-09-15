"""File asset domain response schemas (uploads happen via multipart form, not JSON body)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import FileOwnerType
from app.schemas.common import ORMBase


class FileRenameRequest(BaseModel):
    """Payload for renaming a stored file's display name (not its on-disk name)."""
    new_filename: str = Field(..., min_length=1, max_length=255)


class FileAssetResponse(ORMBase):
    """Full file metadata representation."""
    id: UUID
    owner_type: FileOwnerType
    project_id: UUID | None
    payment_id: UUID | None
    original_filename: str
    extension: str
    mime_type: str
    size_bytes: int
    size_human: str
    download_url: str
    created_at: datetime


class FileUploadResponse(BaseModel):
    """Response returned immediately after a successful upload."""
    file: FileAssetResponse
    message: str = "File uploaded successfully"
