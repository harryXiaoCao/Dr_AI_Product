from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: UserRole
    invite_code: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    display_name: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse


class MeResponse(UserResponse):
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class DashboardResponse(BaseModel):
    role: UserRole
    data: dict[str, object]


class PatientSummaryResponse(BaseModel):
    patient_id: UUID
    display_name: str
    synthetic_identifier: str
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class PatientListResponse(BaseModel):
    items: list[PatientSummaryResponse]
    next_cursor: None = None


class PatientConnectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    patient_code: str = Field(min_length=6, max_length=80)


class PatientProfileResponse(PatientSummaryResponse):
    relationship_label: str
    overview: str
    demographics: "PatientDemographicsResponse"


class PatientDemographicsUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str | None = Field(default=None, min_length=2, max_length=120)
    birth_year: int | None = Field(default=None, ge=1900, le=2026)
    sex: str | None = Field(default=None, min_length=2, max_length=40)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=80)
    contact_preference: str | None = Field(default=None, min_length=2, max_length=80)


class PatientDemographicsResponse(BaseModel):
    display_name: str
    birth_year: int | None
    sex: str | None
    preferred_language: str | None
    contact_preference: str | None


class MedicalRecordResponse(BaseModel):
    id: UUID
    patient_id: UUID
    title: str
    category: str
    summary: str
    recorded_at: datetime


class MedicalRecordListResponse(BaseModel):
    items: list[MedicalRecordResponse]
    next_cursor: None = None


class MedicationResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    name: str
    dosage: str
    schedule: str
    status: str
    note: str


class MedicationListResponse(BaseModel):
    items: list[MedicationResponse]
    next_cursor: None = None


class MedicationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    name: str = Field(min_length=2, max_length=160)
    dosage: str = Field(min_length=1, max_length=120)
    schedule: str = Field(min_length=2, max_length=160)
    status: Literal["active", "paused", "stopped", "entered_in_error"] = "active"
    note: str = Field(default="", max_length=800)


class PrescriptionMedicationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    medication_id: UUID | None = None
    name: str = Field(min_length=2, max_length=160)
    dosage: str = Field(min_length=1, max_length=120)
    schedule: str = Field(min_length=2, max_length=160)
    start_date: date | None = None
    end_date: date | None = None


class PrescriptionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    status: Literal["draft", "issued", "cancelled"] = "draft"
    issued_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1200)
    medications: list[PrescriptionMedicationInput] = Field(min_length=1, max_length=12)


class PrescriptionMedicationResponse(BaseModel):
    id: UUID
    medication_id: UUID | None
    name: str
    dosage: str
    schedule: str
    start_date: date | None
    end_date: date | None


class PrescriptionResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    status: Literal["draft", "issued", "cancelled"]
    issued_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    medications: list[PrescriptionMedicationResponse]


class PrescriptionListResponse(BaseModel):
    items: list[PrescriptionResponse]
    next_cursor: None = None


class MedicationReminderRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    medication_id: UUID | None = None
    prescription_medication_id: UUID | None = None
    reminder_type: Literal["medication", "refill"] = "medication"
    schedule_label: str = Field(min_length=2, max_length=160)
    channel: Literal["in_app"] = "in_app"
    status: Literal["active", "paused", "completed", "cancelled"] = "active"
    next_due_at: datetime | None = None


class MedicationReminderResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    medication_id: UUID | None
    prescription_medication_id: UUID | None
    reminder_type: Literal["medication", "refill"]
    schedule_label: str
    channel: Literal["in_app"]
    status: Literal["active", "paused", "completed", "cancelled"]
    next_due_at: datetime | None
    last_sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MedicationReminderListResponse(BaseModel):
    items: list[MedicationReminderResponse]
    next_cursor: None = None


class NotificationResponse(BaseModel):
    id: UUID
    clinical_event_id: UUID | None
    notification_type: str
    channel: Literal["in_app"]
    status: Literal["queued", "sent", "cancelled"]
    scheduled_for: datetime | None
    sent_at: datetime | None
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    next_cursor: None = None


class DoctorNoteResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    title: str
    body: str
    created_at: datetime
    updated_at: datetime


class DoctorNoteListResponse(BaseModel):
    items: list[DoctorNoteResponse]
    next_cursor: None = None


