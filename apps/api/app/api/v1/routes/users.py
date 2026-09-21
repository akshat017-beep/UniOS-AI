from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import Profile, User, UserRole
from app.schemas.user import ProfileUpdate, UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me/profile", response_model=UserOut)
def update_my_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    profile = user.profile or Profile(user_id=user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "",
    response_model=list[UserOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))],
)
def list_users(db: Session = Depends(get_db), limit: int = 50, offset: int = 0) -> list[User]:
    """Administrative listing. Students and faculty receive 403."""
    limit = max(1, min(limit, 200))
    statement = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement))
