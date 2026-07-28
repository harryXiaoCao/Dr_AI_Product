"""Idempotent, wholly synthetic Slice E demonstration workflow.

This module is restricted to local/test environments. It uses an in-process,
deterministic provider fixture and never performs a network or model call.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.care_cost import (
    PayerDoctorResponseCreate,
    PayerReviewRequest,
    append_doctor_payer_response,
    review_payer_request,
)
from app.care_reference_engine import EvaluationContext, EvaluationRequest
from app.config import Settings
from app.expected_care_candidates import (
    ProviderCandidateResponse,
    generate_expected_care_candidate,
)
from app.expected_care_comparison import create_comparison
from app.expected_care_explanations import generate_explanation
from app.expected_care_review import (
    ClinicalRationaleInput,
    ClinicianResponseInput,
    submit_clinician_response,
)
from app.models import (
    CareCostItem,
    CareRelationship,
    ClinicalEvent,
    ClinicalEventUpdate,
    ClinicalService,
    ConsultationRequest,
    Diagnosis,
    DoctorNote,
    DoctorProfile,
    ExpectedCareClinicianResponse,
    ExpectedCarePublishedBaseline,
    ExpectedCareResponseHead,
    MedicalImagingAsset,
    MedicalRecord,
    Medication,
    PatientProfile,
    PayerMembership,
    PayerRequest,
    PayerRequestLine,
    Prescription,
    PrescriptionMedication,
    RecoveryPlan,
    RecoveryTask,
    RecoveryTaskCompletion,
    User,
    UserRole,
    VisitHistory,
)
from app.synthetic_care_reference import (
    SYNTHETIC_SERVICE_CODE,
    install_synthetic_care_reference_bundle,
    synthetic_active_selection,
)

DEMO_FIXTURE_KEY = "slice-e-local-demo-v1"
DEMO_PRODUCT_PATH_VERSION = "phase4-combined-product-path-v2"
DEMO_DOCTOR_EMAIL = "doctor.demo@example.com"
DEMO_PATIENT_EMAIL = "patient.demo@example.com"
DEMO_PAYER_EMAIL = "payer.demo@example.com"


@dataclass(frozen=True)
class SyntheticExpectedCareDemoResult:
    patient_id: uuid.UUID
    clinical_event_id: uuid.UUID
    payer_request_id: uuid.UUID
    unresponded_candidate_result_id: uuid.UUID
    concurred_candidate_result_id: uuid.UUID
    published_baseline_id: uuid.UUID
    combined_payer_request_id: uuid.UUID
    combined_candidate_result_id: uuid.UUID
    combined_published_baseline_id: uuid.UUID
    combined_comparison_id: uuid.UUID
    doctor_route: str
    patient_route: str
    payer_route: str
    combined_doctor_route: str
    combined_patient_route: str
    combined_payer_route: str


class SyntheticExpectedCareProvider:
    """Deterministic local fixture implementing the candidate-provider protocol."""

    def generate(self, *, provider_input, output_schema, settings):
        del output_schema, settings
        context = provider_input["context"]
        totals = provider_input["server_totals"]
        return ProviderCandidateResponse(
            output={
                "purpose_code": provider_input["purpose_code"],
                "purpose_contract_version": provider_input["purpose_contract_version"],
                "schema_version": provider_input["schema_version"],
                "minimum_input_checksum_sha256": provider_input["minimum_input_checksum_sha256"],
                "scenario_release_id": provider_input["scenario_release_id"],
                "reference_date": context["reference_date"],
                "jurisdiction": context["jurisdiction"],
                "region": context["region"],
                "facility_ownership": context["facility_ownership"],
                "facility_level": context["facility_level"],
                "currency": context["currency"],
                "assumptions": copy.deepcopy(provider_input["allowed_assumptions"]),
                "missing_information": copy.deepcopy(provider_input["allowed_missing_information"]),
                "attributable_exceptions": [],
                "confidence_category": "moderate",
                "confidence_limitations": copy.deepcopy(
                    provider_input["allowed_confidence_limitations"]
                ),
                "items": copy.deepcopy(provider_input["admitted_candidates"]),
                "total_low_minor": totals["total_low_minor"],
                "total_high_minor": totals["total_high_minor"],
                "release_lineage": copy.deepcopy(provider_input["release_lineage"]),
            },
            provider="deterministic_local_fixture",
            model="synthetic-expected-care-v1",
            input_tokens=1,
            output_tokens=1,
            cost_microunits=1,
        )


def _user(db: Session, *, email: str, role: UserRole) -> User:
    user = db.scalar(
        select(User).where(
            User.email == email,
            User.role == role,
            User.is_active.is_(True),
        )
    )
    if user is None:
        raise RuntimeError(f"synthetic_slice_e_account_missing:{role.value}")
    return user


def _scope(
    db: Session,
    *,
    doctor_user: User,
    patient_user: User,
    payer_user: User,
) -> tuple[DoctorProfile, PatientProfile, PayerMembership]:
    doctor = db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == doctor_user.id))
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == patient_user.id))
    membership = db.scalar(
        select(PayerMembership).where(
            PayerMembership.user_id == payer_user.id,
            PayerMembership.status == "active",
        )
    )
    if doctor is None or patient is None or membership is None:
        raise RuntimeError("synthetic_slice_e_profile_or_membership_missing")
    relationship = db.scalar(
        select(CareRelationship).where(
            CareRelationship.doctor_id == doctor.id,
            CareRelationship.patient_id == patient.id,
            CareRelationship.is_active.is_(True),
        )
    )
    if relationship is None:
        raise RuntimeError("synthetic_slice_e_active_relationship_missing")
    return doctor, patient, membership


def _event(db: Session, *, doctor: DoctorProfile, patient: PatientProfile) -> ClinicalEvent:
    event = db.scalar(
        select(ClinicalEvent).where(
            ClinicalEvent.patient_id == patient.id,
            ClinicalEvent.doctor_id == doctor.id,
            ClinicalEvent.metadata_json["fixture_key"].astext == DEMO_FIXTURE_KEY,
        )
    )
    if event is not None:
        return event
    event = ClinicalEvent(
        patient_id=patient.id,
        doctor_id=doctor.id,
        title="Synthetic rehabilitation planning review",
        chief_complaint="Wholly synthetic post-visit rehabilitation planning fixture.",
        symptom_summary=("Synthetic workflow context only; no real symptoms or patient data."),
        status="active",
        metadata_json={
            "fixture_key": DEMO_FIXTURE_KEY,
            "data_class": "wholly_synthetic",
            "purpose": "interactive_slice_e_local_review",
        },
    )
    db.add(event)
    db.flush()
    return event


def _combined_product_path(
    db: Session,
    *,
    doctor_user: User,
    patient_user: User,
    doctor: DoctorProfile,
    patient: PatientProfile,
    event: ClinicalEvent,
) -> list[CareCostItem]:
    """Add the versioned, wholly synthetic Phase 4 product-path facts."""

    event_metadata = dict(event.metadata_json)
    if event_metadata.get("product_path_fixture_version") != DEMO_PRODUCT_PATH_VERSION:
        event_metadata["product_path_fixture_version"] = DEMO_PRODUCT_PATH_VERSION
        event_metadata["vision_stage"] = "not_created_deepseek_image_input_unsupported"
        event.metadata_json = event_metadata
    event.chief_complaint = (
        "Wholly synthetic knee stiffness and reduced mobility after a simulated visit."
    )
    event.symptom_summary = (
        "Synthetic mild activity-related discomfort; no real symptoms or patient data."
    )
    event.diagnosis_summary = (
        "Clinician-recorded synthetic mobility limitation; not an AI diagnosis."
    )
    event.onset_date = date(2026, 7, 20)
    patient.neuro_history = patient.neuro_history or (
        "Wholly synthetic history: no recorded neurologic condition."
    )
    patient.surgery_history = patient.surgery_history or (
        "Wholly synthetic remote knee procedure for product-path testing."
    )
    patient.patient_reported_medications = patient.patient_reported_medications or (
        "Wholly synthetic topical analgesic use."
    )
    patient.medical_history_setup_completed = True

    def add_once(model, predicate, value):
        existing = db.scalar(select(model).where(*predicate))
        if existing is not None:
            return existing
        db.add(value)
        db.flush()
        return value

    add_once(
        MedicalRecord,
        (
            MedicalRecord.patient_id == patient.id,
            MedicalRecord.title == "Synthetic Phase 4 rehabilitation history",
        ),
        MedicalRecord(
            patient_id=patient.id,
            title="Synthetic Phase 4 rehabilitation history",
            category="synthetic_history",
            summary=(
                "Wholly synthetic patient-level record. It is intentionally not "
                "treated as event-bound cost evidence."
            ),
            recorded_at=datetime(2026, 7, 20, 8, 0, tzinfo=UTC),
        ),
    )
    add_once(
        VisitHistory,
        (
            VisitHistory.patient_id == patient.id,
            VisitHistory.clinical_event_id == event.id,
            VisitHistory.title == "Synthetic rehabilitation assessment",
        ),
        VisitHistory(
            patient_id=patient.id,
            clinical_event_id=event.id,
            visit_type="outpatient",
            title="Synthetic rehabilitation assessment",
            summary="Wholly synthetic event-linked assessment record.",
            occurred_at=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
            clinician_label="Synthetic Community Hospital clinician",
            recorded_by_user_id=doctor_user.id,
        ),
    )
    add_once(
        ClinicalEventUpdate,
        (
            ClinicalEventUpdate.patient_id == patient.id,
            ClinicalEventUpdate.clinical_event_id == event.id,
            ClinicalEventUpdate.update_type == "symptom_update",
        ),
        ClinicalEventUpdate(
            patient_id=patient.id,
            clinical_event_id=event.id,
            submitted_by_user_id=patient_user.id,
            update_type="symptom_update",
            summary="Wholly synthetic report: mobility improved after the first session.",
            occurred_at=datetime(2026, 7, 26, 18, 0, tzinfo=UTC),
        ),
    )
    add_once(
        Diagnosis,
        (
            Diagnosis.patient_id == patient.id,
            Diagnosis.clinical_event_id == event.id,
            Diagnosis.label == "Synthetic clinician-confirmed mobility limitation",
        ),
        Diagnosis(
            patient_id=patient.id,
            clinical_event_id=event.id,
            label="Synthetic clinician-confirmed mobility limitation",
            status="active",
            diagnosed_on=date(2026, 7, 23),
            notes=(
                "Recorded manually by the synthetic doctor fixture; not generated "
                "from imaging or by AI."
            ),
            recorded_by_user_id=doctor_user.id,
        ),
    )
    add_once(
        DoctorNote,
        (
            DoctorNote.patient_id == patient.id,
            DoctorNote.clinical_event_id == event.id,
            DoctorNote.title == "Synthetic cost-path justification",
        ),
        DoctorNote(
            patient_id=patient.id,
            doctor_id=doctor.id,
            clinical_event_id=event.id,
            title="Synthetic cost-path justification",
            body=(
                "Wholly synthetic clinician note explaining the rehabilitation, "
                "laboratory, imaging, consultation, and treatment pathway."
            ),
        ),
    )

    service_specs = (
        (
            "SYN-P4-REHAB-002",
            "rehabilitation",
            "Synthetic supervised rehabilitation course",
            "session",
            None,
            3,
            9000,
            7000,
        ),
        (
            "SYN-P4-LAB-001",
            "laboratory",
            "Synthetic mobility safety laboratory panel",
            "panel",
            None,
            1,
            2400,
            1800,
        ),
        (
            "SYN-P4-IMG-001",
            "imaging",
            "Synthetic knee radiograph",
            "radiograph",
            "knee",
            1,
            3200,
            2400,
        ),
        (
            "SYN-P4-CONSULT-001",
            "consultation",
            "Synthetic rehabilitation consultation",
            "specialist_review",
            None,
            1,
            4500,
            3000,
        ),
        (
            "SYN-P4-TREAT-001",
            "treatment",
            "Synthetic supervised mobility treatment",
            "procedure",
            "knee",
            2,
            6000,
            4200,
        ),
    )
    services: dict[str, ClinicalService] = {}
    costs: list[CareCostItem] = []
    for index, (
        code,
        category,
        name,
        subtype,
        body_region,
        quantity,
        actual_minor,
        payer_minor,
    ) in enumerate(service_specs):
        service = add_once(
            ClinicalService,
            (
                ClinicalService.clinical_event_id == event.id,
                ClinicalService.service_code == code,
            ),
            ClinicalService(
                patient_id=patient.id,
                clinical_event_id=event.id,
                category=category,
                name=name,
                service_subtype=subtype,
                body_region=body_region,
                service_code=code,
                ordered_by_doctor_id=doctor.id,
                performing_provider_name="Synthetic Community Hospital",
                status="completed",
                ordered_at=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
                scheduled_at=datetime(2026, 7, 24 + index, 9, 0, tzinfo=UTC),
                performed_at=datetime(2026, 7, 24 + index, 10, 0, tzinfo=UTC),
                indication_summary="Wholly synthetic Phase 4 product-path fixture.",
            ),
        )
        services[code] = service
        cost = add_once(
            CareCostItem,
            (CareCostItem.clinical_service_id == service.id,),
            CareCostItem(
                patient_id=patient.id,
                clinical_event_id=event.id,
                created_by_user_id=doctor_user.id,
                clinical_service_id=service.id,
                item_type=category,
                label=name,
                service_date=date(2026, 7, 24 + index),
                status="completed",
                pricing_state="final",
                quantity=quantity,
                currency="CNY",
                actual_cost_minor=actual_minor,
                payer_requested_minor=payer_minor,
                patient_responsibility_minor=actual_minor - payer_minor,
                ai_review_status="not_evaluated",
                notes=(f"Wholly synthetic {DEMO_PRODUCT_PATH_VERSION} delivered cost."),
            ),
        )
        costs.append(cost)

    medication = add_once(
        Medication,
        (
            Medication.patient_id == patient.id,
            Medication.clinical_event_id == event.id,
            Medication.name == "Synthetic topical analgesic",
        ),
        Medication(
            patient_id=patient.id,
            clinical_event_id=event.id,
            name="Synthetic topical analgesic",
            dosage="Synthetic 1 unit",
            schedule="Once daily for 7 synthetic days",
            status="taking",
            note="Wholly synthetic medication record; not medical advice.",
        ),
    )
    medication_cost = add_once(
        CareCostItem,
        (CareCostItem.medication_id == medication.id,),
        CareCostItem(
            patient_id=patient.id,
            clinical_event_id=event.id,
            created_by_user_id=doctor_user.id,
            medication_id=medication.id,
            item_type="medication",
            label="Synthetic topical analgesic",
            service_date=date(2026, 7, 24),
            status="completed",
            pricing_state="final",
            quantity=1,
            currency="CNY",
            actual_cost_minor=1200,
            payer_requested_minor=800,
            patient_responsibility_minor=400,
            ai_review_status="not_evaluated",
            notes="Wholly synthetic medication cost.",
        ),
    )
    costs.append(medication_cost)
    prescription = add_once(
        Prescription,
        (
            Prescription.patient_id == patient.id,
            Prescription.clinical_event_id == event.id,
            Prescription.notes == "Wholly synthetic Phase 4 prescription.",
        ),
        Prescription(
            patient_id=patient.id,
            clinical_event_id=event.id,
            prescribed_by_user_id=doctor_user.id,
            status="issued",
            issued_at=datetime(2026, 7, 23, 10, 0, tzinfo=UTC),
            notes="Wholly synthetic Phase 4 prescription.",
        ),
    )
    add_once(
        PrescriptionMedication,
        (
            PrescriptionMedication.prescription_id == prescription.id,
            PrescriptionMedication.name == medication.name,
        ),
        PrescriptionMedication(
            prescription_id=prescription.id,
            medication_id=medication.id,
            name=medication.name,
            dosage=medication.dosage,
            schedule=medication.schedule,
            start_date=date(2026, 7, 24),
            end_date=date(2026, 7, 30),
            metadata_json={"fixture_version": DEMO_PRODUCT_PATH_VERSION},
        ),
    )

    plan = add_once(
        RecoveryPlan,
        (
            RecoveryPlan.patient_id == patient.id,
            RecoveryPlan.clinical_event_id == event.id,
            RecoveryPlan.title == "Synthetic seven-day mobility recovery plan",
        ),
        RecoveryPlan(
            patient_id=patient.id,
            doctor_id=doctor.id,
            clinical_event_id=event.id,
            title="Synthetic seven-day mobility recovery plan",
            instructions="Complete the wholly synthetic mobility task once daily.",
            status="active",
            review_status="approved",
            safety_label="synthetic_fixture_not_medical_advice",
            review_actor_user_id=doctor_user.id,
            submitted_at=datetime(2026, 7, 23, 10, 0, tzinfo=UTC),
            reviewed_at=datetime(2026, 7, 23, 10, 5, tzinfo=UTC),
            approved_at=datetime(2026, 7, 23, 10, 5, tzinfo=UTC),
            activated_at=datetime(2026, 7, 24, 8, 0, tzinfo=UTC),
        ),
    )
    task = add_once(
        RecoveryTask,
        (
            RecoveryTask.plan_id == plan.id,
            RecoveryTask.title == "Synthetic guided mobility check",
        ),
        RecoveryTask(
            plan_id=plan.id,
            patient_id=patient.id,
            medication_id=None,
            category="exercise",
            title="Synthetic guided mobility check",
            detail="Wholly synthetic completion evidence.",
            due_label="2026-07-25",
            notification_time=None,
            sort_order=1,
        ),
    )
    add_once(
        RecoveryTaskCompletion,
        (
            RecoveryTaskCompletion.task_id == task.id,
            RecoveryTaskCompletion.patient_id == patient.id,
        ),
        RecoveryTaskCompletion(
            task_id=task.id,
            patient_id=patient.id,
            actor_user_id=patient_user.id,
            completed_at=datetime(2026, 7, 25, 18, 0, tzinfo=UTC),
        ),
    )
    consultation_service = services["SYN-P4-CONSULT-001"]
    add_once(
        ConsultationRequest,
        (ConsultationRequest.clinical_service_id == consultation_service.id,),
        ConsultationRequest(
            patient_id=patient.id,
            clinical_event_id=event.id,
            clinical_service_id=consultation_service.id,
            requested_by_user_id=doctor_user.id,
            specialty="Synthetic rehabilitation medicine",
            question_summary="Review the wholly synthetic mobility pathway.",
            priority="routine",
            status="completed",
            safety_label="synthetic_fixture_only",
        ),
    )
    imaging_service = services["SYN-P4-IMG-001"]
    add_once(
        MedicalImagingAsset,
        (
            MedicalImagingAsset.patient_id == patient.id,
            MedicalImagingAsset.object_key == f"synthetic/{event.id}/phase4-knee-radiograph-v2.png",
        ),
        MedicalImagingAsset(
            patient_id=patient.id,
            clinical_event_id=event.id,
            clinical_service_id=imaging_service.id,
            uploaded_by_user_id=doctor_user.id,
            reviewed_by_user_id=doctor_user.id,
            storage_provider="local",
            content_type="image/png",
            file_extension=".png",
            size_bytes=1024,
            uploaded_size_bytes=1024,
            object_key=f"synthetic/{event.id}/phase4-knee-radiograph-v2.png",
            upload_status="uploaded",
            review_status="reviewed",
            finding_summary=(
                "Wholly synthetic manual observation recorded by the doctor; "
                "no Vision model was invoked."
            ),
            measurement_summary="Synthetic alignment measurement: 0 units.",
            observed_at=datetime(2026, 7, 25, 10, 0, tzinfo=UTC),
            treatment_relevance_date=date(2026, 7, 25),
            etag="synthetic-phase4-etag-v2",
            checksum_sha256="2" * 64,
            expires_at=datetime(2027, 7, 27, 0, 0, tzinfo=UTC),
            uploaded_at=datetime(2026, 7, 25, 10, 5, tzinfo=UTC),
            reviewed_at=datetime(2026, 7, 25, 11, 0, tzinfo=UTC),
        ),
    )
    db.flush()
    return list(
        db.scalars(
            select(CareCostItem)
            .where(CareCostItem.clinical_event_id == event.id)
            .order_by(CareCostItem.service_date, CareCostItem.id)
        ).all()
    )


def _combined_payer_request(
    db: Session,
    *,
    doctor: DoctorProfile,
    patient: PatientProfile,
    membership: PayerMembership,
    event: ClinicalEvent,
    costs: list[CareCostItem],
) -> PayerRequest:
    eligible_costs = [item for item in costs if item.clinical_service_id is not None]
    summary = "Wholly synthetic Phase 4 combined request with manual human review only."
    request = db.scalar(
        select(PayerRequest).where(
            PayerRequest.clinical_event_id == event.id,
            PayerRequest.doctor_id == doctor.id,
            PayerRequest.payer_organization_id == membership.payer_organization_id,
            PayerRequest.doctor_summary == summary,
        )
    )
    if request is not None:
        return request
    request = PayerRequest(
        clinical_event_id=event.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        payer_organization_id=membership.payer_organization_id,
        status="submitted",
        currency="CNY",
        requested_total_minor=sum(item.payer_requested_minor for item in eligible_costs),
        doctor_summary=summary,
        ai_review_status="not_evaluated",
    )
    db.add(request)
    db.flush()
    for item in eligible_costs:
        db.add(
            PayerRequestLine(
                payer_request_id=request.id,
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
    db.flush()
    return request


def _payer_request(
    db: Session,
    *,
    doctor_user: User,
    doctor: DoctorProfile,
    patient: PatientProfile,
    membership: PayerMembership,
    event: ClinicalEvent,
) -> PayerRequest:
    service = db.scalar(
        select(ClinicalService).where(
            ClinicalService.clinical_event_id == event.id,
            ClinicalService.service_code == SYNTHETIC_SERVICE_CODE,
        )
    )
    if service is None:
        service = ClinicalService(
            patient_id=patient.id,
            clinical_event_id=event.id,
            category="therapy",
            name="Synthetic rehabilitation session",
            service_subtype="wholly_synthetic_fixture",
            service_code=SYNTHETIC_SERVICE_CODE,
            ordered_by_doctor_id=doctor.id,
            performing_provider_name="Synthetic Community Hospital",
            status="completed",
            ordered_at=datetime(2026, 7, 24, 9, 0, tzinfo=UTC),
            performed_at=datetime(2026, 7, 25, 9, 0, tzinfo=UTC),
            indication_summary="Synthetic Slice E workflow demonstration only.",
        )
        db.add(service)
        db.flush()
    cost = db.scalar(select(CareCostItem).where(CareCostItem.clinical_service_id == service.id))
    if cost is None:
        cost = CareCostItem(
            patient_id=patient.id,
            clinical_event_id=event.id,
            created_by_user_id=doctor_user.id,
            clinical_service_id=service.id,
            item_type="therapy",
            label="Synthetic rehabilitation session",
            service_date=date(2026, 7, 25),
            status="completed",
            pricing_state="final",
            quantity=1,
            currency="CNY",
            actual_cost_minor=3000,
            payer_requested_minor=2000,
            patient_responsibility_minor=1000,
            ai_review_status="not_evaluated",
            notes="Wholly synthetic local Slice E fixture.",
        )
        db.add(cost)
        db.flush()
    request = db.scalar(
        select(PayerRequest).where(
            PayerRequest.clinical_event_id == event.id,
            PayerRequest.patient_id == patient.id,
            PayerRequest.doctor_id == doctor.id,
            PayerRequest.payer_organization_id == membership.payer_organization_id,
            PayerRequest.doctor_summary == "Wholly synthetic immutable Slice E request scope.",
        )
    )
    if request is not None:
        return request
    request = PayerRequest(
        clinical_event_id=event.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        payer_organization_id=membership.payer_organization_id,
        status="submitted",
        currency="CNY",
        requested_total_minor=cost.payer_requested_minor,
        doctor_summary="Wholly synthetic immutable Slice E request scope.",
        ai_review_status="not_evaluated",
    )
    db.add(request)
    db.flush()
    db.add(
        PayerRequestLine(
            payer_request_id=request.id,
            care_cost_item_id=cost.id,
            item_type=cost.item_type,
            label=cost.label,
            service_date=cost.service_date,
            currency=cost.currency,
            actual_cost_minor=cost.actual_cost_minor,
            requested_minor=cost.payer_requested_minor,
            patient_responsibility_minor=cost.patient_responsibility_minor,
        )
    )
    db.flush()
    return request


def bootstrap_synthetic_expected_care_demo(
    db: Session,
    settings: Settings,
    *,
    doctor_email: str = DEMO_DOCTOR_EMAIL,
    patient_email: str = DEMO_PATIENT_EMAIL,
    payer_email: str = DEMO_PAYER_EMAIL,
) -> SyntheticExpectedCareDemoResult:
    """Create the complete local Slice E review path and return stable routes."""

    if settings.environment not in {"local", "test"}:
        raise RuntimeError("synthetic_slice_e_demo_is_local_test_only")
    doctor_user = _user(db, email=doctor_email, role=UserRole.doctor)
    patient_user = _user(db, email=patient_email, role=UserRole.patient)
    payer_user = _user(db, email=payer_email, role=UserRole.payer)
    doctor, patient, membership = _scope(
        db,
        doctor_user=doctor_user,
        patient_user=patient_user,
        payer_user=payer_user,
    )
    event = _event(db, doctor=doctor, patient=patient)
    payer_request = _payer_request(
        db,
        doctor_user=doctor_user,
        doctor=doctor,
        patient=patient,
        membership=membership,
        event=event,
    )
    combined_costs = _combined_product_path(
        db,
        doctor_user=doctor_user,
        patient_user=patient_user,
        doctor=doctor,
        patient=patient,
        event=event,
    )
    combined_payer_request = _combined_payer_request(
        db,
        doctor=doctor,
        patient=patient,
        membership=membership,
        event=event,
        costs=combined_costs,
    )
    install_synthetic_care_reference_bundle(db)
    db.commit()

    fixture_settings = settings.model_copy(
        update={
            "expected_care_candidate_enabled": True,
            "expected_care_provider": "deterministic_local_fixture",
            "expected_care_model": "synthetic-expected-care-v1",
            # The richer bounded fact object is larger than the original Slice E
            # fixture. This local/test-only ceiling never authorizes a paid call.
            "expected_care_max_cost_microunits": 10_000,
        }
    )
    evaluation = EvaluationRequest(
        context=EvaluationContext(
            evaluated_on=date(2026, 7, 26),
            reference_date=date(2026, 7, 26),
            jurisdiction="CN",
            region="Synthetic Province",
            encounter_type="outpatient",
            facility_ownership="public",
            facility_level="primary",
            currency="CNY",
            patient_age=40,
        )
    )
    concurred = generate_expected_care_candidate(
        db,
        actor_user_id=doctor_user.id,
        patient_id=patient.id,
        clinical_event_id=event.id,
        selection=synthetic_active_selection(),
        request=evaluation,
        idempotency_key="slice-e-demo-reviewed-candidate-v1",
        settings=fixture_settings,
        provider=SyntheticExpectedCareProvider(),
        payer_request_id=payer_request.id,
    )
    db.commit()
    existing_response = db.scalar(
        select(ExpectedCareClinicianResponse).where(
            ExpectedCareClinicianResponse.actor_user_id == doctor_user.id,
            ExpectedCareClinicianResponse.clinical_event_id == event.id,
            ExpectedCareClinicianResponse.idempotency_key == "slice-e-demo-doctor-concurrence-v2",
        )
    )
    response_head = db.get(ExpectedCareResponseHead, concurred.result.id)
    response = submit_clinician_response(
        patient_id=patient.id,
        event_id=event.id,
        candidate_result_id=concurred.result.id,
        payload=ClinicianResponseInput(
            position="concur",
            expected_version=(
                existing_response.accepted_head_version
                if existing_response is not None
                else response_head.version
                if response_head
                else 0
            ),
            rationale=ClinicalRationaleInput(
                exception_code="synthetic_demo_context",
                rationale=(
                    "The clinician concurs only for demonstrating the immutable "
                    "Slice E baseline workflow with wholly synthetic local data."
                ),
                patient_safe_summary=(
                    "This range is part of a wholly synthetic local demonstration."
                ),
                applies_to_item_keys=[],
            ),
        ),
        db=db,
        user=doctor_user,
        idempotency_key="slice-e-demo-doctor-concurrence-v2",
    )
    pending = generate_expected_care_candidate(
        db,
        actor_user_id=doctor_user.id,
        patient_id=patient.id,
        clinical_event_id=event.id,
        selection=synthetic_active_selection(),
        request=evaluation,
        idempotency_key="slice-e-demo-pending-candidate-v1",
        settings=fixture_settings,
        provider=SyntheticExpectedCareProvider(),
    )
    # Preserve an unambiguous episode timeline: PostgreSQL `now()` is stable for
    # a transaction, so the pending and combined baselines must not share the
    # same creation timestamp when the patient route selects the newest
    # immutable envelope.
    db.commit()
    combined = generate_expected_care_candidate(
        db,
        actor_user_id=doctor_user.id,
        patient_id=patient.id,
        clinical_event_id=event.id,
        selection=synthetic_active_selection(),
        request=evaluation,
        idempotency_key="phase4-combined-product-path-candidate-v2",
        settings=fixture_settings,
        provider=SyntheticExpectedCareProvider(),
        payer_request_id=combined_payer_request.id,
    )
    db.commit()
    combined_existing_response = db.scalar(
        select(ExpectedCareClinicianResponse).where(
            ExpectedCareClinicianResponse.actor_user_id == doctor_user.id,
            ExpectedCareClinicianResponse.clinical_event_id == event.id,
            ExpectedCareClinicianResponse.idempotency_key
            == "phase4-combined-clinician-response-v2",
        )
    )
    combined_head = db.get(ExpectedCareResponseHead, combined.result.id)
    combined_response = submit_clinician_response(
        patient_id=patient.id,
        event_id=event.id,
        candidate_result_id=combined.result.id,
        payload=ClinicianResponseInput(
            position="concur",
            expected_version=(
                combined_existing_response.accepted_head_version
                if combined_existing_response is not None
                else combined_head.version
                if combined_head
                else 0
            ),
            rationale=ClinicalRationaleInput(
                exception_code="synthetic_combined_path_reviewed",
                rationale=(
                    "The synthetic doctor reviewed the combined symptoms, history, "
                    "manual imaging finding, prescription, medication, recovery, "
                    "consultation, services, quantities, dates, and costs."
                ),
                patient_safe_summary=(
                    "The responsible synthetic doctor reviewed this combined "
                    "demonstration pathway. It is not medical advice."
                ),
                applies_to_item_keys=[],
            ),
        ),
        db=db,
        user=doctor_user,
        idempotency_key="phase4-combined-clinician-response-v2",
    )
    combined_baseline_id = combined_response["baseline_id"]
    if not isinstance(combined_baseline_id, uuid.UUID):
        raise RuntimeError("synthetic_phase4_combined_baseline_missing")
    combined_baseline = db.get(ExpectedCarePublishedBaseline, combined_baseline_id)
    if combined_baseline is None:
        raise RuntimeError("synthetic_phase4_combined_baseline_missing")
    comparison, _ = create_comparison(
        db,
        actor_user_id=doctor_user.id,
        baseline=combined_baseline,
        idempotency_key="phase4-combined-comparison-v2",
        include_submitted_facts=True,
    )
    review_payer_request(
        combined_payer_request.id,
        PayerReviewRequest(
            action="request_clarification",
            expected_version=1,
            reason_code="synthetic_manual_clarification",
            note=(
                "Wholly synthetic reviewer requests human clarification; no "
                "automated adverse decision."
            ),
        ),
        payer_user,
        db,
        idempotency_key="phase4-combined-payer-clarification-v2",
    )
    append_doctor_payer_response(
        combined_payer_request.id,
        PayerDoctorResponseCreate(
            expected_version=2,
            response_type="justification",
            summary=(
                "Wholly synthetic doctor justification: the submitted services "
                "are linked to the combined event; final payer judgment remains manual."
            ),
            baseline_id=combined_baseline.id,
            comparison_id=comparison.id,
        ),
        doctor_user,
        db,
        idempotency_key="phase4-combined-doctor-justification-v2",
    )
    review_payer_request(
        combined_payer_request.id,
        PayerReviewRequest(
            action="accept",
            expected_version=3,
            reason_code="synthetic_manual_acceptance",
            note=(
                "Wholly synthetic manual acceptance for product-path verification; "
                "not a real coverage decision."
            ),
        ),
        payer_user,
        db,
        idempotency_key="phase4-combined-payer-acceptance-v2",
    )
    fallback_settings = settings.model_copy(
        update={
            "expected_care_explanation_enabled": False,
            "expected_care_explanation_kill_switch": True,
        }
    )
    for role, actor_id, locale in (
        ("doctor", doctor_user.id, "en"),
        ("patient", patient_user.id, "zh-Hans"),
        ("payer", payer_user.id, "en"),
    ):
        generate_explanation(
            db,
            actor_user_id=actor_id,
            comparison=comparison,
            role=role,
            locale=locale,
            idempotency_key=f"phase4-combined-{role}-fallback-v2",
            settings=fallback_settings,
        )
    baseline_id = response["baseline_id"]
    if not isinstance(baseline_id, uuid.UUID):
        raise RuntimeError("synthetic_slice_e_published_baseline_missing")
    return SyntheticExpectedCareDemoResult(
        patient_id=patient.id,
        clinical_event_id=event.id,
        payer_request_id=payer_request.id,
        unresponded_candidate_result_id=pending.result.id,
        concurred_candidate_result_id=concurred.result.id,
        published_baseline_id=baseline_id,
        combined_payer_request_id=combined_payer_request.id,
        combined_candidate_result_id=combined.result.id,
        combined_published_baseline_id=combined_baseline.id,
        combined_comparison_id=comparison.id,
        doctor_route=(f"/doctor/expected-care?patient={patient.id}&event={event.id}"),
        patient_route=f"/patient/expected-care/{event.id}",
        payer_route=f"/payer/requests/{payer_request.id}/expected-care",
        combined_doctor_route=(f"/doctor/expected-care?patient={patient.id}&event={event.id}"),
        combined_patient_route=f"/patient/expected-care/{event.id}",
        combined_payer_route=(f"/payer/requests/{combined_payer_request.id}/expected-care"),
    )
