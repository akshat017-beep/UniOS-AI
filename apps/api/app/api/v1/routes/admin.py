"""Administration: platform statistics, user management and observability."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.embeddings import embeddings_are_configured
from app.ai.registry import ai_is_configured
from app.api.deps import require_roles
from app.core.observability import metrics
from app.db.session import get_db
from app.models.chat import Conversation, Message
from app.models.document import Document, DocumentChunk
from app.models.university import Announcement
from app.models.user import User, UserRole
from app.schemas.university import AdminStats, AdminUserOut

router = APIRouter()

ADMIN_ROLES = (UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


@router.get("/stats", response_model=AdminStats)
def stats(
    user: User = Depends(require_roles(*ADMIN_ROLES)), db: Session = Depends(get_db)
) -> AdminStats:
    by_role = {
        str(role.value if hasattr(role, "value") else role): int(count)
        for role, count in db.execute(select(User.role, func.count()).group_by(User.role)).all()
    }
    return AdminStats(
        users_total=_count(db, User),
        users_by_role=by_role,
        conversations_total=_count(db, Conversation),
        messages_total=_count(db, Message),
        documents_total=_count(db, Document),
        document_chunks_total=_count(db, DocumentChunk),
        announcements_total=_count(db, Announcement),
        ai_configured=ai_is_configured(),
        embeddings_configured=embeddings_are_configured(),
    )


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    q: str | None = Query(default=None, max_length=200),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
) -> list[User]:
    statement = select(User).order_by(User.created_at.desc()).limit(200)
    if q:
        pattern = f"%{q}%"
        statement = statement.where(User.email.ilike(pattern) | User.full_name.ilike(pattern))
    return list(db.scalars(statement))


@router.post("/users/{user_id}/active", response_model=AdminUserOut)
def set_active(
    user_id: UUID,
    is_active: bool,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == actor.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    if target.role == UserRole.SUPER_ADMIN and actor.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only a super admin can change this account")
    target.is_active = is_active
    db.commit()
    db.refresh(target)
    return target


@router.get("/metrics")
def platform_metrics(user: User = Depends(require_roles(*ADMIN_ROLES))) -> dict:
    return metrics.snapshot()
