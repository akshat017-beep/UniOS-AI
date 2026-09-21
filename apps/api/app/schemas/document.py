from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    filename: str
    content_type: str
    size_bytes: int
    pages: int
    status: str
    error: str | None
    created_at: datetime


class CitationOut(BaseModel):
    document_id: UUID
    document_title: str
    page: int
    snippet: str
    score: float


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    document_ids: list[UUID] | None = None
    limit: int = Field(default=6, ge=1, le=20)


class DocumentSearchResponse(BaseModel):
    citations: list[CitationOut]
    injection_warnings: list[str] = []


class RagStatus(BaseModel):
    embeddings_configured: bool
    provider: str
    model: str | None
    vector_backend: str
    detail: str