class PatientCareBundleResponse(BaseModel):
    patient: PatientProfileResponse
    clinical_events: list["ClinicalEventResponse"]
    clinical_event_updates: list["ClinicalEventUpdateResponse"]
    medical_history_reviews: list["MedicalHistoryReviewResponse"]
    allergies: list["PatientAllergyResponse"]
    chronic_diseases: list["ChronicDiseaseResponse"]
    visit_history: list["VisitHistoryResponse"]
    diagnoses: list["DiagnosisResponse"]
    records: list[MedicalRecordResponse]
    imaging_assets: list["MedicalImagingAssetResponse"]
    medications: list[MedicationResponse]
    prescriptions: list[PrescriptionResponse]
    medication_reminders: list[MedicationReminderResponse]
    recovery_plans: list["RecoveryPlanResponse"]
    doctor_notes: list[DoctorNoteResponse]


class PatientAllergyRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    label: str = Field(min_length=2, max_length=160)
    reaction: str | None = Field(default=None, max_length=240)
    severity: Literal["unknown", "mild", "moderate", "severe"] = "unknown"
    status: Literal["active", "inactive", "entered_in_error"] = "active"


class PatientAllergyResponse(BaseModel):
    id: UUID
    patient_id: UUID
    label: str
    reaction: str | None
    severity: Literal["unknown", "mild", "moderate", "severe"]
    status: Literal["active", "inactive", "entered_in_error"]
    created_at: datetime
    updated_at: datetime


class PatientAllergyListResponse(BaseModel):
    items: list[PatientAllergyResponse]
    next_cursor: None = None


class ChronicDiseaseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=160)
    status: Literal["active", "inactive", "resolved", "entered_in_error"] = "active"
    diagnosed_on: date | None = None
    notes: str | None = Field(default=None, max_length=800)


class ChronicDiseaseResponse(BaseModel):
    id: UUID
    patient_id: UUID
    name: str
    status: Literal["active", "inactive", "resolved", "entered_in_error"]
    diagnosed_on: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ChronicDiseaseListResponse(BaseModel):
    items: list[ChronicDiseaseResponse]
    next_cursor: None = None


class MedicalHistoryReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    target_type: Literal["allergy", "chronic_disease", "medical_record"]
    target_id: UUID
    action: Literal["verified", "amendment", "correction_requested"]
    amendment_summary: str | None = Field(default=None, max_length=1200)
    correction_request: str | None = Field(default=None, max_length=1200)


class MedicalHistoryReviewResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID | None
    target_type: Literal["allergy", "chronic_disease", "medical_record"]
    target_id: UUID
    action: Literal["verified", "amendment", "correction_requested"]
    amendment_summary: str | None
    correction_request: str | None
    created_at: datetime


class MedicalHistoryReviewListResponse(BaseModel):
    items: list[MedicalHistoryReviewResponse]
    next_cursor: None = None


class VisitHistoryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    visit_type: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=3, max_length=160)
    summary: str = Field(min_length=3, max_length=1200)
    occurred_at: datetime
    clinician_label: str | None = Field(default=None, max_length=160)


class VisitHistoryResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    visit_type: str
    title: str
    summary: str
    occurred_at: datetime
    clinician_label: str | None
    created_at: datetime
    updated_at: datetime


class VisitHistoryListResponse(BaseModel):
    items: list[VisitHistoryResponse]
    next_cursor: None = None


class DiagnosisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    label: str = Field(min_length=2, max_length=160)
    status: Literal["active", "resolved", "entered_in_error"] = "active"
    diagnosed_on: date | None = None
    notes: str | None = Field(default=None, max_length=800)


class DiagnosisResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    label: str
    status: Literal["active", "resolved", "entered_in_error"]
    diagnosed_on: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class DiagnosisListResponse(BaseModel):
    items: list[DiagnosisResponse]
    next_cursor: None = None


class ClinicalEventRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=3, max_length=160)
    chief_complaint: str = Field(min_length=3, max_length=240)
    symptom_summary: str | None = Field(default=None, max_length=1200)
    diagnosis_summary: str | None = Field(default=None, max_length=1200)
    onset_date: date | None = None
    status: Literal["active", "monitoring", "resolved", "entered_in_error"] = "active"


