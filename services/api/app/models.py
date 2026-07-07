import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
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


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(160))
    hospital_name: Mapped[str] = mapped_column(String(160))

    user: Mapped[User] = relationship(back_populates="doctor_profile")
    care_relationships: Mapped[list["CareRelationship"]] = relationship(back_populates="doctor")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(120))
    synthetic_identifier: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    user: Mapped[User] = relationship(back_populates="patient_profile")
    care_relationships: Mapped[list["CareRelationship"]] = relationship(back_populates="patient")
    medical_records: Mapped[list["MedicalRecord"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    medications: Mapped[list["Medication"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    doctor_notes: Mapped[list["DoctorNote"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    demo_assets: Mapped[list["DemoMedicalAsset"]] = relationship(
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


class Medication(Base):
    __tablename__ = "medications"
    __table_args__ = (Index("ix_medications_patient_status", "patient_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(160))
    dosage: Mapped[str] = mapped_column(String(120))
    schedule: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40))
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[PatientProfile] = relationship(back_populates="medications")


class DoctorNote(Base):
    __tablename__ = "doctor_notes"
    __table_args__ = (Index("ix_doctor_notes_patient_created", "patient_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[PatientProfile] = relationship(back_populates="doctor_notes")
    doctor: Mapped[DoctorProfile] = relationship()


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
    __table_args__ = (Index("ix_recovery_plans_patient_status", "patient_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(160))
    instructions: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    safety_label: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    patient: Mapped[PatientProfile] = relationship(back_populates="recovery_plans")
    doctor: Mapped[DoctorProfile] = relationship()
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
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recovery_plans.id", ondelete="CASCADE")
    )
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
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recovery_tasks.id", ondelete="CASCADE")
    )
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
    thread_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_threads.id", ondelete="CASCADE")
    )
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
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE")
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
