from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import AuditLog, Profile, User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.user import UserOut

router = APIRouter()


def _record(db: Session, user_id, action: str, request: Request) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            ip_address=request.client.host if request.client else None,
        )
    )


def _tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_token(str(user.id), "access", user.role.value),
        refresh_token=create_token(str(user.id), "refresh"),
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest, request: Request, db: Session = Depends(get_db)
) -> TokenPair:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role,
    )
    user.profile = Profile()
    db.add(user)
    db.flush()
    _record(db, user.id, "auth.register", request)
    db.commit()
    db.refresh(user)
    return _tokens(user)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.hashed_password):
        # Same message for unknown email and wrong password — no account enumeration.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    _record(db, user.id, "auth.login", request)
    db.commit()
    return _tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token, "refresh")
        user = db.get(User, UUID(str(claims["sub"])))
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    return _tokens(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    # Tokens are stateless; the client discards them. The event is audited here.
    _record(db, user.id, "auth.logout", request)
    db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
