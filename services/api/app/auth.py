import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.dependencies import AppSettings, CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    DoctorProfile,
    PatientProfile,
    RefreshSession,
    User,
    UserRole,
)
from app.schemas import (
    AuthTokenResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)
from app.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/api/v1", tags=["authentication"])
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _display_name(user: User) -> str:
    if user.role == UserRole.doctor and user.doctor_profile:
        return user.doctor_profile.display_name
    if user.role == UserRole.patient and user.patient_profile:
        return user.patient_profile.display_name
    return "Invited beta user"


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        display_name=_display_name(user),
    )


def _create_session(
    db: Session,
    user: User,
    settings: Settings,
    *,
    family_id: uuid.UUID | None = None,
) -> AuthTokenResponse:
    raw_refresh_token = new_refresh_token()
    refresh_session = RefreshSession(
        family_id=family_id or uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    db.add(refresh_session)
    db.flush()
    access_token, _ = create_access_token(user, refresh_session.id, settings)
    db.commit()
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        expires_in=settings.access_token_minutes * 60,
        user=_user_response(user),
    )


def _expected_invite(settings: Settings, role: UserRole) -> str | None:
    configured = (
        settings.doctor_invite_code if role == UserRole.doctor else settings.patient_invite_code
    )
    return configured.get_secret_value() if configured else None


@router.post(
    "/auth/register",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: RegisterRequest,
    db: DbSession,
    settings: AppSettings,
) -> AuthTokenResponse:
    expected_invite = _expected_invite(settings, body.role)
    if expected_invite is None or not secrets.compare_digest(expected_invite, body.invite_code):
        raise ApiError(403, "forbidden", "Registration is not available for this invitation.")

    user = User(
        email=_normalize_email(str(body.email)),
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.flush()
    if body.role == UserRole.doctor:
        db.add(
            DoctorProfile(
                user_id=user.id,
                display_name="Invited Demo Doctor",
                title="Invited beta clinician",
                hospital_name="Synthetic Community Hospital",
            )
        )
    else:
        db.add(
            PatientProfile(
                user_id=user.id,
                display_name="Invited Demo Patient",
                synthetic_identifier=f"SYN-{str(user.id)[:8].upper()}",
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "conflict", "An account already exists for this email.") from None
    db.refresh(user)
    return _create_session(db, user, settings)


@router.post("/auth/login", response_model=AuthTokenResponse)
def login(
    body: LoginRequest,
    db: DbSession,
    settings: AppSettings,
) -> AuthTokenResponse:
    user = db.scalar(select(User).where(User.email == _normalize_email(str(body.email))))
    encoded_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(body.password, encoded_hash)
    if user is None or not user.is_active or not password_is_valid:
        raise ApiError(401, "unauthenticated", "The email or password is incorrect.")
    return _create_session(db, user, settings)


@router.post("/auth/refresh", response_model=AuthTokenResponse)
def refresh(
    body: RefreshRequest,
    db: DbSession,
    settings: AppSettings,
) -> AuthTokenResponse:
    now = datetime.now(UTC)
    token_hash = hash_refresh_token(body.refresh_token)
    current = db.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash).with_for_update()
    )
    if current is None:
        raise ApiError(401, "unauthenticated", "The refresh session is invalid or expired.")
    if current.used_at is not None or current.revoked_at is not None:
        db.execute(
            update(RefreshSession)
            .where(RefreshSession.family_id == current.family_id)
            .values(revoked_at=now)
        )
        db.commit()
        raise ApiError(401, "unauthenticated", "The refresh session is invalid or expired.")
    if current.expires_at <= now:
        current.revoked_at = now
        db.commit()
        raise ApiError(401, "unauthenticated", "The refresh session is invalid or expired.")

    user = db.scalar(select(User).where(User.id == current.user_id, User.is_active.is_(True)))
    if user is None:
        current.revoked_at = now
        db.commit()
        raise ApiError(401, "unauthenticated", "The refresh session is invalid or expired.")

    raw_refresh_token = new_refresh_token()
    replacement = RefreshSession(
        family_id=current.family_id,
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=now + timedelta(days=settings.refresh_token_days),
    )
    db.add(replacement)
    db.flush()
    current.used_at = now
    current.revoked_at = now
    current.replaced_by_id = replacement.id
    access_token, _ = create_access_token(user, replacement.id, settings, now=now)
    db.commit()
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        expires_in=settings.access_token_minutes * 60,
        user=_user_response(user),
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: LogoutRequest, db: DbSession, user: CurrentUser) -> Response:
    token_hash = hash_refresh_token(body.refresh_token)
    current = db.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash).with_for_update()
    )
    if current is not None and current.user_id == user.id and current.revoked_at is None:
        current.revoked_at = datetime.now(UTC)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser) -> MeResponse:
    return MeResponse(**_user_response(user).model_dump())
