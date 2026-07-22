import uuid
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    AuditEvent,
    CareCostItem,
    CareRelationship,
    ClinicalEvent,
    PatientProfile,
    PayerMembership,
    PayerOrganization,
    PayerRequest,
    PayerRequestLine,
    PayerReview,
    UserRole,
)

router = APIRouter(prefix="/api/v1", tags=["care-and-cost transparency"])

ItemType = Literal[
    "medication",
    "prescription",
    "imaging",
    "laboratory",
    "procedure",
    "consultation",
    "booking",
    "follow_up",
    "therapy",
    "equipment",
    "other",
]
ItemStatus = Literal["planned", "scheduled", "completed", "cancelled"]
ReviewAction = Literal["request_clarification", "accept", "escalate", "close"]


class CareCostItemRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    item_type: ItemType
    label: str = Field(min_length=2, max_length=200)
    service_date: date
    status: ItemStatus = "planned"
    quantity: int = Field(default=1, ge=1, le=999)
    currency: Literal["CNY"] = "CNY"
    actual_cost_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    payer_requested_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    patient_responsibility_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_amounts(self) -> "CareCostItemRequest":
        allocated = self.payer_requested_minor + self.patient_responsibility_minor
        if allocated > self.actual_cost_minor:
            raise ValueError("Payer and patient amounts cannot exceed the actual cost.")
        return self


class CareCostItemResponse(BaseModel):
    id: uuid.UUID
    clinical_event_id: uuid.UUID
    item_type: str
    label: str
    service_date: date
    status: str
    quantity: int
    currency: str
    actual_cost_minor: int
    payer_requested_minor: int
    patient_responsibility_minor: int
    ai_review_score: int | None
    ai_review_status: str
    ai_review_summary: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CareCostEventResponse(BaseModel):
    clinical_event_id: uuid.UUID
    title: str
    status: str
    actual_total_minor: int
    payer_requested_total_minor: int
    patient_responsibility_total_minor: int
    currency: str
    items: list[CareCostItemResponse]


class CareCostLedgerResponse(BaseModel):
    patient_id: uuid.UUID
    patient_display_name: str
    actual_total_minor: int
    payer_requested_total_minor: int
    patient_responsibility_total_minor: int
    currency: str
    events: list[CareCostEventResponse]


class PayerOrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    organization_type: str
    jurisdiction_code: str
    verification_status: str


class PayerRequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    payer_organization_id: uuid.UUID
    care_cost_item_ids: list[uuid.UUID] = Field(default_factory=list, max_length=200)
    doctor_summary: str = Field(min_length=10, max_length=4000)


class PayerRequestLineResponse(BaseModel):
    id: uuid.UUID
    care_cost_item_id: uuid.UUID | None
    item_type: str
    label: str
    service_date: date
    currency: str
    actual_cost_minor: int
    requested_minor: int
    patient_responsibility_minor: int


class PayerReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    action: ReviewAction
    reason_code: str = Field(min_length=2, max_length=80)
    note: str | None = Field(default=None, max_length=4000)


class PayerReviewResponse(BaseModel):
    id: uuid.UUID
    action: str
    reason_code: str
    note: str | None
    created_at: datetime


class PayerRequestResponse(BaseModel):
    id: uuid.UUID
    clinical_event_id: uuid.UUID
    clinical_event_title: str
    patient_id: uuid.UUID
    patient_display_name: str
    doctor_display_name: str
    payer_organization: PayerOrganizationResponse
    status: str
    currency: str
    requested_total_minor: int
    doctor_summary: str
    ai_review_status: str
    ai_review_score: int | None
    ai_review_summary: str | None
    created_at: datetime
    reviewed_at: datetime | None
    lines: list[PayerRequestLineResponse]
    reviews: list[PayerReviewResponse]


class PayerRequestListResponse(BaseModel):
    items: list[PayerRequestResponse]


class PayerProfileResponse(BaseModel):
    membership_id: uuid.UUID
    display_name: str
    title: str
    status: str
    scope: str
    organization: PayerOrganizationResponse


class PayerDashboardResponse(BaseModel):
    profile: PayerProfileResponse
    open_requests: int
    clarification_requests: int
    completed_reviews: int
    pending_requested_total_minor: int
    currency: str = "CNY"


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "The requested resource was not found.")


