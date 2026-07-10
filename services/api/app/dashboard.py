import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.ai_chat import DeepSeekChatError, deepseek_chat_adapter
from app.dependencies import AppSettings, CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    AuditEvent,
    CareRelationship,
    ChatMessage,
    ChatRateLimit,
    ChatThread,
    ChronicDisease,
    ClinicalEvent,
    ClinicalEventUpdate,
    ConsultationRequest,
    DashboardSnapshot,
    DemoMedicalAsset,
    Diagnosis,
    DoctorNote,
    DoctorProfile,
    MedicalHistoryReview,
    MedicalImagingAsset,
    MedicalRecord,
    Medication,
    MedicationReminder,
    Notification,
    PatientAllergy,
    PatientProfile,
    Prescription,
    PrescriptionMedication,
    RecoveryPlan,
    RecoveryTask,
    RecoveryTaskCompletion,
    SimulatedAssessment,
    UserRole,
    VisitHistory,
)
from app.schemas import (
    AssessmentListResponse,
    AssessmentRequest,
    AssessmentResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChronicDiseaseListResponse,
    ChronicDiseaseRequest,
    ChronicDiseaseResponse,
    ClinicalEventListResponse,
    ClinicalEventRequest,
    ClinicalEventResponse,
    ClinicalEventTimelineEntry,
    ClinicalEventUpdateListResponse,
    ClinicalEventUpdateRequest,
    ClinicalEventUpdateResponse,
    ConsultationCreateRequest,
    ConsultationListResponse,
    ConsultationResponse,
    DashboardResponse,
    DemoAssetPresignRequest,
    DemoAssetPresignResponse,
    DiagnosisListResponse,
    DiagnosisRequest,
    DiagnosisResponse,
    DoctorNoteCreateRequest,
    DoctorNoteListResponse,
    DoctorNoteResponse,
    DoctorNoteUpdateRequest,
    DoctorProfileResponse,
    DoctorProfileUpdateRequest,
    MedicalHistoryReviewListResponse,
    MedicalHistoryReviewRequest,
    MedicalHistoryReviewResponse,
    MedicalImagingAssetListResponse,
    MedicalImagingAssetResponse,
    MedicalImagingCompleteRequest,
    MedicalImagingPresignRequest,
    MedicalImagingPresignResponse,
    MedicalImagingReviewRequest,
    MedicalRecordListResponse,
    MedicalRecordRequest,
    MedicalRecordResponse,
    MedicationListResponse,
    MedicationReminderListResponse,
    MedicationReminderRequest,
    MedicationReminderResponse,
    MedicationRequest,
    MedicationResponse,
    NotificationListResponse,
    NotificationResponse,
    PatientAllergyListResponse,
    PatientAllergyRequest,
    PatientAllergyResponse,
    PatientCareBundleResponse,
    PatientConnectRequest,
    PatientDemographicsResponse,
    PatientDemographicsUpdateRequest,
    PatientDoctorContactListResponse,
    PatientDoctorContactResponse,
    PatientListResponse,
    PatientMatchPreviewResponse,
    PatientProfileResponse,
    PatientSummaryResponse,
    PrescriptionListResponse,
    PrescriptionMedicationResponse,
    PrescriptionRequest,
    PrescriptionResponse,
    RecoveryPlanCreateRequest,
    RecoveryPlanListResponse,
    RecoveryPlanProgressResponse,
    RecoveryPlanResponse,
    RecoveryPlanUpdateRequest,
    RecoveryTaskInput,
    RecoveryTaskResponse,
    TaskCompletionRequest,
    TaskCompletionResponse,
    VisitHistoryListResponse,
    VisitHistoryRequest,
    VisitHistoryResponse,
)

router = APIRouter(prefix="/api/v1", tags=["dashboard"])

SIMULATION_LABEL = "Research simulation - not for diagnosis."
SYNTHETIC_DATA_LABEL = "Synthetic demonstration data only. Do not enter real patient data."
EDUCATIONAL_LABEL = "Educational information only - not medical advice."
EMERGENCY_LABEL = "If this may be an emergency, contact local emergency services now."
RED_FLAG_MESSAGE = (
    "If this may be an emergency, contact local emergency services now. "
    "For symptoms such as chest pain, trouble breathing, stroke signs, severe bleeding, "
    "overdose, or thoughts of self-harm, seek urgent local help immediately. "
    "Dr. AI cannot evaluate emergencies."
)
UNSAFE_PROMPT_MESSAGE = (
    "Educational information only - not medical advice. I cannot diagnose, interpret personal "
    "records, or recommend medication changes. Use this space to prepare general questions for "
    "a qualified clinician."
)
DEEPSEEK_FALLBACK_MESSAGE = (
    "Educational information only - not medical advice. The educational chat service is "
    "temporarily using a safe fallback. Prepare questions about your synthetic recovery plan, "
    "what to monitor, and when to contact a qualified clinician."
)
DEMO_UPLOAD_MAX_SIZE_BYTES = 10_485_760
DEMO_UPLOAD_TTL_MINUTES = 15
IMAGING_STORAGE_PROVIDER = "tencent_cos"
FIXTURE_SIMULATOR_VERSION = "fixture-simulator-1.0.0"
DEMO_UPLOAD_ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "image/jpeg": {"jpg", "jpeg"},
    "image/png": {"png"},
    "application/dicom": {"dcm", "dicom"},
}


@dataclass(frozen=True)
class AssessmentFixture:
    risk_band: str
    demo_score: float
    input_completeness: str


ASSESSMENT_FIXTURES: dict[str, AssessmentFixture] = {
    "synthetic_lung_case_001": AssessmentFixture(
        risk_band="moderate",
        demo_score=0.54,
        input_completeness="complete",
    ),
    "synthetic_lung_case_002": AssessmentFixture(
        risk_band="low",
        demo_score=0.21,
        input_completeness="partial",
    ),
}

ASSESSMENT_LIMITATIONS = [
    "Synthetic fixture result; no clinical inference was performed.",
    "Not validated for diagnosis, treatment, or prognosis.",
]
ASSESSMENT_NEXT_STEPS = [
    "Review the synthetic case with a qualified clinician.",
    "Do not use this demo result for medication, diagnosis, or care decisions.",
]
RECOVERY_PLAN_STATUSES = {"draft", "active", "completed"}
RECOVERY_PLAN_REVIEW_STATUSES = {"draft", "in_review", "changes_requested", "approved"}
RECOVERY_TASK_CATEGORIES = {"medication", "exercise", "diet", "follow_up"}
DEFAULT_CHAT_THREAD_KEY = "patient-education"
CONSULTATION_STATUSES = {"requested", "accepted", "completed", "cancelled"}
RED_FLAG_PATTERNS = (
    r"\b(chest pain|can'?t breathe|cannot breathe|shortness of breath)\b",
    r"\b(stroke|face drooping|severe bleeding|overdose)\b",
    r"\b(suicidal|self[- ]?harm|kill myself)\b",
)
UNSAFE_PROMPT_PATTERNS = (
    r"\b(diagnose|diagnosis|change my dose|change dosage|stop (my )?medication)\b",
    r"\b(prescribe|interpret my ct|interpret my scan|raw record|medical record|lab result)\b",
    r"\b(ignore (all )?(previous|prior) instructions|system prompt|developer message)\b",
    r"\b(reveal (your )?prompt|show (your )?prompt|contact info|phone number)\b",
    r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
    r"\b(?:\+?\d[\d .-]{7,}\d)\b",
)


def _neutral_not_found() -> ApiError:
    return ApiError(404, "not_found", "The requested resource was not found.")


def _patient_overview(profile: PatientProfile) -> str:
    return (
        f"Patient code {profile.synthetic_identifier} lets a doctor connect "
        "with this account after the patient shares it."
    )


def _patient_response(profile: PatientProfile) -> PatientProfileResponse:
    return PatientProfileResponse(
        patient_id=profile.id,
        display_name=profile.display_name,
        synthetic_identifier=profile.synthetic_identifier,
        relationship_label="Care relationship active",
        overview=_patient_overview(profile),
        demographics=_demographics_response(profile),
    )


def _demographics_response(profile: PatientProfile) -> PatientDemographicsResponse:
    return PatientDemographicsResponse(
        display_name=profile.display_name,
        birth_date=profile.birth_date,
        birth_year=profile.birth_year,
        sex=profile.sex,
        gender=profile.gender,
        contact_phone=profile.contact_phone,
        emergency_contact_name=profile.emergency_contact_name,
        emergency_contact_phone=profile.emergency_contact_phone,
        preferred_language=profile.preferred_language,
        contact_preference=profile.contact_preference,
        avatar_url=profile.avatar_url,
        country=profile.country,
        province=profile.province,
        city=profile.city,
        home_address=profile.home_address,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        medical_history_setup_completed=profile.medical_history_setup_completed,
    )


def _doctor_profile_response(profile: DoctorProfile) -> DoctorProfileResponse:
    last_active_at = profile.user.last_active_at
    return DoctorProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        title=profile.title,
        birth_date=profile.birth_date,
        gender=profile.gender,
        contact_phone=profile.contact_phone,
        avatar_url=profile.avatar_url,
        country=profile.country,
        province=profile.province,
        city=profile.city,
        hospital_name=profile.hospital_name,
        specialty=profile.specialty,
        department=profile.department,
        preferred_language=profile.preferred_language,
        last_active_at=last_active_at,
        is_recently_active=_is_recently_active(last_active_at),
    )


def _is_recently_active(
    last_active_at: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    reference = now or datetime.now(UTC)
    return last_active_at is not None and last_active_at >= reference - timedelta(days=14)


def _clinical_event_linked_counts(
    event: ClinicalEvent,
    db: DbSession,
) -> dict[str, int]:
    return {
        "visit_history": db.scalar(
            select(func.count())
            .select_from(VisitHistory)
            .where(VisitHistory.clinical_event_id == event.id)
        )
        or 0,
        "diagnoses": db.scalar(
            select(func.count())
            .select_from(Diagnosis)
            .where(Diagnosis.clinical_event_id == event.id)
        )
        or 0,
        "medications": db.scalar(
            select(func.count())
            .select_from(Medication)
            .where(Medication.clinical_event_id == event.id)
        )
        or 0,
        "prescriptions": db.scalar(
            select(func.count())
            .select_from(Prescription)
            .where(Prescription.clinical_event_id == event.id)
        )
        or 0,
        "medication_reminders": db.scalar(
            select(func.count())
            .select_from(MedicationReminder)
            .where(MedicationReminder.clinical_event_id == event.id)
        )
        or 0,
        "recovery_plans": db.scalar(
            select(func.count())
            .select_from(RecoveryPlan)
            .where(RecoveryPlan.clinical_event_id == event.id)
        )
        or 0,
        "imaging_assets": db.scalar(
            select(func.count())
            .select_from(MedicalImagingAsset)
            .where(MedicalImagingAsset.clinical_event_id == event.id)
        )
        or 0,
        "doctor_notes": db.scalar(
            select(func.count())
            .select_from(DoctorNote)
            .where(DoctorNote.clinical_event_id == event.id)
        )
        or 0,
        "consultations": db.scalar(
            select(func.count())
            .select_from(ConsultationRequest)
            .where(ConsultationRequest.clinical_event_id == event.id)
        )
        or 0,
        "notifications": db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.clinical_event_id == event.id)
        )
        or 0,
        "patient_updates": db.scalar(
            select(func.count())
            .select_from(ClinicalEventUpdate)
            .where(ClinicalEventUpdate.clinical_event_id == event.id)
        )
        or 0,
    }


def _clinical_event_response(event: ClinicalEvent, db: DbSession) -> ClinicalEventResponse:
    return ClinicalEventResponse(
        id=event.id,
        patient_id=event.patient_id,
        doctor_id=event.doctor_id,
        title=event.title,
        chief_complaint=event.chief_complaint,
        symptom_summary=event.symptom_summary,
        diagnosis_summary=event.diagnosis_summary,
        onset_date=event.onset_date,
        status=event.status,  # type: ignore[arg-type]
        linked_resource_counts=_clinical_event_linked_counts(event, db),
        timeline=_clinical_event_timeline(event, db),
        patient_updates=[
            _clinical_event_update_response(update)
            for update in db.scalars(
                select(ClinicalEventUpdate)
                .where(ClinicalEventUpdate.clinical_event_id == event.id)
                .order_by(ClinicalEventUpdate.occurred_at.desc())
            ).all()
        ],
        created_at=event.created_at,
        updated_at=event.updated_at,
        safety_label=SYNTHETIC_DATA_LABEL,
    )


def _clinical_event_timeline(
    event: ClinicalEvent,
    db: DbSession,
) -> list[ClinicalEventTimelineEntry]:
    entries = [
        ClinicalEventTimelineEntry(
            entry_type="clinical_event_created",
            resource_id=event.id,
            title="Clinical Event created",
            occurred_at=event.created_at,
        )
    ]
    for visit in db.scalars(
        select(VisitHistory).where(VisitHistory.clinical_event_id == event.id)
    ).all():
        entries.append(
            ClinicalEventTimelineEntry(
                entry_type="encounter_update",
                resource_id=visit.id,
                title=f"Encounter update recorded: {visit.visit_type}",
                occurred_at=visit.occurred_at,
            )
        )
    for diagnosis in db.scalars(
        select(Diagnosis).where(Diagnosis.clinical_event_id == event.id)
    ).all():
        entries.append(
            ClinicalEventTimelineEntry(
                entry_type="diagnosis_updated",
                resource_id=diagnosis.id,
                title=f"Diagnosis status updated: {diagnosis.status}",
                occurred_at=diagnosis.created_at,
            )
        )
    for prescription in db.scalars(
        select(Prescription).where(Prescription.clinical_event_id == event.id)
    ).all():
        entries.append(
            ClinicalEventTimelineEntry(
                entry_type="prescription_issued",
                resource_id=prescription.id,
                title=f"Prescription {prescription.status}",
                occurred_at=prescription.issued_at,
            )
        )
    for plan in db.scalars(
        select(RecoveryPlan).where(RecoveryPlan.clinical_event_id == event.id)
    ).all():
        entries.append(
            ClinicalEventTimelineEntry(
                entry_type="recovery_plan_updated",
                resource_id=plan.id,
                title=f"Recovery plan {plan.status}; review {plan.review_status}",
                occurred_at=plan.updated_at,
            )
        )
    for asset in db.scalars(
        select(MedicalImagingAsset).where(MedicalImagingAsset.clinical_event_id == event.id)
    ).all():
        entries.append(
            ClinicalEventTimelineEntry(
                entry_type="imaging_review",
                resource_id=asset.id,
                title=f"Imaging {asset.review_status}",
                occurred_at=asset.reviewed_at or asset.uploaded_at or asset.created_at,
            )
        )
    for note in db.scalars(
        select(DoctorNote).where(DoctorNote.clinical_event_id == event.id)
    ).all():
        entries.append(
            ClinicalEventTimelineEntry(
                entry_type="doctor_note",
                resource_id=note.id,
                title="Doctor note added",
                occurred_at=note.created_at,
            )
        )
    for request in db.scalars(
        select(ConsultationRequest).where(ConsultationRequest.clinical_event_id == event.id)
    ).all():
        entries.append(
            ClinicalEventTimelineEntry(
                entry_type="consultation_requested",
                resource_id=request.id,
                title=f"Specialist consultation {request.status}",
                occurred_at=request.created_at,
            )
        )
    for update in db.scalars(
        select(ClinicalEventUpdate).where(ClinicalEventUpdate.clinical_event_id == event.id)
    ).all():
        entries.append(
            ClinicalEventTimelineEntry(
                entry_type="patient_update",
                resource_id=update.id,
                title=f"Patient update: {update.update_type}",
                occurred_at=update.occurred_at,
            )
        )
    return sorted(entries, key=lambda entry: entry.occurred_at, reverse=True)


