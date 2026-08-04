import hashlib
import json
import uuid
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Header, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.clinical_event_intelligence_models import (
    ClinicalEventIntelligenceArtifact,
    ClinicalEventIntelligenceLineageEvent,
)
from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    AuditEvent,
    CareCostItem,
    CareRelationship,
    ClinicalEvent,
    ClinicalService,
    ConsultationRequest,
    ExpectedCareComparison,
    ExpectedCarePublishedBaseline,
    PatientProfile,
    PayerDoctorResponse,
    PayerMembership,
    PayerOrganization,
    PayerRequest,
    PayerRequestLine,
    PayerReview,
    User,
    UserRole,
)
from app.notification_service import create_notification
from app.payer_scope import require_active_payer_membership
from app.schemas import ClinicalFinancialInput

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
ReviewAction = Literal[
    "request_clarification",
    "accept",
    "reject",
    "escalate",
    "close",
]


class CareCostItemRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    item_type: ItemType
    label: str = Field(min_length=2, max_length=200)
    service_date: date
    status: ItemStatus = "planned"
    quantity: int = Field(default=1, ge=1, le=999)
    currency: Literal["CNY"] = "CNY"
    pricing_state: Literal["pending_cost", "estimated", "final"] = "final"
    actual_cost_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    payer_requested_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    patient_responsibility_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_amounts(self) -> "CareCostItemRequest":
        allocated = self.payer_requested_minor + self.patient_responsibility_minor
        if self.pricing_state == "pending_cost":
            if any(
                (
                    self.actual_cost_minor,
                    self.payer_requested_minor,
                    self.patient_responsibility_minor,
                )
            ):
                raise ValueError("Pending-cost records cannot contain partial amounts.")
        elif self.actual_cost_minor <= 0 or allocated != self.actual_cost_minor:
            raise ValueError(
                "Requested payer and expected patient amounts must equal the total cost."
            )
        return self


class CareCostItemResponse(BaseModel):
    id: uuid.UUID
    clinical_event_id: uuid.UUID
    item_type: str
    label: str
    service_date: date
    status: str
    pricing_state: str
    source_type: str
    source_record_id: uuid.UUID | None
    source_category: str
    source_status: str
    ordered_at: datetime | None
    scheduled_at: datetime | None
    performed_at: datetime | None
    already_submitted: bool
    submission_eligible: bool
    ineligibility_reason: str | None
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
    care_cost_item_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)
    doctor_summary: str = Field(min_length=10, max_length=4000)


class PayerRequestLineResponse(BaseModel):
    id: uuid.UUID
    care_cost_item_id: uuid.UUID | None
    item_type: str
    label: str
    code_system: str | None
    service_code: str | None
    quantity: int
    unit: str
    service_date: date
    currency: str
    actual_cost_minor: int
    requested_minor: int
    patient_responsibility_minor: int


class PayerReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    action: ReviewAction
    expected_version: int = Field(ge=1)
    reason_code: str = Field(min_length=2, max_length=80)
    note: str | None = Field(default=None, max_length=4000)


class PayerReviewResponse(BaseModel):
    id: uuid.UUID
    action: str
    reason_code: str
    note: str | None
    reviewer_membership_id: uuid.UUID
    reviewer_display_name: str
    reviewer_title: str
    from_status: str
    to_status: str
    version: int
    created_at: datetime


class PayerDoctorResponseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    expected_version: int = Field(ge=1)
    response_type: Literal["justification", "clarification_response", "additional_information"]
    summary: str = Field(min_length=10, max_length=4000)
    baseline_id: uuid.UUID | None = None
    comparison_id: uuid.UUID | None = None


class PayerDoctorResponseResponse(BaseModel):
    id: uuid.UUID
    response_type: str
    summary: str
    doctor_id: uuid.UUID
    doctor_display_name: str
    baseline_id: uuid.UUID | None
    comparison_id: uuid.UUID | None
    version: int
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
    version: int
    currency: str
    requested_total_minor: int
    doctor_summary: str
    ai_review_status: str
    ai_review_score: int | None
    ai_review_summary: str | None
    created_at: datetime
    reviewed_at: datetime | None
    lines: list[PayerRequestLineResponse]
    doctor_responses: list[PayerDoctorResponseResponse]
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


class PayerProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    title: str | None = Field(default=None, min_length=2, max_length=120)


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
    return require_active_payer_membership(db, user)


def _item_response(item: CareCostItem, *, already_submitted: bool = False) -> CareCostItemResponse:
    ineligibility_reason = _submission_ineligibility(item, already_submitted=already_submitted)
    source_type = "legacy"
    source_record_id = None
    source_category = item.item_type
    source_status = item.status
    ordered_at = None
    scheduled_at = None
    performed_at = None
    if item.medication_id is not None:
        source_type = "medication"
        source_record_id = item.medication_id
        source_category = "medication"
        if item.medication is not None:
            source_status = item.medication.status
    elif item.clinical_service_id is not None:
        source_type = "clinical_service"
        source_record_id = item.clinical_service_id
        if item.clinical_service is not None:
            source_type = item.clinical_service.category
            source_category = item.clinical_service.category
            source_status = item.clinical_service.status
            ordered_at = item.clinical_service.ordered_at
            scheduled_at = item.clinical_service.scheduled_at
            performed_at = item.clinical_service.performed_at
    return CareCostItemResponse(
        id=item.id,
        clinical_event_id=item.clinical_event_id,
        item_type=item.item_type,
        label=item.label,
        service_date=item.service_date,
        status=item.status,
        pricing_state=item.pricing_state,
        source_type=source_type,
        source_record_id=source_record_id,
        source_category=source_category,
        source_status=source_status,
        ordered_at=ordered_at,
        scheduled_at=scheduled_at,
        performed_at=performed_at,
        already_submitted=already_submitted,
        submission_eligible=ineligibility_reason is None,
        ineligibility_reason=ineligibility_reason,
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


def _submission_ineligibility(item: CareCostItem, *, already_submitted: bool = False) -> str | None:
    if already_submitted:
        return "already_submitted"
    if item.status == "cancelled":
        return "cancelled"
    if item.pricing_state == "pending_cost":
        return "cost_pending"
    if item.currency != "CNY":
        return "unsupported_currency"
    if item.actual_cost_minor <= 0:
        return "total_required"
    if item.payer_requested_minor + item.patient_responsibility_minor != item.actual_cost_minor:
        return "allocation_incomplete"
    if item.medication_id is None and item.clinical_service_id is None:
        return "unlinked_legacy_item"
    if item.medication_id is not None:
        medication = item.medication
        if (
            medication is None
            or medication.patient_id != item.patient_id
            or medication.clinical_event_id != item.clinical_event_id
        ):
            return "source_mismatch"
        if medication.status == "entered_in_error":
            return "source_ineligible"
    if item.clinical_service_id is not None:
        service = item.clinical_service
        if (
            service is None
            or service.patient_id != item.patient_id
            or service.clinical_event_id != item.clinical_event_id
        ):
            return "source_mismatch"
        if service.status in {"cancelled", "not_completed"}:
            return "source_ineligible"
    return None


def sync_clinical_financial(
    db: DbSession,
    user: CurrentUser,
    *,
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID | None,
    source_type: Literal["medication", "service"],
    source_record_id: uuid.UUID,
    label: str,
    source_status: str,
    financial: ClinicalFinancialInput | None,
) -> CareCostItem | None:
    """Create or synchronize one active financial companion without committing."""

    source_column = (
        CareCostItem.medication_id
        if source_type == "medication"
        else CareCostItem.clinical_service_id
    )
    item = db.scalar(select(CareCostItem).where(source_column == source_record_id))
    if item is None and financial is None:
        return None
    if clinical_event_id is None:
        raise ApiError(
            422,
            "validation_failed",
            "A billable clinical record must belong to a Clinical Event.",
        )
    event = db.scalar(
        select(ClinicalEvent).where(
            ClinicalEvent.id == clinical_event_id,
            ClinicalEvent.patient_id == patient_id,
        )
    )
    if event is None:
        raise _not_found()
    source_item_type = "medication"
    if source_type == "service":
        service = db.scalar(
            select(ClinicalService).where(
                ClinicalService.id == source_record_id,
                ClinicalService.patient_id == patient_id,
                ClinicalService.clinical_event_id == clinical_event_id,
            )
        )
        if service is None:
            raise _not_found()
        source_item_type = service.category
    mapped_status = (
        "cancelled"
        if source_status in {"cancelled", "entered_in_error"}
        else "scheduled"
        if source_type == "service" and source_status in {"ordered", "requested", "scheduled"}
        else "planned"
        if source_type == "service" and source_status == "in_progress"
        else "completed"
    )
    if item is None:
        assert financial is not None
        item = CareCostItem(
            patient_id=patient_id,
            clinical_event_id=clinical_event_id,
            created_by_user_id=user.id,
            medication_id=source_record_id if source_type == "medication" else None,
            clinical_service_id=source_record_id if source_type == "service" else None,
            item_type=source_item_type,
            label=label,
            service_date=financial.service_date or date.today(),
            status=mapped_status,
            pricing_state=financial.pricing_state,
            quantity=1,
            currency=financial.currency,
            actual_cost_minor=financial.total_cost_minor,
            payer_requested_minor=financial.payer_requested_minor,
            patient_responsibility_minor=financial.patient_responsibility_minor,
            ai_review_status="not_evaluated",
        )
        db.add(item)
    else:
        item.patient_id = patient_id
        item.clinical_event_id = clinical_event_id
        item.item_type = source_item_type
        item.label = label
        item.status = mapped_status
        if financial is not None:
            item.service_date = financial.service_date or item.service_date
            item.pricing_state = financial.pricing_state
            item.currency = financial.currency
            item.actual_cost_minor = financial.total_cost_minor
            item.payer_requested_minor = financial.payer_requested_minor
            item.patient_responsibility_minor = financial.patient_responsibility_minor
    db.flush()
    return item


def _ledger(db: DbSession, patient: PatientProfile) -> CareCostLedgerResponse:
    submitted_item_ids = set(
        db.scalars(
            select(PayerRequestLine.care_cost_item_id)
            .join(PayerRequest)
            .where(
                PayerRequest.patient_id == patient.id,
                PayerRequestLine.care_cost_item_id.is_not(None),
            )
        ).all()
    )
    events = db.scalars(
        select(ClinicalEvent)
        .options(
            selectinload(ClinicalEvent.care_cost_items).selectinload(CareCostItem.clinical_service),
            selectinload(ClinicalEvent.care_cost_items).selectinload(CareCostItem.medication),
        )
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
                items=[
                    _item_response(item, already_submitted=item.id in submitted_item_ids)
                    for item in items
                ],
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
        version=request.version,
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
                code_system=line.code_system,
                service_code=line.service_code,
                quantity=line.quantity,
                unit=line.unit,
                service_date=line.service_date,
                currency=line.currency,
                actual_cost_minor=line.actual_cost_minor,
                requested_minor=line.requested_minor,
                patient_responsibility_minor=line.patient_responsibility_minor,
            )
            for line in sorted(request.lines, key=lambda row: (row.service_date, row.id))
        ],
        doctor_responses=[
            PayerDoctorResponseResponse(
                id=response.id,
                response_type=response.response_type,
                summary=response.summary,
                doctor_id=response.doctor_id,
                doctor_display_name=response.doctor.display_name,
                baseline_id=response.baseline_id,
                comparison_id=response.comparison_id,
                version=response.version,
                created_at=response.created_at,
            )
            for response in sorted(
                request.doctor_responses, key=lambda row: (row.created_at, row.id)
            )
        ],
        reviews=[
            PayerReviewResponse(
                id=review.id,
                action=review.action,
                reason_code=review.reason_code,
                note=review.note if include_reviewer_notes else None,
                reviewer_membership_id=review.payer_membership_id,
                reviewer_display_name=review.payer_membership.display_name,
                reviewer_title=review.payer_membership.title,
                from_status=review.from_status,
                to_status=review.to_status,
                version=review.version,
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
        selectinload(PayerRequest.reviews).selectinload(PayerReview.payer_membership),
        selectinload(PayerRequest.doctor_responses).selectinload(PayerDoctorResponse.doctor),
    )


def _content_checksum(payload: BaseModel) -> str:
    canonical = json.dumps(
        payload.model_dump(mode="json", exclude_none=True),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _version_conflict(current_version: int) -> ApiError:
    return ApiError(
        409,
        "conflict",
        "The payer request changed. Reload it before recording another action.",
        [
            {
                "field": "expected_version",
                "code": "stale_version",
                "message": f"The current request version is {current_version}.",
            }
        ],
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
    raise ApiError(
        409,
        "integrated_financial_required",
        "Create cost information from the billable clinical record.",
    )


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
    if item.medication_id is not None or item.clinical_service_id is not None:
        raise ApiError(
            409,
            "integrated_financial_required",
            "Update cost information from the linked clinical record.",
        )
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
    if item.medication_id is not None or item.clinical_service_id is not None:
        raise ApiError(
            409,
            "integrated_financial_required",
            "Delete or archive the linked clinical record instead.",
        )
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


@router.put(
    "/patients/{patient_id}/consultations/{consultation_id}/financial",
    response_model=CareCostItemResponse,
)
def update_consultation_financial(
    patient_id: uuid.UUID,
    consultation_id: uuid.UUID,
    body: ClinicalFinancialInput,
    user: CurrentUser,
    db: DbSession,
) -> CareCostItemResponse:
    _require_doctor_patient(db, user, patient_id)
    consultation = db.scalar(
        select(ConsultationRequest).where(
            ConsultationRequest.id == consultation_id,
            ConsultationRequest.patient_id == patient_id,
        )
    )
    if consultation is None:
        raise _not_found()
    if consultation.clinical_service_id is None:
        raise ApiError(
            409,
            "clinical_service_required",
            "This consultation has no linked clinical service.",
        )
    service = db.scalar(
        select(ClinicalService).where(
            ClinicalService.id == consultation.clinical_service_id,
            ClinicalService.patient_id == patient_id,
        )
    )
    if service is None:
        raise _not_found()
    item = sync_clinical_financial(
        db,
        user,
        patient_id=patient_id,
        clinical_event_id=service.clinical_event_id,
        source_type="service",
        source_record_id=service.id,
        label=service.name,
        source_status=service.status,
        financial=body,
    )
    assert item is not None
    _audit(
        db,
        user,
        "clinical_financial_updated",
        target_id=item.id,
        patient_id=str(patient_id),
        clinical_event_id=str(consultation.clinical_event_id),
        source_type="clinical_service",
        source_record_id=str(service.id),
        pricing_state=item.pricing_state,
    )
    db.commit()
    db.refresh(item)
    return _item_response(item)


@router.put(
    "/patients/{patient_id}/clinical-services/{service_id}/financial",
    response_model=CareCostItemResponse,
)
def update_clinical_service_financial(
    patient_id: uuid.UUID,
    service_id: uuid.UUID,
    body: ClinicalFinancialInput,
    user: CurrentUser,
    db: DbSession,
) -> CareCostItemResponse:
    _require_doctor_patient(db, user, patient_id)
    service = db.scalar(
        select(ClinicalService).where(
            ClinicalService.id == service_id,
            ClinicalService.patient_id == patient_id,
        )
    )
    if service is None:
        raise _not_found()
    item = sync_clinical_financial(
        db,
        user,
        patient_id=patient_id,
        clinical_event_id=service.clinical_event_id,
        source_type="service",
        source_record_id=service.id,
        label=service.name,
        source_status=service.status,
        financial=body,
    )
    assert item is not None
    _audit(
        db,
        user,
        "clinical_financial_updated",
        target_id=item.id,
        patient_id=str(patient_id),
        clinical_event_id=str(service.clinical_event_id),
        source_type="clinical_service",
        source_record_id=str(service.id),
        source_category=service.category,
        pricing_state=item.pricing_state,
    )
    db.commit()
    db.refresh(item)
    return _item_response(item)


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
    if len(set(body.care_cost_item_ids)) != len(body.care_cost_item_ids):
        raise ApiError(422, "validation_failed", "Each care item may be selected once.")
    item_query = item_query.where(CareCostItem.id.in_(body.care_cost_item_ids))
    items = db.scalars(item_query.order_by(CareCostItem.service_date, CareCostItem.id)).all()
    if len(items) != len(body.care_cost_item_ids):
        raise ApiError(422, "validation_failed", "Select valid care items for this event.")
    submitted_item_ids = set(
        db.scalars(
            select(PayerRequestLine.care_cost_item_id).where(
                PayerRequestLine.care_cost_item_id.in_(body.care_cost_item_ids)
            )
        ).all()
    )
    if submitted_item_ids:
        raise ApiError(
            409,
            "conflict",
            "One or more selected care items were already submitted in an earlier request.",
        )
    currencies = {item.currency for item in items}
    if currencies != {"CNY"}:
        raise ApiError(422, "validation_failed", "All selected items must use CNY.")
    blocked = {
        str(item.id): reason
        for item in items
        if (reason := _submission_ineligibility(item)) is not None
    }
    if blocked:
        raise ApiError(
            422,
            "validation_failed",
            "Complete valid cost allocation for every selected clinical item.",
            [
                {
                    "field": "care_cost_item_ids",
                    "code": reason,
                    "message": f"Care item {item_id} is not eligible for submission.",
                }
                for item_id, reason in blocked.items()
            ],
        )
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
                code_system=(
                    "DR_AI_INTERNAL"
                    if item.clinical_service is not None and item.clinical_service.service_code
                    else None
                ),
                service_code=(
                    item.clinical_service.service_code
                    if item.clinical_service is not None and item.clinical_service.service_code
                    else None
                ),
                quantity=item.quantity,
                unit="item",
                service_date=item.service_date,
                currency=item.currency,
                actual_cost_minor=item.actual_cost_minor,
                requested_minor=item.payer_requested_minor,
                patient_responsibility_minor=item.patient_responsibility_minor,
            )
        )
    payer_memberships = db.scalars(
        select(PayerMembership).where(
            PayerMembership.payer_organization_id == organization.id,
            PayerMembership.status == "active",
        )
    ).all()
    for membership in payer_memberships:
        payer_user = db.get(User, membership.user_id)
        if payer_user is None:
            continue
        create_notification(
            db,
            recipient=payer_user,
            event_type="payer_request_submitted",
            source_resource_id=payer_request.id,
            scheduled_for=datetime.now(UTC),
            patient_id=patient_id,
            clinical_event_id=event_id,
            payer_organization_id=organization.id,
            payer_request_id=payer_request.id,
            occurrence_key=f"submitted:v{payer_request.version}",
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


@router.post(
    "/doctor/me/payer-requests/{request_id}/responses",
    response_model=PayerRequestResponse,
)
def append_doctor_payer_response(
    request_id: uuid.UUID,
    body: PayerDoctorResponseCreate,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=12, max_length=120),
) -> PayerRequestResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _not_found()
    payer_request = db.scalar(
        _request_query()
        .where(
            PayerRequest.id == request_id,
            PayerRequest.doctor_id == user.doctor_profile.id,
        )
        .with_for_update()
    )
    if payer_request is None:
        raise _not_found()
    checksum = _content_checksum(body)
    replay = db.scalar(
        select(PayerDoctorResponse).where(
            PayerDoctorResponse.payer_request_id == payer_request.id,
            PayerDoctorResponse.doctor_id == user.doctor_profile.id,
            PayerDoctorResponse.idempotency_key == idempotency_key,
        )
    )
    if replay is not None:
        if replay.request_checksum != checksum:
            raise ApiError(
                409,
                "conflict",
                "The idempotency key was already used for different response content.",
            )
        return _request_response(payer_request, include_reviewer_notes=False)
    if body.expected_version != payer_request.version:
        raise _version_conflict(payer_request.version)
    if payer_request.status in {"accepted", "rejected", "closed"}:
        raise ApiError(409, "conflict", "This payer request is already in a terminal state.")
    baseline = None
    if body.baseline_id is not None:
        baseline = db.scalar(
            select(ExpectedCarePublishedBaseline).where(
                ExpectedCarePublishedBaseline.id == body.baseline_id,
                ExpectedCarePublishedBaseline.patient_id == payer_request.patient_id,
                ExpectedCarePublishedBaseline.clinical_event_id == payer_request.clinical_event_id,
            )
        )
        if baseline is None:
            raise _not_found()
    comparison = None
    if body.comparison_id is not None:
        comparison = db.scalar(
            select(ExpectedCareComparison).where(
                ExpectedCareComparison.id == body.comparison_id,
                ExpectedCareComparison.patient_id == payer_request.patient_id,
                ExpectedCareComparison.clinical_event_id == payer_request.clinical_event_id,
            )
        )
        if comparison is None or (baseline is not None and comparison.baseline_id != baseline.id):
            raise _not_found()
    payer_request.version += 1
    if payer_request.status == "clarification_requested":
        payer_request.status = "under_review"
    response = PayerDoctorResponse(
        payer_request_id=payer_request.id,
        doctor_id=user.doctor_profile.id,
        baseline_id=baseline.id if baseline else None,
        comparison_id=comparison.id if comparison else None,
        response_type=body.response_type,
        summary=body.summary,
        request_checksum=checksum,
        idempotency_key=idempotency_key,
        version=payer_request.version,
        doctor=user.doctor_profile,
    )
    payer_request.doctor_responses.append(response)
    payer_memberships = db.scalars(
        select(PayerMembership).where(
            PayerMembership.payer_organization_id == payer_request.payer_organization_id,
            PayerMembership.status == "active",
        )
    ).all()
    for membership in payer_memberships:
        payer_user = db.get(User, membership.user_id)
        if payer_user is None:
            continue
        create_notification(
            db,
            recipient=payer_user,
            event_type="payer_doctor_response_added",
            source_resource_id=payer_request.id,
            scheduled_for=datetime.now(UTC),
            patient_id=payer_request.patient_id,
            clinical_event_id=payer_request.clinical_event_id,
            payer_organization_id=payer_request.payer_organization_id,
            payer_request_id=payer_request.id,
            occurrence_key=f"doctor-response:v{payer_request.version}",
        )
    _audit(
        db,
        user,
        "payer_doctor_response_appended",
        target_id=payer_request.id,
        patient_id=str(payer_request.patient_id),
        clinical_event_id=str(payer_request.clinical_event_id),
        response_type=body.response_type,
        baseline_linked=baseline is not None,
        comparison_linked=comparison is not None,
        version=payer_request.version,
    )
    db.commit()
    saved = db.scalar(_request_query().where(PayerRequest.id == payer_request.id))
    assert saved is not None
    return _request_response(saved, include_reviewer_notes=False)


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


@router.patch("/payer/me/profile", response_model=PayerProfileResponse)
def update_own_payer_profile(
    body: PayerProfileUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> PayerProfileResponse:
    membership = _require_membership(db, user)
    updated_fields: list[str] = []
    for field in ("display_name", "title"):
        value = getattr(body, field)
        if value is not None and getattr(membership, field) != value:
            setattr(membership, field, value)
            updated_fields.append(field)
    if not updated_fields:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "profile",
                    "code": "no_fields_updated",
                    "message": "Provide at least one changed reviewer profile field.",
                }
            ],
        )
    _audit(
        db,
        user,
        "payer_profile_updated",
        target_id=membership.id,
        payer_organization_id=str(membership.payer_organization_id),
        fields=updated_fields,
        actor_role=user.role.value,
    )
    db.commit()
    db.refresh(membership)
    return _profile_response(membership)


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
        completed_reviews=sum(
            item.status in {"accepted", "rejected", "closed"} for item in requests
        ),
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
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=12, max_length=120),
) -> PayerRequestResponse:
    membership = _require_membership(db, user)
    payer_request = db.scalar(
        _request_query()
        .where(
            PayerRequest.id == request_id,
            PayerRequest.payer_organization_id == membership.payer_organization_id,
        )
        .with_for_update()
    )
    if payer_request is None:
        raise _not_found()
    checksum = _content_checksum(body)
    replay = db.scalar(
        select(PayerReview).where(
            PayerReview.payer_request_id == payer_request.id,
            PayerReview.payer_membership_id == membership.id,
            PayerReview.idempotency_key == idempotency_key,
        )
    )
    if replay is not None:
        if replay.request_checksum != checksum:
            raise ApiError(
                409,
                "conflict",
                "The idempotency key was already used for different review content.",
            )
        return _request_response(payer_request, include_reviewer_notes=True)
    if body.expected_version != payer_request.version:
        raise _version_conflict(payer_request.version)
    next_status = {
        "request_clarification": "clarification_requested",
        "accept": "accepted",
        "reject": "rejected",
        "escalate": "escalated",
        "close": "closed",
    }[body.action]
    allowed_actions = {
        "submitted": {"request_clarification", "accept", "reject", "escalate", "close"},
        "clarification_requested": {"request_clarification", "escalate", "close"},
        "under_review": {"request_clarification", "accept", "reject", "escalate", "close"},
        "escalated": {"request_clarification", "accept", "reject", "close"},
    }
    if body.action not in allowed_actions.get(payer_request.status, set()):
        raise ApiError(
            409,
            "conflict",
            "This review action is not valid from the request's current state.",
        )
    from_status = payer_request.status
    payer_request.version += 1
    review = PayerReview(
            payer_membership_id=membership.id,
            action=body.action,
            reason_code=body.reason_code,
            note=body.note,
            request_checksum=checksum,
            idempotency_key=idempotency_key,
            from_status=from_status,
            to_status=next_status,
            version=payer_request.version,
        )
    payer_request.reviews.append(review)
    payer_request.status = next_status
    payer_request.reviewed_at = datetime.now(UTC)
    db.flush()
    intelligence_artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact)
        .where(ClinicalEventIntelligenceArtifact.payer_request_id == payer_request.id)
        .order_by(ClinicalEventIntelligenceArtifact.artifact_version.desc())
    )
    if intelligence_artifact is not None:
        db.add(
            ClinicalEventIntelligenceLineageEvent(
                artifact_id=intelligence_artifact.id,
                actor_user_id=user.id,
                doctor_response_id=None,
                payer_review_id=review.id,
                event_type="payer_human_resolution",
                source_event_key=f"payer-review:{review.id}",
                source_checksum_sha256=checksum,
                occurred_at=payer_request.reviewed_at,
                metadata_json={
                    "action": body.action,
                    "from_status": from_status,
                    "to_status": next_status,
                    "human_owned": True,
                },
            )
        )
    doctor_user = db.get(User, payer_request.doctor.user_id)
    patient_user = db.get(User, payer_request.patient.user_id)
    for recipient in (doctor_user, patient_user):
        if recipient is None:
            continue
        create_notification(
            db,
            recipient=recipient,
            event_type=(
                "payer_request_closed"
                if next_status == "closed"
                else "payer_final_outcome"
                if next_status in {"accepted", "rejected"}
                else "payer_clarification_requested"
                if next_status == "clarification_requested" and recipient.role.value == "doctor"
                else "payer_manual_review_transition"
            ),
            source_resource_id=payer_request.id,
            scheduled_for=payer_request.reviewed_at,
            patient_id=payer_request.patient_id,
            clinical_event_id=payer_request.clinical_event_id,
            payer_organization_id=payer_request.payer_organization_id,
            payer_request_id=payer_request.id,
            occurrence_key=f"{next_status}:v{payer_request.version}",
        )
    _audit(
        db,
        user,
        "payer_request_reviewed",
        target_id=payer_request.id,
        payer_organization_id=str(membership.payer_organization_id),
        action=body.action,
        reason_code=body.reason_code,
        from_status=from_status,
        to_status=next_status,
        version=payer_request.version,
    )
    db.commit()
    saved = db.scalar(_request_query().where(PayerRequest.id == payer_request.id))
    assert saved is not None
    return _request_response(saved, include_reviewer_notes=True)
