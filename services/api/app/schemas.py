from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models import UserRole


class PatientSignupProfileRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    birth_date: date | None = None
    gender: str | None = Field(default=None, min_length=2, max_length=40)
    contact_phone: str | None = Field(default=None, min_length=5, max_length=40)
    avatar_url: str | None = Field(default=None, max_length=3_000_000)
    country: str | None = Field(default=None, min_length=2, max_length=80)
    province: str | None = Field(default=None, min_length=2, max_length=80)
    city: str | None = Field(default=None, min_length=2, max_length=80)
    home_address: str | None = Field(default=None, min_length=2, max_length=240)
    height_cm: float | None = Field(default=None, ge=30, le=260)
    weight_kg: float | None = Field(default=None, ge=1, le=400)


class DoctorSignupProfileRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    birth_date: date | None = None
    gender: str | None = Field(default=None, min_length=2, max_length=40)
    contact_phone: str | None = Field(default=None, min_length=5, max_length=40)
    country: str | None = Field(default=None, min_length=2, max_length=80)
    province: str | None = Field(default=None, min_length=2, max_length=80)
    city: str | None = Field(default=None, min_length=2, max_length=80)
    hospital_name: str | None = Field(default=None, min_length=2, max_length=160)
    custom_hospital: bool = False
    avatar_url: str | None = Field(default=None, max_length=3_000_000)
    specialty: str | None = Field(default=None, min_length=2, max_length=120)
    department: str | None = Field(default=None, min_length=2, max_length=120)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=80)


class PayerSignupProfileRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str = Field(min_length=1, max_length=120)
    organization_name: str = Field(min_length=2, max_length=180)
    title: str = Field(default="Reviewer", min_length=2, max_length=120)
    organization_type: Literal["public_payer", "commercial_payer", "observer"] = "public_payer"


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=5, max_length=40)
    password: str = Field(min_length=8, max_length=20)
    role: UserRole
    verification_code: str = Field(min_length=6, max_length=12)
    terms_accepted: bool
    patient_profile: PatientSignupProfileRequest | None = None
    doctor_profile: DoctorSignupProfileRequest | None = None
    payer_profile: PayerSignupProfileRequest | None = None

    @model_validator(mode="after")
    def validate_registration(self) -> "RegisterRequest":
        if self.phone_number is None:
            raise ValueError("Provide a phone number.")
        if not self.terms_accepted:
            raise ValueError("Privacy and terms must be accepted.")
        if self.role == UserRole.payer and self.payer_profile is None:
            raise ValueError("Payer organization details are required.")
        return self


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=5, max_length=40)
    password: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_login_identifier(self) -> "LoginRequest":
        if self.email is None and self.phone_number is None:
            raise ValueError("Provide an email address or phone number.")
        return self


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=20)


class PhoneVerificationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    phone_number: str = Field(min_length=5, max_length=40)


class PhoneVerificationResponse(BaseModel):
    message: str
    expires_in: int
    debug_code: str | None = None


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    phone_number: str = Field(min_length=5, max_length=40)
    verification_code: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=20)


class AccountEmailUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr | None = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_is_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr | None
    phone_number: str | None = None
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


class PatientDoctorContactResponse(BaseModel):
    relationship_id: UUID
    doctor_id: UUID
    display_name: str
    title: str
    hospital_name: str
    specialty: str | None
    department: str | None
    avatar_url: str | None
    relationship_status: Literal["pending_patient_approval", "active", "rejected", "revoked"]
    request_version: int
    requested_at: datetime
    approved_at: datetime | None
    revoked_at: datetime | None


class PatientDoctorContactListResponse(BaseModel):
    items: list[PatientDoctorContactResponse]


class CareRelationshipActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)


class CareRelationshipResponse(BaseModel):
    relationship_id: UUID
    doctor_id: UUID
    patient_id: UUID
    status: Literal["pending_patient_approval", "active", "rejected", "revoked"]
    request_version: int
    requested_at: datetime
    responded_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None
    revoked_at: datetime | None