def _clinical_event_update_response(
    update: ClinicalEventUpdate,
) -> ClinicalEventUpdateResponse:
    return ClinicalEventUpdateResponse(
        id=update.id,
        patient_id=update.patient_id,
        clinical_event_id=update.clinical_event_id,
        submitted_by_user_id=update.submitted_by_user_id,
        update_type=update.update_type,  # type: ignore[arg-type]
        summary=update.summary,
        occurred_at=update.occurred_at,
        created_at=update.created_at,
    )


def _record_response(record: MedicalRecord) -> MedicalRecordResponse:
    return MedicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        title=record.title,
        category=record.category,
        summary=record.summary,
        recorded_at=record.recorded_at,
    )


def _medical_history_review_response(
    review: MedicalHistoryReview,
) -> MedicalHistoryReviewResponse:
    return MedicalHistoryReviewResponse(
        id=review.id,
        patient_id=review.patient_id,
        doctor_id=review.doctor_id,
        target_type=review.target_type,  # type: ignore[arg-type]
        target_id=review.target_id,
        action=review.action,  # type: ignore[arg-type]
        amendment_summary=review.amendment_summary,
        correction_request=review.correction_request,
        created_at=review.created_at,
    )


def _medication_response(medication: Medication) -> MedicationResponse:
    return MedicationResponse(
        id=medication.id,
        patient_id=medication.patient_id,
        clinical_event_id=medication.clinical_event_id,
        name=medication.name,
        dosage=medication.dosage,
        schedule=medication.schedule,
        status=medication.status,
        note=medication.note,
    )


def _prescription_medication_response(
    item: PrescriptionMedication,
) -> PrescriptionMedicationResponse:
    return PrescriptionMedicationResponse(
        id=item.id,
        medication_id=item.medication_id,
        name=item.name,
        dosage=item.dosage,
        schedule=item.schedule,
        start_date=item.start_date,
        end_date=item.end_date,
    )


def _prescription_response(prescription: Prescription) -> PrescriptionResponse:
    lines = sorted(prescription.medications, key=lambda item: item.name)
    return PrescriptionResponse(
        id=prescription.id,
        patient_id=prescription.patient_id,
        clinical_event_id=prescription.clinical_event_id,
        status=prescription.status,  # type: ignore[arg-type]
        issued_at=prescription.issued_at,
        notes=prescription.notes,
        created_at=prescription.created_at,
        updated_at=prescription.updated_at,
        medications=[_prescription_medication_response(item) for item in lines],
    )


def _reminder_type(reminder: MedicationReminder) -> str:
    value = reminder.metadata_json.get("reminder_type")
    return value if value in {"medication", "refill"} else "medication"


def _medication_reminder_response(reminder: MedicationReminder) -> MedicationReminderResponse:
    return MedicationReminderResponse(
        id=reminder.id,
        patient_id=reminder.patient_id,
        clinical_event_id=reminder.clinical_event_id,
        medication_id=reminder.medication_id,
        prescription_medication_id=reminder.prescription_medication_id,
        reminder_type=_reminder_type(reminder),  # type: ignore[arg-type]
        schedule_label=reminder.schedule_label,
        channel=reminder.channel,  # type: ignore[arg-type]
        status=reminder.status,  # type: ignore[arg-type]
        next_due_at=reminder.next_due_at,
        last_sent_at=reminder.last_sent_at,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )


def _notification_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        clinical_event_id=notification.clinical_event_id,
        notification_type=notification.notification_type,
        channel=notification.channel,  # type: ignore[arg-type]
        status=notification.status,  # type: ignore[arg-type]
        scheduled_for=notification.scheduled_for,
        sent_at=notification.sent_at,
        metadata_json=notification.metadata_json,
        created_at=notification.created_at,
        updated_at=notification.updated_at,
    )


def _imaging_asset_response(asset: MedicalImagingAsset) -> MedicalImagingAssetResponse:
    return MedicalImagingAssetResponse(
        id=asset.id,
        patient_id=asset.patient_id,
        clinical_event_id=asset.clinical_event_id,
        storage_provider=asset.storage_provider,  # type: ignore[arg-type]
        content_type=asset.content_type,
        file_extension=asset.file_extension,
        size_bytes=asset.size_bytes,
        uploaded_size_bytes=asset.uploaded_size_bytes,
        upload_status=asset.upload_status,  # type: ignore[arg-type]
        review_status=asset.review_status,  # type: ignore[arg-type]
        finding_summary=asset.finding_summary,
        measurement_summary=asset.measurement_summary,
        observed_at=asset.observed_at,
        treatment_relevance_date=asset.treatment_relevance_date,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        expires_at=asset.expires_at,
        uploaded_at=asset.uploaded_at,
        reviewed_at=asset.reviewed_at,
        safety_label=SYNTHETIC_DATA_LABEL,
    )


def _note_response(note: DoctorNote) -> DoctorNoteResponse:
    return DoctorNoteResponse(
        id=note.id,
        patient_id=note.patient_id,
        clinical_event_id=note.clinical_event_id,
        title=note.title,
        body=note.body,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _allergy_response(allergy: PatientAllergy) -> PatientAllergyResponse:
    return PatientAllergyResponse(
        id=allergy.id,
        patient_id=allergy.patient_id,
        label=allergy.label,
        reaction=allergy.reaction,
        severity=allergy.severity,  # type: ignore[arg-type]
        status=allergy.status,  # type: ignore[arg-type]
        created_at=allergy.created_at,
        updated_at=allergy.updated_at,
    )


def _chronic_disease_response(condition: ChronicDisease) -> ChronicDiseaseResponse:
    return ChronicDiseaseResponse(
        id=condition.id,
        patient_id=condition.patient_id,
        name=condition.name,
        status=condition.status,  # type: ignore[arg-type]
        diagnosed_on=condition.diagnosed_on,
        notes=condition.notes,
        created_at=condition.created_at,
        updated_at=condition.updated_at,
    )


def _visit_history_response(visit: VisitHistory) -> VisitHistoryResponse:
    return VisitHistoryResponse(
        id=visit.id,
        patient_id=visit.patient_id,
        clinical_event_id=visit.clinical_event_id,
        visit_type=visit.visit_type,
        title=visit.title,
        summary=visit.summary,
        occurred_at=visit.occurred_at,
        clinician_label=visit.clinician_label,
        created_at=visit.created_at,
        updated_at=visit.updated_at,
    )


def _diagnosis_response(diagnosis: Diagnosis) -> DiagnosisResponse:
    return DiagnosisResponse(
        id=diagnosis.id,
        patient_id=diagnosis.patient_id,
        clinical_event_id=diagnosis.clinical_event_id,
        label=diagnosis.label,
        status=diagnosis.status,  # type: ignore[arg-type]
        diagnosed_on=diagnosis.diagnosed_on,
        notes=diagnosis.notes,
        created_at=diagnosis.created_at,
        updated_at=diagnosis.updated_at,
    )


def _assessment_response(assessment: SimulatedAssessment) -> AssessmentResponse:
    return AssessmentResponse(
        assessment_id=assessment.id,
        mode="simulated",
        status="completed",
        risk_band=assessment.risk_band,  # type: ignore[arg-type]
        demo_score=float(assessment.demo_score),
        input_completeness=assessment.input_completeness,  # type: ignore[arg-type]
        model_version=assessment.model_version,
        limitations=list(assessment.limitations),
        recommended_next_steps=list(assessment.recommended_next_steps),
        safety_label=SIMULATION_LABEL,
        created_at=assessment.created_at,
    )


def _completion_map(tasks: list[RecoveryTask]) -> dict[uuid.UUID, RecoveryTaskCompletion]:
    completions: dict[uuid.UUID, RecoveryTaskCompletion] = {}
    for task in tasks:
        if task.completions:
            completions[task.id] = task.completions[0]
    return completions


def _recovery_task_response(
    task: RecoveryTask,
    completions: dict[uuid.UUID, RecoveryTaskCompletion],
) -> RecoveryTaskResponse:
    completion = completions.get(task.id)
    notification_status = None
    if task.category == "medication":
        notification_status = (
            f"Local demo notification shell scheduled for {task.notification_time}"
            if task.notification_time
            else "Local demo notification shell available"
        )
    return RecoveryTaskResponse(
        task_id=task.id,
        plan_id=task.plan_id,
        category=task.category,  # type: ignore[arg-type]
        title=task.title,
        detail=task.detail,
        due_label=task.due_label,
        notification_time=task.notification_time,
        medication_id=task.medication_id,
        is_completed=completion is not None,
        completed_at=completion.completed_at if completion is not None else None,
        notification_status=notification_status,
    )


def _recovery_plan_response(plan: RecoveryPlan) -> RecoveryPlanResponse:
    tasks = list(plan.tasks)
    completions = _completion_map(tasks)
    completed_task_count = len(completions)
    task_count = len(tasks)
    completion_percent = 0
    if task_count > 0:
        completion_percent = round(completed_task_count * 100 / task_count)
    return RecoveryPlanResponse(
        plan_id=plan.id,
        patient_id=plan.patient_id,
        clinical_event_id=plan.clinical_event_id,
        title=plan.title,
        instructions=plan.instructions,
        status=plan.status,  # type: ignore[arg-type]
        review_status=plan.review_status,  # type: ignore[arg-type]
        safety_label=SYNTHETIC_DATA_LABEL,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        submitted_at=plan.submitted_at,
        reviewed_at=plan.reviewed_at,
        approved_at=plan.approved_at,
        activated_at=plan.activated_at,
        completed_at=plan.completed_at,
        progress_summary=RecoveryPlanProgressResponse(
            task_count=task_count,
            completed_task_count=completed_task_count,
            remaining_task_count=task_count - completed_task_count,
            completion_percent=completion_percent,
        ),
        tasks=[_recovery_task_response(task, completions) for task in tasks],
    )


def _record_audit_event(
    db: DbSession,
    *,
    actor_user_id: uuid.UUID,
    patient_id: uuid.UUID | None,
    event_type: str,
    resource_type: str,
    resource_id: uuid.UUID | None,
    metadata: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            patient_id=patient_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
    )


def _contains_pattern(message: str, patterns: tuple[str, ...]) -> bool:
    normalized = message.lower()
    return any(re.search(pattern, normalized) for pattern in patterns)


def _response_chunks(content: str) -> list[str]:
    words = content.split()
    if not words:
        return [content]
    chunks: list[str] = []
    for index in range(0, len(words), 9):
        chunks.append(" ".join(words[index : index + 9]))
    return chunks


def _fallback_content(reason: str) -> str:
    if reason == "unsafe_prompt":
        return UNSAFE_PROMPT_MESSAGE
    if reason == "red_flag":
        return RED_FLAG_MESSAGE
    return DEEPSEEK_FALLBACK_MESSAGE


def _unsafe_consultation_fields(
    specialty: str,
    question_summary: str,
) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    for field, value in (
        ("specialty", specialty),
        ("question_summary", question_summary),
    ):
        if _contains_pattern(value, UNSAFE_PROMPT_PATTERNS):
            details.append(
                {
                    "field": field,
                    "code": "unsafe_content",
                    "message": "Use synthetic, non-identifying consultation text.",
                }
            )
    return details


def _consultation_response(request: ConsultationRequest) -> ConsultationResponse:
    return ConsultationResponse(
        consultation_id=request.id,
        patient_id=request.patient_id,
        clinical_event_id=request.clinical_event_id,
        specialty=request.specialty,
        question_summary=request.question_summary,
        priority=request.priority,  # type: ignore[arg-type]
        status=request.status,  # type: ignore[arg-type]
        safety_label=SYNTHETIC_DATA_LABEL,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def _chat_thread_for_request(
    thread_id: str,
    profile: PatientProfile,
    user: CurrentUser,
    db: DbSession,
) -> ChatThread:
    thread_uuid: uuid.UUID | None = None
    try:
        thread_uuid = uuid.UUID(thread_id)
    except ValueError:
        thread_uuid = None

    if thread_uuid is not None:
        thread = db.scalar(
            select(ChatThread).where(
                ChatThread.id == thread_uuid,
                ChatThread.patient_id == profile.id,
            )
        )
        if thread is None:
            raise _neutral_not_found()
        return thread

    if thread_id != DEFAULT_CHAT_THREAD_KEY:
        raise _neutral_not_found()
    thread = db.scalar(
        select(ChatThread).where(
            ChatThread.patient_id == profile.id,
            ChatThread.thread_key == DEFAULT_CHAT_THREAD_KEY,
        )
    )
    if thread is not None:
        return thread
    thread = ChatThread(
        patient_id=profile.id,
        created_by_user_id=user.id,
        thread_key=DEFAULT_CHAT_THREAD_KEY,
        title="Educational question preparation",
    )
    db.add(thread)
    db.flush()
    return thread


def _check_chat_rate_limit(user: CurrentUser, db: DbSession, settings: AppSettings) -> None:
    now = datetime.now(UTC)
    limit = db.get(ChatRateLimit, user.id)
    if limit is None:
        db.add(ChatRateLimit(user_id=user.id, window_start=now, message_count=1))
        return
    window_age = (now - limit.window_start).total_seconds()
    if window_age >= settings.chat_rate_limit_window_seconds:
        limit.window_start = now
        limit.message_count = 1
        return
    if limit.message_count >= settings.chat_rate_limit_messages:
        raise ApiError(
            429,
            "rate_limited",
            "Educational chat is temporarily rate limited. Please try again shortly.",
        )
    limit.message_count += 1


def _record_chat_exchange(
    db: DbSession,
    *,
    thread: ChatThread,
    user: CurrentUser,
    message: str,
    safety_category: str,
    fallback_reason: str | None,
    model: str,
) -> tuple[ChatMessage, ChatMessage]:
    now = datetime.now(UTC)
    prompt_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
    user_message = ChatMessage(
        thread_id=thread.id,
        patient_id=thread.patient_id,
        actor_user_id=user.id,
        role="user",
        prompt_hash=prompt_hash,
        prompt_char_count=len(message),
        safety_category=safety_category,
        fallback_reason=fallback_reason,
        model=None,
        metadata_json={"content_redacted": True},
        created_at=now,
    )
    assistant_message = ChatMessage(
        thread_id=thread.id,
        patient_id=thread.patient_id,
        actor_user_id=user.id,
        role="assistant",
        prompt_hash=None,
        prompt_char_count=None,
        safety_category=safety_category,
        fallback_reason=fallback_reason,
        model=model,
        metadata_json={"content_redacted": True, "response_mode": "stream_ready"},
        created_at=now,
    )
    thread.last_message_at = now
    db.add_all([user_message, assistant_message])
    return user_message, assistant_message


def _authorized_patient(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> PatientProfile:
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
    return profile


def _require_doctor_user(user: CurrentUser) -> None:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()


def _authorized_clinical_event(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, ClinicalEvent]:
    profile = _authorized_patient(patient_id, user, db)
    event = db.scalar(
        select(ClinicalEvent).where(
            ClinicalEvent.id == event_id,
            ClinicalEvent.patient_id == profile.id,
        )
    )
    if event is None:
        raise _neutral_not_found()
    return profile, event


def _optional_clinical_event(
    clinical_event_id: uuid.UUID | None,
    *,
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> ClinicalEvent | None:
    if clinical_event_id is None:
        return None
    _, event = _authorized_clinical_event(patient_id, clinical_event_id, user, db)
    return event


def _authorized_history_review_target(
    patient_id: uuid.UUID,
    target_type: str,
    target_id: uuid.UUID,
    db: DbSession,
) -> None:
    model_by_type = {
        "allergy": PatientAllergy,
        "chronic_disease": ChronicDisease,
        "medical_record": MedicalRecord,
    }
    model = model_by_type.get(target_type)
    if model is None:
        raise _neutral_not_found()
    target = db.scalar(select(model).where(model.id == target_id, model.patient_id == patient_id))
    if target is None:
        raise _neutral_not_found()


def _authorized_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, PatientAllergy]:
    profile = _authorized_patient(patient_id, user, db)
    allergy = db.scalar(
        select(PatientAllergy).where(
            PatientAllergy.id == allergy_id,
            PatientAllergy.patient_id == profile.id,
        )
    )
    if allergy is None:
        raise _neutral_not_found()
    return profile, allergy


def _authorized_chronic_disease(
    patient_id: uuid.UUID,
    condition_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, ChronicDisease]:
    profile = _authorized_patient(patient_id, user, db)
    condition = db.scalar(
        select(ChronicDisease).where(
            ChronicDisease.id == condition_id,
            ChronicDisease.patient_id == profile.id,
        )
    )
    if condition is None:
        raise _neutral_not_found()
    return profile, condition


def _authorized_visit_history(
    patient_id: uuid.UUID,
    visit_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, VisitHistory]:
    profile = _authorized_patient(patient_id, user, db)
    visit = db.scalar(
        select(VisitHistory).where(
            VisitHistory.id == visit_id,
            VisitHistory.patient_id == profile.id,
        )
    )
    if visit is None:
        raise _neutral_not_found()
    return profile, visit


def _authorized_diagnosis(
    patient_id: uuid.UUID,
    diagnosis_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, Diagnosis]:
    profile = _authorized_patient(patient_id, user, db)
    diagnosis = db.scalar(
        select(Diagnosis).where(Diagnosis.id == diagnosis_id, Diagnosis.patient_id == profile.id)
    )
    if diagnosis is None:
        raise _neutral_not_found()
    return profile, diagnosis


def _authorized_doctor_note(
    patient_id: uuid.UUID,
    note_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, DoctorNote]:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    note = db.scalar(
        select(DoctorNote).where(DoctorNote.id == note_id, DoctorNote.patient_id == profile.id)
    )
    if note is None:
        raise _neutral_not_found()
    return profile, note


def _authorized_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, Medication]:
    profile = _authorized_patient(patient_id, user, db)
    medication = db.scalar(
        select(Medication).where(
            Medication.id == medication_id,
            Medication.patient_id == profile.id,
        )
    )
    if medication is None:
        raise _neutral_not_found()
    return profile, medication


def _authorized_prescription(
    patient_id: uuid.UUID,
    prescription_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, Prescription]:
    profile = _authorized_patient(patient_id, user, db)
    prescription = db.scalar(
        select(Prescription)
        .options(selectinload(Prescription.medications))
        .where(Prescription.id == prescription_id, Prescription.patient_id == profile.id)
    )
    if prescription is None:
        raise _neutral_not_found()
    return profile, prescription


def _authorized_medication_reminder(
    patient_id: uuid.UUID,
    reminder_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, MedicationReminder]:
    profile = _authorized_patient(patient_id, user, db)
    reminder = db.scalar(
        select(MedicationReminder).where(
            MedicationReminder.id == reminder_id,
            MedicationReminder.patient_id == profile.id,
        )
    )
    if reminder is None:
        raise _neutral_not_found()
    return profile, reminder


def _authorized_imaging_asset(
    patient_id: uuid.UUID,
    asset_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, MedicalImagingAsset]:
    profile = _authorized_patient(patient_id, user, db)
    asset = db.scalar(
        select(MedicalImagingAsset).where(
            MedicalImagingAsset.id == asset_id,
            MedicalImagingAsset.patient_id == profile.id,
        )
    )
    if asset is None:
        raise _neutral_not_found()
    return profile, asset


def _apply_demographics_update(
    profile: PatientProfile,
    request: PatientDemographicsUpdateRequest,
) -> list[str]:
    updated_fields: list[str] = []
    if request.birth_date is not None and profile.birth_date != request.birth_date:
        profile.birth_date = request.birth_date
        profile.birth_year = request.birth_date.year
        updated_fields.extend(["birth_date", "birth_year"])
    if request.gender is not None and profile.gender != request.gender:
        profile.gender = request.gender
        profile.sex = request.gender
        updated_fields.extend(["gender", "sex"])
    for field in (
        "display_name",
        "birth_year",
        "sex",
        "contact_phone",
        "emergency_contact_name",
        "emergency_contact_phone",
        "preferred_language",
        "contact_preference",
        "avatar_url",
        "country",
        "province",
        "city",
        "home_address",
        "height_cm",
        "weight_kg",
        "medical_history_setup_completed",
    ):
        value = getattr(request, field)
        if value is not None and getattr(profile, field) != value:
            setattr(profile, field, value)
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
                    "message": "Provide at least one changed profile field.",
                }
            ],
        )
    return updated_fields