class ClinicalEventTimelineEntry(BaseModel):
    entry_type: str
    resource_id: UUID | None = None
    title: str
    occurred_at: datetime


class ClinicalEventUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    update_type: Literal[
        "symptom_update",
        "medication_note",
        "recovery_check_in",
        "general_update",
    ] = "general_update"
    summary: str = Field(min_length=3, max_length=1200)
    occurred_at: datetime | None = None


class ClinicalEventUpdateResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID
    submitted_by_user_id: UUID
    update_type: Literal[
        "symptom_update",
        "medication_note",
        "recovery_check_in",
        "general_update",
    ]
    summary: str
    occurred_at: datetime
    created_at: datetime


class ClinicalEventUpdateListResponse(BaseModel):
    items: list[ClinicalEventUpdateResponse]
    next_cursor: None = None


class ClinicalEventResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID | None
    title: str
    chief_complaint: str
    symptom_summary: str | None
    diagnosis_summary: str | None
    onset_date: date | None
    status: Literal["active", "monitoring", "resolved", "entered_in_error"]
    linked_resource_counts: dict[str, int]
    timeline: list[ClinicalEventTimelineEntry] = Field(default_factory=list)
    patient_updates: list[ClinicalEventUpdateResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class ClinicalEventListResponse(BaseModel):
    items: list[ClinicalEventResponse]
    next_cursor: None = None


class DoctorNoteCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=3, max_length=1200)


class DoctorNoteUpdateRequest(DoctorNoteCreateRequest):
    pass


class DemoAssetPresignRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    filename: str = Field(min_length=3, max_length=160, pattern=r"^[A-Za-z0-9._ -]+$")
    content_type: str = Field(min_length=3, max_length=80)
    size_bytes: int = Field(ge=1)


class DemoAssetPresignResponse(BaseModel):
    asset_id: UUID
    patient_id: UUID
    upload_url: str
    method: Literal["PUT"] = "PUT"
    object_key: str
    headers: dict[str, str]
    expires_at: datetime
    max_size_bytes: int
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class MedicalImagingPresignRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    filename: str = Field(min_length=3, max_length=160, pattern=r"^[A-Za-z0-9._ -]+$")
    content_type: str = Field(min_length=3, max_length=80)
    size_bytes: int = Field(ge=1)


class MedicalImagingPresignResponse(BaseModel):
    asset_id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    upload_url: str
    method: Literal["PUT"] = "PUT"
    headers: dict[str, str]
    expires_at: datetime
    max_size_bytes: int
    upload_status: Literal["pending_upload", "uploaded", "failed", "expired"]
    review_status: Literal["not_ready", "pending_review", "reviewed", "rejected"]
    storage_provider: Literal["tencent_cos"]
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class MedicalImagingCompleteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    uploaded_size_bytes: int = Field(ge=1)
    etag: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern=r'^[A-Za-z0-9._"-]+$',
    )
    checksum_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]+$",
    )


class MedicalImagingReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    review_status: Literal["reviewed", "rejected"]
    finding_summary: str | None = Field(default=None, max_length=1200)
    measurement_summary: str | None = Field(default=None, max_length=240)
    observed_at: datetime | None = None
    treatment_relevance_date: date | None = None


class MedicalImagingAssetResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    storage_provider: Literal["tencent_cos"]
    content_type: str
    file_extension: str
    size_bytes: int
    uploaded_size_bytes: int | None
    upload_status: Literal["pending_upload", "uploaded", "failed", "expired"]
    review_status: Literal["not_ready", "pending_review", "reviewed", "rejected"]
    finding_summary: str | None
    measurement_summary: str | None
    observed_at: datetime | None
    treatment_relevance_date: date | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    uploaded_at: datetime | None
    reviewed_at: datetime | None
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class MedicalImagingAssetListResponse(BaseModel):
    items: list[MedicalImagingAssetResponse]
    next_cursor: None = None


class AssessmentRequest(BaseModel):
    mode: Literal["simulated"]
    fixture_id: str = Field(min_length=8, max_length=80)
    idempotency_key: str = Field(min_length=12, max_length=120)


