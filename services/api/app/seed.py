from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import SessionLocal
from app.models import (
    CareRelationship,
    DashboardSnapshot,
    DoctorNote,
    DoctorProfile,
    MedicalRecord,
    Medication,
    PatientProfile,
    RecoveryPlan,
    RecoveryTask,
    User,
    UserRole,
)
from app.security import hash_password


@dataclass(frozen=True)
class SeedResult:
    users_created: int
    relationships_created: int
    dashboards_created: int
    records_created: int
    medications_created: int
    notes_created: int
    recovery_plans_created: int
    recovery_tasks_created: int


def _required_password(settings: Settings, field_name: str) -> str:
    value = getattr(settings, field_name)
    if value is None:
        env_name = f"DR_AI_{field_name.upper()}"
        raise RuntimeError(f"{env_name} is required to create synthetic seed accounts")
    password = value.get_secret_value()
    if len(password) < 12:
        raise RuntimeError(f"DR_AI_{field_name.upper()} must contain at least 12 characters")
    return password


def _get_or_create_user(
    db: Session,
    *,
    email: str,
    password: str,
    role: UserRole,
    display_name: str,
    synthetic_identifier: str | None = None,
) -> tuple[User, bool]:
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user, False
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()
    if role == UserRole.doctor:
        db.add(
            DoctorProfile(
                user_id=user.id,
                display_name=display_name,
                title="Head of Synthetic Community Hospital",
                hospital_name="Synthetic Community Hospital",
            )
        )
    else:
        db.add(
            PatientProfile(
                user_id=user.id,
                display_name=display_name,
                synthetic_identifier=synthetic_identifier or "SYNTHETIC-DEMO",
            )
        )
    db.flush()
    return user, True