def _validate_prescription_request(
    request: PrescriptionRequest,
    *,
    patient_id: uuid.UUID,
    db: DbSession,
) -> None:
    for index, item in enumerate(request.medications):
        if (
            item.start_date is not None
            and item.end_date is not None
            and item.end_date < item.start_date
        ):
            raise ApiError(
                422,
                "validation_failed",
                "The request could not be validated.",
                [
                    {
                        "field": f"medications.{index}.end_date",
                        "code": "before_start_date",
                        "message": "End date must be on or after start date.",
                    }
                ],
            )
        if item.medication_id is not None:
            medication = db.scalar(
                select(Medication).where(
                    Medication.id == item.medication_id,
                    Medication.patient_id == patient_id,
                )
            )
            if medication is None:
                raise _neutral_not_found()


def _replace_prescription_medications(
    prescription: Prescription,
    request: PrescriptionRequest,
) -> None:
    prescription.medications.clear()
    for item in request.medications:
        prescription.medications.append(
            PrescriptionMedication(
                medication_id=item.medication_id,
                name=item.name,
                dosage=item.dosage,
                schedule=item.schedule,
                start_date=item.start_date,
                end_date=item.end_date,
                metadata_json={},
            )
        )


def _validate_medication_reminder_request(
    request: MedicationReminderRequest,
    *,
    patient_id: uuid.UUID,
    db: DbSession,
) -> None:
    if request.medication_id is None and request.prescription_medication_id is None:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "medication_id",
                    "code": "required_reference",
                    "message": "Reference a medication or prescription medication.",
                }
            ],
        )
    if request.medication_id is not None:
        medication = db.scalar(
            select(Medication).where(
                Medication.id == request.medication_id,
                Medication.patient_id == patient_id,
            )
        )
        if medication is None:
            raise _neutral_not_found()
    if request.prescription_medication_id is not None:
        prescription_medication = db.scalar(
            select(PrescriptionMedication)
            .join(Prescription)
            .where(
                PrescriptionMedication.id == request.prescription_medication_id,
                Prescription.patient_id == patient_id,
            )
        )
        if prescription_medication is None:
            raise _neutral_not_found()


def _apply_medication_reminder_request(
    reminder: MedicationReminder,
    request: MedicationReminderRequest,
) -> None:
    reminder.clinical_event_id = request.clinical_event_id
    reminder.medication_id = request.medication_id
    reminder.prescription_medication_id = request.prescription_medication_id
    reminder.schedule_label = request.schedule_label
    reminder.channel = request.channel
    reminder.status = request.status
    reminder.next_due_at = request.next_due_at
    reminder.metadata_json = {"reminder_type": request.reminder_type}


def _queue_reminder_notification(
    db: DbSession,
    *,
    profile: PatientProfile,
    reminder: MedicationReminder,
) -> Notification | None:
    if reminder.status != "active":
        return None
    notification = Notification(
        user_id=profile.user_id,
        patient_id=profile.id,
        clinical_event_id=reminder.clinical_event_id,
        notification_type=f"{_reminder_type(reminder)}_reminder",
        channel="in_app",
        status="queued",
        scheduled_for=reminder.next_due_at,
        metadata_json={
            "source": "phase2_in_app_queue",
            "reminder_id": str(reminder.id),
            "reminder_type": _reminder_type(reminder),
            "medication_id": str(reminder.medication_id) if reminder.medication_id else None,
            "prescription_medication_id": (
                str(reminder.prescription_medication_id)
                if reminder.prescription_medication_id
                else None
            ),
        },
    )
    db.add(notification)
    return notification


def _cancel_queued_reminder_notifications(
    db: DbSession,
    *,
    profile: PatientProfile,
    reminder: MedicationReminder,
) -> int:
    notifications = db.scalars(
        select(Notification).where(
            Notification.patient_id == profile.id,
            Notification.status == "queued",
            Notification.metadata_json["reminder_id"].astext == str(reminder.id),
        )
    ).all()
    for notification in notifications:
        notification.status = "cancelled"
    return len(notifications)


def _authorized_recovery_plan(
    patient_id: uuid.UUID,
    plan_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> tuple[PatientProfile, RecoveryPlan]:
    profile = _authorized_patient(patient_id, user, db)
    plan = db.scalar(
        select(RecoveryPlan)
        .options(selectinload(RecoveryPlan.tasks).selectinload(RecoveryTask.completions))
        .where(RecoveryPlan.id == plan_id, RecoveryPlan.patient_id == profile.id)
    )
    if plan is None:
        raise _neutral_not_found()
    return profile, plan


def _validate_recovery_tasks(
    tasks: list[RecoveryTaskInput],
    *,
    patient_id: uuid.UUID,
    db: DbSession,
) -> None:
    categories = {task.category for task in tasks}
    if not {"medication", "exercise", "diet", "follow_up"}.issubset(categories):
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "tasks",
                    "code": "missing_required_categories",
                    "message": "Include medication, exercise, diet, and follow-up tasks.",
                }
            ],
        )
    for task in tasks:
        if task.category not in RECOVERY_TASK_CATEGORIES:
            raise ApiError(
                422,
                "validation_failed",
                "The request could not be validated.",
            )
        if task.category == "medication" and task.notification_time is None:
            raise ApiError(
                422,
                "validation_failed",
                "The request could not be validated.",
                [
                    {
                        "field": "tasks.notification_time",
                        "code": "required_for_medication",
                        "message": "Medication tasks need a local notification time label.",
                    }
                ],
            )
        if task.medication_id is not None:
            medication = db.scalar(
                select(Medication).where(
                    Medication.id == task.medication_id,
                    Medication.patient_id == patient_id,
                )
            )
            if medication is None:
                raise _neutral_not_found()


def _replace_recovery_tasks(
    plan: RecoveryPlan,
    tasks: list[RecoveryTaskInput],
) -> None:
    plan.tasks.clear()
    for index, task in enumerate(tasks):
        plan.tasks.append(
            RecoveryTask(
                patient_id=plan.patient_id,
                medication_id=task.medication_id,
                category=task.category,
                title=task.title,
                detail=task.detail,
                due_label=task.due_label,
                notification_time=task.notification_time,
                sort_order=index,
            )
        )


def _recovery_plan_audit_metadata(
    plan: RecoveryPlan,
    *,
    source: str,
    replaced_active_count: int = 0,
) -> dict[str, object]:
    tasks = list(plan.tasks)
    completions = _completion_map(tasks)
    return {
        "status": plan.status,
        "review_status": plan.review_status,
        "task_count": len(tasks),
        "completed_task_count": len(completions),
        "task_categories": sorted({task.category for task in tasks}),
        "replaced_active_count": replaced_active_count,
        "source": source,
        "clinical_event_id": str(plan.clinical_event_id) if plan.clinical_event_id else None,
    }


def _ensure_recovery_plan_editable(plan: RecoveryPlan) -> None:
    if plan.status != "draft" or plan.review_status == "in_review":
        raise ApiError(
            409,
            "conflict",
            "This recovery plan cannot be edited in its current review state.",
        )


def _complete_other_active_recovery_plans(
    profile: PatientProfile,
    plan: RecoveryPlan,
    db: DbSession,
) -> int:
    active_query = select(RecoveryPlan).where(
        RecoveryPlan.patient_id == profile.id,
        RecoveryPlan.status == "active",
        RecoveryPlan.id != plan.id,
    )
    if plan.clinical_event_id is not None:
        active_query = active_query.where(RecoveryPlan.clinical_event_id == plan.clinical_event_id)
    else:
        active_query = active_query.where(RecoveryPlan.clinical_event_id.is_(None))
    active_plans = db.scalars(active_query).all()
    now = datetime.now(UTC)
    for active_plan in active_plans:
        active_plan.status = "completed"
        active_plan.completed_at = now
    return len(active_plans)


def _approve_recovery_plan(
    plan: RecoveryPlan,
    profile: PatientProfile,
    user: CurrentUser,
    db: DbSession,
    *,
    source: str,
) -> int:
    replaced_active_count = _complete_other_active_recovery_plans(profile, plan, db)
    now = datetime.now(UTC)
    plan.status = "active"
    plan.review_status = "approved"
    plan.review_actor_user_id = user.id
    plan.reviewed_at = now
    plan.approved_at = now
    plan.activated_at = now
    plan.completed_at = None
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="recovery_plan_approved",
        resource_type="recovery_plan",
        resource_id=plan.id,
        metadata=_recovery_plan_audit_metadata(
            plan,
            source=source,
            replaced_active_count=replaced_active_count,
        ),
    )
    return replaced_active_count


def _validate_demo_asset_presign_request(request: DemoAssetPresignRequest) -> str:
    content_type = request.content_type.strip().lower()
    allowed_extensions = DEMO_UPLOAD_ALLOWED_EXTENSIONS.get(content_type)
    if allowed_extensions is None:
        raise ApiError(
            415,
            "unsupported_media_type",
            "Only PNG, JPEG, or DICOM demo upload metadata is supported.",
            [
                {
                    "field": "content_type",
                    "code": "unsupported_value",
                    "message": "Use image/png, image/jpeg, or application/dicom.",
                }
            ],
        )
    if request.size_bytes > DEMO_UPLOAD_MAX_SIZE_BYTES:
        raise ApiError(
            413,
            "payload_too_large",
            "Demo upload metadata exceeds the maximum supported size.",
            [
                {
                    "field": "size_bytes",
                    "code": "too_large",
                    "message": "Demo uploads are limited to 10485760 bytes.",
                }
            ],
        )
    extension = request.filename.rsplit(".", 1)[-1].lower() if "." in request.filename else ""
    if extension not in allowed_extensions:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "filename",
                    "code": "content_type_mismatch",
                    "message": "The filename extension must match the content type.",
                }
            ],
        )
    return content_type


