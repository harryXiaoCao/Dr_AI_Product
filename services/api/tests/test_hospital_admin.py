"""Hospital boundaries and operational transitions, including direct API access."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    AuditEvent,
    Clinic,
    ClinicResource,
    DoctorProfile,
    Equipment,
    EquipmentBooking,
    Hospital,
    RoleAssignment,
    User,
    UserRole,
)
from app.security import hash_password
from tests.helpers import auth_header


def _login(client, email: str, password: str) -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def _fixture() -> dict[str, str]:
    with SessionLocal.begin() as db:
        hospitals = [Hospital(name="Hospital A"), Hospital(name="Hospital B")]
        db.add_all(hospitals)
        db.flush()
        clinics = [Clinic(hospital_id=h.id, name="Imaging") for h in hospitals]
        db.add_all(clinics)
        db.flush()
        admins = [
            User(
                email=f"admin{i}@example.com",
                password_hash=hash_password("admin-password-123"),
                role=UserRole.admin,
            )
            for i in range(2)
        ]
        doctor = User(
            email="doctor@example.com",
            password_hash=hash_password("doctor-password-123"),
            role=UserRole.doctor,
        )
        db.add_all([*admins, doctor])
        db.flush()
        db.add(
            DoctorProfile(
                user_id=doctor.id,
                display_name="Dr Synthetic",
                title="Doctor",
                hospital_name="Hospital A",
            )
        )
        db.add_all(
            [
                RoleAssignment(
                    user_id=admin.id,
                    role=UserRole.admin,
                    hospital_id=h.id,
                    clinic_id=None,
                    status="active",
                )
                for admin, h in zip(admins, hospitals, strict=True)
            ]
        )
        resources = [
            ClinicResource(
                clinic_id=c.id,
                resource_type="equipment",
                name="Scanner",
                status="available",
                capacity_current=1,
                capacity_total=1,
            )
            for c in clinics
        ]
        db.add_all(resources)
        db.flush()
        equipment = [
            Equipment(
                clinic_id=c.id,
                resource_id=r.id,
                name="Scanner 1",
                equipment_type="scanner",
                status="available",
            )
            for c, r in zip(clinics, resources, strict=True)
        ]
        db.add_all(equipment)
        db.flush()
        bookings = [
            EquipmentBooking(
                equipment_id=e.id,
                requested_by_user_id=doctor.id,
                status="requested",
                start_at=datetime.now(UTC),
                end_at=datetime.now(UTC) + timedelta(hours=1),
                purpose="Synthetic imaging",
            )
            for e in equipment
        ]
        db.add_all(bookings)
        db.flush()
        return {
            "a_clinic": str(clinics[0].id),
            "b_clinic": str(clinics[1].id),
            "a_resource": str(resources[0].id),
            "b_resource": str(resources[1].id),
            "a_booking": str(bookings[0].id),
            "b_booking": str(bookings[1].id),
            "doctor": str(doctor.id),
        }


def test_admin_scope_and_cross_hospital_direct_access(client):
    ids = _fixture()
    admin = auth_header(_login(client, "admin0@example.com", "admin-password-123")["access_token"])
    other = auth_header(_login(client, "admin1@example.com", "admin-password-123")["access_token"])
    doctor = auth_header(
        _login(client, "doctor@example.com", "doctor-password-123")["access_token"]
    )
    response = client.get("/api/v1/hospital-admin/workspace", headers=admin)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert {row["id"] for row in response.json()["bookings"]} == {ids["a_booking"]}
    assert client.get("/api/v1/hospital-admin/workspace", headers=doctor).status_code == 403
    assert client.get("/api/v1/doctor/hospital-resources", headers=doctor).json()["resources"] == []
    assert (
        client.get(
            "/api/v1/hospital-admin/workspace", params={"clinic_id": ids["b_clinic"]}, headers=admin
        ).status_code
        == 404
    )
    for route, payload in [
        (f"resources/{ids['b_resource']}", {"status": "limited", "reason": "Maintenance"}),
        (f"bookings/{ids['b_booking']}", {"status": "approved", "reason": "Capacity confirmed"}),
    ]:
        assert (
            client.patch(f"/api/v1/hospital-admin/{route}", json=payload, headers=admin).status_code
            == 404
        )
    assert (
        client.post(
            "/api/v1/hospital-admin/staff-access",
            headers=other,
            json={
                "email": "doctor@example.com",
                "clinic_id": ids["a_clinic"],
                "active": True,
                "reason": "New staff",
            },
        ).status_code
        == 404
    )


def test_admin_requires_controlled_provisioning_and_supports_multiple_people(client):
    ids = _fixture()
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "public-admin@example.com",
            "phone_number": "+15551119999",
            "password": "PublicAdmin123!",
            "role": "admin",
            "verification_code": "123456",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 403
    with SessionLocal.begin() as db:
        hospital_id = db.get(Clinic, ids["a_clinic"]).hospital_id
        second = User(
            email="second.admin@example.com",
            password_hash=hash_password("second-admin-123"),
            role=UserRole.admin,
        )
        db.add(second)
        db.flush()
        db.add(
            RoleAssignment(
                user_id=second.id,
                role=UserRole.admin,
                hospital_id=hospital_id,
                clinic_id=None,
                status="active",
            )
        )
    first = auth_header(_login(client, "admin0@example.com", "admin-password-123")["access_token"])
    second = auth_header(
        _login(client, "second.admin@example.com", "second-admin-123")["access_token"]
    )
    assert client.get("/api/v1/hospital-admin/workspace", headers=first).json()["total"] == 1
    assert client.get("/api/v1/hospital-admin/workspace", headers=second).json()["total"] == 1


def test_resource_booking_staff_transitions_are_audited(client):
    ids = _fixture()
    admin = auth_header(_login(client, "admin0@example.com", "admin-password-123")["access_token"])
    resource_url = f"/api/v1/hospital-admin/resources/{ids['a_resource']}"
    booking_url = f"/api/v1/hospital-admin/bookings/{ids['a_booking']}"
    staff_url = "/api/v1/hospital-admin/staff-access"
    assert (
        client.patch(
            resource_url,
            headers=admin,
            json={"status": "limited", "capacity_current": 2, "reason": "Test"},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            resource_url,
            headers=admin,
            json={"status": "unavailable", "capacity_current": 0, "reason": "Maintenance"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            booking_url, headers=admin, json={"status": "approved", "reason": "Reviewed"}
        ).status_code
        == 409
    )
    assert (
        client.patch(
            resource_url,
            headers=admin,
            json={"status": "available", "capacity_current": 1, "reason": "Returned to service"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            booking_url, headers=admin, json={"status": "approved", "reason": "Reviewed"}
        ).status_code
        == 200
    )
    assert (
        client.patch(
            booking_url, headers=admin, json={"status": "approved", "reason": "Duplicate"}
        ).status_code
        == 409
    )
    assert (
        client.patch(
            booking_url, headers=admin, json={"status": "completed", "reason": "Service complete"}
        ).status_code
        == 200
    )
    grant = {
        "email": "doctor@example.com",
        "clinic_id": ids["a_clinic"],
        "active": True,
        "reason": "Staff verified",
    }
    assert client.post(staff_url, headers=admin, json=grant).status_code == 200
    doctor = auth_header(
        _login(client, "doctor@example.com", "doctor-password-123")["access_token"]
    )
    scoped_resources = client.get("/api/v1/doctor/hospital-resources", headers=doctor)
    assert scoped_resources.status_code == 200
    assert {row["id"] for row in scoped_resources.json()["resources"]} == {ids["a_resource"]}
    assert client.post(staff_url, headers=admin, json=grant).status_code == 409
    assert client.post(staff_url, headers=admin, json={**grant, "active": False}).status_code == 200
    assert client.get("/api/v1/doctor/hospital-resources", headers=doctor).json()["resources"] == []
    with SessionLocal() as db:
        events = db.scalars(
            select(AuditEvent).where(
                AuditEvent.event_type.in_(
                    [
                        "resource_availability_changed",
                        "equipment_booking_status_changed",
                        "doctor_department_access_changed",
                    ]
                )
            )
        ).all()
        assert len(events) == 6
        assert all(
            event.metadata_json["reason"]
            if "reason" in event.metadata_json
            else event.metadata_json["after"]["reason"]
            for event in events
        )
