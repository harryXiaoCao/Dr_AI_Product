"""Server-owned clinical-event fact accounting for expected-care estimation.

The snapshot is deliberately provider-neutral. It contains only bounded,
structured, synthetic-development facts and never includes account/contact
identifiers, storage keys, credentials, raw attachments, or reviewer-only
notes. The snapshot is persisted inside the immutable candidate request JSON.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CareCostItem,
    ChronicDisease,
    ClinicalEvent,
    ClinicalEventUpdate,
    ClinicalService,
    ConsultationRequest,
    Diagnosis,
    DoctorNote,
    MedicalImagingAsset,
    MedicalRecord,
    Medication,
    PatientAllergy,
    PatientProfile,
    Prescription,
    PrescriptionMedication,
    RecoveryPlan,
    RecoveryTask,
    RecoveryTaskCompletion,
    VisitHistory,
)

FACT_SNAPSHOT_SCHEMA_VERSION = "cost-estimation-fact-snapshot.v1"
MAX_FACTS_PER_CATEGORY = 12
MAX_TEXT_LENGTH = 240


class CostFactScopeError(ValueError):
    """The requested patient/event pair is not an exact persisted scope."""


def _checksum(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    if not normalized:
        return None
    return normalized[:MAX_TEXT_LENGTH]


def _scalar(value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _clean(value: object) -> object:
    if isinstance(value, str):
        return _text(value)
    if isinstance(value, dict):
        return {
            str(key): cleaned
            for key, item in value.items()
            if (cleaned := _clean(item)) is not None
        }
    if isinstance(value, (list, tuple)):
        return [cleaned for item in value if (cleaned := _clean(item)) is not None]
    return _scalar(value)


def _provenance(
    source_type: str,
    *,
    source_scope: str,
    recorded_at: object | None = None,
) -> dict[str, object]:
    value: dict[str, object] = {
        "source_type": source_type,
        "source_scope": source_scope,
        "server_selected": True,
    }
    if recorded_at is not None:
        value["recorded_at"] = _scalar(recorded_at)
    return value


def _fact(
    *,
    fact_id: str,
    category: str,
    label: str,
    value: object,
    source_type: str,
    source_scope: str,
    recorded_at: object | None = None,
) -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "category": category,
        "label": label,
        "value": _clean(value),
        "provenance": _provenance(
            source_type,
            source_scope=source_scope,
            recorded_at=recorded_at,
        ),
        "selection_reason": "authorized_relevant_structured_fact",
    }


def build_cost_estimation_fact_snapshot(
    db: Session,
    *,
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
) -> dict[str, object]:
    """Build one bounded, exact-scope snapshot before any provider call."""

    patient = db.get(PatientProfile, patient_id)
    event = db.get(ClinicalEvent, clinical_event_id)
    if patient is None or event is None or event.patient_id != patient.id:
        raise CostFactScopeError("clinical_event_scope_not_found")

    used: list[dict[str, object]] = []
    not_used: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    category_counts: dict[str, int] = {}

    def add(
        *,
        category: str,
        label: str,
        value: object,
        source_type: str,
        source_scope: str,
        recorded_at: object | None = None,
    ) -> None:
        count = category_counts.get(category, 0) + 1
        category_counts[category] = count
        if count > MAX_FACTS_PER_CATEGORY:
            return
        used.append(
            _fact(
                fact_id=f"{category}.{count}",
                category=category,
                label=label,
                value=value,
                source_type=source_type,
                source_scope=source_scope,
                recorded_at=recorded_at,
            )
        )

    if _text(event.chief_complaint) or _text(event.symptom_summary):
        add(
            category="symptoms",
            label="Clinical Event symptoms and complaint",
            value={
                "chief_complaint": event.chief_complaint,
                "symptom_summary": event.symptom_summary,
                "onset_date": event.onset_date,
                "status": event.status,
            },
            source_type="clinical_event",
            source_scope="exact_clinical_event",
            recorded_at=event.updated_at,
        )
    if _text(event.diagnosis_summary):
        add(
            category="doctor_confirmed_finding",
            label="Doctor-recorded diagnosis or provisional diagnosis",
            value={"diagnosis_summary": event.diagnosis_summary},
            source_type="clinical_event",
            source_scope="exact_clinical_event",
            recorded_at=event.updated_at,
        )

    history_fields = {
        "heart_history": patient.heart_history,
        "endocrine_history": patient.endocrine_history,
        "neuro_history": patient.neuro_history,
        "digestive_history": patient.digestive_history,
        "respiratory_history": patient.respiratory_history,
        "kidney_history": patient.kidney_history,
        "cancer_history": patient.cancer_history,
        "surgery_history": patient.surgery_history,
        "family_history": patient.family_history,
    }
    for field, value in history_fields.items():
        if _text(value):
            add(
                category="medical_history",
                label=field,
                value={"summary": value},
                source_type="patient_profile",
                source_scope="authorized_patient_context",
                recorded_at=patient.context_recorded_at,
            )
    if _text(patient.patient_reported_medications):
        add(
            category="current_medication",
            label="Patient-reported current medications",
            value={"summary": patient.patient_reported_medications},
            source_type="patient_profile",
            source_scope="authorized_patient_context",
            recorded_at=patient.context_recorded_at,
        )

    allergies = db.scalars(
        select(PatientAllergy)
        .where(PatientAllergy.patient_id == patient.id, PatientAllergy.status == "active")
        .order_by(PatientAllergy.created_at, PatientAllergy.id)
    ).all()
    for row in allergies:
        add(
            category="allergy",
            label="Active allergy",
            value={
                "label": row.label,
                "reaction": row.reaction,
                "severity": row.severity,
            },
            source_type="patient_allergy",
            source_scope="authorized_patient_context",
            recorded_at=row.updated_at,
        )

    chronic = db.scalars(
        select(ChronicDisease)
        .where(ChronicDisease.patient_id == patient.id, ChronicDisease.status == "active")
        .order_by(ChronicDisease.created_at, ChronicDisease.id)
    ).all()
    for row in chronic:
        add(
            category="chronic_condition",
            label="Active chronic condition",
            value={
                "name": row.name,
                "diagnosed_on": row.diagnosed_on,
                "notes": row.notes,
            },
            source_type="chronic_disease",
            source_scope="authorized_patient_context",
            recorded_at=row.updated_at,
        )

    updates = db.scalars(
        select(ClinicalEventUpdate)
        .where(
            ClinicalEventUpdate.patient_id == patient.id,
            ClinicalEventUpdate.clinical_event_id == event.id,
        )
        .order_by(ClinicalEventUpdate.occurred_at, ClinicalEventUpdate.id)
    ).all()
    for row in updates:
        add(
            category="event_update",
            label="Patient Clinical Event update",
            value={
                "update_type": row.update_type,
                "summary": row.summary,
                "occurred_at": row.occurred_at,
            },
            source_type="clinical_event_update",
            source_scope="exact_clinical_event",
            recorded_at=row.created_at,
        )

    visits = db.scalars(
        select(VisitHistory)
        .where(
            VisitHistory.patient_id == patient.id,
            VisitHistory.clinical_event_id == event.id,
        )
        .order_by(VisitHistory.occurred_at, VisitHistory.id)
    ).all()
    for row in visits:
        add(
            category="medical_record",
            label="Event-linked visit record",
            value={
                "visit_type": row.visit_type,
                "title": row.title,
                "summary": row.summary,
                "occurred_at": row.occurred_at,
            },
            source_type="visit_history",
            source_scope="exact_clinical_event",
            recorded_at=row.updated_at,
        )

    diagnoses = db.scalars(
        select(Diagnosis)
        .where(
            Diagnosis.patient_id == patient.id,
            Diagnosis.clinical_event_id == event.id,
        )
        .order_by(Diagnosis.created_at, Diagnosis.id)
    ).all()
    for row in diagnoses:
        add(
            category="doctor_confirmed_finding",
            label="Doctor-recorded diagnosis",
            value={
                "label": row.label,
                "status": row.status,
                "diagnosed_on": row.diagnosed_on,
                "notes": row.notes,
            },
            source_type="diagnosis",
            source_scope="exact_clinical_event",
            recorded_at=row.updated_at,
        )

    imaging = db.scalars(
        select(MedicalImagingAsset)
        .where(
            MedicalImagingAsset.patient_id == patient.id,
            MedicalImagingAsset.clinical_event_id == event.id,
        )
        .order_by(MedicalImagingAsset.created_at, MedicalImagingAsset.id)
    ).all()
    for row in imaging:
        if row.upload_status != "uploaded":
            not_used.append(
                {
                    "category": "imaging",
                    "count": 1,
                    "reason": "upload_not_finalized",
                    "provenance": _provenance(
                        "medical_imaging_asset",
                        source_scope="exact_clinical_event",
                        recorded_at=row.updated_at,
                    ),
                }
            )
            continue
        add(
            category="imaging",
            label="Finalized imaging evidence and manual review",
            value={
                "content_type": row.content_type,
                "review_status": row.review_status,
                "finding_summary": row.finding_summary,
                "measurement_summary": row.measurement_summary,
                "observed_at": row.observed_at,
                "treatment_relevance_date": row.treatment_relevance_date,
                "clinical_service_linked": row.clinical_service_id is not None,
            },
            source_type="medical_imaging_asset",
            source_scope="exact_clinical_event",
            recorded_at=row.updated_at,
        )

    medications = db.scalars(
        select(Medication)
        .where(
            Medication.patient_id == patient.id,
            (Medication.clinical_event_id == event.id)
            | (
                Medication.clinical_event_id.is_(None)
                & Medication.status.in_(("active", "taking", "current"))
            ),
        )
        .order_by(Medication.created_at, Medication.id)
    ).all()
    for row in medications:
        add(
            category="medication",
            label="Medication record",
            value={
                "name": row.name,
                "dosage": row.dosage,
                "schedule": row.schedule,
                "status": row.status,
                "note": row.note,
                "event_linked": row.clinical_event_id == event.id,
            },
            source_type="medication",
            source_scope=(
                "exact_clinical_event"
                if row.clinical_event_id == event.id
                else "authorized_current_medication"
            ),
            recorded_at=row.created_at,
        )

    prescriptions = db.scalars(
        select(Prescription)
        .where(
            Prescription.patient_id == patient.id,
            Prescription.clinical_event_id == event.id,
        )
        .order_by(Prescription.created_at, Prescription.id)
    ).all()
    prescription_ids = [row.id for row in prescriptions]
    prescribed_items = (
        db.scalars(
            select(PrescriptionMedication)
            .where(PrescriptionMedication.prescription_id.in_(prescription_ids))
            .order_by(PrescriptionMedication.id)
        ).all()
        if prescription_ids
        else []
    )
    items_by_prescription: dict[uuid.UUID, list[PrescriptionMedication]] = {}
    for item in prescribed_items:
        items_by_prescription.setdefault(item.prescription_id, []).append(item)
    for row in prescriptions:
        add(
            category="prescription",
            label="Event-linked prescription",
            value={
                "status": row.status,
                "issued_at": row.issued_at,
                "medications": [
                    {
                        "name": item.name,
                        "dosage": item.dosage,
                        "schedule": item.schedule,
                        "start_date": item.start_date,
                        "end_date": item.end_date,
                    }
                    for item in items_by_prescription.get(row.id, [])
                ],
            },
            source_type="prescription",
            source_scope="exact_clinical_event",
            recorded_at=row.updated_at,
        )

    plans = db.scalars(
        select(RecoveryPlan)
        .where(
            RecoveryPlan.patient_id == patient.id,
            RecoveryPlan.clinical_event_id == event.id,
        )
        .order_by(RecoveryPlan.created_at, RecoveryPlan.id)
    ).all()
    plan_ids = [row.id for row in plans]
    tasks = (
        db.scalars(
            select(RecoveryTask)
            .where(
                RecoveryTask.patient_id == patient.id,
                RecoveryTask.plan_id.in_(plan_ids),
            )
            .order_by(RecoveryTask.plan_id, RecoveryTask.sort_order)
        ).all()
        if plan_ids
        else []
    )
    task_ids = [row.id for row in tasks]
    completion_ids = set(
        db.scalars(
            select(RecoveryTaskCompletion.task_id).where(
                RecoveryTaskCompletion.patient_id == patient.id,
                RecoveryTaskCompletion.task_id.in_(task_ids),
            )
        ).all()
        if task_ids
        else []
    )
    tasks_by_plan: dict[uuid.UUID, list[RecoveryTask]] = {}
    for task in tasks:
        tasks_by_plan.setdefault(task.plan_id, []).append(task)
    for row in plans:
        plan_tasks = tasks_by_plan.get(row.id, [])
        add(
            category="recovery_progress",
            label="Event-linked recovery plan and adherence",
            value={
                "title": row.title,
                "status": row.status,
                "review_status": row.review_status,
                "task_count": len(plan_tasks),
                "completed_task_count": sum(task.id in completion_ids for task in plan_tasks),
                "task_categories": [task.category for task in plan_tasks],
            },
            source_type="recovery_plan",
            source_scope="exact_clinical_event",
            recorded_at=row.updated_at,
        )

    consultations = db.scalars(
        select(ConsultationRequest)
        .where(
            ConsultationRequest.patient_id == patient.id,
            ConsultationRequest.clinical_event_id == event.id,
        )
        .order_by(ConsultationRequest.created_at, ConsultationRequest.id)
    ).all()
    for row in consultations:
        add(
            category="consultation",
            label="Event-linked consultation",
            value={
                "specialty": row.specialty,
                "question_summary": row.question_summary,
                "priority": row.priority,
                "status": row.status,
                "delivered_service_linked": row.clinical_service_id is not None,
            },
            source_type="consultation_request",
            source_scope="exact_clinical_event",
            recorded_at=row.updated_at,
        )

    services = db.scalars(
        select(ClinicalService)
        .where(
            ClinicalService.patient_id == patient.id,
            ClinicalService.clinical_event_id == event.id,
        )
        .order_by(ClinicalService.created_at, ClinicalService.id)
    ).all()
    for row in services:
        add(
            category="clinical_service",
            label="Event-linked clinical service",
            value={
                "category": row.category,
                "name": row.name,
                "service_subtype": row.service_subtype,
                "body_region": row.body_region,
                "service_code": row.service_code,
                "status": row.status,
                "ordered_at": row.ordered_at,
                "scheduled_at": row.scheduled_at,
                "performed_at": row.performed_at,
            },
            source_type="clinical_service",
            source_scope="exact_clinical_event",
            recorded_at=row.updated_at,
        )

    costs = db.scalars(
        select(CareCostItem)
        .where(
            CareCostItem.patient_id == patient.id,
            CareCostItem.clinical_event_id == event.id,
        )
        .order_by(CareCostItem.service_date, CareCostItem.id)
    ).all()
    for row in costs:
        add(
            category="cost",
            label="Event-linked delivered-service cost",
            value={
                "item_type": row.item_type,
                "label": row.label,
                "service_date": row.service_date,
                "status": row.status,
                "pricing_state": row.pricing_state,
                "quantity": row.quantity,
                "currency": row.currency,
                "actual_cost_minor": row.actual_cost_minor,
                "payer_requested_minor": row.payer_requested_minor,
                "patient_responsibility_minor": row.patient_responsibility_minor,
                "source_type": (
                    "medication"
                    if row.medication_id is not None
                    else "clinical_service"
                    if row.clinical_service_id is not None
                    else "unlinked"
                ),
            },
            source_type="care_cost_item",
            source_scope="exact_clinical_event",
            recorded_at=row.updated_at,
        )

    patient_wide_records = db.scalar(
        select(MedicalRecord).where(MedicalRecord.patient_id == patient.id).limit(1)
    )
    if patient_wide_records is not None:
        record_count = len(
            db.scalars(select(MedicalRecord.id).where(MedicalRecord.patient_id == patient.id)).all()
        )
        not_used.append(
            {
                "category": "medical_record",
                "count": record_count,
                "reason": "patient_wide_record_has_no_clinical_event_binding",
                "provenance": _provenance(
                    "medical_record",
                    source_scope="authorized_patient_but_not_exact_event",
                ),
            }
        )
    note_count = len(
        db.scalars(
            select(DoctorNote.id).where(
                DoctorNote.patient_id == patient.id,
                DoctorNote.clinical_event_id == event.id,
            )
        ).all()
    )
    if note_count:
        not_used.append(
            {
                "category": "doctor_note",
                "count": note_count,
                "reason": "free_text_note_not_required_for_cost_estimation",
                "provenance": _provenance(
                    "doctor_note",
                    source_scope="exact_clinical_event",
                ),
            }
        )
    for category, count in sorted(category_counts.items()):
        if count > MAX_FACTS_PER_CATEGORY:
            not_used.append(
                {
                    "category": category,
                    "count": count - MAX_FACTS_PER_CATEGORY,
                    "reason": "bounded_minimum_necessary_limit",
                    "provenance": _provenance(
                        "multiple_records",
                        source_scope="exact_or_authorized_patient_context",
                    ),
                }
            )

    required_categories = {
        "symptoms": "No symptom or chief-complaint fact is recorded.",
        "medical_history": "No relevant structured medical-history fact is recorded.",
        "imaging": "No finalized event-linked imaging fact is available.",
        "doctor_confirmed_finding": "No doctor-confirmed finding is recorded.",
        "prescription": "No event-linked prescription is recorded.",
        "medication": "No event-linked or current medication record is available.",
        "recovery_progress": "No event-linked recovery adherence fact is available.",
        "consultation": "No event-linked consultation is recorded.",
        "clinical_service": "No event-linked clinical service is recorded.",
        "cost": "No event-linked delivered-service cost is recorded.",
    }
    for category, reason in required_categories.items():
        if category_counts.get(category, 0) == 0:
            missing.append(
                {
                    "category": category,
                    "reason": reason,
                    "expected_provenance": "server_authorized_persistence",
                }
            )
    missing.append(
        {
            "category": "ai_imaging_observation_draft",
            "reason": "DeepSeek image input is unsupported; no AI imaging draft is used.",
            "expected_provenance": "separately_governed_vision_purpose",
        }
    )

    snapshot: dict[str, object] = {
        "schema_version": FACT_SNAPSHOT_SCHEMA_VERSION,
        "scope": {
            "patient_bound": True,
            "clinical_event_bound": True,
            "synthetic_only": event.metadata_json.get("data_class")
            in {"synthetic", "wholly_synthetic"},
        },
        "facts_used": used,
        "facts_not_used": not_used,
        "missing_facts": missing,
        "counts": {
            "facts_used": len(used),
            "facts_not_used": sum(int(item["count"]) for item in not_used),
            "missing_categories": len(missing),
        },
        "authority_boundary": {
            "server_selected": True,
            "provider_may_not_add_or_modify_facts": True,
            "doctor_owns_findings_and_diagnoses": True,
            "deterministic_cost_validation_authoritative": True,
        },
    }
    snapshot["snapshot_checksum_sha256"] = _checksum(snapshot)
    return snapshot


def serialize_cost_fact_snapshot(
    snapshot: object,
    *,
    role: Literal["provider", "doctor", "patient", "payer"],
) -> dict[str, object]:
    """Return a role-safe copy while retaining transparent fact accounting."""

    if not isinstance(snapshot, dict):
        return {
            "schema_version": FACT_SNAPSHOT_SCHEMA_VERSION,
            "facts_used": [],
            "facts_not_used": [],
            "missing_facts": [
                {
                    "category": "fact_snapshot",
                    "reason": "No immutable cost-estimation fact snapshot is available.",
                    "expected_provenance": "candidate_request",
                }
            ],
            "counts": {
                "facts_used": 0,
                "facts_not_used": 0,
                "missing_categories": 1,
            },
        }
    value = json.loads(json.dumps(snapshot, default=str))
    facts = value.get("facts_used", [])
    if not isinstance(facts, list):
        facts = []
    if role == "payer":
        clinically_sensitive = {
            "symptoms",
            "medical_history",
            "allergy",
            "chronic_condition",
            "current_medication",
            "medication",
            "event_update",
            "medical_record",
        }
        for fact in facts:
            if isinstance(fact, dict) and fact.get("category") in clinically_sensitive:
                fact["value"] = {
                    "present": True,
                    "detail_withheld": True,
                    "withholding_reason": "minimum_necessary_payer_view",
                }
    if role == "patient":
        for fact in facts:
            if not isinstance(fact, dict):
                continue
            value_item = fact.get("value")
            if isinstance(value_item, dict):
                value_item.pop("service_code", None)
    if role in {"patient", "payer"}:
        value.pop("snapshot_checksum_sha256", None)
    value["role_view"] = role
    return value
