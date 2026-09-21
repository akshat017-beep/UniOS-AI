import json
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.document import CitationOut


class AgentInfo(BaseModel):
    name: str
    title: str
    description: str


class RoutingInfo(BaseModel):
    agent: str
    title: str
    confidence: float
    signals: list[str]


class RouteRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    agent: str | None
    model: str | None
    created_at: datetime
    citations: list[CitationOut] = []

    @field_validator("citations", mode="before")
    @classmethod
    def _parse_citations(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value or []


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


class SendMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: UUID | None = None
    agent: str | None = Field(default=None, max_length=32)
    # Restrict retrieval to these documents; omit to search everything the user owns.
    document_ids: list[UUID] | None = None
    use_documents: bool = False


class SendMessageResponse(BaseModel):
    conversation_id: UUID
    routing: RoutingInfo
    message: MessageOut
    injection_warnings: list[str] = []


class AIStatus(BaseModel):
    configured: bool
    provider: str
    model: str | None
    detail: str
