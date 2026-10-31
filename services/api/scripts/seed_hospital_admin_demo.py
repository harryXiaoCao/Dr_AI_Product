"""Create idempotent synthetic hospital operations records in a local database."""

import getpass
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import (
    Appointment,
    Clinic,
    ClinicResource,
    DoctorProfile,
    Equipment,
    EquipmentBooking,
    Hospital,
    PatientProfile,
    RoleAssignment,
    User,
    UserRole,
)
from app.security import hash_password


def main() -> None:
    if get_settings().environment != "local":
        raise SystemExit("Synthetic demo seeding is local-only.")
    password = getpass.getpass("Synthetic doctor password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters.")
    with SessionLocal.begin() as db:
        code = "SYN-HOSPITAL-ADMIN-DEMO"
        hospital = db.scalar(select(Hospital).where(Hospital.organization_code == code))
        if hospital is not None:
            print(f"Demo already exists: {hospital.id}")
            return
        hospital = Hospital(
            name="Hospital Operations Demo", organization_code=code, status="active"
        )
        db.add(hospital)
        db.flush()
        clinics = [
            Clinic(hospital_id=hospital.id, name=name, status="active")
            for name in ("Imaging", "Rehabilitation")
        ]
        db.add_all(clinics)
        db.flush()
        doctor = User(
            email="hospital.demo.doctor@example.com",
            password_hash=hash_password(password),
            role=UserRole.doctor,
        )
        patient = User(
            email="hospital.demo.patient@example.com",
            password_hash=hash_password(secrets.token_urlsafe(24)),
            role=UserRole.patient,
        )
        db.add_all([doctor, patient])
        db.flush()
        doctor_profile = DoctorProfile(
            user_id=doctor.id,
            display_name="Dr. Morgan Demo",
            title="Synthetic clinician",
            hospital_name=hospital.name,
        )
        patient_profile = PatientProfile(
            user_id=patient.id,
            display_name="Synthetic Patient",
            synthetic_identifier="SYN-HOSPITAL-ADMIN-PATIENT",
        )
        db.add_all([doctor_profile, patient_profile])
        db.add(
            RoleAssignment(
                user_id=doctor.id,
                role=UserRole.doctor,
                hospital_id=hospital.id,
                clinic_id=clinics[0].id,
                status="active",
            )
        )
        db.flush()
        resources = [
            ClinicResource(
                clinic_id=clinic.id,
                resource_type="equipment",
                name=name,
                status="available",
                capacity_current=1,
                capacity_total=2,
            )
            for clinic, name in zip(clinics, ("CT scanner", "Therapy room"), strict=True)
        ]
        db.add_all(resources)
        db.flush()
        equipment = Equipment(
            clinic_id=clinics[0].id,
            resource_id=resources[0].id,
            name="CT scanner A",
            equipment_type="ct",
            status="available",
        )
        db.add(equipment)
        db.flush()
        now = datetime.now(UTC)
        for index in range(32):
            start = now + timedelta(days=1, hours=index)
            db.add(
                EquipmentBooking(
                    equipment_id=equipment.id,
                    requested_by_user_id=doctor.id,
                    patient_id=patient_profile.id,
                    status="requested",
                    start_at=start,
                    end_at=start + timedelta(minutes=45),
                    purpose=f"Synthetic imaging request {index + 1}",
                )
            )
        for index, status in enumerate(("requested", "scheduled", "completed")):
            start = now + timedelta(days=index + 1)
            db.add(
                Appointment(
                    clinic_id=clinics[0].id,
                    patient_id=patient_profile.id,
                    doctor_id=doctor_profile.id,
                    status=status,
                    scheduled_start=start,
                    scheduled_end=start + timedelta(minutes=30),
                    reason_code="synthetic_demo",
                )
            )
        print(f"Created {hospital.name}: {hospital.id}; doctor {doctor.email}; 32 requests")


if __name__ == "__main__":
    main()
