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
    Hospital,
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


def _normalize_phone(phone_number: str | None) -> str | None:
    if phone_number is None:
        return None
    normalized = "".join(char for char in phone_number.strip() if char.isdigit() or char == "+")
    return normalized or None


def _display_name(user: User) -> str:
    if user.role == UserRole.doctor and user.doctor_profile:
        return user.doctor_profile.display_name
    if user.role == UserRole.patient and user.patient_profile:
        return user.patient_profile.display_name
    return "Dr. AI user"


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        phone_number=user.phone_number,
        role=user.role,
        display_name=_display_name(user),
    )


def _patient_code(user_id: uuid.UUID) -> str:
    return f"PAT-{str(user_id)[:8].upper()}"


def _doctor_hospital_name(body: RegisterRequest) -> str:
    profile = body.doctor_profile
    if profile and profile.hospital_name:
        return profile.hospital_name
    return "Hospital not specified"


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
    if body.role not in (UserRole.doctor, UserRole.patient):
        raise ApiError(403, "forbidden", "Registration is not available for this role.")

    email = _normalize_email(str(body.email)) if body.email is not None else None
    phone_number = _normalize_phone(body.phone_number)
    user = User(
        email=email,
        phone_number=phone_number,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.flush()
    if body.role == UserRole.doctor:
        doctor_profile = body.doctor_profile
        hospital_name = _doctor_hospital_name(body)
        db.add(
            DoctorProfile(
                user_id=user.id,
                display_name=doctor_profile.display_name
                if doctor_profile and doctor_profile.display_name
                else "Doctor profile",
                title="Clinician",
                hospital_name=hospital_name,
                birth_date=doctor_profile.birth_date if doctor_profile else None,
                gender=doctor_profile.gender if doctor_profile else None,
                contact_phone=doctor_profile.contact_phone or phone_number
                if doctor_profile
                else phone_number,
                avatar_url=doctor_profile.avatar_url if doctor_profile else None,
                country=doctor_profile.country if doctor_profile else None,
                province=doctor_profile.province if doctor_profile else None,
                city=doctor_profile.city if doctor_profile else None,
            )
        )
        db.add(
            Hospital(
                name=hospital_name,
                legal_name=None,
                status=(
                    "pending_review"
                    if doctor_profile and doctor_profile.custom_hospital
                    else "active"
                ),
                metadata_json={
                    "source": "doctor_signup",
                    "country": doctor_profile.country if doctor_profile else None,
                    "province": doctor_profile.province if doctor_profile else None,
                    "city": doctor_profile.city if doctor_profile else None,
                    "custom_hospital": doctor_profile.custom_hospital if doctor_profile else False,
                },
            )
        )
    else:
        patient_profile = body.patient_profile
        birth_date = patient_profile.birth_date if patient_profile else None
        gender = patient_profile.gender if patient_profile else None
        db.add(
            PatientProfile(
                user_id=user.id,
                display_name=patient_profile.display_name
                if patient_profile and patient_profile.display_name
                else "New Patient",
                synthetic_identifier=_patient_code(user.id),
                birth_date=birth_date,
                birth_year=birth_date.year if birth_date else None,
                sex=gender,
                gender=gender,
                contact_phone=patient_profile.contact_phone or phone_number
                if patient_profile
                else phone_number,
                avatar_url=patient_profile.avatar_url if patient_profile else None,
                country=patient_profile.country if patient_profile else None,
                province=patient_profile.province if patient_profile else None,
                city=patient_profile.city if patient_profile else None,
                home_address=patient_profile.home_address if patient_profile else None,
                medical_history_setup_completed=False,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "conflict", "An account already exists for this contact.") from None
    db.refresh(user)
    return _create_session(db, user, settings)


@router.post("/auth/login", response_model=AuthTokenResponse)
def login(
    body: LoginRequest,
    db: DbSession,
    settings: AppSettings,
) -> AuthTokenResponse:
    if body.email is not None:
        user = db.scalar(select(User).where(User.email == _normalize_email(str(body.email))))
    else:
        user = db.scalar(
            select(User).where(User.phone_number == _normalize_phone(body.phone_number))
        )
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