class AssessmentResponse(BaseModel):
    assessment_id: UUID
    mode: Literal["simulated"]
    status: Literal["completed"]
    risk_band: Literal["low", "moderate", "high"]
    demo_score: float = Field(ge=0.0, le=1.0)
    input_completeness: Literal["complete", "partial", "insufficient"]
    model_version: str
    limitations: list[str]
    recommended_next_steps: list[str]
    safety_label: Literal["Research simulation - not for diagnosis."] = (
        "Research simulation - not for diagnosis."
    )
    created_at: datetime


class AssessmentListResponse(BaseModel):
    items: list[AssessmentResponse]
    next_cursor: None = None


class RecoveryTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    category: Literal["medication", "exercise", "diet", "follow_up"]
    title: str = Field(min_length=3, max_length=160)
    detail: str = Field(min_length=3, max_length=800)
    due_label: str = Field(min_length=3, max_length=80)
    notification_time: str | None = Field(default=None, max_length=20)
    medication_id: UUID | None = None


class RecoveryPlanCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    title: str = Field(min_length=3, max_length=160)
    instructions: str = Field(min_length=3, max_length=1200)
    tasks: list[RecoveryTaskInput] = Field(min_length=1, max_length=12)


class RecoveryPlanUpdateRequest(RecoveryPlanCreateRequest):
    pass


class RecoveryTaskResponse(BaseModel):
    task_id: UUID
    plan_id: UUID
    category: Literal["medication", "exercise", "diet", "follow_up"]
    title: str
    detail: str
    due_label: str
    notification_time: str | None
    medication_id: UUID | None
    is_completed: bool
    completed_at: datetime | None
    notification_status: str | None = None


class RecoveryPlanProgressResponse(BaseModel):
    task_count: int
    completed_task_count: int
    remaining_task_count: int
    completion_percent: int


class RecoveryPlanResponse(BaseModel):
    plan_id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    title: str
    instructions: str
    status: Literal["draft", "active", "completed"]
    review_status: Literal["draft", "in_review", "changes_requested", "approved"]
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    reviewed_at: datetime | None
    approved_at: datetime | None
    activated_at: datetime | None
    completed_at: datetime | None
    progress_summary: RecoveryPlanProgressResponse
    tasks: list[RecoveryTaskResponse]


class RecoveryPlanListResponse(BaseModel):
    items: list[RecoveryPlanResponse]
    next_cursor: None = None


class TaskCompletionRequest(BaseModel):
    completed: Literal[True] = True


class TaskCompletionResponse(BaseModel):
    task: RecoveryTaskResponse


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=3, max_length=800)
    stream: bool = True


class ChatMessageResponse(BaseModel):
    thread_id: UUID
    thread_key: str
    message_id: UUID
    assistant_message_id: UUID
    content: str
    response_chunks: list[str]
    response_mode: Literal["stream_ready"] = "stream_ready"
    safety_label: Literal["Educational information only - not medical advice."] = (
        "Educational information only - not medical advice."
    )
    emergency_label: str | None = None
    is_red_flag: bool
    fallback_reason: str | None = None
    model: str
    created_at: datetime


class ConsultationCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_id: UUID
    clinical_event_id: UUID | None = None
    specialty: str = Field(min_length=3, max_length=120)
    question_summary: str = Field(min_length=8, max_length=240)
    priority: Literal["routine", "soon"] = "routine"


class ConsultationResponse(BaseModel):
    consultation_id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    specialty: str
    question_summary: str
    priority: Literal["routine", "soon"]
    status: Literal["requested", "accepted", "completed", "cancelled"]
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )
    created_at: datetime
    updated_at: datetime


class ConsultationListResponse(BaseModel):
    items: list[ConsultationResponse]
    next_cursor: None = None


class SupportRequestCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    request_type: Literal["support", "deletion", "feedback"]
    subject: str = Field(min_length=3, max_length=160)
    message: str = Field(min_length=8, max_length=2000)


class SupportRequestResponse(BaseModel):
    request_id: UUID
    request_type: Literal["support", "deletion", "feedback"]
    status: Literal["queued", "reviewing", "resolved", "cancelled"]
    subject: str
    created_at: datetime
    updated_at: datetime
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class SupportRequestListResponse(BaseModel):
    items: list[SupportRequestResponse]
    next_cursor: None = None
