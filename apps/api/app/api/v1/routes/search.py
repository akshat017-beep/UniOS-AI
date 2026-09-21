"""Global search across the user's own data plus published university content."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.chat import Conversation, Message
from app.models.document import Document, DocumentChunk
from app.models.university import Announcement, CalendarEvent
from app.models.user import User
from app.schemas.university import SearchHit, SearchResponse

router = APIRouter()


def _snippet(text: str, query: str, width: int = 180) -> str:
    lowered = text.lower()
    index = lowered.find(query.lower())
    if index == -1:
        return text[:width].strip()
    start = max(index - width // 3, 0)
    return ("…" if start else "") + text[start : start + width].strip() + "…"


@router.get("", response_model=SearchResponse)
def global_search(
    q: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    pattern = f"%{q}%"
    hits: list[SearchHit] = []

    for document in db.scalars(
        select(Document)
        .where(Document.user_id == user.id, Document.title.ilike(pattern))
        .limit(limit)
    ):
        hits.append(
            SearchHit(
                kind="document",
                id=str(document.id),
                title=document.title,
                snippet=f"{document.pages} page(s) · {document.status}",
                link="/documents",
            )
        )

    for chunk, title in db.execute(
        select(DocumentChunk, Document.title)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.user_id == user.id, DocumentChunk.content.ilike(pattern))
        .limit(limit)
    ).all():
        hits.append(
            SearchHit(
                kind="passage",
                id=str(chunk.id),
                title=f"{title} — page {chunk.page}",
                snippet=_snippet(chunk.content, q),
                link="/documents",
            )
        )

    for conversation, message in db.execute(
        select(Conversation, Message)
        .join(Message, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == user.id,
            or_(Message.content.ilike(pattern), Conversation.title.ilike(pattern)),
        )
        .limit(limit)
    ).all():
        hits.append(
            SearchHit(
                kind="conversation",
                id=str(conversation.id),
                title=conversation.title,
                snippet=_snippet(message.content, q),
                link=f"/chat?c={conversation.id}",
            )
        )

    for event in db.scalars(
        select(CalendarEvent)
        .where(CalendarEvent.user_id == user.id, CalendarEvent.title.ilike(pattern))
        .limit(limit)
    ):
        hits.append(
            SearchHit(
                kind="event",
                id=str(event.id),
                title=event.title,
                snippet=event.starts_at.isoformat(),
                link="/calendar",
            )
        )

    for announcement in db.scalars(
        select(Announcement)
        .where(
            Announcement.is_published.is_(True),
            or_(Announcement.title.ilike(pattern), Announcement.body.ilike(pattern)),
        )
        .limit(limit)
    ):
        hits.append(
            SearchHit(
                kind="announcement",
                id=str(announcement.id),
                title=announcement.title,
                snippet=_snippet(announcement.body, q),
                link="/announcements",
            )
        )

    return SearchResponse(query=q, hits=hits[:limit])