def _validate_imaging_presign_request(request: MedicalImagingPresignRequest) -> tuple[str, str]:
    content_type = request.content_type.strip().lower()
    allowed_extensions = DEMO_UPLOAD_ALLOWED_EXTENSIONS.get(content_type)
    if allowed_extensions is None:
        raise ApiError(
            415,
            "unsupported_media_type",
            "Only PNG, JPEG, or DICOM imaging upload metadata is supported.",
            [
                {
                    "field": "content_type",
                    "code": "unsupported_value",
                    "message": "Use image/png, image/jpeg, or application/dicom.",
                }
            ],
        )
    if request.size_bytes > DEMO_UPLOAD_MAX_SIZE_BYTES:
        raise ApiError(
            413,
            "payload_too_large",
            "Imaging upload metadata exceeds the maximum supported size.",
            [
                {
                    "field": "size_bytes",
                    "code": "too_large",
                    "message": "Imaging uploads are limited to 10485760 bytes.",
                }
            ],
        )
    extension = request.filename.rsplit(".", 1)[-1].lower() if "." in request.filename else ""
    if extension not in allowed_extensions:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "filename",
                    "code": "content_type_mismatch",
                    "message": "The filename extension must match the content type.",
                }
            ],
        )
    return content_type, extension


def _validate_imaging_completion(
    asset: MedicalImagingAsset,
    request: MedicalImagingCompleteRequest,
) -> None:
    if request.uploaded_size_bytes != asset.size_bytes:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "uploaded_size_bytes",
                    "code": "size_mismatch",
                    "message": "Uploaded size must match the prepared upload size.",
                }
            ],
        )
    if asset.upload_status == "pending_upload" and asset.expires_at < datetime.now(UTC):
        asset.upload_status = "expired"
        raise ApiError(
            409,
            "conflict",
            "The prepared upload has expired.",
            [
                {
                    "field": "asset_id",
                    "code": "upload_expired",
                    "message": "Request a new upload before completing this asset.",
                }
            ],
        )


@router.get("/me/dashboard", response_model=DashboardResponse)
def own_dashboard(user: CurrentUser, db: DbSession) -> DashboardResponse:
    if user.role not in {UserRole.doctor, UserRole.patient}:
        raise ApiError(403, "forbidden", "This role is not enabled for this workflow.")
    snapshot = db.scalar(select(DashboardSnapshot).where(DashboardSnapshot.user_id == user.id))
    if snapshot is None:
        return DashboardResponse(role=user.role, data={})
    return DashboardResponse(role=user.role, data=snapshot.payload)


@router.get("/patient/me/contacts", response_model=PatientDoctorContactListResponse)
def own_patient_contacts(
    user: CurrentUser,
    db: DbSession,
) -> PatientDoctorContactListResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    doctors = db.scalars(
        select(DoctorProfile)
        .join(CareRelationship)
        .where(
            CareRelationship.patient_id == user.patient_profile.id,
            CareRelationship.is_active.is_(True),
        )
        .order_by(DoctorProfile.display_name, DoctorProfile.id)
    ).all()
    return PatientDoctorContactListResponse(
        items=[
            PatientDoctorContactResponse(
                doctor_id=doctor.id,
                display_name=doctor.display_name,
                title=doctor.title,
                hospital_name=doctor.hospital_name,
                specialty=doctor.specialty,
                department=doctor.department,
                avatar_url=doctor.avatar_url,
            )
            for doctor in doctors
        ]
    )


@router.get("/patients", response_model=PatientListResponse)
def assigned_patients(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=50),
    q: str | None = Query(default=None, min_length=1, max_length=80),
) -> PatientListResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    normalized_query = q.strip() if q else None
    filters = [
        CareRelationship.doctor_id == user.doctor_profile.id,
        CareRelationship.is_active.is_(True),
    ]
    if normalized_query:
        pattern = f"%{normalized_query}%"
        filters.append(
            PatientProfile.display_name.ilike(pattern)
            | PatientProfile.synthetic_identifier.ilike(pattern)
        )
    profiles = db.scalars(
        select(PatientProfile)
        .join(CareRelationship)
        .where(*filters)
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


@router.post("/patients/connect", response_model=PatientProfileResponse)
def connect_patient_by_code(
    request: PatientConnectRequest,
    user: CurrentUser,
    db: DbSession,
) -> PatientProfileResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    patient_code = request.patient_code.strip()
    profile = db.scalar(
        select(PatientProfile).where(
            func.lower(PatientProfile.synthetic_identifier) == patient_code.lower()
        )
    )
    if profile is None:
        raise _neutral_not_found()
    relationship = db.scalar(
        select(CareRelationship).where(
            CareRelationship.doctor_id == user.doctor_profile.id,
            CareRelationship.patient_id == profile.id,
        )
    )
    created = relationship is None
    reactivated = False
    if relationship is None:
        relationship = CareRelationship(
            doctor_id=user.doctor_profile.id,
            patient_id=profile.id,
            is_active=True,
        )
        db.add(relationship)
        db.flush()
    elif not relationship.is_active:
        relationship.is_active = True
        relationship.revoked_at = None
        reactivated = True
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="care_relationship_connected",
        resource_type="care_relationship",
        resource_id=relationship.id,
        metadata={
            "actor_role": user.role.value,
            "created": created,
            "reactivated": reactivated,
            "patient_code_supplied": True,
        },
    )
    db.commit()
    db.refresh(profile)
    return _patient_response(profile)


@router.post("/patients/connect/preview", response_model=PatientMatchPreviewResponse)
def preview_patient_by_code(
    request: PatientConnectRequest,
    user: CurrentUser,
    db: DbSession,
) -> PatientMatchPreviewResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    patient_code = request.patient_code.strip()
    profile = db.scalar(
        select(PatientProfile).where(
            func.lower(PatientProfile.synthetic_identifier) == patient_code.lower()
        )
    )
    if profile is None:
        raise _neutral_not_found()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="patient_match_previewed",
        resource_type="patient_profile",
        resource_id=profile.id,
        metadata={"actor_role": user.role.value, "patient_code_supplied": True},
    )
    db.commit()
    suffix = profile.synthetic_identifier[-4:]
    return PatientMatchPreviewResponse(
        display_name=profile.display_name,
        masked_patient_code=f"Patient ID ending in {suffix}",
    )


@router.get("/patients/{patient_id}", response_model=PatientProfileResponse)
def patient_summary(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> PatientProfileResponse:
    return _patient_response(_authorized_patient(patient_id, user, db))


@router.patch("/patients/{patient_id}/profile", response_model=PatientProfileResponse)
def update_patient_profile(
    patient_id: uuid.UUID,
    request: PatientDemographicsUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> PatientProfileResponse:
    profile = _authorized_patient(patient_id, user, db)
    updated_fields = _apply_demographics_update(profile, request)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="patient_profile_updated",
        resource_type="patient_profile",
        resource_id=profile.id,
        metadata={"fields": updated_fields, "actor_role": user.role.value},
    )
    db.commit()
    db.refresh(profile)
    return _patient_response(profile)


@router.get("/patients/{patient_id}/clinical-events", response_model=ClinicalEventListResponse)
def patient_clinical_events(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> ClinicalEventListResponse:
    profile = _authorized_patient(patient_id, user, db)
    events = db.scalars(
        select(ClinicalEvent)
        .where(ClinicalEvent.patient_id == profile.id)
        .order_by(ClinicalEvent.updated_at.desc())
    ).all()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="clinical_events_listed",
        resource_type="clinical_event",
        resource_id=None,
        metadata={
            "actor_role": user.role.value,
            "event_count": len(events),
            "statuses": sorted({event.status for event in events}),
        },
    )
    db.commit()
    return ClinicalEventListResponse(
        items=[_clinical_event_response(event, db) for event in events]
    )


@router.post("/patients/{patient_id}/clinical-events", response_model=ClinicalEventResponse)
def create_patient_clinical_event(
    patient_id: uuid.UUID,
    request: ClinicalEventRequest,
    user: CurrentUser,
    db: DbSession,
) -> ClinicalEventResponse:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    event = ClinicalEvent(
        patient_id=profile.id,
        doctor_id=user.doctor_profile.id,
        title=request.title,
        chief_complaint=request.chief_complaint,
        symptom_summary=request.symptom_summary,
        diagnosis_summary=request.diagnosis_summary,
        onset_date=request.onset_date,
        status=request.status,
        metadata_json={"source": "phase2_workflow_clarification"},
    )
    db.add(event)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="clinical_event_created",
        resource_type="clinical_event",
        resource_id=event.id,
        metadata={
            "actor_role": user.role.value,
            "status": event.status,
            "fields": [
                "title",
                "chief_complaint",
                "symptom_summary",
                "diagnosis_summary",
                "onset_date",
                "status",
            ],
        },
    )
    db.commit()
    db.refresh(event)
    return _clinical_event_response(event, db)


@router.get(
    "/patients/{patient_id}/clinical-events/{event_id}",
    response_model=ClinicalEventResponse,
)
def patient_clinical_event_detail(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> ClinicalEventResponse:
    profile, event = _authorized_clinical_event(patient_id, event_id, user, db)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="clinical_event_read",
        resource_type="clinical_event",
        resource_id=event.id,
        metadata={"actor_role": user.role.value, "status": event.status},
    )
    db.commit()
    return _clinical_event_response(event, db)


@router.put(
    "/patients/{patient_id}/clinical-events/{event_id}",
    response_model=ClinicalEventResponse,
)
def update_patient_clinical_event(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    request: ClinicalEventRequest,
    user: CurrentUser,
    db: DbSession,
) -> ClinicalEventResponse:
    _require_doctor_user(user)
    profile, event = _authorized_clinical_event(patient_id, event_id, user, db)
    event.title = request.title
    event.chief_complaint = request.chief_complaint
    event.symptom_summary = request.symptom_summary
    event.diagnosis_summary = request.diagnosis_summary
    event.onset_date = request.onset_date
    event.status = request.status
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="clinical_event_updated",
        resource_type="clinical_event",
        resource_id=event.id,
        metadata={
            "actor_role": user.role.value,
            "status": event.status,
            "fields": [
                "title",
                "chief_complaint",
                "symptom_summary",
                "diagnosis_summary",
                "onset_date",
                "status",
            ],
        },
    )
    db.commit()
    db.refresh(event)
    return _clinical_event_response(event, db)


@router.get("/patients/{patient_id}/records", response_model=MedicalRecordListResponse)
def patient_records(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> MedicalRecordListResponse:
    profile = _authorized_patient(patient_id, user, db)
    records = db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == profile.id)
        .order_by(MedicalRecord.recorded_at.desc())
    ).all()
    return MedicalRecordListResponse(items=[_record_response(item) for item in records])


@router.post("/patients/{patient_id}/records", response_model=MedicalRecordResponse)
def create_patient_record(
    patient_id: uuid.UUID,
    request: MedicalRecordRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicalRecordResponse:
    profile = _authorized_patient(patient_id, user, db)
    record = MedicalRecord(
        patient_id=profile.id,
        title=request.title,
        category=request.category,
        summary=request.summary,
        recorded_at=datetime.now(UTC),
    )
    db.add(record)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medical_record_created",
        resource_type="medical_record",
        resource_id=record.id,
        metadata={"category": request.category, "actor_role": user.role.value},
    )
    db.commit()
    db.refresh(record)
    return _record_response(record)


