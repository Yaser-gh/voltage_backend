"""Low-level file utilities: safe naming, checksums, MIME sniffing, human sizes."""
from __future__ import annotations

import hashlib
from uuid import uuid4


def generate_stored_filename(extension: str) -> str:
    """Generate a random, non-guessable filename for on-disk storage.

    Never persist files under their original (user-supplied) name — this
    prevents overwrite attacks, path traversal, and leaks no information
    about original content.
    """
    return f"{uuid4().hex}.{extension.lower()}"


def sha256_of_bytes(data: bytes) -> str:
    """Compute the SHA-256 checksum of a byte string, for integrity/dedup tracking."""
    return hashlib.sha256(data).hexdigest()


def sniff_mime_type(header_bytes: bytes) -> str | None:
    """Best-effort magic-byte MIME sniffing for common formats, independent of
    the client-declared Content-Type header (which can be spoofed).

    Returns None if the type could not be determined from the header bytes.
    """
    signatures: list[tuple[bytes, str]] = [
        (b"\xff\xd8\xff", "image/jpeg"),
        (b"\x89PNG\r\n\x1a\n", "image/png"),
        (b"GIF87a", "image/gif"),
        (b"GIF89a", "image/gif"),
        (b"%PDF-", "application/pdf"),
        (b"PK\x03\x04", "application/zip"),  # also docx/xlsx/pptx (zip-based)
        (b"Rar!\x1a\x07", "application/vnd.rar"),
        (b"7z\xbc\xaf\x27\x1c", "application/x-7z-compressed"),
    ]
    for magic, mime in signatures:
        if header_bytes.startswith(magic):
            return mime
    return None


def human_readable_size(size_bytes: int) -> str:
    """Format a byte count as a human-readable string (e.g. '2.3 MB')."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
