from __future__ import annotations

import re
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot_contracts import (
    PatientContextBundle,
    PatientContextCategory,
    PatientContextItem,
    PatientContextProvenance,
)
from app.config import Settings
from app.models import (
    ChronicDisease,
    ClinicalEvent,
    Diagnosis,
    Medication,
    PatientProfile,
    Prescription,
    PrescriptionMedication,
    RecoveryPlan,
    UserRole,
)

MAX_CONTEXT_ITEMS = 16
MAX_ITEMS_PER_CATEGORY = 4

CATEGORY_PATTERNS: dict[PatientContextCategory, tuple[str, ...]] = {
    PatientContextCategory.profile: (
        r"\b(age|birth|sex|gender|pregnan|smok|alcohol|my profile)\b",
        r"(年龄|出生|性别|怀孕|吸烟|饮酒|我的资料)",
    ),
    PatientContextCategory.measurements: (
        r"\b(blood pressure|bp|systolic|diastolic|weight|height|measurement|reading)\b",
        r"(血压|收缩压|舒张压|体重|身高|测量|读数)",
    ),
    PatientContextCategory.conditions: (
        r"\b(condition|disease|diagnos|hypertension|diabetes|chronic|medical history)\b",
        r"(疾病|病情|诊断|高血压|糖尿病|慢性病|病史)",
    ),
    PatientContextCategory.medications: (
        r"\b(medicine|medication|drug|prescription|dose|dosage|pill|schedule)\b",
        r"(药|用药|处方|剂量|服药|药物)",
    ),
    PatientContextCategory.clinical_events: (
        r"\b(symptom|care episode|clinical event|complaint|current problem|follow-up)\b",
        r"(症状|临床事件|就诊事件|主诉|当前问题|复诊)",
    ),
    PatientContextCategory.recovery_plan: (
        r"\b(recovery|care plan|task|exercise|diet|rehab)\b",
        r"(康复|恢复计划|任务|运动|饮食|复健)",
    ),
}


def _matches_category(message: str, category: PatientContextCategory) -> bool:
    return any(
        re.search(pattern, message, flags=re.IGNORECASE) for pattern in CATEGORY_PATTERNS[category]
    )


def _as_date(value: date | datetime | None, *, fallback: date) -> date:
    if isinstance(value, datetime):
        return value.astimezone(UTC).date() if value.tzinfo else value.date()
    return value or fallback


def _trim(value: object) -> str:
    return str(value).strip()[:500]


def _item(
    *,
    context_id: str,
    category: PatientContextCategory,
    field_name: str,
    value: object,
    provenance: PatientContextProvenance,
    attribution_phrase: str,
    recorded_on: date,
    resource_id: object,
) -> PatientContextItem:
    return PatientContextItem(
        context_id=context_id,
        category=category,
        field_name=field_name,
        value=_trim(value),
        provenance=provenance,
        attribution_phrase=attribution_phrase,
        recorded_on=recorded_on,
        resource_id=str(resource_id),
    )


def _profile_items(
    profile: PatientProfile, category: PatientContextCategory
) -> list[PatientContextItem]:
    recorded_on = (
        profile.measurements_recorded_at.date()
        if category == PatientContextCategory.measurements
        and profile.measurements_recorded_at is not None
        else profile.context_recorded_at.date()
    )
    fields: tuple[tuple[str, object | None], ...]
    if category == PatientContextCategory.measurements:
        blood_pressure = None
        if (
            profile.systolic_blood_pressure is not None
            and profile.diastolic_blood_pressure is not None
        ):
            blood_pressure = (
                f"{profile.systolic_blood_pressure}/{profile.diastolic_blood_pressure} mmHg; "
                "this is a recorded observation, not a diagnosis"
            )
        fields = (
            ("blood_pressure", blood_pressure),
            ("height_cm", profile.height_cm),
            ("weight_kg", profile.weight_kg),
        )
    else:
        fields = (
            ("birth_date", profile.birth_date),
            ("birth_year", profile.birth_year),
            ("sex", profile.sex or profile.gender),
            ("smoking_status", profile.smoking_status),
            ("alcohol_consumption", profile.alcohol_consumption),
            ("pregnancy_status", profile.pregnancy_status),
        )
    return [
        _item(
            context_id=f"ctx-profile-{field_name}",
            category=category,
            field_name=field_name,
            value=value,
            provenance=PatientContextProvenance.patient_profile,
            attribution_phrase="your profile records",
            recorded_on=recorded_on,
            resource_id=profile.id,
        )
        for field_name, value in fields
        if value is not None and str(value).strip()
    ][:MAX_ITEMS_PER_CATEGORY]


