"""Campus platform: notifications, calendar with AI planning, announcements."""

import json
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.base import ProviderNotConfiguredError, ProviderRequestError
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.university import Announcement, CalendarEvent, Notification
from app.models.user import User, UserRole
from app.schemas.university import (
    AnnouncementCreate,
    AnnouncementOut,
    EventCreate,
    EventOut,
    NotificationCreate,
    NotificationOut,
    PlannedItem,
    PlanRequest,
    PlanResponse,
)
from app.services.generation import generate

router = APIRouter()

PUBLISHER_ROLES = (UserRole.FACULTY, UserRole.CLUB, UserRole.ADMIN, UserRole.SUPER_ADMIN)


# --------------------------------------------------------------------- notifications
@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Notification]:
    statement = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))
    return list(db.scalars(statement.order_by(Notification.created_at.desc()).limit(100)))


@router.post(
    "/notifications", response_model=NotificationOut, status_code=status.HTTP_201_CREATED
)
def create_notification(
    payload: NotificationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    notification = Notification(user_id=user.id, **payload.model_dump())
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


# -------------------------------------------------------------------------- calendar
@router.get("/events", response_model=list[EventOut])
def list_events(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CalendarEvent]:
    horizon = datetime.now(UTC) + timedelta(days=days)
    return list(
        db.scalars(
            select(CalendarEvent)
            .where(CalendarEvent.user_id == user.id, CalendarEvent.starts_at <= horizon)
            .order_by(CalendarEvent.starts_at)
            .limit(500)
        )
    )


@router.post("/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CalendarEvent:
    event = CalendarEvent(user_id=user.id, source="manual", **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    event = db.scalar(
        select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == user.id)
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()


_JSON_BLOCK = re.compile(r"\[.*\]", re.DOTALL)


@router.post("/plan", response_model=PlanResponse)
async def plan_schedule(
    payload: PlanRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlanResponse:
    """Turn a goal into calendar blocks. The AI proposes; the user decides to save."""
    start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    instruction = (
        "Produce a study/work schedule as STRICT JSON only — a single array, no prose and "
        "no code fence. Each item: {\"title\": string, \"description\": string, "
        "\"category\": one of study|revision|project|exam|break, \"day_offset\": integer "
        "starting at 0, \"start_hour\": integer 6-22, \"duration_minutes\": integer}. "
        f"Cover {payload.days} days with about {payload.hours_per_day} hours per day. "
        f"The first day is {start.date().isoformat()}."
    )
    try:
        text, model = await generate(
            agent_name="study", instruction=instruction, content=payload.goal
        )
    except ProviderNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    match = _JSON_BLOCK.search(text)
    if match is None:
        raise HTTPException(
            status_code=502,
            detail="The model did not return a parsable schedule. Try again or rephrase the goal.",
        )
    try:
        raw_items = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502, detail="The returned schedule was not valid JSON."
        ) from exc

    items: list[PlannedItem] = []
    for raw in raw_items[:200]:
        if not isinstance(raw, dict) or not raw.get("title"):
            continue
        try:
            day_offset = int(raw.get("day_offset", 0))
            start_hour = min(max(int(raw.get("start_hour", 9)), 0), 23)
            duration = min(max(int(raw.get("duration_minutes", 60)), 15), 480)
        except (TypeError, ValueError):
            continue
        begins = (start + timedelta(days=day_offset)).replace(hour=start_hour)
        items.append(
            PlannedItem(
                title=str(raw["title"])[:255],
                description=str(raw.get("description", ""))[:4000],
                category=str(raw.get("category", "study"))[:32],
                starts_at=begins,
                ends_at=begins + timedelta(minutes=duration),
            )
        )

    if payload.save and items:
        for item in items:
            db.add(
                CalendarEvent(
                    user_id=user.id,
                    title=item.title,
                    description=item.description,
                    category=item.category,
                    starts_at=item.starts_at,
                    ends_at=item.ends_at,
                    source="ai",
                )
            )
        db.commit()

    return PlanResponse(
        items=items,
        saved=bool(payload.save and items),
        model=model,
        note="Generated by AI — review the blocks before relying on them.",
    )


# --------------------------------------------------------------------- announcements
@router.get("/announcements", response_model=list[AnnouncementOut])
def list_announcements(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Announcement]:
    return list(
        db.scalars(
            select(Announcement)
            .where(Announcement.is_published.is_(True))
            .order_by(Announcement.created_at.desc())
            .limit(100)
        )
    )


@router.post(
    "/announcements", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED
)
def create_announcement(
    payload: AnnouncementCreate,
    user: User = Depends(require_roles(*PUBLISHER_ROLES)),
    db: Session = Depends(get_db),
) -> Announcement:
    announcement = Announcement(
        author_id=user.id,
        title=payload.title,
        body=payload.body,
        audience=payload.audience,
    )
    db.add(announcement)
    db.flush()
    if payload.notify:
        recipients = db.scalars(select(User.id).where(User.is_active.is_(True))).all()
        for recipient_id in recipients:
            db.add(
                Notification(
                    user_id=recipient_id,
                    title=payload.title,
                    body=payload.body[:1000],
                    category="announcement",
                    link="/announcements",
                )
            )
    db.commit()
    db.refresh(announcement)
    return announcement


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: UUID,
    user: User = Depends(require_roles(*PUBLISHER_ROLES)),
    db: Session = Depends(get_db),
) -> None:
    announcement = db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    if announcement.author_id != user.id and user.role not in (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ):
        raise HTTPException(status_code=403, detail="You can only delete your own announcements")
    db.delete(announcement)
    db.commit()