@router.get("/patients/{patient_id}/medications", response_model=MedicationListResponse)
def patient_medications(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> MedicationListResponse:
    profile = _authorized_patient(patient_id, user, db)
    medications = db.scalars(
        select(Medication).where(Medication.patient_id == profile.id).order_by(Medication.name)
    ).all()
    return MedicationListResponse(items=[_medication_response(item) for item in medications])


@router.post("/patients/{patient_id}/medications", response_model=MedicationResponse)
def create_patient_medication(
    patient_id: uuid.UUID,
    request: MedicationRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicationResponse:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    medication = Medication(
        patient_id=profile.id,
        clinical_event_id=event.id if event else None,
        name=request.name,
        dosage=request.dosage,
        schedule=request.schedule,
        status=request.status,
        note=request.note,
    )
    db.add(medication)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medication_created",
        resource_type="medication",
        resource_id=medication.id,
        metadata={
            "status": medication.status,
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(medication)
    return _medication_response(medication)


@router.put("/patients/{patient_id}/medications/{medication_id}", response_model=MedicationResponse)
def update_patient_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    request: MedicationRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicationResponse:
    _require_doctor_user(user)
    profile, medication = _authorized_medication(patient_id, medication_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    medication.clinical_event_id = event.id if event else None
    medication.name = request.name
    medication.dosage = request.dosage
    medication.schedule = request.schedule
    medication.status = request.status
    medication.note = request.note
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medication_updated",
        resource_type="medication",
        resource_id=medication.id,
        metadata={
            "status": medication.status,
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(medication)
    return _medication_response(medication)


@router.delete("/patients/{patient_id}/medications/{medication_id}", status_code=204)
def delete_patient_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    _require_doctor_user(user)
    profile, medication = _authorized_medication(patient_id, medication_id, user, db)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medication_deleted",
        resource_type="medication",
        resource_id=medication.id,
        metadata={"actor_role": user.role.value},
    )
    db.delete(medication)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/patients/{patient_id}/prescriptions", response_model=PrescriptionListResponse)
def patient_prescriptions(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> PrescriptionListResponse:
    profile = _authorized_patient(patient_id, user, db)
    prescriptions = db.scalars(
        select(Prescription)
        .options(selectinload(Prescription.medications))
        .where(Prescription.patient_id == profile.id)
        .order_by(Prescription.created_at.desc())
    ).all()
    return PrescriptionListResponse(items=[_prescription_response(item) for item in prescriptions])


@router.post("/patients/{patient_id}/prescriptions", response_model=PrescriptionResponse)
def create_patient_prescription(
    patient_id: uuid.UUID,
    request: PrescriptionRequest,
    user: CurrentUser,
    db: DbSession,
) -> PrescriptionResponse:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    _validate_prescription_request(request, patient_id=profile.id, db=db)
    prescription = Prescription(
        patient_id=profile.id,
        clinical_event_id=event.id if event else None,
        prescribed_by_user_id=user.id,
        status=request.status,
        issued_at=request.issued_at,
        notes=request.notes,
    )
    db.add(prescription)
    db.flush()
    _replace_prescription_medications(prescription, request)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="prescription_created",
        resource_type="prescription",
        resource_id=prescription.id,
        metadata={
            "status": prescription.status,
            "line_count": len(request.medications),
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(prescription)
    return _prescription_response(prescription)


@router.put(
    "/patients/{patient_id}/prescriptions/{prescription_id}",
    response_model=PrescriptionResponse,
)
def update_patient_prescription(
    patient_id: uuid.UUID,
    prescription_id: uuid.UUID,
    request: PrescriptionRequest,
    user: CurrentUser,
    db: DbSession,
) -> PrescriptionResponse:
    _require_doctor_user(user)
    profile, prescription = _authorized_prescription(patient_id, prescription_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    _validate_prescription_request(request, patient_id=profile.id, db=db)
    prescription.clinical_event_id = event.id if event else None
    prescription.status = request.status
    prescription.issued_at = request.issued_at
    prescription.notes = request.notes
    _replace_prescription_medications(prescription, request)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="prescription_updated",
        resource_type="prescription",
        resource_id=prescription.id,
        metadata={
            "status": prescription.status,
            "line_count": len(request.medications),
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(prescription)
    return _prescription_response(prescription)


@router.delete("/patients/{patient_id}/prescriptions/{prescription_id}", status_code=204)
def delete_patient_prescription(
    patient_id: uuid.UUID,
    prescription_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    _require_doctor_user(user)
    profile, prescription = _authorized_prescription(patient_id, prescription_id, user, db)
    line_count = len(prescription.medications)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="prescription_deleted",
        resource_type="prescription",
        resource_id=prescription.id,
        metadata={"line_count": line_count, "actor_role": user.role.value},
    )
    db.delete(prescription)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/patients/{patient_id}/medication-reminders",
    response_model=MedicationReminderListResponse,
)
def patient_medication_reminders(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> MedicationReminderListResponse:
    profile = _authorized_patient(patient_id, user, db)
    reminders = db.scalars(
        select(MedicationReminder)
        .where(MedicationReminder.patient_id == profile.id)
        .order_by(
            MedicationReminder.next_due_at.asc().nullslast(),
            MedicationReminder.created_at.desc(),
        )
    ).all()
    return MedicationReminderListResponse(
        items=[_medication_reminder_response(item) for item in reminders]
    )


@router.post(
    "/patients/{patient_id}/medication-reminders",
    response_model=MedicationReminderResponse,
)
def create_patient_medication_reminder(
    patient_id: uuid.UUID,
    request: MedicationReminderRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicationReminderResponse:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    _validate_medication_reminder_request(request, patient_id=profile.id, db=db)
    reminder = MedicationReminder(patient_id=profile.id)
    _apply_medication_reminder_request(reminder, request)
    db.add(reminder)
    db.flush()
    notification = _queue_reminder_notification(db, profile=profile, reminder=reminder)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medication_reminder_created",
        resource_type="medication_reminder",
        resource_id=reminder.id,
        metadata={
            "reminder_type": _reminder_type(reminder),
            "status": reminder.status,
            "channel": reminder.channel,
            "notification_queued": notification is not None,
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(reminder)
    return _medication_reminder_response(reminder)


@router.put(
    "/patients/{patient_id}/medication-reminders/{reminder_id}",
    response_model=MedicationReminderResponse,
)
def update_patient_medication_reminder(
    patient_id: uuid.UUID,
    reminder_id: uuid.UUID,
    request: MedicationReminderRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicationReminderResponse:
    _require_doctor_user(user)
    profile, reminder = _authorized_medication_reminder(patient_id, reminder_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    _validate_medication_reminder_request(request, patient_id=profile.id, db=db)
    cancelled_count = _cancel_queued_reminder_notifications(db, profile=profile, reminder=reminder)
    _apply_medication_reminder_request(reminder, request)
    db.flush()
    notification = _queue_reminder_notification(db, profile=profile, reminder=reminder)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medication_reminder_updated",
        resource_type="medication_reminder",
        resource_id=reminder.id,
        metadata={
            "reminder_type": _reminder_type(reminder),
            "status": reminder.status,
            "channel": reminder.channel,
            "cancelled_queued_notifications": cancelled_count,
            "notification_queued": notification is not None,
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(reminder)
    return _medication_reminder_response(reminder)


@router.delete("/patients/{patient_id}/medication-reminders/{reminder_id}", status_code=204)
def delete_patient_medication_reminder(
    patient_id: uuid.UUID,
    reminder_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    _require_doctor_user(user)
    profile, reminder = _authorized_medication_reminder(patient_id, reminder_id, user, db)
    cancelled_count = _cancel_queued_reminder_notifications(db, profile=profile, reminder=reminder)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medication_reminder_deleted",
        resource_type="medication_reminder",
        resource_id=reminder.id,
        metadata={
            "reminder_type": _reminder_type(reminder),
            "cancelled_queued_notifications": cancelled_count,
            "actor_role": user.role.value,
        },
    )
    db.delete(reminder)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/patients/{patient_id}/doctor-notes", response_model=DoctorNoteListResponse)
def patient_doctor_notes(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> DoctorNoteListResponse:
    if user.role != UserRole.doctor:
        raise _neutral_not_found()
    profile = _authorized_patient(patient_id, user, db)
    notes = db.scalars(
        select(DoctorNote)
        .where(DoctorNote.patient_id == profile.id)
        .order_by(DoctorNote.created_at.desc())
    ).all()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="doctor_notes_listed",
        resource_type="doctor_note",
        resource_id=None,
        metadata={"count": len(notes)},
    )
    db.commit()
    return DoctorNoteListResponse(items=[_note_response(item) for item in notes])


@router.post("/patients/{patient_id}/doctor-notes", response_model=DoctorNoteResponse)
def create_patient_doctor_note(
    patient_id: uuid.UUID,
    request: DoctorNoteCreateRequest,
    user: CurrentUser,
    db: DbSession,
) -> DoctorNoteResponse:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    note = DoctorNote(
        patient_id=profile.id,
        doctor_id=user.doctor_profile.id,
        clinical_event_id=event.id if event else None,
        title=request.title,
        body=request.body,
    )
    db.add(note)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="doctor_note_created",
        resource_type="doctor_note",
        resource_id=note.id,
        metadata={
            "fields": ["title", "body", "clinical_event_id"],
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(note)
    return _note_response(note)


@router.put("/patients/{patient_id}/doctor-notes/{note_id}", response_model=DoctorNoteResponse)
def update_patient_doctor_note(
    patient_id: uuid.UUID,
    note_id: uuid.UUID,
    request: DoctorNoteUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> DoctorNoteResponse:
    profile, note = _authorized_doctor_note(patient_id, note_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    note.clinical_event_id = event.id if event else None
    note.title = request.title
    note.body = request.body
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="doctor_note_updated",
        resource_type="doctor_note",
        resource_id=note.id,
        metadata={
            "fields": ["title", "body", "clinical_event_id"],
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(note)
    return _note_response(note)


@router.delete(
    "/patients/{patient_id}/doctor-notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_patient_doctor_note(
    patient_id: uuid.UUID,
    note_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    profile, note = _authorized_doctor_note(patient_id, note_id, user, db)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="doctor_note_deleted",
        resource_type="doctor_note",
        resource_id=note.id,
        metadata={"actor_role": user.role.value},
    )
    db.delete(note)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/patients/{patient_id}/allergies", response_model=PatientAllergyListResponse)
def patient_allergies(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> PatientAllergyListResponse:
    profile = _authorized_patient(patient_id, user, db)
    allergies = db.scalars(
        select(PatientAllergy)
        .where(PatientAllergy.patient_id == profile.id)
        .order_by(PatientAllergy.created_at.desc())
    ).all()
    return PatientAllergyListResponse(items=[_allergy_response(item) for item in allergies])


@router.post("/patients/{patient_id}/allergies", response_model=PatientAllergyResponse)
def create_patient_allergy(
    patient_id: uuid.UUID,
    request: PatientAllergyRequest,
    user: CurrentUser,
    db: DbSession,
) -> PatientAllergyResponse:
    profile = _authorized_patient(patient_id, user, db)
    allergy = PatientAllergy(
        patient_id=profile.id,
        label=request.label,
        reaction=request.reaction,
        severity=request.severity,
        status=request.status,
        recorded_by_user_id=user.id,
    )
    db.add(allergy)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="patient_allergy_created",
        resource_type="patient_allergy",
        resource_id=allergy.id,
        metadata={
            "severity": request.severity,
            "status": request.status,
            "actor_role": user.role.value,
        },
    )
    db.commit()
    db.refresh(allergy)
    return _allergy_response(allergy)


@router.put("/patients/{patient_id}/allergies/{allergy_id}", response_model=PatientAllergyResponse)
def update_patient_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    request: PatientAllergyRequest,
    user: CurrentUser,
    db: DbSession,
) -> PatientAllergyResponse:
    profile, allergy = _authorized_allergy(patient_id, allergy_id, user, db)
    allergy.label = request.label
    allergy.reaction = request.reaction
    allergy.severity = request.severity
    allergy.status = request.status
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="patient_allergy_updated",
        resource_type="patient_allergy",
        resource_id=allergy.id,
        metadata={
            "severity": request.severity,
            "status": request.status,
            "actor_role": user.role.value,
        },
    )
    db.commit()
    db.refresh(allergy)
    return _allergy_response(allergy)


@router.delete(
    "/patients/{patient_id}/allergies/{allergy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_patient_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    profile, allergy = _authorized_allergy(patient_id, allergy_id, user, db)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="patient_allergy_deleted",
        resource_type="patient_allergy",
        resource_id=allergy.id,
        metadata={"actor_role": user.role.value},
    )
    db.delete(allergy)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/patients/{patient_id}/chronic-diseases",
    response_model=ChronicDiseaseListResponse,
)
def patient_chronic_diseases(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> ChronicDiseaseListResponse:
    profile = _authorized_patient(patient_id, user, db)
    conditions = db.scalars(
        select(ChronicDisease)
        .where(ChronicDisease.patient_id == profile.id)
        .order_by(ChronicDisease.created_at.desc())
    ).all()
    return ChronicDiseaseListResponse(
        items=[_chronic_disease_response(item) for item in conditions]
    )


@router.post(
    "/patients/{patient_id}/chronic-diseases",
    response_model=ChronicDiseaseResponse,
)
def create_patient_chronic_disease(
    patient_id: uuid.UUID,
    request: ChronicDiseaseRequest,
    user: CurrentUser,
    db: DbSession,
) -> ChronicDiseaseResponse:
    profile = _authorized_patient(patient_id, user, db)
    condition = ChronicDisease(
        patient_id=profile.id,
        name=request.name,
        status=request.status,
        diagnosed_on=request.diagnosed_on,
        notes=request.notes,
        recorded_by_user_id=user.id,
    )
    db.add(condition)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="chronic_disease_created",
        resource_type="chronic_disease",
        resource_id=condition.id,
        metadata={"status": request.status, "actor_role": user.role.value},
    )
    db.commit()
    db.refresh(condition)
    return _chronic_disease_response(condition)


@router.put(
    "/patients/{patient_id}/chronic-diseases/{condition_id}",
    response_model=ChronicDiseaseResponse,
)
def update_patient_chronic_disease(
    patient_id: uuid.UUID,
    condition_id: uuid.UUID,
    request: ChronicDiseaseRequest,
    user: CurrentUser,
    db: DbSession,
) -> ChronicDiseaseResponse:
    profile, condition = _authorized_chronic_disease(patient_id, condition_id, user, db)
    condition.name = request.name
    condition.status = request.status
    condition.diagnosed_on = request.diagnosed_on
    condition.notes = request.notes
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="chronic_disease_updated",
        resource_type="chronic_disease",
        resource_id=condition.id,
        metadata={"status": request.status, "actor_role": user.role.value},
    )
    db.commit()
    db.refresh(condition)
    return _chronic_disease_response(condition)


@router.delete(
    "/patients/{patient_id}/chronic-diseases/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_patient_chronic_disease(
    patient_id: uuid.UUID,
    condition_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    profile, condition = _authorized_chronic_disease(patient_id, condition_id, user, db)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="chronic_disease_deleted",
        resource_type="chronic_disease",
        resource_id=condition.id,
        metadata={"actor_role": user.role.value},
    )
    db.delete(condition)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/patients/{patient_id}/medical-history-reviews",
    response_model=MedicalHistoryReviewListResponse,
)
def patient_medical_history_reviews(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> MedicalHistoryReviewListResponse:
    profile = _authorized_patient(patient_id, user, db)
    reviews = db.scalars(
        select(MedicalHistoryReview)
        .where(MedicalHistoryReview.patient_id == profile.id)
        .order_by(MedicalHistoryReview.created_at.desc())
    ).all()
    return MedicalHistoryReviewListResponse(
        items=[_medical_history_review_response(item) for item in reviews]
    )


@router.post(
    "/patients/{patient_id}/medical-history-reviews",
    response_model=MedicalHistoryReviewResponse,
)
def create_patient_medical_history_review(
    patient_id: uuid.UUID,
    request: MedicalHistoryReviewRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicalHistoryReviewResponse:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    if request.action == "amendment" and not request.amendment_summary:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "amendment_summary",
                    "code": "required_for_amendment",
                    "message": "Doctor amendments need an amendment summary.",
                }
            ],
        )
    if request.action == "correction_requested" and not request.correction_request:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "correction_request",
                    "code": "required_for_correction_request",
                    "message": "Correction requests need patient-facing correction text.",
                }
            ],
        )
    _authorized_history_review_target(
        profile.id,
        request.target_type,
        request.target_id,
        db,
    )
    review = MedicalHistoryReview(
        patient_id=profile.id,
        doctor_id=user.doctor_profile.id if user.doctor_profile else None,
        target_type=request.target_type,
        target_id=request.target_id,
        action=request.action,
        amendment_summary=request.amendment_summary,
        correction_request=request.correction_request,
    )
    db.add(review)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medical_history_review_created",
        resource_type="medical_history_review",
        resource_id=review.id,
        metadata={
            "actor_role": user.role.value,
            "target_type": review.target_type,
            "target_id": str(review.target_id),
            "action": review.action,
            "has_amendment_summary": request.amendment_summary is not None,
            "has_correction_request": request.correction_request is not None,
        },
    )
    db.commit()
    db.refresh(review)
    return _medical_history_review_response(review)


@router.get("/patients/{patient_id}/visit-history", response_model=VisitHistoryListResponse)
def patient_visit_history(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> VisitHistoryListResponse:
    profile = _authorized_patient(patient_id, user, db)
    visits = db.scalars(
        select(VisitHistory)
        .where(VisitHistory.patient_id == profile.id)
        .order_by(VisitHistory.occurred_at.desc())
    ).all()
    return VisitHistoryListResponse(items=[_visit_history_response(item) for item in visits])


@router.post("/patients/{patient_id}/visit-history", response_model=VisitHistoryResponse)
def create_patient_visit_history(
    patient_id: uuid.UUID,
    request: VisitHistoryRequest,
    user: CurrentUser,
    db: DbSession,
) -> VisitHistoryResponse:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    visit = VisitHistory(
        patient_id=profile.id,
        clinical_event_id=event.id if event else None,
        visit_type=request.visit_type,
        title=request.title,
        summary=request.summary,
        occurred_at=request.occurred_at,
        clinician_label=request.clinician_label,
        recorded_by_user_id=user.id,
    )
    db.add(visit)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="visit_history_created",
        resource_type="visit_history",
        resource_id=visit.id,
        metadata={
            "visit_type": request.visit_type,
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(visit)
    return _visit_history_response(visit)


@router.put(
    "/patients/{patient_id}/visit-history/{visit_id}",
    response_model=VisitHistoryResponse,
)
def update_patient_visit_history(
    patient_id: uuid.UUID,
    visit_id: uuid.UUID,
    request: VisitHistoryRequest,
    user: CurrentUser,
    db: DbSession,
) -> VisitHistoryResponse:
    _require_doctor_user(user)
    profile, visit = _authorized_visit_history(patient_id, visit_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    visit.clinical_event_id = event.id if event else None
    visit.visit_type = request.visit_type
    visit.title = request.title
    visit.summary = request.summary
    visit.occurred_at = request.occurred_at
    visit.clinician_label = request.clinician_label
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="visit_history_updated",
        resource_type="visit_history",
        resource_id=visit.id,
        metadata={
            "visit_type": request.visit_type,
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(visit)
    return _visit_history_response(visit)


@router.delete(
    "/patients/{patient_id}/visit-history/{visit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_patient_visit_history(
    patient_id: uuid.UUID,
    visit_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    _require_doctor_user(user)
    profile, visit = _authorized_visit_history(patient_id, visit_id, user, db)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="visit_history_deleted",
        resource_type="visit_history",
        resource_id=visit.id,
        metadata={"actor_role": user.role.value},
    )
    db.delete(visit)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/patients/{patient_id}/diagnoses", response_model=DiagnosisListResponse)
def patient_diagnoses(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> DiagnosisListResponse:
    profile = _authorized_patient(patient_id, user, db)
    diagnoses = db.scalars(
        select(Diagnosis)
        .where(Diagnosis.patient_id == profile.id)
        .order_by(Diagnosis.created_at.desc())
    ).all()
    return DiagnosisListResponse(items=[_diagnosis_response(item) for item in diagnoses])


@router.post("/patients/{patient_id}/diagnoses", response_model=DiagnosisResponse)
def create_patient_diagnosis(
    patient_id: uuid.UUID,
    request: DiagnosisRequest,
    user: CurrentUser,
    db: DbSession,
) -> DiagnosisResponse:
    _require_doctor_user(user)
    profile = _authorized_patient(patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    diagnosis = Diagnosis(
        patient_id=profile.id,
        clinical_event_id=event.id if event else None,
        label=request.label,
        status=request.status,
        diagnosed_on=request.diagnosed_on,
        notes=request.notes,
        recorded_by_user_id=user.id,
    )
    db.add(diagnosis)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="diagnosis_created",
        resource_type="diagnosis",
        resource_id=diagnosis.id,
        metadata={
            "status": request.status,
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(diagnosis)
    return _diagnosis_response(diagnosis)


@router.put("/patients/{patient_id}/diagnoses/{diagnosis_id}", response_model=DiagnosisResponse)
def update_patient_diagnosis(
    patient_id: uuid.UUID,
    diagnosis_id: uuid.UUID,
    request: DiagnosisRequest,
    user: CurrentUser,
    db: DbSession,
) -> DiagnosisResponse:
    _require_doctor_user(user)
    profile, diagnosis = _authorized_diagnosis(patient_id, diagnosis_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    diagnosis.clinical_event_id = event.id if event else None
    diagnosis.label = request.label
    diagnosis.status = request.status
    diagnosis.diagnosed_on = request.diagnosed_on
    diagnosis.notes = request.notes
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="diagnosis_updated",
        resource_type="diagnosis",
        resource_id=diagnosis.id,
        metadata={
            "status": request.status,
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(diagnosis)
    return _diagnosis_response(diagnosis)


@router.delete(
    "/patients/{patient_id}/diagnoses/{diagnosis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_patient_diagnosis(
    patient_id: uuid.UUID,
    diagnosis_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    _require_doctor_user(user)
    profile, diagnosis = _authorized_diagnosis(patient_id, diagnosis_id, user, db)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="diagnosis_deleted",
        resource_type="diagnosis",
        resource_id=diagnosis.id,
        metadata={"actor_role": user.role.value},
    )
    db.delete(diagnosis)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/patients/{patient_id}/care", response_model=PatientCareBundleResponse)
def patient_care_bundle(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> PatientCareBundleResponse:
    profile = _authorized_patient(patient_id, user, db)
    clinical_events = db.scalars(
        select(ClinicalEvent)
        .where(ClinicalEvent.patient_id == profile.id)
        .order_by(ClinicalEvent.updated_at.desc())
    ).all()
    clinical_event_updates = db.scalars(
        select(ClinicalEventUpdate)
        .where(ClinicalEventUpdate.patient_id == profile.id)
        .order_by(ClinicalEventUpdate.occurred_at.desc())
    ).all()
    medical_history_reviews = db.scalars(
        select(MedicalHistoryReview)
        .where(MedicalHistoryReview.patient_id == profile.id)
        .order_by(MedicalHistoryReview.created_at.desc())
    ).all()
    allergies = db.scalars(
        select(PatientAllergy)
        .where(PatientAllergy.patient_id == profile.id)
        .order_by(PatientAllergy.created_at.desc())
    ).all()
    conditions = db.scalars(
        select(ChronicDisease)
        .where(ChronicDisease.patient_id == profile.id)
        .order_by(ChronicDisease.created_at.desc())
    ).all()
    visits = db.scalars(
        select(VisitHistory)
        .where(VisitHistory.patient_id == profile.id)
        .order_by(VisitHistory.occurred_at.desc())
    ).all()
    diagnoses = db.scalars(
        select(Diagnosis)
        .where(Diagnosis.patient_id == profile.id)
        .order_by(Diagnosis.created_at.desc())
    ).all()
    records = db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == profile.id)
        .order_by(MedicalRecord.recorded_at.desc())
    ).all()
    imaging_assets = db.scalars(
        select(MedicalImagingAsset)
        .where(MedicalImagingAsset.patient_id == profile.id)
        .order_by(MedicalImagingAsset.created_at.desc())
    ).all()
    medications = db.scalars(
        select(Medication).where(Medication.patient_id == profile.id).order_by(Medication.name)
    ).all()
    prescriptions = db.scalars(
        select(Prescription)
        .options(selectinload(Prescription.medications))
        .where(Prescription.patient_id == profile.id)
        .order_by(Prescription.created_at.desc())
    ).all()
    reminders = db.scalars(
        select(MedicationReminder)
        .where(MedicationReminder.patient_id == profile.id)
        .order_by(
            MedicationReminder.next_due_at.asc().nullslast(),
            MedicationReminder.created_at.desc(),
        )
    ).all()
    recovery_plans = db.scalars(
        select(RecoveryPlan)
        .options(selectinload(RecoveryPlan.tasks).selectinload(RecoveryTask.completions))
        .where(RecoveryPlan.patient_id == profile.id)
        .order_by(RecoveryPlan.created_at.desc())
    ).all()
    notes: list[DoctorNote] = []
    if user.role == UserRole.doctor:
        notes = list(
            db.scalars(
                select(DoctorNote)
                .where(DoctorNote.patient_id == profile.id)
                .order_by(DoctorNote.created_at.desc())
            ).all()
        )
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="patient_care_bundle_read",
        resource_type="patient_profile",
        resource_id=profile.id,
        metadata={
            "actor_role": user.role.value,
            "clinical_event_count": len(clinical_events),
            "clinical_event_update_count": len(clinical_event_updates),
            "medical_history_review_count": len(medical_history_reviews),
            "allergy_count": len(allergies),
            "chronic_disease_count": len(conditions),
            "visit_count": len(visits),
            "diagnosis_count": len(diagnoses),
            "record_count": len(records),
            "imaging_asset_count": len(imaging_assets),
            "medication_count": len(medications),
            "prescription_count": len(prescriptions),
            "medication_reminder_count": len(reminders),
            "recovery_plan_count": len(recovery_plans),
            "doctor_note_count": len(notes),
        },
    )
    db.commit()
    return PatientCareBundleResponse(
        patient=_patient_response(profile),
        clinical_events=[_clinical_event_response(item, db) for item in clinical_events],
        clinical_event_updates=[
            _clinical_event_update_response(item) for item in clinical_event_updates
        ],
        medical_history_reviews=[
            _medical_history_review_response(item) for item in medical_history_reviews
        ],
        allergies=[_allergy_response(item) for item in allergies],
        chronic_diseases=[_chronic_disease_response(item) for item in conditions],
        visit_history=[_visit_history_response(item) for item in visits],
        diagnoses=[_diagnosis_response(item) for item in diagnoses],
        records=[_record_response(item) for item in records],
        imaging_assets=[_imaging_asset_response(item) for item in imaging_assets],
        medications=[_medication_response(item) for item in medications],
        prescriptions=[_prescription_response(item) for item in prescriptions],
        medication_reminders=[_medication_reminder_response(item) for item in reminders],
        recovery_plans=[_recovery_plan_response(item) for item in recovery_plans],
        doctor_notes=[_note_response(item) for item in notes],
    )


@router.patch("/patient/me/profile", response_model=PatientProfileResponse)
def update_own_patient_profile(
    request: PatientDemographicsUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> PatientProfileResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    profile = _authorized_patient(user.patient_profile.id, user, db)
    updated_fields = _apply_demographics_update(profile, request)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="patient_profile_updated",
        resource_type="patient_profile",
        resource_id=profile.id,
        metadata={"fields": updated_fields, "actor_role": user.role.value},
    )
    db.commit()
    db.refresh(profile)
    return _patient_response(profile)


@router.get("/doctor/me/profile", response_model=DoctorProfileResponse)
def own_doctor_profile(user: CurrentUser) -> DoctorProfileResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    return _doctor_profile_response(user.doctor_profile)


@router.patch("/doctor/me/profile", response_model=DoctorProfileResponse)
def update_own_doctor_profile(
    request: DoctorProfileUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> DoctorProfileResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile = user.doctor_profile
    updated_fields: list[str] = []
    for field in (
        "display_name",
        "title",
        "birth_date",
        "gender",
        "contact_phone",
        "avatar_url",
        "country",
        "province",
        "city",
        "specialty",
        "department",
        "preferred_language",
    ):
        value = getattr(request, field)
        if value is not None and getattr(profile, field) != value:
            setattr(profile, field, value)
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
                    "message": "Provide at least one changed profile field.",
                }
            ],
        )
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=None,
        event_type="doctor_profile_updated",
        resource_type="doctor_profile",
        resource_id=profile.id,
        metadata={"fields": updated_fields, "actor_role": user.role.value},
    )
    db.commit()
    db.refresh(profile)
    return _doctor_profile_response(profile)


@router.post("/patients/{patient_id}/assets/presign", response_model=DemoAssetPresignResponse)
def presign_demo_asset_upload(
    patient_id: uuid.UUID,
    request: DemoAssetPresignRequest,
    user: CurrentUser,
    db: DbSession,
) -> DemoAssetPresignResponse:
    profile = _authorized_patient(patient_id, user, db)
    content_type = _validate_demo_asset_presign_request(request)
    expires_at = datetime.now(UTC) + timedelta(minutes=DEMO_UPLOAD_TTL_MINUTES)
    asset_id = uuid.uuid4()
    suffix = request.filename.rsplit(".", 1)[-1].lower() if "." in request.filename else "img"
    object_key = f"demo-assets/{profile.id}/{asset_id}.{suffix}"
    asset = DemoMedicalAsset(
        id=asset_id,
        patient_id=profile.id,
        uploaded_by_user_id=user.id,
        filename=request.filename,
        content_type=content_type,
        size_bytes=request.size_bytes,
        object_key=object_key,
        status="presigned",
        expires_at=expires_at,
    )
    db.add(asset)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="demo_asset_presigned",
        resource_type="demo_medical_asset",
        resource_id=asset_id,
        metadata={
            "content_type": content_type,
            "size_bytes": request.size_bytes,
            "status": "presigned",
        },
    )
    db.commit()
    return DemoAssetPresignResponse(
        asset_id=asset.id,
        patient_id=profile.id,
        upload_url=f"https://demo-upload.invalid/{object_key}",
        object_key=object_key,
        headers={
            "Content-Type": content_type,
            "x-dr-ai-demo-upload": "synthetic-only",
        },
        expires_at=expires_at,
        max_size_bytes=DEMO_UPLOAD_MAX_SIZE_BYTES,
        safety_label=SYNTHETIC_DATA_LABEL,
    )


@router.post("/patients/{patient_id}/imaging/presign", response_model=MedicalImagingPresignResponse)
def presign_medical_imaging_upload(
    patient_id: uuid.UUID,
    request: MedicalImagingPresignRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicalImagingPresignResponse:
    profile = _authorized_patient(patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    content_type, extension = _validate_imaging_presign_request(request)
    expires_at = datetime.now(UTC) + timedelta(minutes=DEMO_UPLOAD_TTL_MINUTES)
    asset_id = uuid.uuid4()
    object_key = f"medical-imaging-assets/{profile.id}/{asset_id}.{extension}"
    asset = MedicalImagingAsset(
        id=asset_id,
        patient_id=profile.id,
        clinical_event_id=event.id if event else None,
        uploaded_by_user_id=user.id,
        storage_provider=IMAGING_STORAGE_PROVIDER,
        content_type=content_type,
        file_extension=extension,
        size_bytes=request.size_bytes,
        uploaded_size_bytes=None,
        object_key=object_key,
        upload_status="pending_upload",
        review_status="not_ready",
        expires_at=expires_at,
    )
    db.add(asset)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medical_imaging_upload_presigned",
        resource_type="medical_imaging_asset",
        resource_id=asset_id,
        metadata={
            "actor_role": user.role.value,
            "content_type": content_type,
            "size_bytes": request.size_bytes,
            "storage_provider": IMAGING_STORAGE_PROVIDER,
            "upload_status": "pending_upload",
            "review_status": "not_ready",
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    return MedicalImagingPresignResponse(
        asset_id=asset.id,
        patient_id=profile.id,
        clinical_event_id=asset.clinical_event_id,
        upload_url=f"https://tencent-cos-upload.invalid/{object_key}",
        headers={
            "Content-Type": content_type,
            "x-dr-ai-upload-purpose": "phase2-imaging-metadata-only",
        },
        expires_at=expires_at,
        max_size_bytes=DEMO_UPLOAD_MAX_SIZE_BYTES,
        upload_status="pending_upload",
        review_status="not_ready",
        storage_provider=IMAGING_STORAGE_PROVIDER,
        safety_label=SYNTHETIC_DATA_LABEL,
    )


@router.post(
    "/patients/{patient_id}/imaging/{asset_id}/complete",
    response_model=MedicalImagingAssetResponse,
)
def complete_medical_imaging_upload(
    patient_id: uuid.UUID,
    asset_id: uuid.UUID,
    request: MedicalImagingCompleteRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicalImagingAssetResponse:
    profile, asset = _authorized_imaging_asset(patient_id, asset_id, user, db)
    _validate_imaging_completion(asset, request)
    if asset.upload_status != "uploaded":
        asset.upload_status = "uploaded"
        asset.review_status = "pending_review"
        asset.uploaded_at = datetime.now(UTC)
    asset.uploaded_size_bytes = request.uploaded_size_bytes
    asset.etag = request.etag
    asset.checksum_sha256 = request.checksum_sha256.lower() if request.checksum_sha256 else None
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medical_imaging_upload_completed",
        resource_type="medical_imaging_asset",
        resource_id=asset.id,
        metadata={
            "actor_role": user.role.value,
            "content_type": asset.content_type,
            "size_bytes": asset.size_bytes,
            "uploaded_size_bytes": request.uploaded_size_bytes,
            "storage_provider": asset.storage_provider,
            "upload_status": asset.upload_status,
            "review_status": asset.review_status,
            "has_etag": request.etag is not None,
            "has_checksum_sha256": request.checksum_sha256 is not None,
        },
    )
    db.commit()
    db.refresh(asset)
    return _imaging_asset_response(asset)


@router.get("/patients/{patient_id}/imaging", response_model=MedicalImagingAssetListResponse)
def patient_imaging_assets(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> MedicalImagingAssetListResponse:
    profile = _authorized_patient(patient_id, user, db)
    assets = db.scalars(
        select(MedicalImagingAsset)
        .where(MedicalImagingAsset.patient_id == profile.id)
        .order_by(MedicalImagingAsset.created_at.desc())
    ).all()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medical_imaging_assets_listed",
        resource_type="medical_imaging_asset",
        resource_id=None,
        metadata={
            "actor_role": user.role.value,
            "asset_count": len(assets),
            "upload_statuses": sorted({asset.upload_status for asset in assets}),
            "review_statuses": sorted({asset.review_status for asset in assets}),
        },
    )
    db.commit()
    return MedicalImagingAssetListResponse(items=[_imaging_asset_response(item) for item in assets])


@router.get(
    "/patients/{patient_id}/imaging/{asset_id}",
    response_model=MedicalImagingAssetResponse,
)
def patient_imaging_asset_detail(
    patient_id: uuid.UUID,
    asset_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> MedicalImagingAssetResponse:
    profile, asset = _authorized_imaging_asset(patient_id, asset_id, user, db)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medical_imaging_asset_read",
        resource_type="medical_imaging_asset",
        resource_id=asset.id,
        metadata={
            "actor_role": user.role.value,
            "content_type": asset.content_type,
            "storage_provider": asset.storage_provider,
            "upload_status": asset.upload_status,
            "review_status": asset.review_status,
        },
    )
    db.commit()
    return _imaging_asset_response(asset)


@router.post(
    "/patients/{patient_id}/imaging/{asset_id}/review",
    response_model=MedicalImagingAssetResponse,
)
def review_medical_imaging_asset(
    patient_id: uuid.UUID,
    asset_id: uuid.UUID,
    request: MedicalImagingReviewRequest,
    user: CurrentUser,
    db: DbSession,
) -> MedicalImagingAssetResponse:
    _require_doctor_user(user)
    profile, asset = _authorized_imaging_asset(patient_id, asset_id, user, db)
    if asset.upload_status != "uploaded":
        raise ApiError(
            409,
            "conflict",
            "Complete the upload before reviewing this imaging asset.",
            [
                {
                    "field": "asset_id",
                    "code": "upload_not_completed",
                    "message": "Complete the upload before review.",
                }
            ],
        )
    asset.review_status = request.review_status
    asset.finding_summary = request.finding_summary
    asset.measurement_summary = request.measurement_summary
    asset.observed_at = request.observed_at
    asset.treatment_relevance_date = request.treatment_relevance_date
    asset.reviewed_by_user_id = user.id
    asset.reviewed_at = datetime.now(UTC)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="medical_imaging_asset_reviewed",
        resource_type="medical_imaging_asset",
        resource_id=asset.id,
        metadata={
            "actor_role": user.role.value,
            "content_type": asset.content_type,
            "storage_provider": asset.storage_provider,
            "upload_status": asset.upload_status,
            "review_status": asset.review_status,
            "has_finding_summary": request.finding_summary is not None,
            "has_measurement_summary": request.measurement_summary is not None,
            "has_observed_at": request.observed_at is not None,
            "has_treatment_relevance_date": request.treatment_relevance_date is not None,
        },
    )
    db.commit()
    db.refresh(asset)
    return _imaging_asset_response(asset)


@router.get("/patient/me/imaging", response_model=MedicalImagingAssetListResponse)
def own_imaging_assets(user: CurrentUser, db: DbSession) -> MedicalImagingAssetListResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    return patient_imaging_assets(user.patient_profile.id, user, db)


@router.get("/patient/me/imaging/{asset_id}", response_model=MedicalImagingAssetResponse)
def own_imaging_asset_detail(
    asset_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> MedicalImagingAssetResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    return patient_imaging_asset_detail(user.patient_profile.id, asset_id, user, db)


@router.get("/patient/me/clinical-events", response_model=ClinicalEventListResponse)
def own_clinical_events(user: CurrentUser, db: DbSession) -> ClinicalEventListResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    return patient_clinical_events(user.patient_profile.id, user, db)


@router.get("/patient/me/clinical-events/{event_id}", response_model=ClinicalEventResponse)
def own_clinical_event_detail(
    event_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> ClinicalEventResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    return patient_clinical_event_detail(user.patient_profile.id, event_id, user, db)


@router.get(
    "/patient/me/clinical-events/{event_id}/updates",
    response_model=ClinicalEventUpdateListResponse,
)
def own_clinical_event_updates(
    event_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> ClinicalEventUpdateListResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    profile, event = _authorized_clinical_event(user.patient_profile.id, event_id, user, db)
    updates = db.scalars(
        select(ClinicalEventUpdate)
        .where(
            ClinicalEventUpdate.patient_id == profile.id,
            ClinicalEventUpdate.clinical_event_id == event.id,
        )
        .order_by(ClinicalEventUpdate.occurred_at.desc())
    ).all()
    return ClinicalEventUpdateListResponse(
        items=[_clinical_event_update_response(item) for item in updates]
    )


@router.post(
    "/patient/me/clinical-events/{event_id}/updates",
    response_model=ClinicalEventUpdateResponse,
)
def create_own_clinical_event_update(
    event_id: uuid.UUID,
    request: ClinicalEventUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> ClinicalEventUpdateResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    profile, event = _authorized_clinical_event(user.patient_profile.id, event_id, user, db)
    update = ClinicalEventUpdate(
        patient_id=profile.id,
        clinical_event_id=event.id,
        submitted_by_user_id=user.id,
        update_type=request.update_type,
        summary=request.summary,
        occurred_at=request.occurred_at or datetime.now(UTC),
    )
    db.add(update)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="clinical_event_patient_update_created",
        resource_type="clinical_event_update",
        resource_id=update.id,
        metadata={
            "actor_role": user.role.value,
            "clinical_event_id": str(event.id),
            "update_type": update.update_type,
            "has_summary": True,
        },
    )
    db.commit()
    db.refresh(update)
    return _clinical_event_update_response(update)


@router.get("/patients/{patient_id}/assessments", response_model=AssessmentListResponse)
def patient_assessments(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> AssessmentListResponse:
    profile = _authorized_patient(patient_id, user, db)
    assessments = db.scalars(
        select(SimulatedAssessment)
        .where(SimulatedAssessment.patient_id == profile.id)
        .order_by(SimulatedAssessment.created_at.desc())
    ).all()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="assessments_listed",
        resource_type="simulated_assessment",
        resource_id=None,
        metadata={"count": len(assessments)},
    )
    db.commit()
    return AssessmentListResponse(items=[_assessment_response(item) for item in assessments])


@router.post("/patients/{patient_id}/assessments", response_model=AssessmentResponse)
def create_simulated_assessment(
    patient_id: uuid.UUID,
    request: AssessmentRequest,
    user: CurrentUser,
    db: DbSession,
) -> AssessmentResponse:
    if user.role != UserRole.doctor:
        raise _neutral_not_found()
    profile = _authorized_patient(patient_id, user, db)
    fixture = ASSESSMENT_FIXTURES.get(request.fixture_id)
    if fixture is None:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "fixture_id",
                    "code": "unsupported_value",
                    "message": "Select a supported synthetic assessment fixture.",
                }
            ],
        )
    request_hash = hashlib.sha256(
        json.dumps(
            {
                "mode": request.mode,
                "fixture_id": request.fixture_id,
                "simulator": FIXTURE_SIMULATOR_VERSION,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    existing = db.scalar(
        select(SimulatedAssessment).where(
            SimulatedAssessment.patient_id == profile.id,
            SimulatedAssessment.actor_user_id == user.id,
            SimulatedAssessment.idempotency_key == request.idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_hash != request_hash:
            raise ApiError(
                409,
                "conflict",
                "The idempotency key was already used for a different request.",
            )
        return _assessment_response(existing)

    assessment = SimulatedAssessment(
        patient_id=profile.id,
        actor_user_id=user.id,
        fixture_id=request.fixture_id,
        idempotency_key=request.idempotency_key,
        request_hash=request_hash,
        mode="simulated",
        status="completed",
        risk_band=fixture.risk_band,
        demo_score=f"{fixture.demo_score:.2f}",
        input_completeness=fixture.input_completeness,
        model_version=FIXTURE_SIMULATOR_VERSION,
        limitations=ASSESSMENT_LIMITATIONS,
        recommended_next_steps=ASSESSMENT_NEXT_STEPS,
        safety_label=SIMULATION_LABEL,
    )
    db.add(assessment)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="simulated_assessment_completed",
        resource_type="simulated_assessment",
        resource_id=assessment.id,
        metadata={
            "fixture_id": request.fixture_id,
            "risk_band": fixture.risk_band,
            "input_completeness": fixture.input_completeness,
            "model_version": FIXTURE_SIMULATOR_VERSION,
        },
    )
    db.commit()
    db.refresh(assessment)
    return _assessment_response(assessment)


@router.get("/patients/{patient_id}/recovery-plans", response_model=RecoveryPlanListResponse)
def patient_recovery_plans(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> RecoveryPlanListResponse:
    profile = _authorized_patient(patient_id, user, db)
    plans = db.scalars(
        select(RecoveryPlan)
        .options(selectinload(RecoveryPlan.tasks).selectinload(RecoveryTask.completions))
        .where(RecoveryPlan.patient_id == profile.id)
        .order_by(RecoveryPlan.created_at.desc())
    ).all()
    return RecoveryPlanListResponse(items=[_recovery_plan_response(plan) for plan in plans])


@router.post("/patients/{patient_id}/recovery-plans", response_model=RecoveryPlanResponse)
def create_recovery_plan(
    patient_id: uuid.UUID,
    request: RecoveryPlanCreateRequest,
    user: CurrentUser,
    db: DbSession,
) -> RecoveryPlanResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile = _authorized_patient(patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    _validate_recovery_tasks(request.tasks, patient_id=profile.id, db=db)
    plan = RecoveryPlan(
        patient_id=profile.id,
        doctor_id=user.doctor_profile.id,
        clinical_event_id=event.id if event else None,
        title=request.title,
        instructions=request.instructions,
        status="draft",
        review_status="draft",
        safety_label=SYNTHETIC_DATA_LABEL,
    )
    db.add(plan)
    db.flush()
    _replace_recovery_tasks(plan, request.tasks)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="recovery_plan_created",
        resource_type="recovery_plan",
        resource_id=plan.id,
        metadata=_recovery_plan_audit_metadata(plan, source="doctor_create"),
    )
    db.commit()
    db.refresh(plan)
    return _recovery_plan_response(plan)


@router.put(
    "/patients/{patient_id}/recovery-plans/{plan_id}",
    response_model=RecoveryPlanResponse,
)
def update_recovery_plan(
    patient_id: uuid.UUID,
    plan_id: uuid.UUID,
    request: RecoveryPlanUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> RecoveryPlanResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile, plan = _authorized_recovery_plan(patient_id, plan_id, user, db)
    if plan.doctor_id != user.doctor_profile.id:
        raise _neutral_not_found()
    if (
        plan.status not in RECOVERY_PLAN_STATUSES
        or plan.review_status not in RECOVERY_PLAN_REVIEW_STATUSES
    ):
        raise _neutral_not_found()
    _ensure_recovery_plan_editable(plan)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    _validate_recovery_tasks(request.tasks, patient_id=profile.id, db=db)
    plan.clinical_event_id = event.id if event else None
    plan.title = request.title
    plan.instructions = request.instructions
    if plan.review_status == "changes_requested":
        plan.review_status = "draft"
        plan.submitted_at = None
        plan.reviewed_at = None
        plan.review_actor_user_id = None
    _replace_recovery_tasks(plan, request.tasks)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="recovery_plan_updated",
        resource_type="recovery_plan",
        resource_id=plan.id,
        metadata=_recovery_plan_audit_metadata(plan, source="doctor_update"),
    )
    db.commit()
    db.refresh(plan)
    return _recovery_plan_response(plan)


@router.post(
    "/patients/{patient_id}/recovery-plans/{plan_id}/submit-review",
    response_model=RecoveryPlanResponse,
)
def submit_recovery_plan_for_review(
    patient_id: uuid.UUID,
    plan_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> RecoveryPlanResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile, plan = _authorized_recovery_plan(patient_id, plan_id, user, db)
    if plan.doctor_id != user.doctor_profile.id:
        raise _neutral_not_found()
    if plan.status != "draft" or plan.review_status not in {"draft", "changes_requested"}:
        raise ApiError(
            409,
            "conflict",
            "This recovery plan cannot be submitted in its current state.",
        )
    plan.review_status = "in_review"
    plan.submitted_at = datetime.now(UTC)
    plan.reviewed_at = None
    plan.review_actor_user_id = None
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="recovery_plan_submitted_for_review",
        resource_type="recovery_plan",
        resource_id=plan.id,
        metadata=_recovery_plan_audit_metadata(plan, source="doctor_submit_review"),
    )
    db.commit()
    db.refresh(plan)
    return _recovery_plan_response(plan)


@router.post(
    "/patients/{patient_id}/recovery-plans/{plan_id}/request-changes",
    response_model=RecoveryPlanResponse,
)
def request_recovery_plan_changes(
    patient_id: uuid.UUID,
    plan_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> RecoveryPlanResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile, plan = _authorized_recovery_plan(patient_id, plan_id, user, db)
    if plan.doctor_id != user.doctor_profile.id:
        raise _neutral_not_found()
    if plan.status != "draft" or plan.review_status != "in_review":
        raise ApiError(
            409,
            "conflict",
            "Only a submitted recovery plan can receive requested changes.",
        )
    plan.review_status = "changes_requested"
    plan.review_actor_user_id = user.id
    plan.reviewed_at = datetime.now(UTC)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="recovery_plan_changes_requested",
        resource_type="recovery_plan",
        resource_id=plan.id,
        metadata=_recovery_plan_audit_metadata(plan, source="doctor_request_changes"),
    )
    db.commit()
    db.refresh(plan)
    return _recovery_plan_response(plan)


@router.post(
    "/patients/{patient_id}/recovery-plans/{plan_id}/approve",
    response_model=RecoveryPlanResponse,
)
def approve_recovery_plan(
    patient_id: uuid.UUID,
    plan_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> RecoveryPlanResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile, plan = _authorized_recovery_plan(patient_id, plan_id, user, db)
    if plan.doctor_id != user.doctor_profile.id:
        raise _neutral_not_found()
    if plan.status != "draft" or plan.review_status != "in_review":
        raise ApiError(
            409,
            "conflict",
            "Only a submitted recovery plan can be approved.",
        )
    _approve_recovery_plan(plan, profile, user, db, source="doctor_approve")
    db.commit()
    db.refresh(plan)
    return _recovery_plan_response(plan)


@router.post(
    "/patients/{patient_id}/recovery-plans/{plan_id}/activate",
    response_model=RecoveryPlanResponse,
)
def activate_recovery_plan(
    patient_id: uuid.UUID,
    plan_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> RecoveryPlanResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile, plan = _authorized_recovery_plan(patient_id, plan_id, user, db)
    if plan.doctor_id != user.doctor_profile.id:
        raise _neutral_not_found()
    if plan.status == "active":
        return _recovery_plan_response(plan)
    if plan.status != "draft" or plan.review_status not in {
        "draft",
        "in_review",
        "changes_requested",
    }:
        raise ApiError(
            409,
            "conflict",
            "This recovery plan cannot be activated in its current state.",
        )
    if plan.review_status in {"draft", "changes_requested"}:
        plan.submitted_at = datetime.now(UTC)
    _approve_recovery_plan(plan, profile, user, db, source="legacy_activate")
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="recovery_plan_activated",
        resource_type="recovery_plan",
        resource_id=plan.id,
        metadata=_recovery_plan_audit_metadata(plan, source="legacy_activate"),
    )
    db.commit()
    db.refresh(plan)
    return _recovery_plan_response(plan)


@router.post(
    "/patients/{patient_id}/recovery-plans/{plan_id}/complete",
    response_model=RecoveryPlanResponse,
)
def complete_recovery_plan(
    patient_id: uuid.UUID,
    plan_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> RecoveryPlanResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile, plan = _authorized_recovery_plan(patient_id, plan_id, user, db)
    if plan.doctor_id != user.doctor_profile.id:
        raise _neutral_not_found()
    if plan.status != "active":
        raise ApiError(
            409,
            "conflict",
            "Only an active recovery plan can be completed.",
        )
    tasks = list(plan.tasks)
    completed_count = len(_completion_map(tasks))
    if completed_count != len(tasks):
        raise ApiError(
            422,
            "validation_failed",
            "All recovery tasks must be completed before closing the plan.",
            [
                {
                    "field": "tasks",
                    "code": "incomplete_tasks",
                    "message": "All recovery tasks must be completed before closing the plan.",
                }
            ],
        )
    plan.status = "completed"
    plan.completed_at = datetime.now(UTC)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="recovery_plan_completed",
        resource_type="recovery_plan",
        resource_id=plan.id,
        metadata=_recovery_plan_audit_metadata(plan, source="doctor_complete"),
    )
    db.commit()
    db.refresh(plan)
    return _recovery_plan_response(plan)


@router.get("/patient/me/today", response_model=DashboardResponse)
def patient_today(user: CurrentUser, db: DbSession) -> DashboardResponse:
    if user.role != UserRole.patient:
        raise _neutral_not_found()
    snapshot = db.scalar(select(DashboardSnapshot).where(DashboardSnapshot.user_id == user.id))
    payload = dict(snapshot.payload) if snapshot is not None else {}
    if user.patient_profile is not None:
        active_plan = db.scalar(
            select(RecoveryPlan)
            .options(selectinload(RecoveryPlan.tasks).selectinload(RecoveryTask.completions))
            .where(
                RecoveryPlan.patient_id == user.patient_profile.id,
                RecoveryPlan.status == "active",
            )
            .order_by(RecoveryPlan.activated_at.desc())
        )
        if active_plan is not None:
            plan_response = _recovery_plan_response(active_plan)
            payload["active_recovery_plan"] = plan_response.model_dump(mode="json")
            payload["today_tasks"] = [task.model_dump(mode="json") for task in plan_response.tasks]
            payload["today_progress"] = plan_response.progress_summary.model_dump(mode="json")
    return DashboardResponse(role=user.role, data=payload)


@router.post(
    "/patient/me/tasks/{task_id}/completion",
    response_model=TaskCompletionResponse,
)
def complete_recovery_task(
    task_id: uuid.UUID,
    request: TaskCompletionRequest,
    user: CurrentUser,
    db: DbSession,
) -> TaskCompletionResponse:
    del request
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    task = db.scalar(
        select(RecoveryTask)
        .join(RecoveryPlan)
        .options(selectinload(RecoveryTask.completions))
        .where(
            RecoveryTask.id == task_id,
            RecoveryTask.patient_id == user.patient_profile.id,
            RecoveryPlan.status == "active",
        )
    )
    if task is None:
        raise _neutral_not_found()
    completion = db.scalar(
        select(RecoveryTaskCompletion).where(
            RecoveryTaskCompletion.task_id == task.id,
            RecoveryTaskCompletion.patient_id == user.patient_profile.id,
        )
    )
    if completion is None:
        completion = RecoveryTaskCompletion(
            task_id=task.id,
            patient_id=user.patient_profile.id,
            actor_user_id=user.id,
        )
        db.add(completion)
        db.flush()
        _record_audit_event(
            db,
            actor_user_id=user.id,
            patient_id=user.patient_profile.id,
            event_type="recovery_task_completed",
            resource_type="recovery_task",
            resource_id=task.id,
            metadata={"category": task.category, "plan_id": str(task.plan_id)},
        )
        db.commit()
        db.refresh(task)
    return TaskCompletionResponse(task=_recovery_task_response(task, {task.id: completion}))


@router.delete(
    "/patient/me/tasks/{task_id}/completion",
    response_model=TaskCompletionResponse,
)
def uncomplete_recovery_task(
    task_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> TaskCompletionResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    task = db.scalar(
        select(RecoveryTask)
        .join(RecoveryPlan)
        .options(selectinload(RecoveryTask.completions))
        .where(
            RecoveryTask.id == task_id,
            RecoveryTask.patient_id == user.patient_profile.id,
            RecoveryPlan.status == "active",
        )
    )
    if task is None:
        raise _neutral_not_found()
    completion = db.scalar(
        select(RecoveryTaskCompletion).where(
            RecoveryTaskCompletion.task_id == task.id,
            RecoveryTaskCompletion.patient_id == user.patient_profile.id,
        )
    )
    if completion is not None:
        db.delete(completion)
        db.flush()
        _record_audit_event(
            db,
            actor_user_id=user.id,
            patient_id=user.patient_profile.id,
            event_type="recovery_task_uncompleted",
            resource_type="recovery_task",
            resource_id=task.id,
            metadata={"category": task.category, "plan_id": str(task.plan_id)},
        )
        db.commit()
        db.refresh(task)
    return TaskCompletionResponse(task=_recovery_task_response(task, {}))


@router.get("/patient/me/care", response_model=PatientCareBundleResponse)
def own_patient_care(user: CurrentUser, db: DbSession) -> PatientCareBundleResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    profile = user.patient_profile
    clinical_events = db.scalars(
        select(ClinicalEvent)
        .where(ClinicalEvent.patient_id == profile.id)
        .order_by(ClinicalEvent.updated_at.desc())
    ).all()
    clinical_event_updates = db.scalars(
        select(ClinicalEventUpdate)
        .where(ClinicalEventUpdate.patient_id == profile.id)
        .order_by(ClinicalEventUpdate.occurred_at.desc())
    ).all()
    medical_history_reviews = db.scalars(
        select(MedicalHistoryReview)
        .where(MedicalHistoryReview.patient_id == profile.id)
        .order_by(MedicalHistoryReview.created_at.desc())
    ).all()
    allergies = db.scalars(
        select(PatientAllergy)
        .where(PatientAllergy.patient_id == profile.id)
        .order_by(PatientAllergy.created_at.desc())
    ).all()
    conditions = db.scalars(
        select(ChronicDisease)
        .where(ChronicDisease.patient_id == profile.id)
        .order_by(ChronicDisease.created_at.desc())
    ).all()
    visits = db.scalars(
        select(VisitHistory)
        .where(VisitHistory.patient_id == profile.id)
        .order_by(VisitHistory.occurred_at.desc())
    ).all()
    diagnoses = db.scalars(
        select(Diagnosis)
        .where(Diagnosis.patient_id == profile.id)
        .order_by(Diagnosis.created_at.desc())
    ).all()
    records = db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == profile.id)
        .order_by(MedicalRecord.recorded_at.desc())
    ).all()
    imaging_assets = db.scalars(
        select(MedicalImagingAsset)
        .where(MedicalImagingAsset.patient_id == profile.id)
        .order_by(MedicalImagingAsset.created_at.desc())
    ).all()
    medications = db.scalars(
        select(Medication).where(Medication.patient_id == profile.id).order_by(Medication.name)
    ).all()
    prescriptions = db.scalars(
        select(Prescription)
        .options(selectinload(Prescription.medications))
        .where(Prescription.patient_id == profile.id)
        .order_by(Prescription.created_at.desc())
    ).all()
    reminders = db.scalars(
        select(MedicationReminder)
        .where(MedicationReminder.patient_id == profile.id)
        .order_by(
            MedicationReminder.next_due_at.asc().nullslast(),
            MedicationReminder.created_at.desc(),
        )
    ).all()
    recovery_plans = db.scalars(
        select(RecoveryPlan)
        .options(selectinload(RecoveryPlan.tasks).selectinload(RecoveryTask.completions))
        .where(RecoveryPlan.patient_id == profile.id)
        .order_by(RecoveryPlan.created_at.desc())
    ).all()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="patient_care_bundle_read",
        resource_type="patient_profile",
        resource_id=profile.id,
        metadata={
            "actor_role": user.role.value,
            "clinical_event_count": len(clinical_events),
            "clinical_event_update_count": len(clinical_event_updates),
            "medical_history_review_count": len(medical_history_reviews),
            "allergy_count": len(allergies),
            "chronic_disease_count": len(conditions),
            "visit_count": len(visits),
            "diagnosis_count": len(diagnoses),
            "record_count": len(records),
            "imaging_asset_count": len(imaging_assets),
            "medication_count": len(medications),
            "prescription_count": len(prescriptions),
            "medication_reminder_count": len(reminders),
            "recovery_plan_count": len(recovery_plans),
            "doctor_note_count": 0,
        },
    )
    db.commit()
    return PatientCareBundleResponse(
        patient=_patient_response(profile),
        clinical_events=[_clinical_event_response(item, db) for item in clinical_events],
        clinical_event_updates=[
            _clinical_event_update_response(item) for item in clinical_event_updates
        ],
        medical_history_reviews=[
            _medical_history_review_response(item) for item in medical_history_reviews
        ],
        allergies=[_allergy_response(item) for item in allergies],
        chronic_diseases=[_chronic_disease_response(item) for item in conditions],
        visit_history=[_visit_history_response(item) for item in visits],
        diagnoses=[_diagnosis_response(item) for item in diagnoses],
        records=[_record_response(item) for item in records],
        imaging_assets=[_imaging_asset_response(item) for item in imaging_assets],
        medications=[_medication_response(item) for item in medications],
        prescriptions=[_prescription_response(item) for item in prescriptions],
        medication_reminders=[_medication_reminder_response(item) for item in reminders],
        recovery_plans=[_recovery_plan_response(item) for item in recovery_plans],
        doctor_notes=[],
    )


@router.post("/chat/threads/{thread_id}/messages", response_model=ChatMessageResponse)
def send_chat_message(
    thread_id: str,
    request: ChatMessageRequest,
    user: CurrentUser,
    db: DbSession,
    settings: AppSettings,
) -> ChatMessageResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    message = request.message.strip()
    profile = user.patient_profile
    thread = _chat_thread_for_request(thread_id, profile, user, db)

    is_red_flag = _contains_pattern(message, RED_FLAG_PATTERNS)
    fallback_reason: str | None = None
    model = settings.deepseek_model
    if is_red_flag:
        content = RED_FLAG_MESSAGE
        fallback_reason = "red_flag"
        safety_category = "red_flag_escalation"
        _record_audit_event(
            db,
            actor_user_id=user.id,
            patient_id=profile.id,
            event_type="chat_red_flag_escalated",
            resource_type="chat_thread",
            resource_id=thread.id,
            metadata={"message_length": len(message), "thread_key": thread.thread_key},
        )
    elif _contains_pattern(message, UNSAFE_PROMPT_PATTERNS):
        content = _fallback_content("unsafe_prompt")
        fallback_reason = "unsafe_prompt"
        safety_category = "unsafe_prompt_fallback"
    else:
        _check_chat_rate_limit(user, db, settings)
        safety_category = "educational_chat"
        try:
            result = deepseek_chat_adapter.complete(message=message, settings=settings)
            content = result.content
            model = result.model
        except DeepSeekChatError as exc:
            fallback_reason = exc.fallback_reason
            content = _fallback_content(exc.fallback_reason)
            model = f"{settings.deepseek_model}:safe-fallback"

    user_message, assistant_message = _record_chat_exchange(
        db,
        thread=thread,
        user=user,
        message=message,
        safety_category=safety_category,
        fallback_reason=fallback_reason,
        model=model,
    )
    db.commit()
    return ChatMessageResponse(
        thread_id=thread.id,
        thread_key=thread.thread_key,
        message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        content=content,
        response_chunks=_response_chunks(content),
        safety_label=EDUCATIONAL_LABEL,
        emergency_label=EMERGENCY_LABEL if is_red_flag else None,
        is_red_flag=is_red_flag,
        fallback_reason=fallback_reason,
        model=model,
        created_at=assistant_message.created_at,
    )


@router.get("/consultations", response_model=ConsultationListResponse)
def list_consultations(user: CurrentUser, db: DbSession) -> ConsultationListResponse:
    if user.role == UserRole.patient and user.patient_profile is not None:
        requests = db.scalars(
            select(ConsultationRequest)
            .where(ConsultationRequest.patient_id == user.patient_profile.id)
            .order_by(ConsultationRequest.created_at.desc())
        ).all()
    elif user.role == UserRole.doctor and user.doctor_profile is not None:
        requests = db.scalars(
            select(ConsultationRequest)
            .join(CareRelationship, CareRelationship.patient_id == ConsultationRequest.patient_id)
            .where(
                CareRelationship.doctor_id == user.doctor_profile.id,
                CareRelationship.is_active.is_(True),
            )
            .order_by(ConsultationRequest.created_at.desc())
        ).all()
    else:
        raise _neutral_not_found()
    return ConsultationListResponse(items=[_consultation_response(item) for item in requests])


@router.post("/consultations", response_model=ConsultationResponse)
def create_consultation(
    request: ConsultationCreateRequest,
    user: CurrentUser,
    db: DbSession,
) -> ConsultationResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _neutral_not_found()
    profile = _authorized_patient(request.patient_id, user, db)
    event = _optional_clinical_event(
        request.clinical_event_id,
        patient_id=profile.id,
        user=user,
        db=db,
    )
    specialty = request.specialty.strip()
    question_summary = request.question_summary.strip()
    unsafe_details = _unsafe_consultation_fields(specialty, question_summary)
    if unsafe_details:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            unsafe_details,
        )
    existing = db.scalar(
        select(ConsultationRequest).where(
            ConsultationRequest.patient_id == profile.id,
            ConsultationRequest.requested_by_user_id == user.id,
            ConsultationRequest.clinical_event_id == (event.id if event else None),
            ConsultationRequest.specialty == specialty,
            ConsultationRequest.question_summary == question_summary,
            ConsultationRequest.priority == request.priority,
            ConsultationRequest.status == "requested",
        )
    )
    if existing is not None:
        return _consultation_response(existing)
    consultation = ConsultationRequest(
        patient_id=profile.id,
        clinical_event_id=event.id if event else None,
        requested_by_user_id=user.id,
        specialty=specialty,
        question_summary=question_summary,
        priority=request.priority,
        status="requested",
        safety_label=SYNTHETIC_DATA_LABEL,
    )
    db.add(consultation)
    db.flush()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="consultation_requested",
        resource_type="consultation_request",
        resource_id=consultation.id,
        metadata={
            "specialty": consultation.specialty,
            "priority": consultation.priority,
            "status": consultation.status,
            "clinical_event_id": str(event.id) if event else None,
        },
    )
    db.commit()
    db.refresh(consultation)
    return _consultation_response(consultation)


@router.get("/medications", response_model=MedicationListResponse)
def own_medications(user: CurrentUser, db: DbSession) -> MedicationListResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    medications = db.scalars(
        select(Medication)
        .where(Medication.patient_id == user.patient_profile.id)
        .order_by(Medication.name)
    ).all()
    return MedicationListResponse(items=[_medication_response(item) for item in medications])


@router.get("/reminders", response_model=MedicationReminderListResponse)
def own_medication_reminders(user: CurrentUser, db: DbSession) -> MedicationReminderListResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    reminders = db.scalars(
        select(MedicationReminder)
        .where(MedicationReminder.patient_id == user.patient_profile.id)
        .order_by(
            MedicationReminder.next_due_at.asc().nullslast(),
            MedicationReminder.created_at.desc(),
        )
    ).all()
    return MedicationReminderListResponse(
        items=[_medication_reminder_response(item) for item in reminders]
    )


@router.get("/patient/me/notifications", response_model=NotificationListResponse)
def own_notifications(user: CurrentUser, db: DbSession) -> NotificationListResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    notifications = db.scalars(
        select(Notification)
        .where(
            Notification.user_id == user.id,
            Notification.patient_id == user.patient_profile.id,
        )
        .order_by(Notification.created_at.desc())
    ).all()
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=user.patient_profile.id,
        event_type="notifications_listed",
        resource_type="notification",
        resource_id=None,
        metadata={"count": len(notifications), "actor_role": user.role.value},
    )
    db.commit()
    return NotificationListResponse(items=[_notification_response(item) for item in notifications])
