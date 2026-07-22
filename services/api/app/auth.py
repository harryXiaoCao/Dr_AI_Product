import uuid
from datetime import UTC, datetime, timedelta
from hmac import compare_digest

from fastapi import APIRouter, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.dependencies import AppSettings, CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    AuditEvent,
    DoctorProfile,
    Hospital,
    PatientProfile,
    PayerMembership,
    PayerOrganization,
    PhoneVerificationChallenge,
    RefreshSession,
    User,
    UserRole,
)
from app.schemas import (
    AccountEmailUpdateRequest,
    AuthTokenResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PhoneVerificationRequest,
    PhoneVerificationResponse,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)
from app.security import (
    create_access_token,
    hash_password,
    hash_phone_verification_code,
    hash_refresh_token,
    new_phone_verification_code,
    new_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/api/v1", tags=["authentication"])
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password")
_REGISTRATION_PURPOSE = "registration"
_PASSWORD_RESET_PURPOSE = "password_reset"
_PASSWORD_RESET_TTL_MINUTES = 10
_PASSWORD_RESET_MAX_ATTEMPTS = 5


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
    if user.role == UserRole.payer and user.payer_memberships:
        return user.payer_memberships[0].display_name
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
    user.last_active_at = datetime.now(UTC)
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
    if body.role not in (UserRole.doctor, UserRole.patient, UserRole.payer):
        raise ApiError(403, "forbidden", "Registration is not available for this role.")

    email = _normalize_email(str(body.email)) if body.email is not None else None
    phone_number = _normalize_phone(body.phone_number)
    registration_challenge: PhoneVerificationChallenge | None = None
    test_code_allowed = settings.environment == "test" and body.verification_code == "123456"
    if not test_code_allowed:
        now = datetime.now(UTC)
        registration_challenge = db.scalar(
            select(PhoneVerificationChallenge)
            .where(
                PhoneVerificationChallenge.phone_number == phone_number,
                PhoneVerificationChallenge.purpose == _REGISTRATION_PURPOSE,
                PhoneVerificationChallenge.consumed_at.is_(None),
                PhoneVerificationChallenge.expires_at > now,
            )
            .order_by(PhoneVerificationChallenge.created_at.desc())
            .with_for_update()
        )
        if (
            registration_challenge is None
            or registration_challenge.attempts >= _PASSWORD_RESET_MAX_ATTEMPTS
        ):
            raise ApiError(
                422,
                "invalid_verification_code",
                "The verification code is invalid or expired.",
            )
        supplied_hash = hash_phone_verification_code(
            registration_challenge.phone_number,
            _REGISTRATION_PURPOSE,
            body.verification_code,
            settings,
        )
        if not compare_digest(registration_challenge.code_hash, supplied_hash):
            registration_challenge.attempts += 1
            db.commit()
            raise ApiError(
                422,
                "invalid_verification_code",
                "The verification code is invalid or expired.",
            )
    user = User(
        email=email,
        phone_number=phone_number,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    try:
        db.add(user)
        db.flush()
        if registration_challenge is not None:
            registration_challenge.user_id = user.id
            registration_challenge.consumed_at = datetime.now(UTC)
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
                    specialty=doctor_profile.specialty if doctor_profile else None,
                    department=doctor_profile.department if doctor_profile else None,
                    preferred_language=doctor_profile.preferred_language
                    if doctor_profile
                    else None,
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
                        "custom_hospital": doctor_profile.custom_hospital
                        if doctor_profile
                        else False,
                    },
                )
            )
        elif body.role == UserRole.patient:
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
                    height_cm=patient_profile.height_cm if patient_profile else None,
                    weight_kg=patient_profile.weight_kg if patient_profile else None,
                    medical_history_setup_completed=False,
                )
            )
        else:
            payer_profile = body.payer_profile
            if payer_profile is None:
                raise ApiError(422, "validation_failed", "Payer organization details are required.")
            organization = PayerOrganization(
                name=payer_profile.organization_name,
                organization_type=payer_profile.organization_type,
                jurisdiction_code="CN",
                verification_status="synthetic_only",
            )
            db.add(organization)
            db.flush()
            db.add(
                PayerMembership(
                    payer_organization_id=organization.id,
                    user_id=user.id,
                    display_name=payer_profile.display_name,
                    title=payer_profile.title,
                    status="active",
                    scope="synthetic_review",
                )
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "conflict", "An account already exists for this contact.") from None
    db.refresh(user)
    return _create_session(db, user, settings)


