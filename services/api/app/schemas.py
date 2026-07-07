from datetime import datetime
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


class PatientProfileResponse(PatientSummaryResponse):
    relationship_label: str
    overview: str


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
    name: str
    dosage: str
    schedule: str
    status: str
    note: str


class MedicationListResponse(BaseModel):
    items: list[MedicationResponse]
    next_cursor: None = None


class DoctorNoteResponse(BaseModel):
    id: UUID
    patient_id: UUID
    title: str
    body: str
    created_at: datetime


class DoctorNoteListResponse(BaseModel):
    items: list[DoctorNoteResponse]
    next_cursor: None = None


class PatientCareBundleResponse(BaseModel):
    patient: PatientProfileResponse
    records: list[MedicalRecordResponse]
    medications: list[MedicationResponse]
    doctor_notes: list[DoctorNoteResponse]


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
    category: Literal["medication", "exercise", "diet", "follow_up"]
    title: str = Field(min_length=3, max_length=160)
    detail: str = Field(min_length=3, max_length=800)
    due_label: str = Field(min_length=3, max_length=80)
    notification_time: str | None = Field(default=None, max_length=20)
    medication_id: UUID | None = None


class RecoveryPlanCreateRequest(BaseModel):
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


class RecoveryPlanResponse(BaseModel):
    plan_id: UUID
    patient_id: UUID
    title: str
    instructions: str
    status: Literal["draft", "active", "completed"]
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )
    created_at: datetime
    updated_at: datetime
    activated_at: datetime | None
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
    specialty: str = Field(min_length=3, max_length=120)
    question_summary: str = Field(min_length=8, max_length=240)
    priority: Literal["routine", "soon"] = "routine"


class ConsultationResponse(BaseModel):
    consultation_id: UUID
    patient_id: UUID
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
