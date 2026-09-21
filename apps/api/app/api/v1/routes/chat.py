import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.registry import get_agent
from app.agents.router import route as route_message
from app.ai.base import ProviderNotConfiguredError, ProviderRequestError
from app.ai.registry import get_chat_model
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.chat import Conversation, Message
from app.models.user import User
from app.rag.pipeline import retrieve
from app.schemas.chat import (
    ConversationDetail,
    ConversationOut,
    MessageOut,
    RoutingInfo,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.chat import build_prompt, create_conversation, get_conversation

router = APIRouter()

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Conversation]:
    return list(
        db.scalars(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
            .limit(100)
        )
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def read_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    conversation = get_conversation(db, user, conversation_id)
    if conversation is None:
        raise _NOT_FOUND
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    conversation = get_conversation(db, user, conversation_id)
    if conversation is None:
        raise _NOT_FOUND
    db.delete(conversation)
    db.commit()


async def _prepare(payload: SendMessageRequest, user: User, db: Session):
    if payload.conversation_id:
        conversation = get_conversation(db, user, payload.conversation_id)
        if conversation is None:
            raise _NOT_FOUND
        history = list(conversation.messages)
    else:
        conversation = create_conversation(db, user, payload.message)
        history = []

    if payload.agent:
        agent = get_agent(payload.agent)
        routing = RoutingInfo(
            agent=agent.name, title=agent.title, confidence=1.0, signals=["chosen by user"]
        )
    else:
        decision = route_message(payload.message)
        agent = decision.agent
        routing = RoutingInfo(
            agent=agent.name,
            title=agent.title,
            confidence=decision.confidence,
            signals=list(decision.signals),
        )

    db.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=payload.message,
            agent=agent.name,
        )
    )
    db.flush()

    retrieval = None
    if payload.use_documents or payload.document_ids:
        try:
            retrieval = await retrieve(
                db,
                user_id=user.id,
                query=payload.message,
                document_ids=payload.document_ids,
            )
        except ProviderNotConfiguredError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc
        if retrieval.has_context:
            agent = get_agent("document")
            routing = RoutingInfo(
                agent=agent.name,
                title=agent.title,
                confidence=1.0,
                signals=["document context attached"],
            )

    prompt = build_prompt(
        agent=agent,
        user=user,
        history=history,
        message=payload.message,
        context=retrieval.context if retrieval else "",
    )
    return conversation, agent, routing, prompt, retrieval


def _model_or_503():
    try:
        return get_chat_model()
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    payload: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SendMessageResponse:
    model = _model_or_503()
    conversation, agent, routing, prompt, retrieval = await _prepare(payload, user, db)

    try:
        result = await model.complete(
            prompt,
            temperature=settings.ai_temperature,
            max_output_tokens=settings.ai_max_output_tokens,
        )
    except ProviderRequestError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    reply = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result.content,
        agent=agent.name,
        model=result.model,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        citations=json.dumps(
            [
                {
                    "document_id": str(citation.document_id),
                    "document_title": citation.document_title,
                    "page": citation.page,
                    "snippet": citation.snippet,
                    "score": citation.score,
                }
                for citation in retrieval.citations
            ]
        )
        if retrieval and retrieval.citations
        else None,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)

    return SendMessageResponse(
        conversation_id=conversation.id,
        routing=routing,
        message=MessageOut.model_validate(reply),
        injection_warnings=retrieval.injection_warnings if retrieval else [],
    )


@router.post("/stream")
async def stream_message(
    payload: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Server-sent events: `meta`, then `token` events, then `done` or `error`."""
    model = _model_or_503()
    conversation, agent, routing, prompt, retrieval = await _prepare(payload, user, db)
    db.commit()
    citations_json = (
        json.dumps(
            [
                {
                    "document_id": str(citation.document_id),
                    "document_title": citation.document_title,
                    "page": citation.page,
                    "snippet": citation.snippet,
                    "score": citation.score,
                }
                for citation in retrieval.citations
            ]
        )
        if retrieval and retrieval.citations
        else None
    )
    conversation_id = conversation.id

    async def events() -> AsyncIterator[str]:
        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        yield sse(
            "meta",
            {
                "conversation_id": str(conversation_id),
                "routing": routing.model_dump(),
                "citations": json.loads(citations_json) if citations_json else [],
                "injection_warnings": retrieval.injection_warnings if retrieval else [],
            },
        )
        buffer: list[str] = []
        try:
            async for piece in model.stream(
                prompt,
                temperature=settings.ai_temperature,
                max_output_tokens=settings.ai_max_output_tokens,
            ):
                buffer.append(piece)
                yield sse("token", {"text": piece})
        except ProviderRequestError as exc:
            yield sse("error", {"detail": str(exc)})
            return

        content = "".join(buffer)
        db.add(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=content,
                agent=agent.name,
                model=model.name,
                citations=citations_json,
            )
        )
        db.commit()
        yield sse("done", {"conversation_id": str(conversation_id)})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