def _condition_items(db: Session, profile: PatientProfile) -> list[PatientContextItem]:
    fallback = profile.context_recorded_at.date()
    items: list[PatientContextItem] = []
    diseases = db.scalars(
        select(ChronicDisease)
        .where(ChronicDisease.patient_id == profile.id, ChronicDisease.status == "active")
        .order_by(ChronicDisease.updated_at.desc())
        .limit(MAX_ITEMS_PER_CATEGORY)
    ).all()
    for disease in diseases:
        doctor_recorded = disease.recorded_by.role == UserRole.doctor
        items.append(
            _item(
                context_id=f"ctx-condition-{disease.id}",
                category=PatientContextCategory.conditions,
                field_name="doctor_recorded_condition"
                if doctor_recorded
                else "patient_reported_condition",
                value=disease.name,
                provenance=(
                    PatientContextProvenance.doctor_record
                    if doctor_recorded
                    else PatientContextProvenance.patient_reported
                ),
                attribution_phrase=(
                    "according to your doctor's record"
                    if doctor_recorded
                    else "your reported history"
                ),
                recorded_on=_as_date(disease.diagnosed_on or disease.updated_at, fallback=fallback),
                resource_id=disease.id,
            )
        )
    if len(items) < MAX_ITEMS_PER_CATEGORY:
        diagnoses = db.scalars(
            select(Diagnosis)
            .where(Diagnosis.patient_id == profile.id, Diagnosis.status == "active")
            .order_by(Diagnosis.updated_at.desc())
            .limit(MAX_ITEMS_PER_CATEGORY - len(items))
        ).all()
        for diagnosis in diagnoses:
            doctor_recorded = diagnosis.recorded_by.role == UserRole.doctor
            items.append(
                _item(
                    context_id=f"ctx-diagnosis-{diagnosis.id}",
                    category=PatientContextCategory.conditions,
                    field_name="doctor_recorded_diagnosis"
                    if doctor_recorded
                    else "patient_reported_diagnosis",
                    value=diagnosis.label,
                    provenance=(
                        PatientContextProvenance.doctor_record
                        if doctor_recorded
                        else PatientContextProvenance.patient_reported
                    ),
                    attribution_phrase=(
                        "according to your doctor's record"
                        if doctor_recorded
                        else "your reported history"
                    ),
                    recorded_on=_as_date(
                        diagnosis.diagnosed_on or diagnosis.updated_at, fallback=fallback
                    ),
                    resource_id=diagnosis.id,
                )
            )
    return items


def _medication_items(db: Session, profile: PatientProfile) -> list[PatientContextItem]:
    items: list[PatientContextItem] = []
    prescription_rows = db.execute(
        select(PrescriptionMedication, Prescription)
        .join(Prescription, Prescription.id == PrescriptionMedication.prescription_id)
        .where(
            Prescription.patient_id == profile.id,
            Prescription.status.in_(("active", "issued")),
        )
        .order_by(Prescription.issued_at.desc().nullslast(), Prescription.created_at.desc())
        .limit(MAX_ITEMS_PER_CATEGORY)
    ).all()
    for medication, prescription in prescription_rows:
        items.append(
            _item(
                context_id=f"ctx-prescription-{medication.id}",
                category=PatientContextCategory.medications,
                field_name="current_prescription",
                value=f"{medication.name}; {medication.dosage}; {medication.schedule}",
                provenance=PatientContextProvenance.current_prescription,
                attribution_phrase="according to your current prescription",
                recorded_on=_as_date(
                    prescription.issued_at or prescription.created_at, fallback=date.today()
                ),
                resource_id=prescription.id,
            )
        )
    if len(items) < MAX_ITEMS_PER_CATEGORY:
        medications = db.scalars(
            select(Medication)
            .where(Medication.patient_id == profile.id, Medication.status == "active")
            .order_by(Medication.created_at.desc())
            .limit(MAX_ITEMS_PER_CATEGORY - len(items))
        ).all()
        for medication in medications:
            items.append(
                _item(
                    context_id=f"ctx-medication-{medication.id}",
                    category=PatientContextCategory.medications,
                    field_name="current_medication_schedule",
                    value=f"{medication.name}; {medication.dosage}; {medication.schedule}",
                    provenance=PatientContextProvenance.medication_schedule,
                    attribution_phrase="according to your current medication schedule",
                    recorded_on=medication.created_at.date(),
                    resource_id=medication.id,
                )
            )
    return items