def seed_database(db: Session, settings: Settings) -> SeedResult:
    doctor_password = _required_password(settings, "seed_doctor_password")
    patient_password = _required_password(settings, "seed_patient_password")
    unrelated_password = _required_password(settings, "seed_unrelated_patient_password")

    users_created = 0
    relationships_created = 0
    dashboards_created = 0
    records_created = 0
    medications_created = 0
    notes_created = 0
    recovery_plans_created = 0
    recovery_tasks_created = 0

    doctor, created = _get_or_create_user(
        db,
        email="doctor.demo@example.com",
        password=doctor_password,
        role=UserRole.doctor,
        display_name="Dr. Avery Demo",
    )
    users_created += int(created)
    reviewer, created = _get_or_create_user(
        db,
        email="reviewer.doctor@example.com",
        password=doctor_password,
        role=UserRole.doctor,
        display_name="Dr. Rowan Reviewer",
    )
    users_created += int(created)
    patient, created = _get_or_create_user(
        db,
        email="patient.demo@example.com",
        password=patient_password,
        role=UserRole.patient,
        display_name="Riley Demo Patient",
        synthetic_identifier="SYN-PATIENT-001",
    )
    users_created += int(created)
    unrelated, created = _get_or_create_user(
        db,
        email="unrelated.patient@example.com",
        password=unrelated_password,
        role=UserRole.patient,
        display_name="Morgan Demo Patient",
        synthetic_identifier="SYN-PATIENT-002",
    )
    users_created += int(created)
    db.flush()

    # A bounded synthetic record exercises the same personalized-context path
    # that later accepts patient-entered production records. One reading is an
    # observation only and is deliberately not paired with a diagnosis.
    if patient.patient_profile.systolic_blood_pressure is None:
        patient.patient_profile.birth_year = 1986
        patient.patient_profile.sex = "female"
        patient.patient_profile.height_cm = 165.0
        patient.patient_profile.weight_kg = 64.0
        patient.patient_profile.systolic_blood_pressure = 138
        patient.patient_profile.diastolic_blood_pressure = 86
        patient.patient_profile.context_recorded_at = datetime(2026, 7, 16, 9, 0, tzinfo=UTC)
        patient.patient_profile.measurements_recorded_at = (
            patient.patient_profile.context_recorded_at
        )

    active = db.scalar(
        select(CareRelationship).where(
            CareRelationship.doctor_id == doctor.doctor_profile.id,
            CareRelationship.patient_id == patient.patient_profile.id,
        )
    )
    if active is None:
        db.add(
            CareRelationship(
                doctor_id=doctor.doctor_profile.id,
                patient_id=patient.patient_profile.id,
                is_active=True,
                status="active",
                can_review_recovery_plans=True,
                requested_at=datetime.now(UTC),
                responded_at=datetime.now(UTC),
                approved_at=datetime.now(UTC),
            )
        )
        relationships_created += 1

    revoked = db.scalar(
        select(CareRelationship).where(
            CareRelationship.doctor_id == doctor.doctor_profile.id,
            CareRelationship.patient_id == unrelated.patient_profile.id,
        )
    )
    if revoked is None:
        db.add(
            CareRelationship(
                doctor_id=doctor.doctor_profile.id,
                patient_id=unrelated.patient_profile.id,
                is_active=False,
                status="revoked",
                can_review_recovery_plans=False,
                requested_at=datetime.now(UTC),
                responded_at=datetime.now(UTC),
                revoked_at=datetime.now(UTC),
            )
        )
        relationships_created += 1

    reviewer_relationship = db.scalar(
        select(CareRelationship).where(
            CareRelationship.doctor_id == reviewer.doctor_profile.id,
            CareRelationship.patient_id == patient.patient_profile.id,
        )
    )
    if reviewer_relationship is None:
        now = datetime.now(UTC)
        db.add(
            CareRelationship(
                doctor_id=reviewer.doctor_profile.id,
                patient_id=patient.patient_profile.id,
                is_active=True,
                status="active",
                can_review_recovery_plans=True,
                requested_at=now,
                responded_at=now,
                approved_at=now,
            )
        )
        relationships_created += 1

    doctor_dashboard = {
        "safety_label": "Synthetic demonstration data only. Do not enter real patient data.",
        "hospital": {
            "name": "Synthetic Community Hospital",
            "location": "Demo County",
            "summary": "Invited beta facility using synthetic demonstration data.",
        },
        "doctor": {
            "name": "Dr. Avery Demo",
            "title": "Head of Synthetic Community Hospital",
            "expertise": "Synthetic care coordination",
            "rating": 4,
        },
        "quick_access": [
            "Imaging records and manual review",
            "Patient medical records",
            "Patient recovery plans",
            "Medical resources (read-only)",
            "Payer requests",
        ],
        "recent_activity": {
            "title": "Synthetic Patient - Demonstration follow-up",
            "time": "20:00",
        },
        "resources": [
            {"name": "CT", "available": 1, "total": 2},
            {"name": "MRI", "available": 1, "total": 1},
            {"name": "X-ray", "available": 2, "total": 2},
            {"name": "Ventilations", "available": 4, "total": 5},
            {"name": "Ultrasound", "available": 1, "total": 2},
        ],
        "team": ["Dr. Rowan Demo", "Dr. Lee Demo", "Dr. Zhao Demo"],
    }
    patient_dashboard = {
        "safety_label": "Synthetic demonstration data only. Do not enter real patient data.",
        "recovery_days": [
            {
                "label": "Today",
                "tasks": [
                    "50mg demo medication fixture",
                    "Drink plenty of water",
                    "Avoid triggers",
                ],
            },
            {
                "label": "Jan. 2",
                "tasks": [
                    "Drink plenty of water",
                    "Avoid triggers",
                    "Contact the demo hospital if needed",
                ],
            },
            {
                "label": "Jan. 3",
                "tasks": [
                    "Drink plenty of water",
                    "Avoid triggers",
                    "Goal: begin light demo activities",
                ],
            },
        ],
        "doctor": {
            "name": "Dr. Avery Demo",
            "title": "Head of Synthetic Community Hospital",
            "expertise": "Synthetic care coordination",
        },
        "medical_records": [],
        "imaging_results": [],
    }
    for user, payload in (
        (doctor, doctor_dashboard),
        (reviewer, doctor_dashboard),
        (patient, patient_dashboard),
        (unrelated, patient_dashboard),
    ):
        snapshot = db.scalar(select(DashboardSnapshot).where(DashboardSnapshot.user_id == user.id))
        if snapshot is None:
            db.add(DashboardSnapshot(user_id=user.id, payload=payload))
            dashboards_created += 1
        else:
            snapshot.payload = payload

    if not db.scalars(
        select(MedicalRecord).where(MedicalRecord.patient_id == patient.patient_profile.id)
    ).first():
        db.add_all(
            [
                MedicalRecord(
                    patient_id=patient.patient_profile.id,
                    title="Synthetic intake summary",
                    category="Demo visit",
                    summary=(
                        "Synthetic Week 2 fixture for care-loop navigation only. "
                        "Not a diagnosis or medical advice."
                    ),
                    recorded_at=datetime(2026, 7, 1, 8, 30, tzinfo=UTC),
                ),
                MedicalRecord(
                    patient_id=patient.patient_profile.id,
                    title="Synthetic follow-up note",
                    category="Demo follow-up",
                    summary=(
                        "Patient-reported demo symptoms are stable inside the "
                        "non-clinical beta scenario."
                    ),
                    recorded_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
                ),
            ]
        )
        records_created += 2

    if not db.scalars(
        select(Medication).where(Medication.patient_id == patient.patient_profile.id)
    ).first():
        db.add_all(
            [
                Medication(
                    patient_id=patient.patient_profile.id,
                    name="Demo Sumatriptan Fixture",
                    dosage="50 mg",
                    schedule="As listed in the synthetic care plan",
                    status="active",
                    note="Fixture medication for UI validation; not a prescription.",
                ),
                Medication(
                    patient_id=patient.patient_profile.id,
                    name="Demo Hydration Reminder",
                    dosage="Non-drug support item",
                    schedule="Today",
                    status="planned",
                    note="Synthetic support task carried forward from the dashboard.",
                ),
            ]
        )
        medications_created += 2

    if not db.scalars(
        select(DoctorNote).where(DoctorNote.patient_id == patient.patient_profile.id)
    ).first():
        db.add_all(
            [
                DoctorNote(
                    patient_id=patient.patient_profile.id,
                    doctor_id=doctor.doctor_profile.id,
                    title="Synthetic care-loop note",
                    body=(
                        "Doctor-facing fixture note for Week 2 navigation. "
                        "No real patient information is present."
                    ),
                )
            ]
        )
        notes_created += 1

    if not db.scalars(
        select(RecoveryPlan).where(RecoveryPlan.patient_id == patient.patient_profile.id)
    ).first():
        plan = RecoveryPlan(
            patient_id=patient.patient_profile.id,
            doctor_id=doctor.doctor_profile.id,
            title="Synthetic Week 3 Recovery Plan",
            instructions=(
                "Demo-only recovery plan for invited beta workflow validation. "
                "This is not diagnosis, treatment, or medical advice."
            ),
            status="active",
            review_status="approved",
            review_actor_user_id=reviewer.id,
            assigned_reviewer_doctor_id=reviewer.doctor_profile.id,
            submitted_version=1,
            safety_label="Synthetic demonstration data only. Do not enter real patient data.",
            submitted_at=datetime(2026, 7, 5, 9, 0, tzinfo=UTC),
            reviewed_at=datetime(2026, 7, 5, 9, 30, tzinfo=UTC),
            approved_at=datetime(2026, 7, 5, 9, 30, tzinfo=UTC),
            activated_at=datetime(2026, 7, 5, 10, 0, tzinfo=UTC),
        )
        db.add(plan)
        db.flush()
        db.add_all(
            [
                RecoveryTask(
                    plan_id=plan.id,
                    patient_id=patient.patient_profile.id,
                    category="medication",
                    title="Demo medication reminder",
                    detail="Review the synthetic medication fixture only.",
                    due_label="Today",
                    scheduled_date=datetime.now(UTC).astimezone().date(),
                    scheduled_time="09:00",
                    notification_time="09:00",
                    sort_order=0,
                ),
                RecoveryTask(
                    plan_id=plan.id,
                    patient_id=patient.patient_profile.id,
                    category="exercise",
                    title="Light demo mobility",
                    detail="Complete a short synthetic walking task if appropriate in the demo.",
                    due_label="Today",
                    scheduled_date=datetime.now(UTC).astimezone().date(),
                    notification_time=None,
                    sort_order=1,
                ),
                RecoveryTask(
                    plan_id=plan.id,
                    patient_id=patient.patient_profile.id,
                    category="diet",
                    title="Demo hydration check",
                    detail="Use this placeholder to validate diet and hydration task display.",
                    due_label="Today",
                    scheduled_date=datetime.now(UTC).astimezone().date(),
                    notification_time=None,
                    sort_order=2,
                ),
                RecoveryTask(
                    plan_id=plan.id,
                    patient_id=patient.patient_profile.id,
                    category="follow_up",
                    title="Synthetic follow-up preparation",
                    detail="Prepare demo questions for the assigned doctor workflow.",
                    due_label="Today",
                    scheduled_date=datetime.now(UTC).astimezone().date(),
                    notification_time=None,
                    sort_order=3,
                ),
            ]
        )
        recovery_plans_created += 1
        recovery_tasks_created += 4

    db.commit()
    return SeedResult(
        users_created,
        relationships_created,
        dashboards_created,
        records_created,
        medications_created,
        notes_created,
        recovery_plans_created,
        recovery_tasks_created,
    )


def main() -> None:
    with SessionLocal() as db:
        result = seed_database(db, get_settings())
    print(
        "Synthetic seed complete: "
        f"users_created={result.users_created}, "
        f"relationships_created={result.relationships_created}, "
        f"dashboards_created={result.dashboards_created}, "
        f"records_created={result.records_created}, "
        f"medications_created={result.medications_created}, "
        f"notes_created={result.notes_created}, "
        f"recovery_plans_created={result.recovery_plans_created}, "
        f"recovery_tasks_created={result.recovery_tasks_created}"
    )


if __name__ == "__main__":
    main()