class DoctorPatientContactResponse(BaseModel):
    patient_id: UUID
    display_name: str
    avatar_url: str | None


class DoctorPatientContactListResponse(BaseModel):
    items: list[DoctorPatientContactResponse]


class PrivateMessageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message: str = Field(min_length=1, max_length=4000)


class PrivateMessageResponse(BaseModel):
    message_id: UUID
    thread_id: UUID
    sender_user_id: UUID
    sender_role: Literal["doctor", "patient"]
    content: str
    created_at: datetime


class PrivateMessageListResponse(BaseModel):
    thread_id: UUID | None
    items: list[PrivateMessageResponse]


class PatientConnectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    patient_code: str = Field(min_length=6, max_length=80)


class PatientMatchPreviewResponse(BaseModel):
    display_name: str
    masked_patient_code: str


class PatientProfileResponse(PatientSummaryResponse):
    relationship_label: str
    overview: str
    demographics: "PatientDemographicsResponse"


class PatientDemographicsUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    birth_date: date | None = None
    birth_year: int | None = Field(default=None, ge=1900, le=2026)
    sex: str | None = Field(default=None, min_length=2, max_length=40)
    gender: str | None = Field(default=None, min_length=2, max_length=40)
    contact_phone: str | None = Field(default=None, min_length=5, max_length=40)
    emergency_contact_name: str | None = Field(default=None, min_length=2, max_length=120)
    emergency_contact_phone: str | None = Field(default=None, min_length=5, max_length=40)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=80)
    contact_preference: str | None = Field(default=None, min_length=2, max_length=80)
    avatar_url: str | None = Field(default=None, max_length=3_000_000)
    country: str | None = Field(default=None, min_length=2, max_length=80)
    province: str | None = Field(default=None, min_length=2, max_length=80)
    city: str | None = Field(default=None, min_length=2, max_length=80)
    home_address: str | None = Field(default=None, min_length=2, max_length=240)
    height_cm: float | None = Field(default=None, ge=30, le=260)
    weight_kg: float | None = Field(default=None, ge=1, le=400)
    blood_type: Literal["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = None
    systolic_blood_pressure: int | None = Field(default=None, ge=50, le=260)
    diastolic_blood_pressure: int | None = Field(default=None, ge=30, le=180)
    smoking_status: Literal["Never", "Former", "Current"] | None = None
    alcohol_consumption: Literal["None or rare", "Occasional", "Weekly", "Daily"] | None = None
    heart_history: str | None = Field(default=None, max_length=2_000)
    endocrine_history: str | None = Field(default=None, max_length=2_000)
    neuro_history: str | None = Field(default=None, max_length=2_000)
    digestive_history: str | None = Field(default=None, max_length=2_000)
    respiratory_history: str | None = Field(default=None, max_length=2_000)
    kidney_history: str | None = Field(default=None, max_length=2_000)
    cancer_history: str | None = Field(default=None, max_length=2_000)
    patient_reported_medications: str | None = Field(default=None, max_length=4_000)
    surgery_history: str | None = Field(default=None, max_length=4_000)
    family_history: str | None = Field(default=None, max_length=4_000)
    lifestyle_notes: str | None = Field(default=None, max_length=4_000)
    pregnancy_status: (
        Literal["Prefer not to say", "Not applicable", "No", "Yes", "Unsure"] | None
    ) = None
    medical_history_setup_completed: bool | None = None


class PatientDemographicsResponse(BaseModel):
    display_name: str
    birth_date: date | None
    birth_year: int | None
    sex: str | None
    gender: str | None
    contact_phone: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    preferred_language: str | None
    contact_preference: str | None
    avatar_url: str | None
    country: str | None
    province: str | None
    city: str | None
    home_address: str | None
    height_cm: float | None
    weight_kg: float | None
    blood_type: str | None
    systolic_blood_pressure: int | None
    diastolic_blood_pressure: int | None
    smoking_status: str | None
    alcohol_consumption: str | None
    heart_history: str | None
    endocrine_history: str | None
    neuro_history: str | None
    digestive_history: str | None
    respiratory_history: str | None
    kidney_history: str | None
    cancer_history: str | None
    patient_reported_medications: str | None
    surgery_history: str | None
    family_history: str | None
    lifestyle_notes: str | None
    pregnancy_status: str | None
    medical_history_setup_completed: bool


class DoctorProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    title: str | None = Field(default=None, min_length=2, max_length=160)
    birth_date: date | None = None
    gender: str | None = Field(default=None, min_length=2, max_length=40)
    contact_phone: str | None = Field(default=None, min_length=5, max_length=40)
    avatar_url: str | None = Field(default=None, max_length=3_000_000)
    country: str | None = Field(default=None, min_length=2, max_length=80)
    province: str | None = Field(default=None, min_length=2, max_length=80)
    city: str | None = Field(default=None, min_length=2, max_length=80)
    specialty: str | None = Field(default=None, min_length=2, max_length=120)
    department: str | None = Field(default=None, min_length=2, max_length=120)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=80)


