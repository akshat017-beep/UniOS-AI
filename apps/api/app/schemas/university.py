from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str
    category: str
    link: str | None
    is_read: bool
    created_at: datetime


class NotificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(default="", max_length=4000)
    category: str = Field(default="general", max_length=32)
    link: str | None = Field(default=None, max_length=512)


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    category: str
    starts_at: datetime
    ends_at: datetime | None
    source: str


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)
    category: str = Field(default="study", max_length=32)
    starts_at: datetime
    ends_at: datetime | None = None


class PlanRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=2000)
    days: int = Field(default=7, ge=1, le=60)
    hours_per_day: float = Field(default=2.0, ge=0.5, le=16)
    save: bool = False


class PlannedItem(BaseModel):
    title: str
    description: str = ""
    category: str = "study"
    starts_at: datetime
    ends_at: datetime | None = None


class PlanResponse(BaseModel):
    items: list[PlannedItem]
    saved: bool
    model: str
    note: str = ""


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str
    audience: str
    is_published: bool
    created_at: datetime
    author_id: UUID


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(default="", max_length=8000)
    audience: str = Field(default="ALL", max_length=32)
    notify: bool = False


class SearchHit(BaseModel):
    kind: str
    id: str
    title: str
    snippet: str
    link: str


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]


class AdminStats(BaseModel):
    users_total: int
    users_by_role: dict[str, int]
    conversations_total: int
    messages_total: int
    documents_total: int
    document_chunks_total: int
    announcements_total: int
    ai_configured: bool
    embeddings_configured: bool


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
