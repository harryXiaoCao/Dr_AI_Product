from datetime import date

import pytest

from app.chatbot_contracts import (
    AuthorityTier,
    EvidencePassage,
    ModelAnswerSection,
    PatientContextBundle,
    PatientContextCategory,
    PatientContextItem,
    PatientContextProvenance,
    SourceCitation,
    SourceStatus,
    StructuredModelOutput,
)
from app.claim_support import ClaimSupportFailure, validate_claim_support

PASSAGE_ID = "KBPASS-CLAIM-SUPPORT"


def _evidence(
    text: str = "规律测量血压并记录结果，有助于医生评估高血压管理情况。",
) -> list[EvidencePassage]:
    citation = SourceCitation(
        source_id="KBS-CLAIM-SUPPORT",
        version_id="KBSV-CLAIM-SUPPORT",
        passage_ids=[PASSAGE_ID],
        title="合成患者教育资料",
        publisher="Dr. AI test fixture",
        official_locator="https://example.invalid/claim-support",
        jurisdiction="CN",
        original_language="zh-Hans",
        publication_date=date(2026, 7, 1),
        last_medical_review_date=date(2026, 7, 1),
        authority_tier=AuthorityTier.a,
        status=SourceStatus.current,
        patient_use_approved=True,
    )
    return [
        EvidencePassage(
            passage_id=PASSAGE_ID,
            source_id=citation.source_id,
            version_id=citation.version_id,
            text=text,
            language="zh-Hans",
            citation=citation,
        )
    ]


def _output(
    text: str,
    *,
    supporting_context_ids: list[str] | None = None,
    uncertainties: list[str] | None = None,
    patient_context_attribution: str | None = None,
) -> StructuredModelOutput:
    context_ids = supporting_context_ids or []
    return StructuredModelOutput(
        answer_language="zh-Hans",
        answer_sections=[
            ModelAnswerSection(
                text=text,
                supporting_passage_ids=[PASSAGE_ID],
                supporting_context_ids=context_ids,
            )
        ],
        uses_patient_context=bool(context_ids),
        patient_context_attribution=(
            patient_context_attribution
            if context_ids
            else None
        ),
        used_patient_context_ids=context_ids,
        uncertainties=uncertainties or [],
    )


@pytest.mark.parametrize(
    "answer",
    [
        "规律测量血压并记录结果，有助于医生评估高血压管理情况。",
        "持续记录血压结果能帮助医生评估管理情况。",
    ],
)
def test_supported_claims_pass(answer: str) -> None:
    assert (
        validate_claim_support(
            _output(answer),
            _evidence(),
            PatientContextBundle(),
            original_message="我的血压高，怎样记录？",
        )
        is None
    )


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        (
            "血压达到180/110 mmHg时应采取这种做法。",
            ClaimSupportFailure.unsupported_numeric,
        ),
        ("这说明你得了肺炎。", ClaimSupportFailure.unsupported_condition),
        ("同时出现咳嗽也很常见。", ClaimSupportFailure.unsupported_presentation),
        (
            "保持充足睡眠可以改善整体健康。",
            ClaimSupportFailure.insufficient_semantic_overlap,
        ),
    ],
)
def test_unsupported_claims_fail_closed(
    answer: str, expected: ClaimSupportFailure
) -> None:
    assert (
        validate_claim_support(
            _output(answer),
            _evidence(),
            PatientContextBundle(),
            original_message="我的血压高，怎样记录？",
        )
        == expected
    )


def test_cited_patient_context_can_support_its_own_measurement() -> None:
    context = PatientContextItem(
        context_id="CTX-BP-1",
        category=PatientContextCategory.measurements,
        field_name="blood_pressure",
        value="138/86 mmHg",
        provenance=PatientContextProvenance.doctor_record,
        attribution_phrase="已授权的诊疗记录显示血压为",
        recorded_on=date(2026, 7, 20),
        resource_id="OBS-BP-1",
    )
    answer = "已授权的诊疗记录显示血压为138/86 mmHg。"

    assert (
        validate_claim_support(
            _output(
                answer,
                supporting_context_ids=[context.context_id],
                patient_context_attribution=context.attribution_phrase,
            ),
            _evidence(),
            PatientContextBundle(items=[context]),
            original_message="我的血压记录怎么样？",
        )
        is None
    )


def test_patient_context_rejects_false_provenance_attribution() -> None:
    context = PatientContextItem(
        context_id="CTX-BP-2",
        category=PatientContextCategory.measurements,
        field_name="blood_pressure",
        value="138/86 mmHg",
        provenance=PatientContextProvenance.doctor_record,
        attribution_phrase="已授权的诊疗记录显示血压为",
        recorded_on=date(2026, 7, 20),
        resource_id="OBS-BP-2",
    )
    output = _output(
        "你自述的血压为138/86 mmHg。",
        supporting_context_ids=[context.context_id],
        patient_context_attribution=context.attribution_phrase,
    )

    assert (
        validate_claim_support(
            output,
            _evidence(),
            PatientContextBundle(items=[context]),
            original_message="我的血压记录怎么样？",
        )
        == ClaimSupportFailure.unsupported_context_attribution
    )


def test_uncertainty_cannot_introduce_an_unmentioned_unsupported_condition() -> None:
    output = _output(
        "持续记录血压结果能帮助医生评估管理情况。",
        uncertainties=["现有信息不能排除肺炎。"],
    )

    assert (
        validate_claim_support(
            output,
            _evidence(),
            PatientContextBundle(),
            original_message="我的血压高，怎样记录？",
        )
        == ClaimSupportFailure.unsupported_condition
    )