class DoctorProfileResponse(BaseModel):
    id: UUID
    display_name: str
    title: str
    birth_date: date | None
    gender: str | None
    contact_phone: str | None
    avatar_url: str | None
    country: str | None
    province: str | None
    city: str | None
    hospital_name: str
    specialty: str | None
    department: str | None
    preferred_language: str | None
    last_active_at: datetime | None
    is_recently_active: bool


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


class MedicalRecordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=80)
    summary: str = Field(min_length=2, max_length=4000)


class MedicationResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    name: str
    dosage: str
    schedule: str
    status: str
    note: str


class ClinicalFinancialInput(BaseModel):
    """Doctor-entered financial companion for a price-bearing clinical source."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    pricing_state: Literal["pending_cost", "estimated", "final"] = "pending_cost"
    service_date: date | None = None
    currency: Literal["CNY"] = "CNY"
    total_cost_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    payer_requested_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    patient_responsibility_minor: int = Field(default=0, ge=0, le=1_000_000_000)

    @model_validator(mode="after")
    def validate_allocation(self) -> "ClinicalFinancialInput":
        allocated = self.payer_requested_minor + self.patient_responsibility_minor
        if self.pricing_state == "pending_cost":
            if any(
                (
                    self.total_cost_minor,
                    self.payer_requested_minor,
                    self.patient_responsibility_minor,
                )
            ):
                raise ValueError("Pending-cost records cannot contain partial amounts.")
            return self
        if self.total_cost_minor <= 0:
            raise ValueError("Estimated and final costs must be greater than zero.")
        if allocated != self.total_cost_minor:
            raise ValueError(
                "Requested payer and expected patient amounts must equal the total cost."
            )
        return self


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
    financial: ClinicalFinancialInput | None = None


class PrescriptionMedicationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    medication_id: UUID | None = None
    name: str = Field(min_length=2, max_length=160)
    dosage: str = Field(min_length=1, max_length=120)
    schedule: str = Field(min_length=2, max_length=160)
    formulation_strength: str | None = Field(default=None, max_length=160)
    route: str | None = Field(default=None, max_length=80)
    recorded_directions: str | None = Field(default=None, max_length=1200)
    quantity: int | None = Field(default=None, ge=1, le=100_000)
    duration_days: int | None = Field(default=None, ge=1, le=3650)
    pricing_state: Literal["pending_cost", "estimated", "final"] = "pending_cost"
    currency: Literal["CNY"] = "CNY"
    unit_amount_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    total_amount_minor: int = Field(default=0, ge=0, le=1_000_000_000)
    start_date: date | None = None
    end_date: date | None = None


class PrescriptionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    status: Literal["draft", "finalized", "issued"] = "draft"
    issued_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1200)
    medications: list[PrescriptionMedicationInput] = Field(min_length=1, max_length=12)
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=120)
    supersedes_prescription_id: UUID | None = None


class PrescriptionMedicationResponse(BaseModel):
    id: UUID
    medication_id: UUID | None
    name: str
    dosage: str
    schedule: str
    formulation_strength: str | None
    route: str | None
    recorded_directions: str | None
    quantity: int | None
    duration_days: int | None
    sort_order: int
    pricing_state: str
    currency: str
    unit_amount_minor: int
    total_amount_minor: int
    start_date: date | None
    end_date: date | None


class PrescriptionResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    status: Literal["draft", "finalized", "issued"]
    version: int
    supersedes_prescription_id: UUID | None
    finalized_at: datetime | None
    content_checksum_sha256: str | None
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
    status: Literal[
        "queued",
        "sent",
        "scheduled",
        "unread",
        "read",
        "dismissed",
        "cancelled",
        "expired",
        "superseded",
    ]
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
    clinical_services: list["ClinicalServiceResponse"]
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


ClinicalServiceStatus = Literal[
    "planned",
    "ordered",
    "requested",
    "scheduled",
    "in_progress",
    "performed",
    "completed",
    "cancelled",
    "not_completed",
]


class ClinicalServiceRequest(BaseModel):
    """Doctor-owned delivered-service contract for the current Clinical Event."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID
    category: Literal[
        "imaging",
        "laboratory",
        "consultation",
        "treatment",
        "procedure",
        "surgery",
        "implant_device",
        "anesthesia",
        "rehabilitation",
        "other_service",
    ]
    name: str = Field(min_length=2, max_length=200)
    service_subtype: str = Field(min_length=2, max_length=80)
    body_region: str | None = Field(default=None, min_length=2, max_length=120)
    service_code: str | None = Field(default=None, max_length=80)
    performing_provider_name: str | None = Field(default=None, max_length=160)
    appointment_id: UUID | None = None
    status: ClinicalServiceStatus = "ordered"
    ordered_at: datetime | None = None
    scheduled_at: datetime | None = None
    performed_at: datetime | None = None
    indication_summary: str | None = Field(default=None, max_length=1200)
    service_date: date | None = None
    facility_name: str | None = Field(default=None, max_length=200)
    quantity: int = Field(default=1, ge=1, le=100_000)
    unit: str = Field(default="service", min_length=1, max_length=60)
    documentation_state: Literal["pending", "available", "reviewed", "not_applicable"] = "pending"
    provenance: dict[str, object] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=120)
    financial: ClinicalFinancialInput | None = None

    @model_validator(mode="after")
    def validate_lifecycle_dates(self) -> "ClinicalServiceRequest":
        if self.category == "imaging" and self.body_region is None:
            raise ValueError("Imaging services require a body region.")
        if (
            self.ordered_at is not None
            and self.scheduled_at is not None
            and self.scheduled_at < self.ordered_at
        ):
            raise ValueError("The scheduled time cannot precede the ordered time.")
        if self.status in {"scheduled", "in_progress"} and self.scheduled_at is None:
            raise ValueError("A scheduled time is required for this service status.")
        if self.status in {"performed", "completed"} and self.performed_at is None:
            raise ValueError("A performed time is required for this service status.")
        return self


class ClinicalServiceResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_event_id: UUID
    category: str
    name: str
    service_subtype: str | None
    body_region: str | None
    service_code: str | None
    ordered_by_doctor_id: UUID
    performing_provider_name: str | None
    clinic_id: UUID | None
    appointment_id: UUID | None
    status: ClinicalServiceStatus
    ordered_at: datetime | None
    scheduled_at: datetime | None
    performed_at: datetime | None
    indication_summary: str | None
    service_date: date | None
    facility_name: str | None
    quantity: int
    unit: str
    documentation_state: str
    provenance: dict[str, object]
    imaging_asset_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


class ClinicalServiceListResponse(BaseModel):
    items: list[ClinicalServiceResponse]
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
    clinical_service_id: UUID | None = None
    filename: str = Field(min_length=3, max_length=160, pattern=r"^[A-Za-z0-9._ -]+$")
    content_type: str = Field(min_length=3, max_length=80)
    size_bytes: int = Field(ge=1)


class MedicalImagingPresignResponse(BaseModel):
    asset_id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    clinical_service_id: UUID | None
    upload_url: str
    method: Literal["PUT"] = "PUT"
    headers: dict[str, str]
    expires_at: datetime
    max_size_bytes: int
    upload_status: Literal["pending_upload", "uploaded", "failed", "expired"]
    review_status: Literal["not_ready", "pending_review", "reviewed", "rejected"]
    storage_provider: Literal["local", "tencent_cos"]
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
    clinical_service_id: UUID | None
    storage_provider: Literal["local", "tencent_cos"]
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
    provenance_versions: list["MedicalImagingProvenanceResponse"] = Field(default_factory=list)
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class MedicalImagingAssetListResponse(BaseModel):
    items: list[MedicalImagingAssetResponse]
    next_cursor: None = None


