"""File upload validation: extension, MIME type, size, and filename safety.

Defends against:
- Path traversal (`../../etc/passwd`)
- Extension spoofing (renaming a .php to .jpg)
- Oversized uploads (DoS via disk exhaustion)
- Null-byte filename tricks
"""
from __future__ import annotations

import os
import re

from fastapi import UploadFile

from app.config.settings import settings
from app.exceptions.custom import (
    FileTooLargeException,
    FileValidationException,
    PathTraversalException,
    UnsupportedMediaTypeException,
)

# Map of allowed extension -> allowed MIME type prefixes/values.
_ALLOWED_MIME_MAP: dict[str, set[str]] = {
    "jpg": {"image/jpeg"}, "jpeg": {"image/jpeg"}, "png": {"image/png"},
    "webp": {"image/webp"}, "gif": {"image/gif"},
    "pdf": {"application/pdf"},
    "doc": {"application/msword"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "xls": {"application/vnd.ms-excel"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "ppt": {"application/vnd.ms-powerpoint"},
    "pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    "zip": {"application/zip", "application/x-zip-compressed"},
    "rar": {"application/vnd.rar", "application/x-rar-compressed"},
    "7z": {"application/x-7z-compressed"},
    "mp4": {"video/mp4"}, "mov": {"video/quicktime"}, "avi": {"video/x-msvideo"}, "mkv": {"video/x-matroska"},
}

_SAFE_FILENAME_RE = re.compile(r"^[\w\-. ]+$", re.UNICODE)


def get_extension(filename: str) -> str:
    """Extract and normalize a file extension (lowercase, no leading dot)."""
    _, ext = os.path.splitext(filename)
    return ext.lower().lstrip(".")


def assert_safe_filename(filename: str) -> None:
    """Reject filenames containing path separators, null bytes, or traversal sequences."""
    if not filename or "\x00" in filename:
        raise FileValidationException("Filename is empty or contains invalid characters")
    if "/" in filename or "\\" in filename or ".." in filename:
        raise PathTraversalException("Filename must not contain path separators or '..'")
    if not _SAFE_FILENAME_RE.match(os.path.basename(filename)):
        raise FileValidationException("Filename contains unsupported characters")


def assert_allowed_extension_and_mime(extension: str, content_type: str | None) -> None:
    """Validate that the extension is allow-listed and its declared MIME type matches.

    NOTE: declared `content_type` is client-supplied and not fully trustworthy;
    combine this with magic-byte sniffing (see utils.file_utils.sniff_mime_type)
    at the service layer before persisting the file.
    """
    all_allowed = (
        set(settings.ALLOWED_IMAGE_EXTENSIONS)
        | set(settings.ALLOWED_DOCUMENT_EXTENSIONS)
        | set(settings.ALLOWED_ARCHIVE_EXTENSIONS)
        | set(settings.ALLOWED_VIDEO_EXTENSIONS)
    )
    if extension not in all_allowed:
        raise UnsupportedMediaTypeException(f"File extension '.{extension}' is not allowed")

    allowed_mimes = _ALLOWED_MIME_MAP.get(extension)
    if allowed_mimes and content_type and content_type not in allowed_mimes:
        raise UnsupportedMediaTypeException(
            f"Declared content type '{content_type}' does not match extension '.{extension}'"
        )


async def validate_upload_file(file: UploadFile, *, max_size_mb: int | None = None) -> str:
    """Run full validation pipeline on an incoming UploadFile.

    Returns the normalized (lowercase, no-dot) extension on success, raises
    an AppException subclass otherwise. Does not persist the file.
    """
    assert_safe_filename(file.filename or "")
    extension = get_extension(file.filename or "")
    assert_allowed_extension_and_mime(extension, file.content_type)

    limit_bytes = (max_size_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    size = 0
    chunk_size = 1024 * 1024
    while chunk := await file.read(chunk_size):
        size += len(chunk)
        if size > limit_bytes:
            raise FileTooLargeException(
                f"File exceeds the maximum allowed size of {max_size_mb or settings.MAX_UPLOAD_SIZE_MB} MB"
            )
    await file.seek(0)
    return extension