def _require_doctor_patient(
    db: DbSession, user: CurrentUser, patient_id: uuid.UUID
) -> PatientProfile:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _not_found()
    patient = db.scalar(
        select(PatientProfile)
        .join(CareRelationship)
        .where(
            PatientProfile.id == patient_id,
            CareRelationship.patient_id == patient_id,
            CareRelationship.doctor_id == user.doctor_profile.id,
            CareRelationship.is_active.is_(True),
        )
    )
    if patient is None:
        raise _not_found()
    return patient


def _require_event(db: DbSession, patient_id: uuid.UUID, event_id: uuid.UUID) -> ClinicalEvent:
    event = db.scalar(
        select(ClinicalEvent).where(
            ClinicalEvent.id == event_id, ClinicalEvent.patient_id == patient_id
        )
    )
    if event is None:
        raise _not_found()
    return event


def _require_membership(db: DbSession, user: CurrentUser) -> PayerMembership:
    if user.role != UserRole.payer:
        raise _not_found()
    membership = db.scalar(
        select(PayerMembership)
        .options(selectinload(PayerMembership.organization))
        .where(PayerMembership.user_id == user.id, PayerMembership.status == "active")
    )
    if membership is None:
        raise _not_found()
    return membership


def _item_response(item: CareCostItem) -> CareCostItemResponse:
    return CareCostItemResponse(
        id=item.id,
        clinical_event_id=item.clinical_event_id,
        item_type=item.item_type,
        label=item.label,
        service_date=item.service_date,
        status=item.status,
        quantity=item.quantity,
        currency=item.currency,
        actual_cost_minor=item.actual_cost_minor,
        payer_requested_minor=item.payer_requested_minor,
        patient_responsibility_minor=item.patient_responsibility_minor,
        ai_review_score=item.ai_review_score,
        ai_review_status=item.ai_review_status,
        ai_review_summary=item.ai_review_summary,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _ledger(db: DbSession, patient: PatientProfile) -> CareCostLedgerResponse:
    events = db.scalars(
        select(ClinicalEvent)
        .options(selectinload(ClinicalEvent.care_cost_items))
        .where(ClinicalEvent.patient_id == patient.id)
        .order_by(ClinicalEvent.updated_at.desc(), ClinicalEvent.id)
    ).all()
    event_rows: list[CareCostEventResponse] = []
    for event in events:
        items = sorted(
            event.care_cost_items,
            key=lambda item: (item.service_date, item.created_at, item.id),
            reverse=True,
        )
        event_rows.append(
            CareCostEventResponse(
                clinical_event_id=event.id,
                title=event.title,
                status=event.status,
                actual_total_minor=sum(item.actual_cost_minor for item in items),
                payer_requested_total_minor=sum(item.payer_requested_minor for item in items),
                patient_responsibility_total_minor=sum(
                    item.patient_responsibility_minor for item in items
                ),
                currency="CNY",
                items=[_item_response(item) for item in items],
            )
        )
    return CareCostLedgerResponse(
        patient_id=patient.id,
        patient_display_name=patient.display_name,
        actual_total_minor=sum(event.actual_total_minor for event in event_rows),
        payer_requested_total_minor=sum(event.payer_requested_total_minor for event in event_rows),
        patient_responsibility_total_minor=sum(
            event.patient_responsibility_total_minor for event in event_rows
        ),
        currency="CNY",
        events=event_rows,
    )


def _organization_response(organization: PayerOrganization) -> PayerOrganizationResponse:
    return PayerOrganizationResponse(
        id=organization.id,
        name=organization.name,
        organization_type=organization.organization_type,
        jurisdiction_code=organization.jurisdiction_code,
        verification_status=organization.verification_status,
    )


def _profile_response(membership: PayerMembership) -> PayerProfileResponse:
    return PayerProfileResponse(
        membership_id=membership.id,
        display_name=membership.display_name,
        title=membership.title,
        status=membership.status,
        scope=membership.scope,
        organization=_organization_response(membership.organization),
    )


def _request_response(
    request: PayerRequest, *, include_reviewer_notes: bool
) -> PayerRequestResponse:
    return PayerRequestResponse(
        id=request.id,
        clinical_event_id=request.clinical_event_id,
        clinical_event_title=request.clinical_event.title,
        patient_id=request.patient_id,
        patient_display_name=request.patient.display_name,
        doctor_display_name=request.doctor.display_name,
        payer_organization=_organization_response(request.payer_organization),
        status=request.status,
        currency=request.currency,
        requested_total_minor=request.requested_total_minor,
        doctor_summary=request.doctor_summary,
        ai_review_status=request.ai_review_status,
        ai_review_score=request.ai_review_score,
        ai_review_summary=request.ai_review_summary,
        created_at=request.created_at,
        reviewed_at=request.reviewed_at,
        lines=[
            PayerRequestLineResponse(
                id=line.id,
                care_cost_item_id=line.care_cost_item_id,
                item_type=line.item_type,
                label=line.label,
                service_date=line.service_date,
                currency=line.currency,
                actual_cost_minor=line.actual_cost_minor,
                requested_minor=line.requested_minor,
                patient_responsibility_minor=line.patient_responsibility_minor,
            )
            for line in sorted(request.lines, key=lambda row: (row.service_date, row.id))
        ],
        reviews=[
            PayerReviewResponse(
                id=review.id,
                action=review.action,
                reason_code=review.reason_code,
                note=review.note if include_reviewer_notes else None,
                created_at=review.created_at,
            )
            for review in sorted(request.reviews, key=lambda row: (row.created_at, row.id))
        ],
    )


def _request_query():
    return select(PayerRequest).options(
        selectinload(PayerRequest.clinical_event),
        selectinload(PayerRequest.patient),
        selectinload(PayerRequest.doctor),
        selectinload(PayerRequest.payer_organization),
        selectinload(PayerRequest.lines),
        selectinload(PayerRequest.reviews),
    )


def _audit(db: DbSession, user: CurrentUser, event_type: str, **metadata: object) -> None:
    target_id = uuid.UUID(str(metadata.pop("target_id")))
    patient_id_value = metadata.pop("patient_id", None)
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            patient_id=(uuid.UUID(str(patient_id_value)) if patient_id_value is not None else None),
            event_type=event_type,
            resource_type="care_cost_workflow",
            resource_id=target_id,
            metadata_json=metadata,
        )
    )