class MedicalImagingProvenanceResponse(BaseModel):
    id: UUID
    version: int
    storage_provider: Literal["local", "tencent_cos"]
    content_type: str
    size_bytes: int
    checksum_sha256: str
    created_at: datetime


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

    category: Literal["medication", "exercise", "diet", "follow_up", "tracking", "custom"]
    title: str = Field(min_length=3, max_length=160)
    detail: str = Field(min_length=3, max_length=800)
    due_label: str = Field(min_length=3, max_length=80)
    scheduled_date: date | None = None
    scheduled_time: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    time_zone: str = Field(default="Asia/Shanghai", min_length=3, max_length=64)
    notification_time: str | None = Field(default=None, max_length=20)
    medication_id: UUID | None = None
    frequency: str = Field(default="as scheduled", min_length=2, max_length=120)
    schedule: str = Field(default="see plan", min_length=2, max_length=200)
    duration: str = Field(default="phase duration", min_length=2, max_length=120)
    responsible_person: str = Field(default="patient", min_length=2, max_length=120)
    completion_criteria: str = Field(
        default="completed as instructed", min_length=3, max_length=800
    )
    reminder: dict[str, object] = Field(default_factory=dict)


class RecoveryPhaseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    start_week: int | None = Field(default=None, ge=1, le=520)
    end_week: int | None = Field(default=None, ge=1, le=520)
    goals: str = Field(min_length=3, max_length=1200)
    instructions: str = Field(min_length=3, max_length=2000)
    precautions: str = Field(default="", max_length=1200)
    progression_criteria: str = Field(min_length=3, max_length=1200)
    hold_escalation_criteria: str = Field(min_length=3, max_length=1200)
    review_checkpoint: str | None = Field(default=None, max_length=800)
    tasks: list[RecoveryTaskInput] = Field(min_length=1, max_length=24)

    @model_validator(mode="after")
    def validate_range(self) -> "RecoveryPhaseInput":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Phase end date must be on or after its start date.")
        if self.start_week and self.end_week and self.end_week < self.start_week:
            raise ValueError("Phase end week must be on or after its start week.")
        if self.start_date is None and self.start_week is None:
            raise ValueError("Each phase requires a start date or start week.")
        return self


class RecoveryPlanCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    clinical_event_id: UUID | None = None
    title: str = Field(min_length=3, max_length=160)
    indication: str = Field(default="Recovery support", min_length=3, max_length=1200)
    start_date: date | None = None
    instructions: str = Field(default="Structured phase plan", min_length=3, max_length=1200)
    phases: list[RecoveryPhaseInput] = Field(default_factory=list, max_length=24)
    tasks: list[RecoveryTaskInput] = Field(default_factory=list, max_length=24)
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=120)
    supersedes_plan_id: UUID | None = None


class RecoveryPlanUpdateRequest(RecoveryPlanCreateRequest):
    pass


class RecoveryPlanSubmitReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_doctor_id: UUID | None = None
    expected_version: int = Field(ge=1)


class RecoveryPlanReviewActionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    expected_version: int = Field(ge=1)
    comment: str | None = Field(default=None, max_length=1200)


