from __future__ import annotations

import re
from enum import StrEnum

from app.chatbot_contracts import (
    EvidencePassage,
    PatientContextBundle,
    PatientContextProvenance,
    StructuredModelOutput,
)
from app.clinical_presentation import ClinicalPresentation, extract_clinical_presentation
from app.knowledge_retrieval import normalize_medical_text, relevance_tokens
from app.retrieval_rescue import mentioned_conditions


class ClaimSupportFailure(StrEnum):
    unsupported_numeric = "unsupported_numeric"
    unsupported_condition = "unsupported_condition"
    unsupported_presentation = "unsupported_presentation"
    unsupported_context_attribution = "unsupported_context_attribution"
    insufficient_semantic_overlap = "insufficient_semantic_overlap"


NUMERIC_EXPRESSION = re.compile(
    r"\d+(?:\.\d+)?\s*(?:/\s*\d+(?:\.\d+)?)?\s*"
    r"(?:℃|°c|度|mmhg|毫米汞柱|mmol\s*/?\s*l|mg/dl|分钟|小时|天|周|个月|年|"
    r"次|片|毫克|克|ml|毫升|%|percent)?",
    re.IGNORECASE,
)
SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？!?；;])\s*|\n+")
MIN_SUPPORT_COVERAGE = 0.12

CORE_PRESENTATION_SUPPORT_FIELDS = (
    "symptoms",
    "anatomy",
    "population",
    "pregnancy",
    "exposures",
    "trauma",
)
MODIFIER_PRESENTATION_SUPPORT_FIELDS = ("onset", "trajectory", "severity")
PROVENANCE_ALIASES = {
    PatientContextProvenance.patient_profile: (
        "个人资料",
        "患者资料",
        "patient profile",
    ),
    PatientContextProvenance.patient_reported: (
        "你说",
        "你报告",
        "你自述",
        "患者自述",
        "you reported",
        "patient reported",
    ),
    PatientContextProvenance.doctor_record: (
        "医生记录",
        "诊疗记录",
        "病历记录",
        "doctor record",
        "medical record",
    ),
    PatientContextProvenance.current_prescription: (
        "当前处方",
        "处方显示",
        "current prescription",
    ),
    PatientContextProvenance.medication_schedule: (
        "用药计划",
        "服药计划",
        "medication schedule",
    ),
    PatientContextProvenance.recovery_plan: (
        "康复计划",
        "recovery plan",
    ),
}


def _sentences(value: str) -> list[str]:
    return [sentence.strip() for sentence in SENTENCE_BOUNDARY.split(value) if sentence.strip()]


def _presentation_codes(presentation: ClinicalPresentation) -> set[str]:
    codes = {
        f"{field}:{code}"
        for field in CORE_PRESENTATION_SUPPORT_FIELDS
        for code in getattr(presentation, field)
    }
    has_clinical_anchor = bool(
        presentation.symptoms
        or presentation.anatomy
        or presentation.associated_signs
        or presentation.measurements
        or presentation.pregnancy
        or presentation.exposures
        or presentation.trauma
    )
    if has_clinical_anchor:
        codes.update(
            f"{field}:{code}"
            for field in MODIFIER_PRESENTATION_SUPPORT_FIELDS
            for code in getattr(presentation, field)
        )
    return codes


def _numeric_expressions(value: str) -> set[str]:
    expressions: set[str] = set()
    for match in NUMERIC_EXPRESSION.finditer(value):
        normalized = normalize_medical_text(match.group(0)).replace(" ", "")
        normalized = normalized.replace("毫米汞柱", "mmhg")
        normalized = normalized.replace("℃", "c").replace("°c", "c")
        normalized = normalized.replace("毫克", "mg").replace("毫升", "ml")
        if normalized:
            expressions.add(normalized)
    return expressions


def _claimed_provenance(value: str) -> set[PatientContextProvenance]:
    normalized = normalize_medical_text(value)
    return {
        provenance
        for provenance, aliases in PROVENANCE_ALIASES.items()
        if any(normalize_medical_text(alias) in normalized for alias in aliases)
    }


