"""Provision one named, hospital-bound admin locally; no HTTP enrollment endpoint."""

import argparse
import getpass
import uuid

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import AuditEvent, Clinic, Hospital, RoleAssignment, User, UserRole
from app.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--hospital-id", type=uuid.UUID, required=True)
    parser.add_argument("--clinic-id", type=uuid.UUID)
    args = parser.parse_args()
    if get_settings().environment not in {"local", "test"}:
        parser.error("Provisioning is restricted to local/test environments.")
    password = getpass.getpass("New admin password: ")
    if len(password) < 12:
        parser.error("Use at least 12 characters.")
    email = args.email.strip().lower()
    with SessionLocal.begin() as db:
        hospital = db.get(Hospital, args.hospital_id)
        if hospital is None or hospital.status != "active":
            parser.error("Active hospital not found.")
        if args.clinic_id:
            clinic = db.get(Clinic, args.clinic_id)
            if clinic is None or clinic.hospital_id != hospital.id or clinic.status != "active":
                parser.error("Active clinic in hospital not found.")
        if db.scalar(select(User.id).where(User.email == email)):
            parser.error("Email already belongs to an account.")
        user = User(email=email, password_hash=hash_password(password), role=UserRole.admin)
        db.add(user)
        db.flush()
        assignment = RoleAssignment(
            user_id=user.id,
            role=UserRole.admin,
            hospital_id=hospital.id,
            clinic_id=args.clinic_id,
            status="active",
        )
        db.add(assignment)
        db.flush()
        db.add(
            AuditEvent(
                actor_user_id=user.id,
                event_type="hospital_admin_locally_provisioned",
                resource_type="role_assignment",
                resource_id=assignment.id,
                metadata_json={
                    "hospital_id": str(hospital.id),
                    "clinic_id": str(args.clinic_id) if args.clinic_id else None,
                    "method": "local_cli",
                },
            )
        )
        print(f"Provisioned {email} for {hospital.name} ({user.id})")


if __name__ == "__main__":
    main()
