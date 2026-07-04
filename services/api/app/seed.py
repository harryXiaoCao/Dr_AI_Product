from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import SessionLocal
from app.models import (
    CareRelationship,
    DashboardSnapshot,
    DoctorProfile,
    PatientProfile,
    User,
    UserRole,
)
from app.security import hash_password


@dataclass(frozen=True)
class SeedResult:
    users_created: int
    relationships_created: int
    dashboards_created: int


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
    unrelated_password = _required_password(
        settings, "seed_unrelated_patient_password"
    )

    users_created = 0
    relationships_created = 0
    dashboards_created = 0

    doctor, created = _get_or_create_user(
        db,
        email="doctor.demo@example.com",
        password=doctor_password,
        role=UserRole.doctor,
        display_name="Dr. Avery Demo",
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
            "AI Supported CT Image Diagnose",
            "AI Supported X-ray Image Diagnose",
            "AI Supported MRI Image Diagnose",
            "Check Patient Medical Records",
            "Check Patient Recovery Plans",
            "Check Imaging Results",
            "Book Medical Equipment",
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
        "fee_items": [
            {"label": "Consultation", "amount": "10 demo credits", "selected": True},
            {"label": "Blood Test", "amount": "50 demo credits", "selected": True},
            {"label": "Medication", "amount": "120 demo credits", "selected": True},
            {
                "label": "Ambulance Service",
                "amount": "50 demo credits",
                "selected": False,
            },
        ],
        "medical_records": [],
        "imaging_results": [],
    }
    for user, payload in (
        (doctor, doctor_dashboard),
        (patient, patient_dashboard),
        (unrelated, patient_dashboard),
    ):
        snapshot = db.scalar(
            select(DashboardSnapshot).where(DashboardSnapshot.user_id == user.id)
        )
        if snapshot is None:
            db.add(DashboardSnapshot(user_id=user.id, payload=payload))
            dashboards_created += 1
        else:
            snapshot.payload = payload

    db.commit()
    return SeedResult(users_created, relationships_created, dashboards_created)


def main() -> None:
    with SessionLocal() as db:
        result = seed_database(db, get_settings())
    print(
        "Synthetic seed complete: "
        f"users_created={result.users_created}, "
        f"relationships_created={result.relationships_created}, "
        f"dashboards_created={result.dashboards_created}"
    )


if __name__ == "__main__":
    main()
