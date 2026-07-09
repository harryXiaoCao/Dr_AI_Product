import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(enum.StrEnum):
    doctor = "doctor"
    patient = "patient"
    specialist = "specialist"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(40), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", native_enum=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    doctor_profile: Mapped["DoctorProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    patient_profile: Mapped["PatientProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    dashboard: Mapped["DashboardSnapshot | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    role_assignments: Mapped[list["RoleAssignment"]] = relationship(
        foreign_keys="RoleAssignment.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(160))
    hospital_name: Mapped[str] = mapped_column(String(160))
    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(40))
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(80))
    province: Mapped[str | None] = mapped_column(String(80))
    city: Mapped[str | None] = mapped_column(String(80))
    specialty: Mapped[str | None] = mapped_column(String(120))
    department: Mapped[str | None] = mapped_column(String(120))
    preferred_language: Mapped[str | None] = mapped_column(String(80))

    user: Mapped[User] = relationship(back_populates="doctor_profile")
    care_relationships: Mapped[list["CareRelationship"]] = relationship(back_populates="doctor")
    clinical_events: Mapped[list["ClinicalEvent"]] = relationship(back_populates="doctor")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(120))
    synthetic_identifier: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_year: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(String(40))
    gender: Mapped[str | None] = mapped_column(String(40))
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    emergency_contact_name: Mapped[str | None] = mapped_column(String(120))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(40))
    preferred_language: Mapped[str | None] = mapped_column(String(80))
    contact_preference: Mapped[str | None] = mapped_column(String(80))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(80))
    province: Mapped[str | None] = mapped_column(String(80))
    city: Mapped[str | None] = mapped_column(String(80))
    home_address: Mapped[str | None] = mapped_column(String(240))
    medical_history_setup_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="patient_profile")
    care_relationships: Mapped[list["CareRelationship"]] = relationship(back_populates="patient")
    medical_records: Mapped[list["MedicalRecord"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    medical_history_reviews: Mapped[list["MedicalHistoryReview"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    medications: Mapped[list["Medication"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    doctor_notes: Mapped[list["DoctorNote"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    allergies: Mapped[list["PatientAllergy"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    chronic_diseases: Mapped[list["ChronicDisease"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    visit_history: Mapped[list["VisitHistory"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    diagnoses: Mapped[list["Diagnosis"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    demo_assets: Mapped[list["DemoMedicalAsset"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    imaging_assets: Mapped[list["MedicalImagingAsset"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    simulated_assessments: Mapped[list["SimulatedAssessment"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    recovery_plans: Mapped[list["RecoveryPlan"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    chat_threads: Mapped[list["ChatThread"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    consultation_requests: Mapped[list["ConsultationRequest"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    clinical_events: Mapped[list["ClinicalEvent"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    clinical_event_updates: Mapped[list["ClinicalEventUpdate"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class CareRelationship(Base):
    __tablename__ = "care_relationships"
    __table_args__ = (
        UniqueConstraint("doctor_id", "patient_id", name="uq_care_doctor_patient"),
        Index("ix_care_active_lookup", "doctor_id", "patient_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="CASCADE")
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    doctor: Mapped[DoctorProfile] = relationship(back_populates="care_relationships")
    patient: Mapped[PatientProfile] = relationship(back_populates="care_relationships")


class ClinicalEvent(Base):
    __tablename__ = "clinical_events"
    __table_args__ = (
        Index("ix_clinical_events_patient_status", "patient_id", "status"),
        Index("ix_clinical_events_doctor_updated", "doctor_id", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(160))
    chief_complaint: Mapped[str] = mapped_column(String(240))
    symptom_summary: Mapped[str | None] = mapped_column(Text)
    diagnosis_summary: Mapped[str | None] = mapped_column(Text)
    onset_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(40), default="active")
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="clinical_events")
    doctor: Mapped[DoctorProfile | None] = relationship(back_populates="clinical_events")
    medications: Mapped[list["Medication"]] = relationship(back_populates="clinical_event")
    doctor_notes: Mapped[list["DoctorNote"]] = relationship(back_populates="clinical_event")
    visit_history: Mapped[list["VisitHistory"]] = relationship(back_populates="clinical_event")
    diagnoses: Mapped[list["Diagnosis"]] = relationship(back_populates="clinical_event")
    imaging_assets: Mapped[list["MedicalImagingAsset"]] = relationship(
        back_populates="clinical_event"
    )
    recovery_plans: Mapped[list["RecoveryPlan"]] = relationship(back_populates="clinical_event")
    prescriptions: Mapped[list["Prescription"]] = relationship(back_populates="clinical_event")
    medication_reminders: Mapped[list["MedicationReminder"]] = relationship(
        back_populates="clinical_event"
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="clinical_event")
    consultation_requests: Mapped[list["ConsultationRequest"]] = relationship(
        back_populates="clinical_event"
    )
    patient_updates: Mapped[list["ClinicalEventUpdate"]] = relationship(
        back_populates="clinical_event", cascade="all, delete-orphan"
    )


class ClinicalEventUpdate(Base):
    __tablename__ = "clinical_event_updates"
    __table_args__ = (
        Index("ix_clinical_event_updates_event_created", "clinical_event_id", "created_at"),
        Index("ix_clinical_event_updates_patient_created", "patient_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="CASCADE")
    )
    submitted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    update_type: Mapped[str] = mapped_column(String(60))
    summary: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[PatientProfile] = relationship(back_populates="clinical_event_updates")
    clinical_event: Mapped[ClinicalEvent] = relationship(back_populates="patient_updates")
    submitted_by: Mapped[User] = relationship()


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    __table_args__ = (
        Index("ix_refresh_family", "family_id"),
        Index("ix_refresh_user_active", "user_id", "revoked_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("refresh_sessions.id", ondelete="SET NULL")
    )

    user: Mapped[User] = relationship(back_populates="refresh_sessions")


class DashboardSnapshot(Base):
    __tablename__ = "dashboard_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    payload: Mapped[dict[str, object]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="dashboard")


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    __table_args__ = (Index("ix_medical_records_patient_recorded", "patient_id", "recorded_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[PatientProfile] = relationship(back_populates="medical_records")


class MedicalHistoryReview(Base):
    __tablename__ = "medical_history_reviews"
    __table_args__ = (
        Index("ix_medical_history_reviews_patient_created", "patient_id", "created_at"),
        Index("ix_medical_history_reviews_target", "target_type", "target_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="SET NULL")
    )
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(40))
    amendment_summary: Mapped[str | None] = mapped_column(Text)
    correction_request: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[PatientProfile] = relationship(back_populates="medical_history_reviews")
    doctor: Mapped[DoctorProfile | None] = relationship()


class Medication(Base):
    __tablename__ = "medications"
    __table_args__ = (
        Index("ix_medications_patient_status", "patient_id", "status"),
        Index("ix_medications_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(160))
    dosage: Mapped[str] = mapped_column(String(120))
    schedule: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40))
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[PatientProfile] = relationship(back_populates="medications")
    clinical_event: Mapped[ClinicalEvent | None] = relationship(back_populates="medications")


class DoctorNote(Base):
    __tablename__ = "doctor_notes"
    __table_args__ = (
        Index("ix_doctor_notes_patient_created", "patient_id", "created_at"),
        Index("ix_doctor_notes_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="doctor_notes")
    doctor: Mapped[DoctorProfile] = relationship()
    clinical_event: Mapped[ClinicalEvent | None] = relationship(back_populates="doctor_notes")


class PatientAllergy(Base):
    __tablename__ = "patient_allergies"
    __table_args__ = (Index("ix_patient_allergies_patient_status", "patient_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String(160))
    reaction: Mapped[str | None] = mapped_column(String(240))
    severity: Mapped[str] = mapped_column(String(40), default="unknown")
    status: Mapped[str] = mapped_column(String(40), default="active")
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="allergies")
    recorded_by: Mapped[User] = relationship()


class ChronicDisease(Base):
    __tablename__ = "chronic_diseases"
    __table_args__ = (Index("ix_chronic_diseases_patient_status", "patient_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active")
    diagnosed_on: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="chronic_diseases")
    recorded_by: Mapped[User] = relationship()


class VisitHistory(Base):
    __tablename__ = "visit_history"
    __table_args__ = (
        Index("ix_visit_history_patient_occurred", "patient_id", "occurred_at"),
        Index("ix_visit_history_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    visit_type: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    clinician_label: Mapped[str | None] = mapped_column(String(160))
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="visit_history")
    recorded_by: Mapped[User] = relationship()
    clinical_event: Mapped[ClinicalEvent | None] = relationship(back_populates="visit_history")


class Diagnosis(Base):
    __tablename__ = "diagnoses"
    __table_args__ = (
        Index("ix_diagnoses_patient_status", "patient_id", "status"),
        Index("ix_diagnoses_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    label: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active")
    diagnosed_on: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="diagnoses")
    recorded_by: Mapped[User] = relationship()
    clinical_event: Mapped[ClinicalEvent | None] = relationship(back_populates="diagnoses")


class DemoMedicalAsset(Base):
    __tablename__ = "demo_medical_assets"
    __table_args__ = (Index("ix_demo_assets_patient_created", "patient_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    filename: Mapped[str] = mapped_column(String(160))
    content_type: Mapped[str] = mapped_column(String(80))
    size_bytes: Mapped[int]
    object_key: Mapped[str] = mapped_column(String(240), unique=True)
    status: Mapped[str] = mapped_column(String(40), default="presigned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    patient: Mapped[PatientProfile] = relationship(back_populates="demo_assets")
    uploaded_by: Mapped[User] = relationship()


class MedicalImagingAsset(Base):
    __tablename__ = "medical_imaging_assets"
    __table_args__ = (
        Index("ix_medical_imaging_patient_created", "patient_id", "created_at"),
        Index("ix_medical_imaging_patient_review", "patient_id", "review_status"),
        Index("ix_medical_imaging_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    storage_provider: Mapped[str] = mapped_column(String(40), default="tencent_cos")
    content_type: Mapped[str] = mapped_column(String(80))
    file_extension: Mapped[str] = mapped_column(String(16))
    size_bytes: Mapped[int]
    uploaded_size_bytes: Mapped[int | None]
    object_key: Mapped[str] = mapped_column(String(260), unique=True)
    upload_status: Mapped[str] = mapped_column(String(40), default="pending_upload")
    review_status: Mapped[str] = mapped_column(String(40), default="not_ready")
    finding_summary: Mapped[str | None] = mapped_column(Text)
    measurement_summary: Mapped[str | None] = mapped_column(String(240))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    treatment_relevance_date: Mapped[date | None] = mapped_column(Date)
    etag: Mapped[str | None] = mapped_column(String(128))
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    patient: Mapped[PatientProfile] = relationship(back_populates="imaging_assets")
    uploaded_by: Mapped[User] = relationship(foreign_keys=[uploaded_by_user_id])
    reviewed_by: Mapped[User | None] = relationship(foreign_keys=[reviewed_by_user_id])
    clinical_event: Mapped[ClinicalEvent | None] = relationship(back_populates="imaging_assets")


class SimulatedAssessment(Base):
    __tablename__ = "simulated_assessments"
    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "actor_user_id",
            "idempotency_key",
            name="uq_sim_assessment_idempotency",
        ),
        Index("ix_sim_assessments_patient_created", "patient_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    fixture_id: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(120))
    request_hash: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40))
    risk_band: Mapped[str] = mapped_column(String(40))
    demo_score: Mapped[str] = mapped_column(String(12))
    input_completeness: Mapped[str] = mapped_column(String(40))
    model_version: Mapped[str] = mapped_column(String(80))
    limitations: Mapped[list[str]] = mapped_column(JSONB)
    recommended_next_steps: Mapped[list[str]] = mapped_column(JSONB)
    safety_label: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[PatientProfile] = relationship(back_populates="simulated_assessments")
    actor: Mapped[User] = relationship()


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"
    __table_args__ = (
        Index("ix_recovery_plans_patient_status", "patient_id", "status"),
        Index("ix_recovery_plans_patient_review", "patient_id", "review_status"),
        Index("ix_recovery_plans_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(160))
    instructions: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    review_status: Mapped[str] = mapped_column(String(40), default="draft")
    safety_label: Mapped[str] = mapped_column(String(120))
    review_actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    patient: Mapped[PatientProfile] = relationship(back_populates="recovery_plans")
    doctor: Mapped[DoctorProfile] = relationship()
    review_actor: Mapped[User | None] = relationship()
    clinical_event: Mapped[ClinicalEvent | None] = relationship(back_populates="recovery_plans")
    tasks: Mapped[list["RecoveryTask"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="RecoveryTask.sort_order"
    )


class RecoveryTask(Base):
    __tablename__ = "recovery_tasks"
    __table_args__ = (
        Index("ix_recovery_tasks_patient_category", "patient_id", "category"),
        Index("ix_recovery_tasks_plan_sort", "plan_id", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_plans.id", ondelete="CASCADE"))
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    medication_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medications.id", ondelete="SET NULL")
    )
    category: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(160))
    detail: Mapped[str] = mapped_column(Text)
    due_label: Mapped[str] = mapped_column(String(80))
    notification_time: Mapped[str | None] = mapped_column(String(20))
    sort_order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plan: Mapped[RecoveryPlan] = relationship(back_populates="tasks")
    patient: Mapped[PatientProfile] = relationship()
    medication: Mapped[Medication | None] = relationship()
    completions: Mapped[list["RecoveryTaskCompletion"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class RecoveryTaskCompletion(Base):
    __tablename__ = "recovery_task_completions"
    __table_args__ = (
        UniqueConstraint("task_id", "patient_id", name="uq_recovery_completion_task_patient"),
        Index("ix_recovery_completions_patient_completed", "patient_id", "completed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_tasks.id", ondelete="CASCADE"))
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    task: Mapped[RecoveryTask] = relationship(back_populates="completions")
    patient: Mapped[PatientProfile] = relationship()
    actor: Mapped[User] = relationship()


class ChatThread(Base):
    __tablename__ = "chat_threads"
    __table_args__ = (
        UniqueConstraint("patient_id", "thread_key", name="uq_chat_thread_patient_key"),
        Index("ix_chat_threads_patient_updated", "patient_id", "last_message_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    thread_key: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    patient: Mapped[PatientProfile] = relationship(back_populates="chat_threads")
    created_by: Mapped[User] = relationship()
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_thread_created", "thread_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_threads.id", ondelete="CASCADE"))
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(40))
    prompt_hash: Mapped[str | None] = mapped_column(String(64))
    prompt_char_count: Mapped[int | None] = mapped_column(Integer)
    safety_category: Mapped[str] = mapped_column(String(80))
    fallback_reason: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(120))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    thread: Mapped[ChatThread] = relationship(back_populates="messages")
    patient: Mapped[PatientProfile] = relationship()
    actor: Mapped[User] = relationship()


class ChatRateLimit(Base):
    __tablename__ = "chat_rate_limits"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship()


class ConsultationRequest(Base):
    __tablename__ = "consultation_requests"
    __table_args__ = (
        Index("ix_consultations_patient_status", "patient_id", "status"),
        Index("ix_consultations_requested_by_created", "requested_by_user_id", "created_at"),
        Index("ix_consultations_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    specialty: Mapped[str] = mapped_column(String(120))
    question_summary: Mapped[str] = mapped_column(String(240))
    priority: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="requested")
    safety_label: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="consultation_requests")
    requested_by: Mapped[User] = relationship()
    clinical_event: Mapped[ClinicalEvent | None] = relationship(
        back_populates="consultation_requests"
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_patient_created", "patient_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    event_type: Mapped[str] = mapped_column(String(80))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    actor: Mapped[User] = relationship()
    patient: Mapped[PatientProfile | None] = relationship()


class Hospital(Base):
    __tablename__ = "hospitals"
    __table_args__ = (Index("ix_hospitals_status", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    legal_name: Mapped[str | None] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(40), default="active")
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    clinics: Mapped[list["Clinic"]] = relationship(
        back_populates="hospital", cascade="all, delete-orphan"
    )


class Clinic(Base):
    __tablename__ = "clinics"
    __table_args__ = (
        UniqueConstraint("hospital_id", "name", name="uq_clinic_hospital_name"),
        Index("ix_clinics_hospital_status", "hospital_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hospitals.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    status: Mapped[str] = mapped_column(String(40), default="active")
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    hospital: Mapped[Hospital] = relationship(back_populates="clinics")


class RoleAssignment(Base):
    __tablename__ = "role_assignments"
    __table_args__ = (
        Index("ix_role_assignments_user_status", "user_id", "status"),
        Index("ix_role_assignments_clinic_role", "clinic_id", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", native_enum=True))
    hospital_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("hospitals.id", ondelete="CASCADE")
    )
    clinic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE")
    )
    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(40), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(foreign_keys=[user_id], back_populates="role_assignments")
    assigned_by: Mapped[User | None] = relationship(foreign_keys=[assigned_by_user_id])
    hospital: Mapped[Hospital | None] = relationship()
    clinic: Mapped[Clinic | None] = relationship()


class DoctorTeam(Base):
    __tablename__ = "doctor_teams"
    __table_args__ = (
        UniqueConstraint("clinic_id", "name", name="uq_doctor_team_clinic_name"),
        Index("ix_doctor_teams_clinic_status", "clinic_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active")
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    clinic: Mapped[Clinic] = relationship()
    memberships: Mapped[list["DoctorTeamMembership"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )


class DoctorTeamMembership(Base):
    __tablename__ = "doctor_team_memberships"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_doctor_team_membership_user"),
        Index("ix_doctor_team_memberships_user_status", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctor_teams.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(80))
    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(40), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    team: Mapped[DoctorTeam] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    assigned_by: Mapped[User | None] = relationship(foreign_keys=[assigned_by_user_id])


class ClinicResource(Base):
    __tablename__ = "clinic_resources"
    __table_args__ = (
        Index("ix_clinic_resources_clinic_type_status", "clinic_id", "resource_type", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"))
    resource_type: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="available")
    capacity_current: Mapped[int | None] = mapped_column(Integer)
    capacity_total: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    clinic: Mapped[Clinic] = relationship()


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (Index("ix_equipment_clinic_status", "clinic_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinic_resources.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(160))
    equipment_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="available")
    location_label: Mapped[str | None] = mapped_column(String(160))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    clinic: Mapped[Clinic] = relationship()
    resource: Mapped[ClinicResource | None] = relationship()


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_patient_start", "patient_id", "scheduled_start"),
        Index("ix_appointments_clinic_status_start", "clinic_id", "status", "scheduled_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"))
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="SET NULL")
    )
    specialist_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(40), default="requested")
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason_code: Mapped[str] = mapped_column(String(80))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    clinic: Mapped[Clinic] = relationship()
    patient: Mapped[PatientProfile] = relationship()
    doctor: Mapped[DoctorProfile | None] = relationship()
    specialist: Mapped[User | None] = relationship()


class EquipmentBooking(Base):
    __tablename__ = "equipment_bookings"
    __table_args__ = (
        Index("ix_equipment_bookings_equipment_start", "equipment_id", "start_at"),
        Index("ix_equipment_bookings_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"))
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL")
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(40), default="requested")
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    purpose: Mapped[str] = mapped_column(String(160))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    equipment: Mapped[Equipment] = relationship()
    appointment: Mapped[Appointment | None] = relationship()
    requested_by: Mapped[User] = relationship()
    patient: Mapped[PatientProfile | None] = relationship()


class Prescription(Base):
    __tablename__ = "prescriptions"
    __table_args__ = (
        Index("ix_prescriptions_patient_status", "patient_id", "status"),
        Index("ix_prescriptions_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    prescribed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(40), default="draft")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship()
    prescribed_by: Mapped[User] = relationship()
    clinical_event: Mapped[ClinicalEvent | None] = relationship(back_populates="prescriptions")
    medications: Mapped[list["PrescriptionMedication"]] = relationship(
        back_populates="prescription",
        cascade="all, delete-orphan",
    )


class PrescriptionMedication(Base):
    __tablename__ = "prescription_medications"
    __table_args__ = (Index("ix_prescription_medications_prescription", "prescription_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prescription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prescriptions.id", ondelete="CASCADE")
    )
    medication_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medications.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(160))
    dosage: Mapped[str] = mapped_column(String(120))
    schedule: Mapped[str] = mapped_column(String(160))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)

    prescription: Mapped[Prescription] = relationship(back_populates="medications")
    medication: Mapped[Medication | None] = relationship()


class MedicationReminder(Base):
    __tablename__ = "medication_reminders"
    __table_args__ = (
        Index("ix_medication_reminders_patient_status", "patient_id", "status"),
        Index("ix_medication_reminders_next_due", "next_due_at"),
        Index("ix_medication_reminders_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    medication_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medications.id", ondelete="SET NULL")
    )
    prescription_medication_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("prescription_medications.id", ondelete="SET NULL")
    )
    schedule_label: Mapped[str] = mapped_column(String(160))
    channel: Mapped[str] = mapped_column(String(40), default="in_app")
    status: Mapped[str] = mapped_column(String(40), default="active")
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship()
    medication: Mapped[Medication | None] = relationship()
    prescription_medication: Mapped[PrescriptionMedication | None] = relationship()
    clinical_event: Mapped[ClinicalEvent | None] = relationship(
        back_populates="medication_reminders"
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_patient_type", "patient_id", "notification_type"),
        Index("ix_notifications_clinical_event", "clinical_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinical_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="SET NULL")
    )
    notification_type: Mapped[str] = mapped_column(String(80))
    channel: Mapped[str] = mapped_column(String(40), default="in_app")
    status: Mapped[str] = mapped_column(String(40), default="queued")
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship()
    patient: Mapped[PatientProfile | None] = relationship()
    clinical_event: Mapped[ClinicalEvent | None] = relationship(back_populates="notifications")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_patient_status", "patient_id", "status"),
        Index("ix_invoices_clinic_status", "clinic_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(40), default="draft")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    total_cents: Mapped[int] = mapped_column(Integer, default=0)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[PatientProfile] = relationship()
    clinic: Mapped[Clinic | None] = relationship()


class PaymentStatus(Base):
    __tablename__ = "payment_statuses"
    __table_args__ = (Index("ix_payment_statuses_invoice_status", "invoice_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(80), default="manual")
    status: Mapped[str] = mapped_column(String(40), default="pending")
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    invoice: Mapped[Invoice] = relationship()


class RevenueSummary(Base):
    __tablename__ = "revenue_summaries"
    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "period_start",
            "period_end",
            name="uq_revenue_summary_period",
        ),
        Index("ix_revenue_summaries_clinic_period", "clinic_id", "period_start", "period_end"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    invoiced_cents: Mapped[int] = mapped_column(Integer, default=0)
    paid_cents: Mapped[int] = mapped_column(Integer, default=0)
    outstanding_cents: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    clinic: Mapped[Clinic] = relationship()


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (
        Index("ix_analytics_events_type_occurred", "event_type", "occurred_at"),
        Index("ix_analytics_events_patient_occurred", "patient_id", "occurred_at"),
        Index("ix_analytics_events_clinic_occurred", "clinic_id", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    clinic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE")
    )
    event_type: Mapped[str] = mapped_column(String(120))
    resource_type: Mapped[str | None] = mapped_column(String(80))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    actor: Mapped[User | None] = relationship()
    patient: Mapped[PatientProfile | None] = relationship()
    clinic: Mapped[Clinic | None] = relationship()


class SupportRequest(Base):
    __tablename__ = "support_requests"
    __table_args__ = (
        Index("ix_support_requests_requester_status", "requester_user_id", "status"),
        Index("ix_support_requests_patient_type_status", "patient_id", "request_type", "status"),
        Index("ix_support_requests_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="SET NULL")
    )
    request_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="queued")
    subject: Mapped[str] = mapped_column(String(160))
    body_redacted: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80), default="authenticated_app")
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    audit_metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    requester: Mapped[User | None] = relationship(foreign_keys=[requester_user_id])
    patient: Mapped[PatientProfile | None] = relationship()
    assigned_to: Mapped[User | None] = relationship(foreign_keys=[assigned_to_user_id])
