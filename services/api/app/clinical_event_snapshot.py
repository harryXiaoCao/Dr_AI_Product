"""Authorization-scoped, deterministic Clinical Event snapshot construction."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.clinical_event_intelligence_contracts import (
    FrozenClinicalEventSnapshot,
    FrozenFact,
    FrozenLocation,
    FrozenRequestedLine,
    canonical_checksum,
)
from app.models import (
    ChronicDisease,
    Clinic,
    ClinicalEvent,
    ClinicalService,
    Diagnosis,
    Hospital,
    MedicalImagingAsset,
    MedicalRecord,
    Medication,
    PatientAllergy,
    PatientProfile,
    PayerRequest,
    PayerRequestLine,
    Prescription,
    RecoveryPlan,
    RecoveryTask,
    RecoveryTaskCompletion,
    RoleAssignment,
)

SNAPSHOT_VERSION = 1
STALE_DAYS = 365


class SnapshotConstructionError(ValueError):
    pass


def _iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _state(value: object, *, verified: bool = False) -> str:
    updated_at = getattr(value, "updated_at", None) or getattr(value, "created_at", None)
    if isinstance(updated_at, datetime):
        age_days = (datetime.now(updated_at.tzinfo) - updated_at).days
        if age_days > STALE_DAYS:
            return "stale"
    return "verified" if verified else "unverified"


def _fact(
    *,
    fact_id: str,
    category: str,
    value: object,
    source_type: str,
    source_id: uuid.UUID | str,
    verification_state: str,
) -> FrozenFact:
    return FrozenFact(
        fact_id=fact_id,
        category=category,
        value=value,
        source_type=source_type,
        source_id=str(source_id),
        verification_state=verification_state,  # type: ignore[arg-type]
    )


def _coded_location(value: object) -> dict[str, object]:
    """Read exact structured keys; never parse prose, IP data, or addresses."""

    metadata = value if isinstance(value, dict) else {}
    nested = metadata.get("location")
    if isinstance(nested, dict):
        metadata = nested
    allowed = {
        "jurisdiction_code",
        "province_code",
        "city_code",
        "facility_level",
        "department_code",
    }
    return {
        key: raw.strip()
        for key, raw in metadata.items()
        if key in allowed and isinstance(raw, str) and raw.strip()
    }


def _location_from_record(
    *,
    source: str,
    metadata: dict[str, object],
    hospital_id: object = None,
    clinic_id: object = None,
) -> FrozenLocation | None:
    coded = _coded_location(metadata)
    required = ("jurisdiction_code", "province_code", "city_code", "facility_level")
    if not any(coded.get(key) for key in required):
        return None
    complete = all(coded.get(key) for key in required)
    return FrozenLocation(
        jurisdiction_code=coded.get("jurisdiction_code"),  # type: ignore[arg-type]
        province_code=coded.get("province_code"),  # type: ignore[arg-type]
        city_code=coded.get("city_code"),  # type: ignore[arg-type]
        facility_level=coded.get("facility_level"),  # type: ignore[arg-type]
        hospital_id=str(hospital_id) if hospital_id else None,
        clinic_id=str(clinic_id) if clinic_id else None,
        department=coded.get("department_code"),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        complete=complete,
    )


def resolve_structured_location(
    db: Session,
    *,
    event: ClinicalEvent,
    services: list[ClinicalService],
) -> FrozenLocation:
    """Resolve coded location in a fixed precedence order from owned records."""

    event_hospital = db.get(Hospital, event.hospital_id) if event.hospital_id else None
    event_clinic = db.get(Clinic, event.clinic_id) if event.clinic_id else None
    direct_metadata: dict[str, object] = {}
    if event_hospital is not None:
        direct_metadata.update(
            {
                "jurisdiction_code": event_hospital.jurisdiction_code,
                "province_code": event_hospital.province,
                "city_code": event_hospital.city,
            }
        )
    if event_clinic is not None:
        direct_metadata.update(
            {
                "facility_level": event_clinic.facility_level,
                "department_code": event.department_code or event_clinic.department_code,
            }
        )
    if event_hospital is not None or event_clinic is not None:
        for key, value in _coded_location(event.metadata_json).items():
            direct_metadata.setdefault(key, value)
    direct = _location_from_record(
        source="clinical_event",
        metadata=direct_metadata,
        hospital_id=event.hospital_id,
        clinic_id=event.clinic_id,
    )
    candidates: list[FrozenLocation] = [direct] if direct is not None else []
    for service in services:
        clinic = service.clinic
        if clinic is None:
            continue
        metadata = {
            "jurisdiction_code": clinic.hospital.jurisdiction_code,
            "province_code": clinic.hospital.province,
            "city_code": clinic.hospital.city,
            "facility_level": clinic.facility_level,
            "department_code": clinic.department_code,
            **_coded_location(clinic.hospital.metadata_json),
            **_coded_location(clinic.metadata_json),
        }
        value = _location_from_record(
            source="clinical_service_facility",
            metadata=metadata,
            hospital_id=clinic.hospital_id,
            clinic_id=clinic.id,
        )
        if value is not None:
            candidates.append(value)
    if not candidates and event.doctor is not None:
        assignments = db.scalars(
            select(RoleAssignment)
            .options(
                selectinload(RoleAssignment.clinic).selectinload(Clinic.hospital),
                selectinload(RoleAssignment.hospital),
            )
            .where(
                RoleAssignment.user_id == event.doctor.user_id,
                RoleAssignment.status == "active",
            )
        ).all()
        for assignment in assignments:
            clinic = assignment.clinic
            hospital = assignment.hospital or (clinic.hospital if clinic else None)
            metadata = {
                "jurisdiction_code": hospital.jurisdiction_code if hospital else None,
                "province_code": hospital.province if hospital else None,
                "city_code": hospital.city if hospital else None,
                "facility_level": clinic.facility_level if clinic else None,
                "department_code": clinic.department_code if clinic else None,
                **_coded_location(hospital.metadata_json if hospital else {}),
                **_coded_location(clinic.metadata_json if clinic else {}),
            }
            value = _location_from_record(
                source="provider_organization",
                metadata=metadata,
                hospital_id=hospital.id if hospital else None,
                clinic_id=clinic.id if clinic else None,
            )
            if value is not None:
                candidates.append(value)
    identities = {
        (
            item.jurisdiction_code,
            item.province_code,
            item.city_code,
            item.facility_level,
            item.hospital_id,
            item.clinic_id,
        )
        for item in candidates
    }
    if len(identities) > 1:
        return FrozenLocation(
            jurisdiction_code=None,
            province_code=None,
            city_code=None,
            facility_level=None,
            source="conflicting_structured_records",
            complete=False,
        )
    if candidates:
        return candidates[0]
    return FrozenLocation(
        jurisdiction_code=None,
        province_code=None,
        city_code=None,
        facility_level=None,
        source="missing_structured_records",
        complete=False,
    )


def _requested_line(line: PayerRequestLine) -> FrozenRequestedLine:
    required = ("quantity", "unit")
    if any(not getattr(line, name, None) for name in required):
        raise SnapshotConstructionError("payer_request_line_snapshot_incomplete")
    return FrozenRequestedLine(
        requested_line_id=str(line.id),
        item_type=line.item_type,
        label=line.label,
        code_system=line.code_system,
        service_code=line.service_code,
        quantity=line.quantity,
        unit=line.unit,
        requested_minor=line.requested_minor,
        actual_cost_minor=line.actual_cost_minor,
        currency=line.currency,
        service_date=line.service_date.isoformat(),
    )


def build_frozen_clinical_event_snapshot(
    db: Session,
    *,
    payer_request: PayerRequest,
) -> FrozenClinicalEventSnapshot:
    """Freeze exact request lines and an allow-listed event context."""

    event = db.scalar(
        select(ClinicalEvent)
        .options(selectinload(ClinicalEvent.doctor))
        .where(
            ClinicalEvent.id == payer_request.clinical_event_id,
            ClinicalEvent.patient_id == payer_request.patient_id,
        )
    )
    patient = db.get(PatientProfile, payer_request.patient_id)
    if event is None or patient is None:
        raise SnapshotConstructionError("payer_request_event_scope_mismatch")
    lines = db.scalars(
        select(PayerRequestLine)
        .where(PayerRequestLine.payer_request_id == payer_request.id)
        .order_by(PayerRequestLine.created_at, PayerRequestLine.id)
    ).all()
    if not lines:
        raise SnapshotConstructionError("payer_request_has_no_lines")
    requested_lines = [_requested_line(line) for line in lines]
    if len({line.requested_line_id for line in requested_lines}) != len(requested_lines):
        raise SnapshotConstructionError("duplicate_payer_request_line")
    services = db.scalars(
        select(ClinicalService)
        .options(selectinload(ClinicalService.clinic).selectinload(Clinic.hospital))
        .where(
            ClinicalService.clinical_event_id == event.id,
            ClinicalService.patient_id == patient.id,
        )
        .order_by(ClinicalService.created_at, ClinicalService.id)
    ).all()
    location = resolve_structured_location(db, event=event, services=list(services))
    facts: list[FrozenFact] = []
    facts_not_used: list[FrozenFact] = []
    for key, value in (
        ("chief_complaint", event.chief_complaint),
        ("symptom_summary", event.symptom_summary),
        ("diagnosis_summary", event.diagnosis_summary),
        ("onset_date", _iso(event.onset_date)),
        ("event_status", event.status),
    ):
        if value not in (None, ""):
            facts.append(
                _fact(
                    fact_id=f"event.{key}",
                    category="clinical_event",
                    value=value,
                    source_type="clinical_event",
                    source_id=event.id,
                    verification_state=_state(event, verified=event.doctor_id is not None),
                )
            )
    admitted_metadata = {
        key: event.metadata_json[key]
        for key in (
            "symptom_duration",
            "symptom_severity",
            "symptom_progression",
            "differential_diagnosis",
            "diagnosis_rationale",
            "confirmed_findings",
            "contraindications",
            "treatment_states",
        )
        if key in event.metadata_json
    }
    for key, value in admitted_metadata.items():
        facts.append(
            _fact(
                fact_id=f"event.structured.{key}",
                category="structured_clinical_event",
                value=value,
                source_type="clinical_event_metadata",
                source_id=event.id,
                verification_state=_state(event, verified=event.doctor_id is not None),
            )
        )
    global_histories = (
        (PatientAllergy, "allergy", ("label", "reaction", "severity", "status")),
        (ChronicDisease, "chronic_condition", ("name", "status", "diagnosed_on", "notes")),
    )
    for model, category, fields in global_histories:
        rows = db.scalars(
            select(model).where(model.patient_id == patient.id).order_by(model.created_at, model.id)
        ).all()
        for index, row in enumerate(rows, 1):
            value = {field: getattr(row, field, None) for field in fields}
            facts.append(
                _fact(
                    fact_id=f"{category}.{index}",
                    category=category,
                    value=value,
                    source_type=model.__tablename__,
                    source_id=row.id,
                    verification_state=_state(row),
                )
            )
    event_histories = (
        (Medication, "medication", ("name", "dosage", "schedule", "status", "note")),
        (Diagnosis, "diagnosis", ("label", "status", "diagnosed_on", "notes")),
    )
    for model, category, fields in event_histories:
        rows = db.scalars(
            select(model).where(model.patient_id == patient.id).order_by(model.created_at, model.id)
        ).all()
        used_index = unused_index = 0
        for row in rows:
            value = {field: getattr(row, field, None) for field in fields}
            target = facts if row.clinical_event_id == event.id else facts_not_used
            if target is facts:
                used_index += 1
                index = used_index
            else:
                unused_index += 1
                index = unused_index
            target.append(
                _fact(
                    fact_id=f"{category}.{'used' if target is facts else 'not_used'}.{index}",
                    category=category,
                    value=value,
                    source_type=model.__tablename__,
                    source_id=row.id,
                    verification_state=_state(row),
                )
            )
    prescriptions = db.scalars(
        select(Prescription)
        .options(selectinload(Prescription.medications))
        .where(
            Prescription.patient_id == patient.id,
            Prescription.clinical_event_id == event.id,
        )
        .order_by(Prescription.created_at, Prescription.id)
    ).all()
    for index, prescription in enumerate(prescriptions, 1):
        facts.append(
            _fact(
                fact_id=f"prescription.{index}",
                category="prescription_and_adherence",
                value={
                    "status": prescription.status,
                    "issued_at": _iso(prescription.issued_at),
                    "medications": [
                        {
                            "name": item.name,
                            "dosage": item.dosage,
                            "schedule": item.schedule,
                            "start_date": _iso(item.start_date),
                            "end_date": _iso(item.end_date),
                            "taken": item.metadata_json.get("taken"),
                            "adherence": item.metadata_json.get("adherence"),
                            "contraindication": item.metadata_json.get("contraindication"),
                        }
                        for item in prescription.medications
                    ],
                },
                source_type="prescriptions",
                source_id=prescription.id,
                verification_state=_state(prescription, verified=True),
            )
        )
    recovery_plans = db.scalars(
        select(RecoveryPlan)
        .where(
            RecoveryPlan.patient_id == patient.id,
            RecoveryPlan.clinical_event_id == event.id,
        )
        .order_by(RecoveryPlan.created_at, RecoveryPlan.id)
    ).all()
    for index, plan in enumerate(recovery_plans, 1):
        task_rows = db.scalars(
            select(RecoveryTask)
            .where(RecoveryTask.plan_id == plan.id)
            .order_by(RecoveryTask.sort_order, RecoveryTask.id)
        ).all()
        completed_task_ids = set(
            db.scalars(
                select(RecoveryTaskCompletion.task_id).where(
                    RecoveryTaskCompletion.task_id.in_([task.id for task in task_rows])
                )
            ).all()
        )
        facts.append(
            _fact(
                fact_id=f"recovery_plan.{index}",
                category="recovery_and_adherence",
                value={
                    "status": plan.status,
                    "review_status": plan.review_status,
                    "tasks": [
                        {
                            "category": task.category,
                            "title": task.title,
                            "completed": task.id in completed_task_ids,
                        }
                        for task in task_rows
                    ],
                },
                source_type="recovery_plans",
                source_id=plan.id,
                verification_state=_state(plan, verified=plan.reviewed_at is not None),
            )
        )
    admitted_record_ids: set[uuid.UUID] = set()
    for value in event.metadata_json.get("medical_record_ids", []):
        try:
            admitted_record_ids.add(uuid.UUID(str(value)))
        except (TypeError, ValueError):
            continue
    records = db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient.id)
        .order_by(MedicalRecord.recorded_at, MedicalRecord.id)
    ).all()
    for index, record in enumerate(records, 1):
        target = facts if record.id in admitted_record_ids else facts_not_used
        target.append(
            _fact(
                fact_id=f"medical_record.{'used' if target is facts else 'not_used'}.{index}",
                category="laboratory_or_report",
                value={
                    "title": record.title,
                    "category": record.category,
                    "summary": record.summary,
                    "recorded_at": _iso(record.recorded_at),
                },
                source_type="medical_records",
                source_id=record.id,
                verification_state=_state(record),
            )
        )
    for index, service in enumerate(services, 1):
        facts.append(
            _fact(
                fact_id=f"service.{index}",
                category="treatment_lifecycle",
                value={
                    "category": service.category,
                    "name": service.name,
                    "service_code": service.service_code,
                    "status": service.status,
                    "ordered_at": _iso(service.ordered_at),
                    "scheduled_at": _iso(service.scheduled_at),
                    "performed_at": _iso(service.performed_at),
                },
                source_type="clinical_services",
                source_id=service.id,
                verification_state=_state(service, verified=True),
            )
        )
    imaging = db.scalars(
        select(MedicalImagingAsset)
        .where(
            MedicalImagingAsset.patient_id == patient.id,
            MedicalImagingAsset.clinical_event_id == event.id,
        )
        .order_by(MedicalImagingAsset.created_at, MedicalImagingAsset.id)
    ).all()
    for index, item in enumerate(imaging, 1):
        facts.append(
            _fact(
                fact_id=f"imaging_report.{index}",
                category="imaging_report",
                value={
                    "modality": getattr(item, "modality", None),
                    "body_region": getattr(item, "body_region", None),
                    "upload_status": item.upload_status,
                    "review_status": item.review_status,
                    "finding_summary": item.finding_summary,
                    "measurement_summary": item.measurement_summary,
                },
                source_type="medical_imaging_assets",
                source_id=item.id,
                verification_state=_state(item, verified=item.reviewed_at is not None),
            )
        )
    missing = []
    if not location.complete:
        missing.append("Structured Clinical Event facility location is incomplete.")
    for line in requested_lines:
        if not line.code_system or not line.service_code:
            missing.append(
                f"Requested line {line.requested_line_id} has no authoritative code snapshot."
            )
    for category, present in (
        ("diagnosis", any(fact.category == "diagnosis" for fact in facts)),
        ("allergy", any(fact.category == "allergy" for fact in facts)),
        ("current medication", any(fact.category == "medication" for fact in facts)),
    ):
        if not present:
            missing.append(f"No {category} record is available in the authorized snapshot.")
    conflicts = (
        ["Structured facility records conflict; no location was selected."]
        if location.source == "conflicting_structured_records"
        else []
    )
    requested_payload = [line.model_dump(mode="json") for line in requested_lines]
    requested_checksum = canonical_checksum(requested_payload)
    payload = {
        "snapshot_version": SNAPSHOT_VERSION,
        "payer_request_version": payer_request.version,
        "patient_id": str(patient.id),
        "clinical_event_id": str(event.id),
        "payer_request_id": str(payer_request.id),
        "encounter_date": _iso(event.encounter_at),
        "location": location.model_dump(mode="json"),
        "facts_used": [fact.model_dump(mode="json") for fact in facts],
        "facts_not_used": [fact.model_dump(mode="json") for fact in facts_not_used],
        "missing_information": missing,
        "conflicting_information": conflicts,
        "requested_lines": requested_payload,
        "requested_item_set_checksum_sha256": requested_checksum,
    }
    return FrozenClinicalEventSnapshot(
        **payload,
        snapshot_checksum_sha256=canonical_checksum(payload),
    )
