import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import select
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
    ConsultationRequest,
    DashboardSnapshot,
    DemoMedicalAsset,
    DoctorNote,
    MedicalRecord,
    Medication,
    PatientProfile,
    RecoveryPlan,
    RecoveryTask,
    RecoveryTaskCompletion,
    SimulatedAssessment,
    UserRole,
)
from app.schemas import (
    AssessmentListResponse,
    AssessmentRequest,
    AssessmentResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ConsultationCreateRequest,
    ConsultationListResponse,
    ConsultationResponse,
    DashboardResponse,
    DemoAssetPresignRequest,
    DemoAssetPresignResponse,
    DoctorNoteListResponse,
    DoctorNoteResponse,
    MedicalRecordListResponse,
    MedicalRecordResponse,
    MedicationListResponse,
    MedicationResponse,
    PatientCareBundleResponse,
    PatientListResponse,
    PatientProfileResponse,
    PatientSummaryResponse,
    RecoveryPlanCreateRequest,
    RecoveryPlanListResponse,
    RecoveryPlanResponse,
    RecoveryPlanUpdateRequest,
    RecoveryTaskInput,
    RecoveryTaskResponse,
    TaskCompletionRequest,
    TaskCompletionResponse,
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
        f"{profile.synthetic_identifier} is synthetic demonstration content for "
        "the Dr. AI v1.0 invited beta. It is not a clinical record."
    )


def _patient_response(profile: PatientProfile) -> PatientProfileResponse:
    return PatientProfileResponse(
        patient_id=profile.id,
        display_name=profile.display_name,
        synthetic_identifier=profile.synthetic_identifier,
        relationship_label="Active synthetic care relationship",
        overview=_patient_overview(profile),
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


def _medication_response(medication: Medication) -> MedicationResponse:
    return MedicationResponse(
        id=medication.id,
        patient_id=medication.patient_id,
        name=medication.name,
        dosage=medication.dosage,
        schedule=medication.schedule,
        status=medication.status,
        note=medication.note,
    )


def _note_response(note: DoctorNote) -> DoctorNoteResponse:
    return DoctorNoteResponse(
        id=note.id,
        patient_id=note.patient_id,
        title=note.title,
        body=note.body,
        created_at=note.created_at,
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
    return RecoveryPlanResponse(
        plan_id=plan.id,
        patient_id=plan.patient_id,
        title=plan.title,
        instructions=plan.instructions,
        status=plan.status,  # type: ignore[arg-type]
        safety_label=SYNTHETIC_DATA_LABEL,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        activated_at=plan.activated_at,
        tasks=[_recovery_task_response(task, completions) for task in tasks],
    )


def _record_audit_event(
    db: DbSession,
    *,
    actor_user_id: uuid.UUID,
    patient_id: uuid.UUID,
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


@router.get("/me/dashboard", response_model=DashboardResponse)
def own_dashboard(user: CurrentUser, db: DbSession) -> DashboardResponse:
    if user.role not in {UserRole.doctor, UserRole.patient}:
        raise ApiError(403, "forbidden", "This role is not enabled for this workflow.")
    snapshot = db.scalar(select(DashboardSnapshot).where(DashboardSnapshot.user_id == user.id))
    if snapshot is None:
        return DashboardResponse(role=user.role, data={})
    return DashboardResponse(role=user.role, data=snapshot.payload)


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


@router.get("/patients/{patient_id}", response_model=PatientProfileResponse)
def patient_summary(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> PatientProfileResponse:
    return _patient_response(_authorized_patient(patient_id, user, db))


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
    return DoctorNoteListResponse(items=[_note_response(item) for item in notes])


@router.get("/patients/{patient_id}/care", response_model=PatientCareBundleResponse)
def patient_care_bundle(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> PatientCareBundleResponse:
    profile = _authorized_patient(patient_id, user, db)
    records = db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == profile.id)
        .order_by(MedicalRecord.recorded_at.desc())
    ).all()
    medications = db.scalars(
        select(Medication).where(Medication.patient_id == profile.id).order_by(Medication.name)
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
    return PatientCareBundleResponse(
        patient=_patient_response(profile),
        records=[_record_response(item) for item in records],
        medications=[_medication_response(item) for item in medications],
        doctor_notes=[_note_response(item) for item in notes],
    )


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
    _validate_recovery_tasks(request.tasks, patient_id=profile.id, db=db)
    plan = RecoveryPlan(
        patient_id=profile.id,
        doctor_id=user.doctor_profile.id,
        title=request.title,
        instructions=request.instructions,
        status="draft",
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
        metadata={
            "status": plan.status,
            "task_count": len(request.tasks),
            "task_categories": sorted({task.category for task in request.tasks}),
        },
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
    if plan.status not in RECOVERY_PLAN_STATUSES:
        raise _neutral_not_found()
    _validate_recovery_tasks(request.tasks, patient_id=profile.id, db=db)
    plan.title = request.title
    plan.instructions = request.instructions
    _replace_recovery_tasks(plan, request.tasks)
    _record_audit_event(
        db,
        actor_user_id=user.id,
        patient_id=profile.id,
        event_type="recovery_plan_updated",
        resource_type="recovery_plan",
        resource_id=plan.id,
        metadata={
            "status": plan.status,
            "task_count": len(request.tasks),
            "task_categories": sorted({task.category for task in request.tasks}),
        },
    )
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
    if plan.status != "active":
        active_plans = db.scalars(
            select(RecoveryPlan).where(
                RecoveryPlan.patient_id == profile.id,
                RecoveryPlan.status == "active",
                RecoveryPlan.id != plan.id,
            )
        ).all()
        for active_plan in active_plans:
            active_plan.status = "completed"
        plan.status = "active"
        plan.activated_at = datetime.now(UTC)
        _record_audit_event(
            db,
            actor_user_id=user.id,
            patient_id=profile.id,
            event_type="recovery_plan_activated",
            resource_type="recovery_plan",
            resource_id=plan.id,
            metadata={
                "replaced_active_count": len(active_plans),
                "task_count": len(plan.tasks),
                "task_categories": sorted({task.category for task in plan.tasks}),
            },
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


@router.get("/patient/me/care", response_model=PatientCareBundleResponse)
def own_patient_care(user: CurrentUser, db: DbSession) -> PatientCareBundleResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise _neutral_not_found()
    profile = user.patient_profile
    records = db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == profile.id)
        .order_by(MedicalRecord.recorded_at.desc())
    ).all()
    medications = db.scalars(
        select(Medication).where(Medication.patient_id == profile.id).order_by(Medication.name)
    ).all()
    return PatientCareBundleResponse(
        patient=_patient_response(profile),
        records=[_record_response(item) for item in records],
        medications=[_medication_response(item) for item in medications],
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
