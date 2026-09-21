from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class SendMessageResponse(BaseModel):
    conversation_id: UUID
    routing: RoutingInfo
    message: MessageOut


class AIStatus(BaseModel):
    configured: bool
    provider: str
    model: str | None
    detail: str
