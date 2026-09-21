"""Page-aware chunking. Every chunk keeps its page so citations stay verifiable."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chunk:
    ordinal: int
    page: int
    content: str


def _split_page(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    pieces: list[str] = []
    step = max(size - overlap, 1)
    for start in range(0, len(words), step):
        window = words[start : start + size]
        if not window:
            break
        pieces.append(" ".join(window))
        if start + size >= len(words):
            break
    return pieces


def chunk_pages(pages: list[str], *, size: int = 220, overlap: int = 40) -> list[Chunk]:
    """`pages` is 0-indexed text per page; returned chunks carry 1-indexed page numbers."""
    chunks: list[Chunk] = []
    ordinal = 0
    for index, page_text in enumerate(pages, start=1):
        for piece in _split_page(page_text, size, overlap):
            chunks.append(Chunk(ordinal=ordinal, page=index, content=piece))
            ordinal += 1
    return chunks