def _clinical_event_items(db: Session, profile: PatientProfile) -> list[PatientContextItem]:
    events = db.scalars(
        select(ClinicalEvent)
        .where(ClinicalEvent.patient_id == profile.id, ClinicalEvent.status == "active")
        .order_by(ClinicalEvent.updated_at.desc())
        .limit(2)
    ).all()
    items: list[PatientContextItem] = []
    for event in events:
        values = (
            ("clinical_event", event.title),
            ("chief_complaint", event.chief_complaint),
            ("symptom_summary", event.symptom_summary),
            ("diagnosis_summary", event.diagnosis_summary),
        )
        for field_name, value in values:
            if value and len(items) < MAX_ITEMS_PER_CATEGORY:
                items.append(
                    _item(
                        context_id=f"ctx-event-{event.id}-{field_name}",
                        category=PatientContextCategory.clinical_events,
                        field_name=field_name,
                        value=value,
                        provenance=PatientContextProvenance.doctor_record,
                        attribution_phrase="according to your doctor's record",
                        recorded_on=event.updated_at.date(),
                        resource_id=event.id,
                    )
                )
    return items


def _recovery_items(db: Session, profile: PatientProfile) -> list[PatientContextItem]:
    plans = db.scalars(
        select(RecoveryPlan)
        .where(RecoveryPlan.patient_id == profile.id, RecoveryPlan.status == "active")
        .order_by(RecoveryPlan.activated_at.desc().nullslast(), RecoveryPlan.updated_at.desc())
        .limit(2)
    ).all()
    items: list[PatientContextItem] = []
    for plan in plans:
        for field_name, value in (("plan_title", plan.title), ("instructions", plan.instructions)):
            if value:
                items.append(
                    _item(
                        context_id=f"ctx-recovery-{plan.id}-{field_name}",
                        category=PatientContextCategory.recovery_plan,
                        field_name=field_name,
                        value=value,
                        provenance=PatientContextProvenance.recovery_plan,
                        attribution_phrase="according to your current recovery plan",
                        recorded_on=_as_date(
                            plan.activated_at or plan.updated_at, fallback=date.today()
                        ),
                        resource_id=plan.id,
                    )
                )
    return items[:MAX_ITEMS_PER_CATEGORY]


def _allowed_for_provider(item: PatientContextItem, settings: Settings) -> bool:
    if settings.chatbot_data_mode == "synthetic_only":
        return True
    allowed = set(settings.chatbot_external_provider_allowed_context_fields)
    return item.field_name in allowed or item.category.value in allowed


def select_patient_context(
    db: Session,
    *,
    profile: PatientProfile,
    message: str,
    settings: Settings,
) -> PatientContextBundle:
    """Select only record fragments relevant to this question.

    This broker is data-origin neutral: the same database records and contract work
    for synthetic fixtures now and real patient records when the deployment's
    external-provider policy enables their categories.
    """

    selected: list[PatientContextItem] = []
    for category in PatientContextCategory:
        if not _matches_category(message, category):
            continue
        if category in {PatientContextCategory.profile, PatientContextCategory.measurements}:
            selected.extend(_profile_items(profile, category))
        elif category == PatientContextCategory.conditions:
            selected.extend(_condition_items(db, profile))
        elif category == PatientContextCategory.medications:
            selected.extend(_medication_items(db, profile))
        elif category == PatientContextCategory.clinical_events:
            selected.extend(_clinical_event_items(db, profile))
        elif category == PatientContextCategory.recovery_plan:
            selected.extend(_recovery_items(db, profile))
    return PatientContextBundle(
        items=[item for item in selected if _allowed_for_provider(item, settings)][
            :MAX_CONTEXT_ITEMS
        ]
    )
