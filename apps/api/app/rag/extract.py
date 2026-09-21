"""Text extraction from uploaded files.

Supported today: PDF (pypdf), plain text and markdown.
Images are stored and can be sent to a vision model, but are not OCR'd here —
that is documented as configuration-dependent rather than silently faked.
"""

from __future__ import annotations

import io

SUPPORTED_TEXT_TYPES = {"text/plain", "text/markdown", "text/csv"}
SUPPORTED_PDF_TYPES = {"application/pdf"}
SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
SUPPORTED_TYPES = SUPPORTED_TEXT_TYPES | SUPPORTED_PDF_TYPES | SUPPORTED_IMAGE_TYPES


class UnsupportedDocumentError(ValueError):
    """The uploaded file type cannot be turned into retrievable text."""


def looks_like_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def extract_pages(data: bytes, content_type: str, filename: str) -> list[str]:
    """Return one string per page. Text files are treated as a single page."""
    ctype = (content_type or "").split(";")[0].strip().lower()
    lowered = filename.lower()

    if ctype in SUPPORTED_PDF_TYPES or lowered.endswith(".pdf") or looks_like_pdf(data):
        return _extract_pdf(data)
    if ctype in SUPPORTED_TEXT_TYPES or lowered.endswith((".txt", ".md", ".csv")):
        return [data.decode("utf-8", errors="replace")]
    if ctype in SUPPORTED_IMAGE_TYPES:
        raise UnsupportedDocumentError(
            "Images are stored for visual questions but are not text-indexed. "
            "Upload a PDF or text file to get cited answers."
        )
    raise UnsupportedDocumentError(f"Unsupported file type '{content_type or filename}'.")


def _extract_pdf(data: bytes) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise UnsupportedDocumentError(
            "PDF support requires the 'pypdf' package to be installed."
        ) from exc

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001 - any parse failure is a user-facing error
        raise UnsupportedDocumentError(f"This PDF could not be read: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:  # noqa: BLE001
            raise UnsupportedDocumentError(
                "This PDF is password protected. Remove the password and upload again."
            ) from exc

    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    if not any(pages):
        raise UnsupportedDocumentError(
            "No selectable text was found. This looks like a scanned PDF; OCR is not "
            "enabled in this deployment."
        )
    return pages
