"""Hospital operations. All queries are scoped from a live role assignment."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    Appointment,
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

router = APIRouter(prefix="/api/v1/hospital-admin", tags=["hospital administration"])
doctor_router = APIRouter(prefix="/api/v1/doctor", tags=["doctor hospital resources"])


@doctor_router.get("/hospital-resources")
def doctor_hospital_resources(db: DbSession, user: CurrentUser) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise ApiError(403, "forbidden", "Doctor access is required.")
    assignments = db.execute(
        select(RoleAssignment, Clinic, Hospital)
        .join(Clinic, RoleAssignment.clinic_id == Clinic.id)
        .join(Hospital, Clinic.hospital_id == Hospital.id)
        .where(
            RoleAssignment.user_id == user.id,
            RoleAssignment.role == UserRole.doctor,
            RoleAssignment.status == "active",
            RoleAssignment.revoked_at.is_(None),
            Hospital.status == "active",
            Clinic.status == "active",
        )
    ).all()
    clinic_ids = {
        clinic.id
        for assignment, clinic, hospital in assignments
        if assignment.hospital_id == hospital.id
    }
    if not clinic_ids:
        return {"clinics": [], "resources": []}
    resources = db.execute(
        select(ClinicResource, Clinic)
        .join(Clinic, ClinicResource.clinic_id == Clinic.id)
        .where(Clinic.id.in_(clinic_ids))
        .order_by(Clinic.name, ClinicResource.name)
    ).all()
    return {
        "clinics": [
            {"id": str(clinic.id), "name": clinic.name}
            for _, clinic, _ in assignments
            if clinic.id in clinic_ids
        ],
        "resources": [
            {
                "id": str(resource.id),
                "name": resource.name,
                "clinic_name": clinic.name,
                "status": resource.status,
                "capacity_current": resource.capacity_current,
                "capacity_total": resource.capacity_total,
            }
            for resource, clinic in resources
        ],
    }


def _scope(db: Session, user: User) -> tuple[Hospital, set[uuid.UUID], list[Clinic]]:
    if user.role != UserRole.admin:
        raise ApiError(403, "forbidden", "Hospital admin access is required.")
    assignments = db.scalars(
        select(RoleAssignment).where(
            RoleAssignment.user_id == user.id,
            RoleAssignment.role == UserRole.admin,
            RoleAssignment.status == "active",
            RoleAssignment.revoked_at.is_(None),
        )
    ).all()
    hospital_ids = {a.hospital_id for a in assignments if a.hospital_id is not None}
    if len(hospital_ids) != 1:
        raise ApiError(403, "forbidden", "A single active hospital assignment is required.")
    hospital = db.get(Hospital, next(iter(hospital_ids)))
    if hospital is None or hospital.status != "active":
        raise ApiError(403, "forbidden", "The hospital is unavailable.")
    clinics = db.scalars(
        select(Clinic)
        .where(Clinic.hospital_id == hospital.id, Clinic.status == "active")
        .order_by(Clinic.name)
    ).all()
    all_clinic_ids = {clinic.id for clinic in clinics}
    if any(a.clinic_id is None for a in assignments):
        allowed_ids = all_clinic_ids
    else:
        allowed_ids = {a.clinic_id for a in assignments if a.clinic_id in all_clinic_ids}
    return hospital, allowed_ids, [clinic for clinic in clinics if clinic.id in allowed_ids]


def _allowed(clinic_id: uuid.UUID, allowed_ids: set[uuid.UUID]) -> None:
    if clinic_id not in allowed_ids:
        raise ApiError(404, "not_found", "The requested resource was not found.")


def _audit(
    db: Session,
    user: User,
    event_type: str,
    resource_type: str,
    resource_id: uuid.UUID,
    hospital_id: uuid.UUID,
    clinic_id: uuid.UUID,
    before: object,
    after: object,
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json={
                "hospital_id": str(hospital_id),
                "clinic_id": str(clinic_id),
                "before": before,
                "after": after,
            },
        )
    )


@router.get("/workspace")
def workspace(
    db: DbSession,
    user: CurrentUser,
    clinic_id: uuid.UUID | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> dict[str, object]:
    hospital, allowed_ids, clinics = _scope(db, user)
    if clinic_id is not None:
        _allowed(clinic_id, allowed_ids)
    selected_ids = {clinic_id} if clinic_id else allowed_ids
    if not selected_ids:
        return {
            "hospital": {"id": str(hospital.id), "name": hospital.name},
            "clinics": [],
            "counts": {},
            "bookings": [],
            "total": 0,
            "resources": [],
            "staff": [],
        }
    booking_base = (
        select(EquipmentBooking, Equipment, Clinic)
        .join(Equipment, EquipmentBooking.equipment_id == Equipment.id)
        .join(Clinic, Equipment.clinic_id == Clinic.id)
        .where(Clinic.id.in_(selected_ids))
    )
    count_rows = db.execute(
        select(EquipmentBooking.status, func.count())
        .join(Equipment, EquipmentBooking.equipment_id == Equipment.id)
        .where(Equipment.clinic_id.in_(selected_ids))
        .group_by(EquipmentBooking.status)
    ).all()
    if status:
        booking_base = booking_base.where(EquipmentBooking.status == status)
    total = db.scalar(select(func.count()).select_from(booking_base.subquery())) or 0
    booking_rows = db.execute(
        booking_base.order_by(EquipmentBooking.created_at.desc(), EquipmentBooking.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    resources = db.scalars(
        select(ClinicResource)
        .where(ClinicResource.clinic_id.in_(selected_ids))
        .order_by(ClinicResource.name)
    ).all()
    staff_rows = db.execute(
        select(RoleAssignment, User, DoctorProfile, Clinic)
        .join(User, RoleAssignment.user_id == User.id)
        .outerjoin(DoctorProfile, DoctorProfile.user_id == User.id)
        .join(Clinic, RoleAssignment.clinic_id == Clinic.id)
        .where(RoleAssignment.role == UserRole.doctor, Clinic.id.in_(selected_ids))
        .order_by(Clinic.name, DoctorProfile.display_name)
    ).all()
    appointment_counts = db.execute(
        select(Appointment.status, func.count())
        .where(Appointment.clinic_id.in_(selected_ids))
        .group_by(Appointment.status)
    ).all()
    return {
        "hospital": {"id": str(hospital.id), "name": hospital.name},
        "clinics": [{"id": str(c.id), "name": c.name} for c in clinics],
        "counts": {
            "equipment_requests": dict(count_rows),
            "appointments": dict(appointment_counts),
        },
        "bookings": [
            {
                "id": str(b.id),
                "clinic_id": str(c.id),
                "clinic_name": c.name,
                "equipment": e.name,
                "status": b.status,
                "purpose": b.purpose,
                "start_at": b.start_at.isoformat(),
                "end_at": b.end_at.isoformat(),
            }
            for b, e, c in booking_rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "resources": [
            {
                "id": str(r.id),
                "clinic_id": str(r.clinic_id),
                "name": r.name,
                "type": r.resource_type,
                "status": r.status,
                "capacity_current": r.capacity_current,
                "capacity_total": r.capacity_total,
            }
            for r in resources
        ],
        "staff": [
            {
                "assignment_id": str(a.id),
                "user_id": str(u.id),
                "email": u.email,
                "name": p.display_name if p else u.email or str(u.id),
                "clinic_id": str(c.id),
                "clinic_name": c.name,
                "status": a.status,
            }
            for a, u, p, c in staff_rows
        ],
    }


class ResourceUpdate(BaseModel):
    status: str
    capacity_current: int | None = Field(default=None, ge=0)
    reason: str = Field(min_length=3, max_length=240)


@router.patch("/resources/{resource_id}")
def update_resource(
    resource_id: uuid.UUID,
    body: ResourceUpdate,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    hospital, allowed_ids, _ = _scope(db, user)
    resource = db.scalar(
        select(ClinicResource).where(ClinicResource.id == resource_id).with_for_update()
    )
    if resource is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    _allowed(resource.clinic_id, allowed_ids)
    if body.status not in {"available", "limited", "unavailable"}:
        raise ApiError(422, "invalid_status", "Unsupported availability status.")
    next_capacity = (
        body.capacity_current
        if "capacity_current" in body.model_fields_set
        else resource.capacity_current
    )
    if (
        resource.capacity_total is not None
        and next_capacity is not None
        and next_capacity > resource.capacity_total
    ):
        raise ApiError(422, "invalid_capacity", "Current capacity exceeds total capacity.")
    before = {"status": resource.status, "capacity_current": resource.capacity_current}
    resource.status = body.status
    resource.capacity_current = next_capacity
    after = {
        "status": resource.status,
        "capacity_current": resource.capacity_current,
        "reason": body.reason.strip(),
    }
    _audit(
        db,
        user,
        "resource_availability_changed",
        "clinic_resource",
        resource.id,
        hospital.id,
        resource.clinic_id,
        before,
        after,
    )
    db.commit()
    return {"id": str(resource.id), **after}


class BookingUpdate(BaseModel):
    status: str
    reason: str = Field(min_length=3, max_length=240)


@router.patch("/bookings/{booking_id}")
def update_booking(
    booking_id: uuid.UUID,
    body: BookingUpdate,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    hospital, allowed_ids, _ = _scope(db, user)
    booking = db.scalar(
        select(EquipmentBooking).where(EquipmentBooking.id == booking_id).with_for_update()
    )
    if booking is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    equipment = db.scalar(
        select(Equipment).where(Equipment.id == booking.equipment_id).with_for_update()
    )
    if equipment is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    _allowed(equipment.clinic_id, allowed_ids)
    transitions = {"requested": {"approved", "declined"}, "approved": {"completed", "cancelled"}}
    if body.status not in transitions.get(booking.status, set()):
        raise ApiError(409, "invalid_transition", "This booking transition is unavailable.")
    if body.status == "approved":
        resource = db.get(ClinicResource, equipment.resource_id) if equipment.resource_id else None
        if equipment.status != "available" or (
            resource is not None and resource.status != "available"
        ):
            raise ApiError(409, "equipment_unavailable", "Equipment is not available.")
        overlap = db.scalar(
            select(EquipmentBooking.id)
            .where(
                EquipmentBooking.equipment_id == equipment.id,
                EquipmentBooking.id != booking.id,
                EquipmentBooking.status == "approved",
                EquipmentBooking.start_at < booking.end_at,
                EquipmentBooking.end_at > booking.start_at,
            )
            .limit(1)
        )
        if overlap is not None:
            raise ApiError(409, "booking_overlap", "Equipment already has an approved booking.")
    before = {"status": booking.status}
    booking.status = body.status
    after = {"status": body.status, "reason": body.reason.strip()}
    _audit(
        db,
        user,
        "equipment_booking_status_changed",
        "equipment_booking",
        booking.id,
        hospital.id,
        equipment.clinic_id,
        before,
        after,
    )
    db.commit()
    return {"id": str(booking.id), **after}


class StaffUpdate(BaseModel):
    email: str
    clinic_id: uuid.UUID
    active: bool
    reason: str = Field(min_length=3, max_length=240)


@router.post("/staff-access")
def update_staff_access(body: StaffUpdate, db: DbSession, user: CurrentUser) -> dict[str, object]:
    hospital, allowed_ids, _ = _scope(db, user)
    _allowed(body.clinic_id, allowed_ids)
    target = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if target is None or target.role != UserRole.doctor or not target.is_active:
        raise ApiError(404, "not_found", "The doctor was not found.")
    other_hospital = db.scalar(
        select(RoleAssignment.id)
        .outerjoin(Clinic, RoleAssignment.clinic_id == Clinic.id)
        .where(
            RoleAssignment.user_id == target.id,
            RoleAssignment.role == UserRole.doctor,
            RoleAssignment.status == "active",
            RoleAssignment.revoked_at.is_(None),
            or_(RoleAssignment.hospital_id != hospital.id, Clinic.hospital_id != hospital.id),
        )
        .limit(1)
    )
    if other_hospital is not None:
        raise ApiError(409, "hospital_conflict", "Doctor has another active hospital assignment.")
    assignment = db.scalar(
        select(RoleAssignment)
        .where(
            RoleAssignment.user_id == target.id,
            RoleAssignment.role == UserRole.doctor,
            RoleAssignment.clinic_id == body.clinic_id,
        )
        .order_by(RoleAssignment.created_at.desc())
        .with_for_update()
    )
    before = assignment.status if assignment else "none"
    after = "active" if body.active else "revoked"
    if before == after or (assignment is None and not body.active):
        raise ApiError(409, "no_change", "The requested access state is already set.")
    if assignment is None:
        assignment = RoleAssignment(
            user_id=target.id,
            role=UserRole.doctor,
            hospital_id=hospital.id,
            clinic_id=body.clinic_id,
            assigned_by_user_id=user.id,
            status="active",
        )
        db.add(assignment)
        db.flush()
    else:
        assignment.status = after
        assignment.hospital_id = hospital.id
        assignment.revoked_at = None if body.active else datetime.now(UTC)
        if body.active:
            assignment.assigned_by_user_id = user.id
    _audit(
        db,
        user,
        "doctor_department_access_changed",
        "role_assignment",
        assignment.id,
        hospital.id,
        body.clinic_id,
        {"status": before},
        {"status": after, "target_user_id": str(target.id), "reason": body.reason.strip()},
    )
    db.commit()
    return {"assignment_id": str(assignment.id), "status": after}
