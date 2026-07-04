import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    CareRelationship,
    DashboardSnapshot,
    PatientProfile,
    UserRole,
)
from app.schemas import (
    DashboardResponse,
    PatientListResponse,
    PatientSummaryResponse,
)

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


def _neutral_not_found() -> ApiError:
    return ApiError(404, "not_found", "The requested resource was not found.")


@router.get("/me/dashboard", response_model=DashboardResponse)
def own_dashboard(user: CurrentUser, db: DbSession) -> DashboardResponse:
    snapshot = db.scalar(
        select(DashboardSnapshot).where(DashboardSnapshot.user_id == user.id)
    )
    if snapshot is None:
        return DashboardResponse(role=user.role, data={})
    return DashboardResponse(role=user.role, data=snapshot.payload)


@router.get("/patients", response_model=PatientListResponse)
def assigned_patients(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=50),
) -> PatientListResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profiles = db.scalars(
        select(PatientProfile)
        .join(CareRelationship)
        .where(
            CareRelationship.doctor_id == user.doctor_profile.id,
            CareRelationship.is_active.is_(True),
        )
        .order_by(PatientProfile.display_name)
        .limit(limit)
    ).all()
    return PatientListResponse(
        items=[
            PatientSummaryResponse(
                patient_id=profile.id,
                display_name=profile.display_name,
                synthetic_identifier=profile.synthetic_identifier,
            )
            for profile in profiles
        ]
    )


@router.get("/patients/{patient_id}", response_model=PatientSummaryResponse)
def patient_summary(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> PatientSummaryResponse:
    profile: PatientProfile | None = None
    if user.role == UserRole.doctor and user.doctor_profile is not None:
        profile = db.scalar(
            select(PatientProfile)
            .join(CareRelationship)
            .where(
                PatientProfile.id == patient_id,
                CareRelationship.doctor_id == user.doctor_profile.id,
                CareRelationship.is_active.is_(True),
            )
        )
    elif user.role == UserRole.patient and user.patient_profile is not None:
        profile = db.scalar(
            select(PatientProfile).where(
                PatientProfile.id == patient_id,
                PatientProfile.user_id == user.id,
            )
        )
    if profile is None:
        raise _neutral_not_found()
    return PatientSummaryResponse(
        patient_id=profile.id,
        display_name=profile.display_name,
        synthetic_identifier=profile.synthetic_identifier,
    )


@router.get("/patient/me/today", response_model=DashboardResponse)
def patient_today(user: CurrentUser, db: DbSession) -> DashboardResponse:
    if user.role != UserRole.patient:
        raise _neutral_not_found()
    snapshot = db.scalar(
        select(DashboardSnapshot).where(DashboardSnapshot.user_id == user.id)
    )
    if snapshot is None:
        return DashboardResponse(role=user.role, data={})
    return DashboardResponse(role=user.role, data=snapshot.payload)
