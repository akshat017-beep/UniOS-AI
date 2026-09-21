"""Upload screening: size, declared type, magic bytes and dangerous payloads.

This is defence in depth, not an antivirus. Deployments that accept uploads from
untrusted networks should additionally scan files with ClamAV — see
`docs/deployment.md`. Nothing here pretends a file has been virus-scanned.
"""

from __future__ import annotations

_MAGIC = {
    b"%PDF-": "application/pdf",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}

_DANGEROUS_EXTENSIONS = (
    ".exe", ".dll", ".so", ".bat", ".cmd", ".com", ".scr", ".msi", ".jar",
    ".sh", ".ps1", ".vbs", ".apk", ".php", ".js", ".html", ".htm", ".svg",
)

_EXECUTABLE_SIGNATURES = (b"MZ", b"\x7fELF", b"PK\x03\x04\x14\x00\x08")


class UnsafeUploadError(ValueError):
    """The upload was rejected before any processing happened."""


def screen_upload(
    data: bytes,
    *,
    filename: str,
    content_type: str,
    allowed_types: set[str],
    max_bytes: int,
) -> str:
    """Return the effective content type, or raise `UnsafeUploadError`."""
    if not data:
        raise UnsafeUploadError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise UnsafeUploadError(
            f"File is larger than the {max_bytes // (1024 * 1024)} MB limit."
        )

    lowered = filename.lower().strip()
    if lowered.endswith(_DANGEROUS_EXTENSIONS):
        raise UnsafeUploadError("This file type is not accepted for security reasons.")
    if "\x00" in filename or "/" in filename.strip("/") and lowered.count("..") > 0:
        raise UnsafeUploadError("Invalid file name.")

    for signature in _EXECUTABLE_SIGNATURES:
        if data.startswith(signature):
            raise UnsafeUploadError("Executable files are not accepted.")

    declared = (content_type or "").split(";")[0].strip().lower()
    detected = next((mime for magic, mime in _MAGIC.items() if data.startswith(magic)), None)
    if detected and declared and detected != declared and declared != "application/octet-stream":
        raise UnsafeUploadError(
            f"File contents ({detected}) do not match the declared type ({declared})."
        )

    effective = detected or declared
    if effective and allowed_types and effective not in allowed_types:
        # Plain text has no magic bytes; accept it when it decodes cleanly.
        if effective.startswith("text/") or _is_text(data):
            return effective or "text/plain"
        raise UnsafeUploadError(f"Unsupported file type '{effective}'.")
    return effective or "text/plain"


def _is_text(data: bytes) -> bool:
    sample = data[:2048]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True