class RecoveryTaskResponse(BaseModel):
    task_id: UUID
    plan_id: UUID
    phase_id: UUID | None
    category: Literal["medication", "exercise", "diet", "follow_up", "tracking", "custom"]
    title: str
    detail: str
    due_label: str
    scheduled_date: date | None
    scheduled_time: str | None
    time_zone: str
    schedule_category: Literal["overdue", "today", "upcoming", "unscheduled"] | None = None
    plan_title: str
    clinical_event_id: UUID | None
    notification_time: str | None
    medication_id: UUID | None
    frequency: str | None
    schedule: str | None
    duration: str | None
    responsible_person: str | None
    completion_criteria: str | None
    reminder: dict[str, object]
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
    indication: str | None
    start_date: date | None
    version: int
    supersedes_plan_id: UUID | None
    status: Literal[
        "draft", "approved", "active", "published", "paused", "completed", "cancelled", "superseded"
    ]
    review_status: Literal["draft", "in_review", "changes_requested", "approved"]
    author_doctor_id: UUID
    assigned_reviewer_doctor_id: UUID | None
    submitted_version: int | None
    review_comment: str | None
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
    published_at: datetime | None
    paused_at: datetime | None
    cancelled_at: datetime | None
    progress_summary: RecoveryPlanProgressResponse
    tasks: list[RecoveryTaskResponse]
    phases: list["RecoveryPhaseResponse"]


class RecoveryPhaseResponse(BaseModel):
    phase_id: UUID
    sort_order: int
    name: str
    start_date: date | None
    end_date: date | None
    start_week: int | None
    end_week: int | None
    goals: str
    instructions: str
    precautions: str
    progression_criteria: str
    hold_escalation_criteria: str
    review_checkpoint: str | None
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
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    patient_id: UUID
    clinical_event_id: UUID | None = None
    specialty: str = Field(min_length=3, max_length=120)
    question_summary: str = Field(min_length=8, max_length=240)
    priority: Literal["routine", "soon"] = "routine"
    consultation_type: str = Field(default="specialist_referral", min_length=2, max_length=80)
    status: Literal["requested", "completed"] = "requested"
    clinician_provider: str = Field(default="Requested clinician", min_length=2, max_length=200)
    service_date: date | None = None
    reason_indication: str = Field(default="Specialist consultation", min_length=3, max_length=1200)
    outcome_summary: dict[str, object] = Field(default_factory=dict)
    follow_up_requirement: str = Field(default="To be determined", min_length=2, max_length=1200)
    quantity: int = Field(default=1, ge=1, le=1000)
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=120)
    financial: ClinicalFinancialInput | None = None


class ConsultationResponse(BaseModel):
    consultation_id: UUID
    patient_id: UUID
    clinical_event_id: UUID | None
    clinical_service_id: UUID | None
    specialty: str
    question_summary: str
    priority: Literal["routine", "soon"]
    consultation_type: str | None
    clinician_provider: str | None
    service_date: date | None
    reason_indication: str | None
    outcome_summary: dict[str, object]
    follow_up_requirement: str | None
    quantity: int
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


class SupportRequestWithdrawRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)


class SupportRequestTimelineEvent(BaseModel):
    sequence: int
    event_type: Literal["submitted", "status_changed", "withdrawn"]
    status: Literal["queued", "reviewing", "resolved", "failed", "cancelled"]
    actor_kind: Literal["requester", "system", "support_team"]
    summary_code: str
    occurred_at: datetime


class SupportRequestResponse(BaseModel):
    request_id: UUID
    reference: str
    request_type: Literal["support", "deletion", "feedback"]
    status: Literal["queued", "reviewing", "resolved", "failed", "cancelled"]
    version: int
    subject: str
    retention_boundary_code: Literal[
        "standard_support_retention",
        "regulated_and_audit_retention_applies",
    ]
    deletion_effect_code: Literal[
        "not_a_deletion_request",
        "request_only_no_immediate_deletion",
    ]
    available_actions: list[Literal["withdraw"]]
    timeline: list[SupportRequestTimelineEvent]
    replayed: bool = False
    created_at: datetime
    updated_at: datetime
    safety_label: Literal["Synthetic demonstration data only. Do not enter real patient data."] = (
        "Synthetic demonstration data only. Do not enter real patient data."
    )


class SupportRequestListResponse(BaseModel):
    items: list[SupportRequestResponse]
    next_cursor: None = None
