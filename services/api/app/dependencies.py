import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.errors import ApiError
from app.models import RefreshSession, User
from app.security import AccessTokenError, decode_access_token

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    db: DbSession,
    settings: AppSettings,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError(401, "unauthenticated", "Authentication is required.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = decode_access_token(token, settings)
        user_id = uuid.UUID(claims["sub"])
        session_id = uuid.UUID(claims["sid"])
    except (AccessTokenError, KeyError, TypeError, ValueError):
        raise ApiError(401, "unauthenticated", "The access token is invalid or expired.") from None

    refresh_session = db.scalar(
        select(RefreshSession).where(
            RefreshSession.id == session_id,
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        )
    )
    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if refresh_session is None or user is None or user.role.value != claims.get("role"):
        raise ApiError(401, "unauthenticated", "The access token is invalid or expired.")
    now = datetime.now(UTC)
    if user.last_active_at is None or user.last_active_at < now - timedelta(minutes=15):
        user.last_active_at = now
        db.commit()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