@router.get("/patient/me/care-costs", response_model=CareCostLedgerResponse)
def own_care_costs(user: CurrentUser, db: DbSession) -> CareCostLedgerResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _not_found()
    return _ledger(db, user.patient_profile)


@router.get("/patients/{patient_id}/care-costs", response_model=CareCostLedgerResponse)
def patient_care_costs(
    patient_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> CareCostLedgerResponse:
    return _ledger(db, _require_doctor_patient(db, user, patient_id))


@router.post(
    "/patients/{patient_id}/clinical-events/{event_id}/care-items",
    response_model=CareCostItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_care_cost_item(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    body: CareCostItemRequest,
    user: CurrentUser,
    db: DbSession,
) -> CareCostItemResponse:
    _require_doctor_patient(db, user, patient_id)
    _require_event(db, patient_id, event_id)
    item = CareCostItem(
        patient_id=patient_id,
        clinical_event_id=event_id,
        created_by_user_id=user.id,
        **body.model_dump(),
        ai_review_status="not_evaluated",
    )
    db.add(item)
    db.flush()
    _audit(
        db,
        user,
        "care_cost_item_created",
        target_id=item.id,
        patient_id=str(patient_id),
        clinical_event_id=str(event_id),
        item_type=item.item_type,
    )
    db.commit()
    db.refresh(item)
    return _item_response(item)


@router.put(
    "/patients/{patient_id}/clinical-events/{event_id}/care-items/{item_id}",
    response_model=CareCostItemResponse,
)
def update_care_cost_item(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    item_id: uuid.UUID,
    body: CareCostItemRequest,
    user: CurrentUser,
    db: DbSession,
) -> CareCostItemResponse:
    _require_doctor_patient(db, user, patient_id)
    item = db.scalar(
        select(CareCostItem).where(
            CareCostItem.id == item_id,
            CareCostItem.patient_id == patient_id,
            CareCostItem.clinical_event_id == event_id,
        )
    )
    if item is None:
        raise _not_found()
    for field, value in body.model_dump().items():
        setattr(item, field, value)
    _audit(
        db,
        user,
        "care_cost_item_updated",
        target_id=item.id,
        patient_id=str(patient_id),
        clinical_event_id=str(event_id),
        item_type=item.item_type,
    )
    db.commit()
    db.refresh(item)
    return _item_response(item)


@router.delete(
    "/patients/{patient_id}/clinical-events/{event_id}/care-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_care_cost_item(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    item_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> None:
    _require_doctor_patient(db, user, patient_id)
    item = db.scalar(
        select(CareCostItem).where(
            CareCostItem.id == item_id,
            CareCostItem.patient_id == patient_id,
            CareCostItem.clinical_event_id == event_id,
        )
    )
    if item is None:
        raise _not_found()
    _audit(
        db,
        user,
        "care_cost_item_deleted",
        target_id=item.id,
        patient_id=str(patient_id),
        clinical_event_id=str(event_id),
        item_type=item.item_type,
    )
    db.delete(item)
    db.commit()


@router.get("/payer-organizations", response_model=list[PayerOrganizationResponse])
def payer_organizations(user: CurrentUser, db: DbSession) -> list[PayerOrganizationResponse]:
    if user.role != UserRole.doctor:
        raise _not_found()
    organizations = db.scalars(
        select(PayerOrganization).order_by(PayerOrganization.name, PayerOrganization.id)
    ).all()
    return [_organization_response(organization) for organization in organizations]


@router.post(
    "/patients/{patient_id}/clinical-events/{event_id}/payer-requests",
    response_model=PayerRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payer_request(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    body: PayerRequestCreate,
    user: CurrentUser,
    db: DbSession,
) -> PayerRequestResponse:
    _require_doctor_patient(db, user, patient_id)
    event = _require_event(db, patient_id, event_id)
    organization = db.get(PayerOrganization, body.payer_organization_id)
    if organization is None:
        raise _not_found()
    item_query = select(CareCostItem).where(
        CareCostItem.patient_id == patient_id,
        CareCostItem.clinical_event_id == event_id,
        CareCostItem.status != "cancelled",
    )
    if body.care_cost_item_ids:
        if len(set(body.care_cost_item_ids)) != len(body.care_cost_item_ids):
            raise ApiError(422, "validation_failed", "Each care item may be selected once.")
        item_query = item_query.where(CareCostItem.id.in_(body.care_cost_item_ids))
    items = db.scalars(item_query.order_by(CareCostItem.service_date, CareCostItem.id)).all()
    if not items or (body.care_cost_item_ids and len(items) != len(body.care_cost_item_ids)):
        raise ApiError(422, "validation_failed", "Select valid care items for this event.")
    currencies = {item.currency for item in items}
    if currencies != {"CNY"}:
        raise ApiError(422, "validation_failed", "All selected items must use CNY.")
    payer_request = PayerRequest(
        clinical_event_id=event.id,
        patient_id=patient_id,
        doctor_id=user.doctor_profile.id,
        payer_organization_id=organization.id,
        status="submitted",
        currency="CNY",
        requested_total_minor=sum(item.payer_requested_minor for item in items),
        doctor_summary=body.doctor_summary,
        ai_review_status="not_evaluated",
    )
    db.add(payer_request)
    db.flush()
    for item in items:
        db.add(
            PayerRequestLine(
                payer_request_id=payer_request.id,
                care_cost_item_id=item.id,
                item_type=item.item_type,
                label=item.label,
                service_date=item.service_date,
                currency=item.currency,
                actual_cost_minor=item.actual_cost_minor,
                requested_minor=item.payer_requested_minor,
                patient_responsibility_minor=item.patient_responsibility_minor,
            )
        )
    _audit(
        db,
        user,
        "payer_request_submitted",
        target_id=payer_request.id,
        patient_id=str(patient_id),
        clinical_event_id=str(event_id),
        payer_organization_id=str(organization.id),
        line_count=len(items),
    )
    db.commit()
    saved = db.scalar(_request_query().where(PayerRequest.id == payer_request.id))
    assert saved is not None
    return _request_response(saved, include_reviewer_notes=False)


@router.get("/doctor/me/payer-requests", response_model=PayerRequestListResponse)
def doctor_payer_requests(user: CurrentUser, db: DbSession) -> PayerRequestListResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _not_found()
    requests = db.scalars(
        _request_query()
        .where(PayerRequest.doctor_id == user.doctor_profile.id)
        .order_by(PayerRequest.created_at.desc(), PayerRequest.id)
    ).all()
    return PayerRequestListResponse(
        items=[_request_response(item, include_reviewer_notes=False) for item in requests]
    )


@router.get("/patient/me/payer-requests", response_model=PayerRequestListResponse)
def own_payer_requests(user: CurrentUser, db: DbSession) -> PayerRequestListResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _not_found()
    requests = db.scalars(
        _request_query()
        .where(PayerRequest.patient_id == user.patient_profile.id)
        .order_by(PayerRequest.created_at.desc(), PayerRequest.id)
    ).all()
    return PayerRequestListResponse(
        items=[_request_response(item, include_reviewer_notes=False) for item in requests]
    )


@router.get("/payer/me/profile", response_model=PayerProfileResponse)
def own_payer_profile(user: CurrentUser, db: DbSession) -> PayerProfileResponse:
    return _profile_response(_require_membership(db, user))


@router.get("/payer/me/dashboard", response_model=PayerDashboardResponse)
def own_payer_dashboard(user: CurrentUser, db: DbSession) -> PayerDashboardResponse:
    membership = _require_membership(db, user)
    requests = db.scalars(
        select(PayerRequest).where(
            PayerRequest.payer_organization_id == membership.payer_organization_id
        )
    ).all()
    open_statuses = {"submitted", "clarification_requested", "under_review"}
    return PayerDashboardResponse(
        profile=_profile_response(membership),
        open_requests=sum(item.status in open_statuses for item in requests),
        clarification_requests=sum(item.status == "clarification_requested" for item in requests),
        completed_reviews=sum(item.status in {"accepted", "closed"} for item in requests),
        pending_requested_total_minor=sum(
            item.requested_total_minor for item in requests if item.status in open_statuses
        ),
    )


@router.get("/payer/me/requests", response_model=PayerRequestListResponse)
def payer_requests(user: CurrentUser, db: DbSession) -> PayerRequestListResponse:
    membership = _require_membership(db, user)
    requests = db.scalars(
        _request_query()
        .where(PayerRequest.payer_organization_id == membership.payer_organization_id)
        .order_by(PayerRequest.created_at.desc(), PayerRequest.id)
    ).all()
    return PayerRequestListResponse(
        items=[_request_response(item, include_reviewer_notes=True) for item in requests]
    )


@router.get("/payer/me/requests/{request_id}", response_model=PayerRequestResponse)
def payer_request_detail(
    request_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> PayerRequestResponse:
    membership = _require_membership(db, user)
    payer_request = db.scalar(
        _request_query().where(
            PayerRequest.id == request_id,
            PayerRequest.payer_organization_id == membership.payer_organization_id,
        )
    )
    if payer_request is None:
        raise _not_found()
    return _request_response(payer_request, include_reviewer_notes=True)


@router.post(
    "/payer/me/requests/{request_id}/reviews",
    response_model=PayerRequestResponse,
)
def review_payer_request(
    request_id: uuid.UUID,
    body: PayerReviewRequest,
    user: CurrentUser,
    db: DbSession,
) -> PayerRequestResponse:
    membership = _require_membership(db, user)
    payer_request = db.scalar(
        _request_query().where(
            PayerRequest.id == request_id,
            PayerRequest.payer_organization_id == membership.payer_organization_id,
        )
    )
    if payer_request is None:
        raise _not_found()
    next_status = {
        "request_clarification": "clarification_requested",
        "accept": "accepted",
        "escalate": "escalated",
        "close": "closed",
    }[body.action]
    payer_request.reviews.append(
        PayerReview(
            payer_membership_id=membership.id,
            action=body.action,
            reason_code=body.reason_code,
            note=body.note,
        )
    )
    payer_request.status = next_status
    payer_request.reviewed_at = datetime.now(UTC)
    _audit(
        db,
        user,
        "payer_request_reviewed",
        target_id=payer_request.id,
        payer_organization_id=str(membership.payer_organization_id),
        action=body.action,
        reason_code=body.reason_code,
    )
    db.commit()
    saved = db.scalar(_request_query().where(PayerRequest.id == payer_request.id))
    assert saved is not None
    return _request_response(saved, include_reviewer_notes=True)