@router.post(
    "/auth/registration-code/request",
    response_model=PhoneVerificationResponse,
)
def request_registration_code(
    body: PhoneVerificationRequest,
    db: DbSession,
    settings: AppSettings,
) -> PhoneVerificationResponse:
    phone_number = _normalize_phone(body.phone_number)
    existing_user = db.scalar(select(User).where(User.phone_number == phone_number))
    debug_code: str | None = None
    if existing_user is None and phone_number is not None:
        now = datetime.now(UTC)
        db.execute(
            update(PhoneVerificationChallenge)
            .where(
                PhoneVerificationChallenge.phone_number == phone_number,
                PhoneVerificationChallenge.purpose == _REGISTRATION_PURPOSE,
                PhoneVerificationChallenge.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        code = new_phone_verification_code()
        db.add(
            PhoneVerificationChallenge(
                user_id=None,
                phone_number=phone_number,
                purpose=_REGISTRATION_PURPOSE,
                code_hash=hash_phone_verification_code(
                    phone_number,
                    _REGISTRATION_PURPOSE,
                    code,
                    settings,
                ),
                attempts=0,
                expires_at=now + timedelta(minutes=_PASSWORD_RESET_TTL_MINUTES),
            )
        )
        db.commit()
        if settings.environment in {"local", "test"}:
            debug_code = code
    return PhoneVerificationResponse(
        message=("If this phone number is available, a verification code will be sent."),
        expires_in=_PASSWORD_RESET_TTL_MINUTES * 60,
        debug_code=debug_code,
    )


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


@router.post(
    "/auth/password-reset/request",
    response_model=PhoneVerificationResponse,
)
def request_password_reset(
    body: PhoneVerificationRequest,
    db: DbSession,
    settings: AppSettings,
) -> PhoneVerificationResponse:
    phone_number = _normalize_phone(body.phone_number)
    user = db.scalar(
        select(User).where(
            User.phone_number == phone_number,
            User.is_active.is_(True),
        )
    )
    debug_code: str | None = None
    if user is not None and phone_number is not None:
        now = datetime.now(UTC)
        db.execute(
            update(PhoneVerificationChallenge)
            .where(
                PhoneVerificationChallenge.user_id == user.id,
                PhoneVerificationChallenge.purpose == _PASSWORD_RESET_PURPOSE,
                PhoneVerificationChallenge.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        code = new_phone_verification_code()
        db.add(
            PhoneVerificationChallenge(
                user_id=user.id,
                phone_number=phone_number,
                purpose=_PASSWORD_RESET_PURPOSE,
                code_hash=hash_phone_verification_code(
                    phone_number,
                    _PASSWORD_RESET_PURPOSE,
                    code,
                    settings,
                ),
                attempts=0,
                expires_at=now + timedelta(minutes=_PASSWORD_RESET_TTL_MINUTES),
            )
        )
        db.commit()
        if settings.environment in {"local", "test"}:
            debug_code = code
    return PhoneVerificationResponse(
        message=("If an active account uses this phone number, a verification code will be sent."),
        expires_in=_PASSWORD_RESET_TTL_MINUTES * 60,
        debug_code=debug_code,
    )


@router.post("/auth/password-reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    body: PasswordResetRequest,
    db: DbSession,
    settings: AppSettings,
) -> Response:
    phone_number = _normalize_phone(body.phone_number)
    now = datetime.now(UTC)
    challenge = db.scalar(
        select(PhoneVerificationChallenge)
        .where(
            PhoneVerificationChallenge.phone_number == phone_number,
            PhoneVerificationChallenge.purpose == _PASSWORD_RESET_PURPOSE,
            PhoneVerificationChallenge.consumed_at.is_(None),
            PhoneVerificationChallenge.expires_at > now,
        )
        .order_by(PhoneVerificationChallenge.created_at.desc())
        .with_for_update()
    )
    if challenge is None or challenge.attempts >= _PASSWORD_RESET_MAX_ATTEMPTS:
        raise ApiError(
            422,
            "invalid_verification_code",
            "The verification code is invalid or expired.",
        )
    supplied_hash = hash_phone_verification_code(
        challenge.phone_number,
        _PASSWORD_RESET_PURPOSE,
        body.verification_code,
        settings,
    )
    if not compare_digest(challenge.code_hash, supplied_hash):
        challenge.attempts += 1
        db.commit()
        raise ApiError(
            422,
            "invalid_verification_code",
            "The verification code is invalid or expired.",
        )
    user = db.scalar(select(User).where(User.id == challenge.user_id).with_for_update())
    if user is None or not user.is_active:
        raise ApiError(
            422,
            "invalid_verification_code",
            "The verification code is invalid or expired.",
        )
    user.password_hash = hash_password(body.new_password)
    challenge.consumed_at = now
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            patient_id=user.patient_profile.id if user.patient_profile else None,
            event_type="account_password_reset",
            resource_type="user",
            resource_id=user.id,
            metadata_json={"verification_channel": "phone"},
        )
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/auth/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: PasswordChangeRequest,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    if not verify_password(body.current_password, user.password_hash):
        raise ApiError(
            422,
            "current_password_incorrect",
            "The current password is incorrect.",
        )
    if verify_password(body.new_password, user.password_hash):
        raise ApiError(
            422,
            "password_unchanged",
            "Choose a password you have not just used.",
        )
    now = datetime.now(UTC)
    user.password_hash = hash_password(body.new_password)
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            patient_id=user.patient_profile.id if user.patient_profile else None,
            event_type="account_password_changed",
            resource_type="user",
            resource_id=user.id,
            metadata_json={"actor_role": user.role.value},
        )
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/auth/account/email", response_model=UserResponse)
def update_account_email(
    body: AccountEmailUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    email = _normalize_email(str(body.email)) if body.email is not None else None
    if user.email == email:
        return _user_response(user)
    patient_id = user.patient_profile.id if user.patient_profile else None
    if email is not None:
        existing_user_id = db.scalar(select(User.id).where(User.email == email, User.id != user.id))
        if existing_user_id is not None:
            raise ApiError(
                409,
                "email_already_in_use",
                "An account already uses this email address.",
            )
    user.email = email
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            patient_id=patient_id,
            event_type="account_email_updated",
            resource_type="user",
            resource_id=user.id,
            metadata_json={
                "actor_role": user.role.value,
                "email_removed": email is None,
            },
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(
            409,
            "email_already_in_use",
            "An account already uses this email address.",
        ) from None
    db.refresh(user)
    return _user_response(user)


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