def _has_meaningful_overlap(claim: str, support: str) -> bool:
    claim_tokens = set(relevance_tokens(claim))
    support_tokens = set(relevance_tokens(support))
    if not claim_tokens:
        return False
    overlap = claim_tokens & support_tokens
    minimum_count = 1 if len(claim_tokens) <= 4 else 2
    return len(overlap) >= minimum_count and (
        len(overlap) / len(claim_tokens) >= MIN_SUPPORT_COVERAGE
    )


def validate_claim_support(
    output: StructuredModelOutput,
    evidence: list[EvidencePassage],
    patient_context: PatientContextBundle,
    *,
    original_message: str,
) -> ClaimSupportFailure | None:
    evidence_by_id = {item.passage_id: item.text for item in evidence}
    context_by_id = {
        item.context_id: " ".join(
            [
                item.attribution_phrase,
                item.value,
                item.recorded_on.isoformat(),
            ]
        )
        for item in patient_context.items
    }
    context_items_by_id = {item.context_id: item for item in patient_context.items}
    used_context_items = [
        context_items_by_id[context_id]
        for context_id in output.used_patient_context_ids
        if context_id in context_items_by_id
    ]
    if used_context_items and output.patient_context_attribution not in {
        item.attribution_phrase for item in used_context_items
    }:
        return ClaimSupportFailure.unsupported_context_attribution
    original_presentation = extract_clinical_presentation(original_message)
    original_codes = _presentation_codes(original_presentation)
    original_numbers = _numeric_expressions(original_message)
    original_conditions = mentioned_conditions(original_message)

    for section in output.answer_sections:
        support_parts = [
            evidence_by_id[passage_id]
            for passage_id in section.supporting_passage_ids
            if passage_id in evidence_by_id
        ]
        support_parts.extend(
            context_by_id[context_id]
            for context_id in section.supporting_context_ids
            if context_id in context_by_id
        )
        support = " ".join(support_parts)
        support_codes = _presentation_codes(extract_clinical_presentation(support))
        support_conditions = mentioned_conditions(support)
        support_numbers = _numeric_expressions(support)
        allowed_provenance = {
            context_items_by_id[context_id].provenance
            for context_id in section.supporting_context_ids
            if context_id in context_items_by_id
        }

        for sentence in _sentences(section.text):
            if not _claimed_provenance(sentence) <= allowed_provenance:
                return ClaimSupportFailure.unsupported_context_attribution
            sentence_numbers = _numeric_expressions(sentence)
            if not sentence_numbers <= support_numbers | original_numbers:
                return ClaimSupportFailure.unsupported_numeric
            if not mentioned_conditions(sentence) <= support_conditions:
                return ClaimSupportFailure.unsupported_condition
            sentence_codes = _presentation_codes(extract_clinical_presentation(sentence))
            if not sentence_codes <= support_codes | original_codes:
                return ClaimSupportFailure.unsupported_presentation
            if not _has_meaningful_overlap(sentence, support):
                return ClaimSupportFailure.insufficient_semantic_overlap

    global_support = " ".join([*evidence_by_id.values(), *context_by_id.values()])
    global_codes = _presentation_codes(extract_clinical_presentation(global_support))
    global_conditions = mentioned_conditions(global_support)
    global_numbers = _numeric_expressions(global_support)
    for uncertainty in output.uncertainties:
        if not _numeric_expressions(uncertainty) <= global_numbers | original_numbers:
            return ClaimSupportFailure.unsupported_numeric
        if not mentioned_conditions(uncertainty) <= global_conditions | original_conditions:
            return ClaimSupportFailure.unsupported_condition
        if not _presentation_codes(
            extract_clinical_presentation(uncertainty)
        ) <= global_codes | original_codes:
            return ClaimSupportFailure.unsupported_presentation
    return None
