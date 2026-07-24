import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_chat import (
    DeepSeekChatAdapter,
    DeepSeekChatError,
    DeepSeekGeneralResult,
    DeepSeekQueryPlanResult,
    DeepSeekStructuredResult,
)
from app.chatbot_contracts import (
    EvidenceDecision,
    GeneralModelOutput,
    ModelAnswerSection,
    PatientChatRequest,
    PatientEvidenceRequest,
    RetrievalQueryPlan,
    SafetyCode,
    StructuredModelOutput,
)
from app.clinical_presentation import extract_clinical_presentation
from app.config import Settings
from app.database import engine
from app.errors import ApiError
from app.knowledge_retrieval import RetrievalResult
from app.models import (
    ChatbotEvent,
    ChatMessage,
    ChatThread,
    KbRightsRecord,
    PatientProfile,
    User,
)
from app.patient_chat import (
    PatientChatIntent,
    _classify_intent,
    _general_knowledge_response,
    _safety_route,
    send_patient_chat_message,
)
from app.patient_context import select_patient_context
from app.retrieval_rescue import (
    RescueOutcome,
    RescueTrigger,
    _fuse,
    _fuse_many,
    attempt_retrieval_rescue,
    choose_trigger,
    validate_rewrite,
)
from app.seed import seed_database
from tests.helpers import auth_header, login
from tests.test_phase3_knowledge_retrieval import _activate_retrieval_corpus

CANONICAL_CONTRACT = (
    Path(__file__).resolve().parents[1]
    / "knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json"
)


class FakeGroundedAdapter:
    def __init__(
        self,
        *,
        passage_id: str | None = None,
        use_context: bool = False,
        first_section_text: str = "规律记录血压有助于医生了解血压管理情况。",
        next_action_code: str | None = None,
    ) -> None:
        self.passage_id = passage_id
        self.use_context = use_context
        self.first_section_text = first_section_text
        self.next_action_code = next_action_code
        self.calls = 0
        self.patient_context = None
        self.conversations = []
        self.urgency_routes = []

    def complete_grounded(
        self,
        *,
        message,
        language,
        response_mode,
        urgency_route,
        evidence,
        patient_context,
        conversation,
        settings,
    ):
        del message, settings
        self.calls += 1
        self.patient_context = patient_context
        self.conversations.append(conversation)
        self.urgency_routes.append(urgency_route)
        passage_id = self.passage_id or next(
            (item.passage_id for item in evidence if "记录" in item.text and "血压" in item.text),
            evidence[0].passage_id,
        )
        context_ids = (
            [patient_context.items[0].context_id]
            if self.use_context and patient_context.items
            else []
        )
        return DeepSeekStructuredResult(
            output=StructuredModelOutput(
                answer_language=language,
                answer_sections=[
                    ModelAnswerSection(
                        text=self.first_section_text,
                        supporting_passage_ids=[passage_id],
                        supporting_context_ids=context_ids,
                    ),
                    ModelAnswerSection(
                        text="连续记录能让医生看到不同时间的变化，而不只是某一次的读数。",
                        supporting_passage_ids=[passage_id],
                    ),
                    ModelAnswerSection(
                        text="可以把测量时间和结果一起记录，复诊时带给医生查看。",
                        supporting_passage_ids=[passage_id],
                    ),
                ],
                uses_patient_context=bool(context_ids),
                patient_context_attribution=(
                    patient_context.items[0].attribution_phrase if context_ids else None
                ),
                used_patient_context_ids=context_ids,
                uncertainties=(
                    ["现有症状和资料不足以确认诊断。"]
                    if response_mode == "permitted_symptom_guidance"
                    else []
                ),
                next_action_code=(
                    self.next_action_code
                    or (
                        "seek_local_care"
                        if urgency_route == "urgent_same_day"
                        else "contact_connected_doctor"
                    )
                ),
            ),
            model="deepseek-v4-flash",
            input_tokens=120,
            output_tokens=40,
        )


class FakeGeneralAdapter:
    def __init__(self) -> None:
        self.calls = 0
        self.payloads: list[dict[str, object]] = []

    def complete_general_knowledge(self, **kwargs):
        self.calls += 1
        self.payloads.append(kwargs)
        decline = kwargs["decline_prohibited_portion"]
        return DeepSeekGeneralResult(
            output=GeneralModelOutput(
                answer_language=kwargs["language"],
                answer_sections=[
                    (
                        "头晕可能与脱水、睡眠不足、血压变化或其他原因有关，"
                        "仅凭这句话不能判断个人原因。"
                        if kwargs["language"] == "zh-Hans"
                        else "Dizziness can have several explanations; this cannot identify "
                        "the cause for one person."
                    )
                ],
                uncertainties=(
                    ["仅凭现有信息不能确认原因。"]
                    if kwargs["response_mode"] != "permitted_education"
                    else []
                ),
                next_action_code="contact_connected_doctor",
                declined_portion=(
                    "我不能告诉你停药或改变剂量；请向开药医生确认。" if decline else None
                ),
            ),
            model="test-general-model",
            input_tokens=40,
            output_tokens=30,
        )


@pytest.mark.parametrize(
    "message",
    [
        "熬夜后心脏像跳空了一下，这是怎么回事？",
        "最近总感觉心脏漏跳一拍，正常吗？",
        "有时心慌、怦怦跳，是什么原因？",
        "I sometimes feel a skipped beat. What could affect that feeling?",
    ],
)
def test_colloquial_symptom_paraphrases_route_to_symptom_guidance(message: str) -> None:
    assert _safety_route(message).value == "permitted_symptom_guidance"
    assert _classify_intent(message) == PatientChatIntent.symptom_guidance


def test_query_planner_is_one_bounded_schema_call(settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "deepseek_api_key", SecretStr("test-key-not-sent"))
    calls = 0

    def fake_request(self, request_body, request_settings):
        nonlocal calls
        del self
        calls += 1
        assert request_settings.deepseek_timeout_seconds <= 2.5
        assert request_body["max_tokens"] == 240
        assert request_body["temperature"] == 0.0
        planner_payload = json.loads(request_body["messages"][1]["content"])
        assert planner_payload["recent_user_messages"] == ["高血压为什么需要定期测量血压？"]
        return {
            "model": "deepseek-v4-flash",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "normalized_intent": "高血压血压测量教育",
                                "concepts": ["高血压", "血压测量"],
                                "synonyms": ["血压监测"],
                                "language": "zh-Hans",
                                "jurisdiction": "CN",
                                "excluded_content_classes": ["raw_clinical_record"],
                                "candidate_queries": ["高血压为什么需要定期测量血压？"],
                                "clarification_needed": False,
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 90,
                "completion_tokens": 30,
                "prompt_tokens_details": {"cached_tokens": 12},
                "prompt_cache_miss_tokens": 78,
            },
        }

    monkeypatch.setattr(DeepSeekChatAdapter, "_request", fake_request)
    result = DeepSeekChatAdapter().plan_retrieval_query(
        message="这个呢？",
        language="zh-Hans",
        excluded_content_classes=["raw_clinical_record"],
        recent_user_messages=[
            "更早的孕期问题。",
            "更早的伤口问题。",
            "高血压为什么需要定期测量血压？",
        ],
        settings=settings,
    )

    assert calls == 1
    assert result.output.candidate_queries == ["高血压为什么需要定期测量血压？"]
    assert result.cache_hit_tokens == 12


def test_query_planner_malformed_output_has_no_repair_call(settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "deepseek_api_key", SecretStr("test-key-not-sent"))
    calls = 0

    def fake_request(self, request_body, request_settings):
        nonlocal calls
        del self, request_body, request_settings
        calls += 1
        return {"choices": [{"message": {"content": "not-json"}}]}

    monkeypatch.setattr(DeepSeekChatAdapter, "_request", fake_request)
    with pytest.raises(DeepSeekChatError) as exc_info:
        DeepSeekChatAdapter().plan_retrieval_query(
            message="这个呢？",
            language="zh-Hans",
            excluded_content_classes=["raw_clinical_record"],
            recent_user_messages=["高血压为什么需要定期测量血压？"],
            settings=settings,
        )

    assert calls == 1
    assert exc_info.value.diagnostic_code == "planner_malformed_output"


def _query_plan(candidate: str) -> RetrievalQueryPlan:
    return RetrievalQueryPlan(
        normalized_intent="症状教育检索",
        concepts=["症状"],
        synonyms=[],
        language="zh-Hans",
        jurisdiction="CN",
        excluded_content_classes=["raw_clinical_record"],
        candidate_queries=[candidate],
        clarification_needed=False,
    )


def test_query_planner_accepts_alias_normalization_without_changing_presentation() -> None:
    assert (
        validate_rewrite(
            _query_plan("心悸或心跳不规律的症状可能类别"),
            original_message="心脏像跳空了一下，怎么回事？",
            recent_user_messages=[],
            language="zh-Hans",
        )
        == "心悸或心跳不规律的症状可能类别"
    )
    assert (
        validate_rewrite(
            _query_plan("高血压日常测量与记录"),
            original_message="血压高平时怎么量和记录？",
            recent_user_messages=[],
            language="zh-Hans",
        )
        == "高血压日常测量与记录"
    )


@pytest.mark.parametrize(
    ("original", "candidate"),
    [
        ("咳嗽三周，有黄痰。", "咳嗽三周、有黄痰和胸痛。"),
        ("伤口流脓，但没有发烧。", "伤口感染并伴有发烧。"),
        ("最近头晕。", "突然严重头晕，血压180/110毫米汞柱。"),
        ("最近一直咳嗽。", "咳嗽可能是肺炎。"),
        ("喷农药后手臂发痒。", "喷农药后手臂发痒，可能是农药中毒。"),
        ("咳嗽三周，有黄痰。", "咳嗽，有黄痰。"),
    ],
)
def test_query_planner_rejects_invented_presentation_or_condition(
    original: str, candidate: str
) -> None:
    assert (
        validate_rewrite(
            _query_plan(candidate),
            original_message=original,
            recent_user_messages=[],
            language="zh-Hans",
        )
        is None
    )


def test_query_planner_cannot_reintroduce_unadmitted_history() -> None:
    trusted_message = "最近头晕。"
    trusted_presentation = extract_clinical_presentation(trusted_message)

    assert (
        validate_rewrite(
            _query_plan("怀孕八个月时最近头晕"),
            original_message=trusted_message,
            recent_user_messages=["我怀孕八个月。"],
            language="zh-Hans",
            trusted_presentation=trusted_presentation,
            trusted_context_message=trusted_message,
        )
        is None
    )


@pytest.mark.parametrize(
    ("elapsed_seconds", "max_cost", "expected_outcome"),
    [
        (2.501, 1000, RescueOutcome.latency_exceeded),
        (0.100, 1, RescueOutcome.cost_exceeded),
    ],
)
def test_retrieval_rescue_separates_latency_and_cost_outcomes(
    settings, monkeypatch, elapsed_seconds, max_cost, expected_outcome
) -> None:
    monkeypatch.setattr(settings, "retrieval_rescue_max_cost_microunits", max_cost)
    ticks = iter((0.0, elapsed_seconds))
    monkeypatch.setattr("app.retrieval_rescue.time.perf_counter", lambda: next(ticks))

    class FakePlanner:
        def plan_retrieval_query(self, **kwargs):
            return DeepSeekQueryPlanResult(
                output=RetrievalQueryPlan(
                    normalized_intent="测量教育检索",
                    concepts=["测量"],
                    synonyms=[],
                    language="zh-Hans",
                    excluded_content_classes=kwargs["excluded_content_classes"],
                    candidate_queries=["怎样正确测量？"],
                ),
                model="deepseek-v4-flash",
                input_tokens=50,
                output_tokens=20,
                cache_hit_tokens=None,
                cache_miss_tokens=50,
            )

    result = attempt_retrieval_rescue(
        None,
        original_message="怎样才算测得对？",
        language="zh-Hans",
        request=PatientEvidenceRequest(query="怎样才算测得对？", language="zh-Hans"),
        initial=_rescue_retrieval(decision=EvidenceDecision.no_eligible_evidence),
        recent_user_messages=[],
        trusted_presentation=extract_clinical_presentation("怎样才算测得对？"),
        trusted_context_message="怎样才算测得对？",
        settings=settings,
        adapter=FakePlanner(),
    )

    assert result.metadata.outcome == expected_outcome


def _rescue_candidate(
    checksum: str,
    source_id: str,
    *,
    coverage: float,
    score: float,
):
    return SimpleNamespace(
        passage=SimpleNamespace(
            content_checksum=checksum,
            stable_id=f"passage-{checksum}",
            conflict_group_key=None,
        ),
        source=SimpleNamespace(stable_id=source_id),
        topic_coverage_score=coverage,
        rerank_score=score,
    )


def _rescue_retrieval(*candidates, decision=EvidenceDecision.sufficient):
    return RetrievalResult(
        request_id="request-test",
        release=SimpleNamespace(id=1),
        original_query="test",
        expanded_terms=[],
        candidates=list(candidates) if decision == EvidenceDecision.sufficient else [],
        ranked_candidates=list(candidates),
        decision=decision,
    )


def test_rescue_ambiguity_requires_missing_standalone_clinical_topic(settings) -> None:
    strong = _rescue_retrieval(
        _rescue_candidate("blood-streaked-sputum", "source-respiratory", coverage=0.60, score=0.80)
    )

    assert choose_trigger("痰里有血丝，要紧吗？", strong, settings) is None
    assert (
        choose_trigger(
            "怎样才算测得对？",
            _rescue_retrieval(decision=EvidenceDecision.no_eligible_evidence),
            settings,
        )
        == RescueTrigger.ambiguous
    )
    assert (
        choose_trigger(
            "请问糖尿病怎么办，一般谁会得糖尿病",
            strong,
            settings,
        )
        is None
    )


def test_drifted_rescue_preserves_sufficient_diabetes_evidence(settings) -> None:
    initial = _rescue_retrieval(
        _rescue_candidate(
            "diabetes-overview",
            "source-diabetes",
            coverage=1.0,
            score=-0.09,
        )
    )

    class DriftedPlanner:
        def plan_retrieval_query(self, **kwargs):
            return DeepSeekQueryPlanResult(
                output=RetrievalQueryPlan(
                    normalized_intent="糖尿病教育检索",
                    concepts=["糖尿病"],
                    synonyms=[],
                    language="zh-Hans",
                    excluded_content_classes=kwargs["excluded_content_classes"],
                    candidate_queries=["请停止降糖药并改变剂量"],
                ),
                model="deepseek-v4-flash",
                input_tokens=50,
                output_tokens=20,
                cache_hit_tokens=None,
                cache_miss_tokens=50,
            )

    result = attempt_retrieval_rescue(
        None,
        original_message="请问糖尿病怎么办，一般谁会得糖尿病",
        language="zh-Hans",
        request=PatientEvidenceRequest(
            query="请问糖尿病怎么办，一般谁会得糖尿病",
            language="zh-Hans",
        ),
        initial=initial,
        recent_user_messages=[],
        trusted_presentation=extract_clinical_presentation("请问糖尿病怎么办，一般谁会得糖尿病"),
        trusted_context_message="请问糖尿病怎么办，一般谁会得糖尿病",
        settings=settings,
        adapter=DriftedPlanner(),
    )

    assert result.metadata.trigger == RescueTrigger.weak_initial_retrieval
    assert result.metadata.outcome == RescueOutcome.meaning_drift
    assert result.retrieval is initial
    assert result.retrieval.decision == EvidenceDecision.sufficient


def test_rescue_fusion_excludes_uncorroborated_original_only_candidates() -> None:
    unrelated = _rescue_candidate("unrelated", "source-hiv", coverage=0.90, score=0.99)
    corroborated_initial = _rescue_candidate(
        "blood-pressure", "source-bp", coverage=0.10, score=0.20
    )
    resolved = _rescue_candidate("blood-pressure", "source-bp", coverage=0.60, score=0.80)

    fused = _fuse(
        _rescue_retrieval(unrelated, corroborated_initial),
        _rescue_retrieval(resolved),
        6,
    )

    assert [item.passage.content_checksum for item in fused.candidates] == ["blood-pressure"]
    assert fused.candidates[0] is resolved


def test_self_contained_rescue_rrf_keeps_original_and_planned_candidates() -> None:
    original_only = _rescue_candidate(
        "original-only",
        "source-original",
        coverage=0.62,
        score=0.82,
    )
    planned_only = _rescue_candidate(
        "planned-only",
        "source-planned",
        coverage=0.64,
        score=0.84,
    )

    fused = _fuse_many(
        _rescue_retrieval(original_only),
        [_rescue_retrieval(planned_only)],
        6,
        context_authoritative=False,
    )

    assert fused.decision == EvidenceDecision.sufficient
    assert {item.passage.content_checksum for item in fused.candidates} == {
        "original-only",
        "planned-only",
    }


def test_reference_rescue_does_not_claim_improvement_without_resolved_evidence(
    settings, monkeypatch
) -> None:
    unrelated = _rescue_candidate("unrelated", "source-hiv", coverage=0.90, score=0.99)
    initial = _rescue_retrieval(unrelated)
    retry = _rescue_retrieval(
        _rescue_candidate("weak", "source-generic", coverage=0.02, score=0.95),
        decision=EvidenceDecision.no_eligible_evidence,
    )
    monkeypatch.setattr("app.retrieval_rescue.retrieve", lambda *args, **kwargs: retry)
    trusted_message = "高血压为什么需要定期测量血压？\nFollow-up: 这个呢？"

    result = attempt_retrieval_rescue(
        None,
        original_message="这个呢？",
        language="zh-Hans",
        request=PatientEvidenceRequest(query="这个呢？", language="zh-Hans"),
        initial=initial,
        recent_user_messages=["高血压为什么需要定期测量血压？"],
        trusted_presentation=extract_clinical_presentation(trusted_message),
        trusted_context_message=trusted_message,
        settings=settings,
        adapter=SimpleNamespace(),
    )

    assert result.metadata.outcome == RescueOutcome.no_improvement
    assert result.retrieval.decision == EvidenceDecision.no_eligible_evidence
    assert result.retrieval.candidates == []


def test_context_rescue_marks_retry_evidence_as_dominant(settings, monkeypatch) -> None:
    initial = _rescue_retrieval(
        _rescue_candidate("unrelated", "source-unrelated", coverage=0.90, score=0.99)
    )
    resolved = _rescue_retrieval(
        _rescue_candidate("blood-pressure", "source-bp", coverage=0.60, score=0.80)
    )

    def resolved_retrieve(*args, **kwargs):
        del args
        assert kwargs["reranker_candidate_limit"] == 1
        presentation = kwargs["presentation"]
        assert presentation.literal_query == "咳嗽三周，有黄痰。 这个呢？"
        assert set(presentation.symptoms) >= {"cough", "sputum"}
        assert "三周" in presentation.duration
        return resolved

    monkeypatch.setattr("app.retrieval_rescue.retrieve", resolved_retrieve)

    trusted_message = "咳嗽三周，有黄痰。\nFollow-up: 这个呢？"
    result = attempt_retrieval_rescue(
        None,
        original_message="这个呢？",
        language="zh-Hans",
        request=PatientEvidenceRequest(query="这个呢？", language="zh-Hans"),
        initial=initial,
        recent_user_messages=["咳嗽三周，有黄痰。"],
        trusted_presentation=extract_clinical_presentation(trusted_message),
        trusted_context_message=trusted_message,
        settings=settings,
        adapter=SimpleNamespace(),
    )

    assert result.metadata.outcome == RescueOutcome.improved
    assert result.metadata.context_dominant is True
    assert result.metadata.resolved_topic_evidence_only is True
    assert {item.source.stable_id for item in result.retrieval.candidates} == {"source-bp"}


def _patient_headers(client: TestClient, settings) -> dict[str, str]:
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    return auth_header(patient["access_token"])


def _post(client: TestClient, settings, message: str):
    return client.post(
        "/api/v1/patient/chat/messages",
        headers=_patient_headers(client, settings),
        json={"message": message, "language": "zh-Hans", "session_id": "session-test-001"},
    )


def test_emergency_routes_before_retrieval_or_model(
    client: TestClient, settings, monkeypatch
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    monkeypatch.setattr(
        "app.patient_chat.retrieve",
        lambda *args, **kwargs: pytest.fail("retrieval ran before emergency handling"),
    )

    response = _post(client, settings, "我胸痛而且无法呼吸")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "emergency"
    assert response.json()["next_action_code"] == "call_120"
    assert response.json()["urgency_route"] == "emergency_120"
    assert response.json()["emergency"] is True
    assert "120" in response.json()["answer_sections"][0]
    assert response.json()["sources"] == []
    assert adapter.calls == 0


@pytest.mark.parametrize(
    ("message", "expected_guidance"),
    [
        ("我刚才药吃多了，怎么办？", "不要催吐"),
        ("我有自残的想法，怕自己会做。", "立即拨打120"),
        ("I took too many pills.", "Do not induce vomiting"),
        ("I have thoughts of self-harm.", "Call 120 now"),
    ],
)
def test_controlled_crisis_signals_route_before_retrieval_or_model(
    client: TestClient,
    settings,
    monkeypatch,
    message: str,
    expected_guidance: str,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    monkeypatch.setattr(
        "app.patient_chat.retrieve",
        lambda *args, **kwargs: pytest.fail("retrieval ran before crisis handling"),
    )

    language = "en" if message.startswith("I ") else "zh-Hans"
    response = client.post(
        "/api/v1/patient/chat/messages",
        headers=_patient_headers(client, settings),
        json={"message": message, "language": language, "session_id": "crisis-test"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["safety_code"] == "emergency"
    assert payload["fallback_code"] == "emergency"
    assert payload["urgency_route"] == "emergency_120"
    assert payload["next_action_code"] == "call_120"
    assert expected_guidance in payload["answer_sections"][0]
    assert payload["sources"] == []
    assert adapter.calls == 0


@pytest.mark.parametrize(
    "message",
    [
        "老人突然嘴歪、一侧手脚无力、说话不清",
        "人倒地叫不醒，而且没有正常呼吸",
        "孩子吃花生后不能说话、不能咳嗽、脸色发紫",
        "烧煤后全家都头痛犯困",
        "高压电击后人清醒了，身上只有一个小伤口",
    ],
)
def test_critical_variants_make_zero_retrieval_or_model_calls(
    client: TestClient, settings, monkeypatch, message: str
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    monkeypatch.setattr(
        "app.patient_chat.retrieve",
        lambda *args, **kwargs: pytest.fail("retrieval ran before emergency handling"),
    )

    response = _post(client, settings, message)

    assert response.status_code == 200
    assert response.json()["safety_code"] == "emergency"
    assert response.json()["fallback_code"] == "emergency"
    assert response.json()["next_action_code"] == "call_120"
    assert response.json()["urgency_route"] == "emergency_120"
    assert adapter.calls == 0


def test_entire_candidate_premodel_set_makes_zero_retrieval_or_model_calls(
    settings, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "chatbot_general_model_knowledge_enabled", False)
    contract = json.loads(CANONICAL_CONTRACT.read_text(encoding="utf-8"))
    inputs: list[tuple[str, str, tuple[str, ...]]] = []
    for case in contract["cases"]:
        route = case["expected_urgency_route"]
        if route not in {"emergency_120", "prohibited_medication_change"}:
            continue
        inputs.append((case["case_id"], route, (case["canonical_question"],)))
        for variant in case["variants"]:
            assert variant["expected_route"] == route
            turns = tuple(variant["turns"] or [variant["text"]])
            inputs.append((variant["variant_id"], route, turns))

    assert len(inputs) == 93
    final_turns = {turns[-1] for _, _, turns in inputs}
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    def unavailable_unless_premodel(db, request, *, audience, presentation):
        del db, audience, presentation
        if request.query in final_turns:
            pytest.fail("retrieval ran before pre-model handling")
        raise ApiError(503, "retrieval_unavailable", "test-only unavailable release")

    monkeypatch.setattr(
        "app.patient_chat.retrieve",
        unavailable_unless_premodel,
    )
    with Session(engine) as db:
        seed_database(db, settings)
        user = db.scalar(select(User).where(User.email == "patient.demo@example.com"))
        assert user is not None
        for index, (case_id, route, turns) in enumerate(inputs):
            response = None
            for turn_index, message in enumerate(turns):
                response = send_patient_chat_message(
                    PatientChatRequest(
                        message=message,
                        language="zh-Hans",
                        session_id=f"premodel-{case_id}",
                    ),
                    SimpleNamespace(
                        state=SimpleNamespace(request_id=f"premodel-{index}-{turn_index}")
                    ),
                    user,
                    db,
                    settings,
                )
            assert response is not None
            assert response.urgency_route == route, case_id
            if route == "emergency_120":
                assert response.safety_code.value == "emergency", case_id
                assert response.fallback_code.value == "emergency", case_id
                assert response.next_action_code.value == "call_120", case_id
            else:
                assert response.safety_code.value == "prohibited_medication_change", case_id
                assert response.fallback_code.value == "prohibited_request", case_id
                assert response.next_action_code.value == "contact_connected_doctor", case_id
        db.rollback()

    assert adapter.calls == 0


def test_live_multi_turn_emergency_follow_up_stays_before_retrieval_or_model(
    client: TestClient, settings, monkeypatch
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    monkeypatch.setattr(
        "app.patient_chat.retrieve",
        lambda *args, **kwargs: pytest.fail("retrieval ran during emergency continuity"),
    )

    first = _post(client, settings, "老人刚才一边手脚没力，话也说不清。")
    second = _post(client, settings, "现在好了，还用去吗？")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["urgency_route"] == "emergency_120"
    assert second.json()["urgency_route"] == "emergency_120"
    assert second.json()["next_action_code"] == "call_120"
    assert adapter.calls == 0


def test_live_multi_turn_acute_confusion_stays_before_retrieval_or_model(
    client: TestClient, settings, monkeypatch
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    monkeypatch.setattr(
        "app.patient_chat.retrieve",
        lambda *args, **kwargs: pytest.fail("retrieval ran during acute-confusion continuity"),
    )

    first = _post(client, settings, "老人刚才突然叫错人。")
    second = _post(client, settings, "没有发烧，但还是很糊涂。")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["urgency_route"] == "emergency_120"
    assert second.json()["urgency_route"] == "emergency_120"
    assert second.json()["next_action_code"] == "call_120"
    assert adapter.calls == 0


def test_live_multi_turn_presentation_carries_only_needed_user_context(
    client: TestClient, settings, monkeypatch
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()

    first = _post(client, settings, "我怀孕八个月。")
    assert first.status_code == 200
    assert first.json()["grounding_mode"] == "fixed_safety_response"
    assert first.json()["fallback_code"] == "provider_unavailable"

    captured = {}

    def unavailable_with_capture(db, request, *, audience, presentation):
        del db, audience
        captured["query"] = request.query
        captured["presentation"] = presentation
        raise ApiError(503, "retrieval_unavailable", "test-only unavailable release")

    monkeypatch.setattr("app.patient_chat.retrieve", unavailable_with_capture)
    second_message = "今天孩子几乎不动了，怎么办？"
    second = _post(client, settings, second_message)

    assert second.status_code == 200
    assert second.json()["urgency_route"] == "urgent_same_day"
    assert second.json()["next_action_code"] == "seek_local_care"
    assert captured["query"] == second_message
    presentation = captured["presentation"]
    assert presentation.literal_query == second_message
    assert "pregnant" in presentation.pregnancy
    assert "decreased_fetal_movement" in presentation.symptoms


def test_live_exposure_follow_up_routes_emergency_before_retrieval_or_model(
    client: TestClient, settings, monkeypatch
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()

    first = _post(client, settings, "我刚喷完农药。")
    assert first.status_code == 200

    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    monkeypatch.setattr(
        "app.patient_chat.retrieve",
        lambda *args, **kwargs: pytest.fail(
            "retrieval ran after exposure follow-up became an emergency"
        ),
    )
    second = _post(client, settings, "现在头晕、恶心，还直流口水。")

    assert second.status_code == 200
    assert second.json()["urgency_route"] == "emergency_120"
    assert second.json()["next_action_code"] == "call_120"
    assert adapter.calls == 0


def test_missing_patient_release_fails_closed_without_model(
    client: TestClient, settings, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "chatbot_general_model_knowledge_enabled", False)
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "高血压平时应该了解哪些健康知识？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "retrieval_unavailable"
    assert response.json()["sources"] == []
    assert adapter.calls == 0


def test_missing_patient_release_uses_separate_general_knowledge_mode(
    client: TestClient, settings, monkeypatch
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGeneralAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "我最近头晕，可能有哪些原因？")

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounding_mode"] == "general_model_knowledge"
    assert payload["sources"] == []
    assert payload["context_used"] == []
    assert payload["fallback_code"] is None
    assert payload["model_version"] is None
    assert payload["uncertainties"]
    assert adapter.calls == 1
    with Session(engine) as db:
        event = db.scalar(select(ChatbotEvent))
        assert event is not None
        assert event.grounding_mode == "general_model_knowledge"
        assert event.general_knowledge_eligible is True
        assert event.general_knowledge_outcome == "generated"
        assert event.model_version == "test-general-model"
        assert "头晕" not in str(event.__dict__)


def test_general_knowledge_response_preserves_no_evidence_decision(settings, monkeypatch) -> None:
    adapter = FakeGeneralAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response, _ = _general_knowledge_response(
        PatientChatRequest(message="我最近头晕，可能有哪些原因？", language="zh-Hans"),
        request_id="request-general-no-evidence",
        thread_id="thread-general-no-evidence",
        safety_code=SafetyCode.permitted_symptom_guidance,
        urgency_route="routine_education",
        settings=settings,
        evidence_decision=EvidenceDecision.no_eligible_evidence,
    )

    assert response.evidence_decision == EvidenceDecision.no_eligible_evidence


def test_mixed_medication_request_answers_safe_portion_and_declines_change(
    client: TestClient, settings, monkeypatch
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGeneralAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    monkeypatch.setattr(
        "app.patient_chat.retrieve",
        lambda *args, **kwargs: pytest.fail("mixed prohibited request reached retrieval"),
    )

    response = _post(
        client,
        settings,
        "阿司匹林有什么作用和常见副作用？我可以现在停药吗？",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounding_mode"] == "general_model_knowledge"
    assert payload["safety_code"] == "prohibited_medication_change"
    assert payload["next_action_code"] == "contact_connected_doctor"
    assert "停药" in payload["answer_sections"][-1]
    assert payload["sources"] == []
    assert adapter.calls == 1
    assert adapter.payloads[0]["decline_prohibited_portion"] is True


def test_same_day_route_survives_missing_evidence_without_model(
    client: TestClient, settings, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "chatbot_general_model_knowledge_enabled", False)
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "孩子半夜发烧39℃，现在应该怎么处理？")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback_code"] == "retrieval_unavailable"
    assert payload["urgency_route"] == "urgent_same_day"
    assert payload["next_action_code"] == "seek_local_care"
    assert "当天" in payload["answer_sections"][0]
    assert adapter.calls == 0


def test_model_cannot_downgrade_server_issued_same_day_action(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter(next_action_code="contact_connected_doctor")
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "血压180/110毫米汞柱，但现在没有不舒服。")

    assert response.status_code == 200
    payload = response.json()
    assert adapter.urgency_routes == ["urgent_same_day"]
    assert payload["fallback_code"] == "policy_validation_failed"
    assert payload["urgency_route"] == "urgent_same_day"
    assert payload["next_action_code"] == "seek_local_care"
    with Session(engine) as db:
        event = db.scalar(select(ChatbotEvent).order_by(ChatbotEvent.occurred_at.desc()))
        assert event is not None
        assert event.provider_error_code == "policy_urgency_next_action"


def test_grounded_same_day_answer_uses_server_constrained_action(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "血压180/110毫米汞柱，但现在没有不舒服。")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback_code"] is None
    assert payload["urgency_route"] == "urgent_same_day"
    assert payload["next_action_code"] == "seek_local_care"
    assert adapter.urgency_routes == ["urgent_same_day"]


@pytest.mark.parametrize("unsafe_action", ["call_120", "seek_local_care"])
def test_model_cannot_upgrade_routine_route(
    client: TestClient, settings, monkeypatch, tmp_path, unsafe_action: str
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter(next_action_code=unsafe_action)
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "高血压为什么需要定期测量血压？")

    assert response.status_code == 200
    payload = response.json()
    assert adapter.urgency_routes == ["routine_education"]
    assert payload["fallback_code"] == "policy_validation_failed"
    assert payload["urgency_route"] == "routine_education"
    assert payload["next_action_code"] not in {"call_120", "seek_local_care"}


def test_sufficient_evidence_without_provider_key_returns_fixed_fallback(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    monkeypatch.setattr(settings, "deepseek_api_key", None)

    response = _post(client, settings, "血压高时，平时记录血压有什么作用？")

    assert response.status_code == 200
    assert response.json()["evidence_decision"] == "sufficient"
    assert response.json()["fallback_code"] == "provider_unavailable"


def test_ordinary_query_does_not_spend_retrieval_rescue_call(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    grounded = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", grounded)

    def unexpected_planner(**kwargs):
        del kwargs
        raise AssertionError("ordinary retrieval must not call the query planner")

    monkeypatch.setattr(
        "app.patient_chat.deepseek_query_planner_adapter.plan_retrieval_query",
        unexpected_planner,
    )

    response = _post(client, settings, "高血压为什么需要定期测量血压？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] is None
    with Session(engine) as db:
        event = db.scalar(select(ChatbotEvent))
        assert event is not None
        assert event.rescue_attempted is False
        assert event.rescue_trigger is None


def test_short_reference_rescue_rewrites_once_and_improves_retrieval(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    grounded = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", grounded)
    planner_calls = 0

    def unexpected_planner(**kwargs):
        nonlocal planner_calls
        del kwargs
        planner_calls += 1
        raise AssertionError("a resolvable short reference must use bounded thread context")

    monkeypatch.setattr(
        "app.patient_chat.deepseek_query_planner_adapter.plan_retrieval_query",
        unexpected_planner,
    )
    first = _post(client, settings, "高血压为什么需要定期测量血压？")
    second = _post(client, settings, "这个呢？")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["fallback_code"] is None
    assert planner_calls == 0
    with Session(engine) as db:
        events = db.scalars(select(ChatbotEvent).order_by(ChatbotEvent.occurred_at)).all()
        rescue = events[-1]
        assert rescue.rescue_trigger == "short_reference"
        assert rescue.rescue_attempted is True
        assert rescue.rescue_outcome == "improved"
        assert rescue.rescue_input_tokens is None
        assert rescue.rescue_cache_hit_tokens is None
        assert rescue.rescue_cost_microunits == 0
        assert rescue.rescue_retrieval_delta > 0
        assert rescue.rescue_retry_request_id is not None


def test_retrieval_rescue_rejects_meaning_drift_without_retrying_generation(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(settings, "chatbot_general_model_knowledge_enabled", False)
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    grounded = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", grounded)

    def drifted_rewrite(**kwargs):
        return DeepSeekQueryPlanResult(
            output=RetrievalQueryPlan(
                normalized_intent="高血压检索",
                concepts=["高血压"],
                synonyms=[],
                language="zh-Hans",
                excluded_content_classes=kwargs["excluded_content_classes"],
                candidate_queries=["请停止降压药并改变剂量"],
            ),
            model="deepseek-v4-flash",
            input_tokens=50,
            output_tokens=20,
            cache_hit_tokens=None,
            cache_miss_tokens=50,
        )

    monkeypatch.setattr(
        "app.patient_chat.deepseek_query_planner_adapter.plan_retrieval_query",
        drifted_rewrite,
    )
    response = _post(client, settings, "完全陌生的健康说法是什么意思？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "no_eligible_evidence"
    assert grounded.calls == 0
    with Session(engine) as db:
        events = db.scalars(select(ChatbotEvent).order_by(ChatbotEvent.occurred_at)).all()
        assert events[-1].rescue_outcome == "meaning_drift"
        assert events[-1].rescue_retry_request_id is None
    assert response.json()["sources"] == []


def test_longer_short_reference_uses_context_without_planner(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    grounded = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", grounded)

    def unexpected_planner(**kwargs):
        del kwargs
        raise AssertionError("longer reference phrase should resolve from bounded context")

    monkeypatch.setattr(
        "app.patient_chat.deepseek_query_planner_adapter.plan_retrieval_query",
        unexpected_planner,
    )
    assert _post(client, settings, "高血压为什么需要定期测量血压？").status_code == 200
    response = _post(client, settings, "那个检查呢？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] is None
    with Session(engine) as db:
        events = db.scalars(select(ChatbotEvent).order_by(ChatbotEvent.occurred_at)).all()
        assert events[-1].rescue_trigger == "short_reference"
        assert events[-1].rescue_outcome == "improved"


def test_ambiguous_rewrite_falls_back_to_context_anchored_query(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    grounded = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", grounded)

    def generic_rewrite(**kwargs):
        return DeepSeekQueryPlanResult(
            output=RetrievalQueryPlan(
                normalized_intent="测量教育检索",
                concepts=["测量"],
                synonyms=[],
                language="zh-Hans",
                excluded_content_classes=kwargs["excluded_content_classes"],
                candidate_queries=["怎样测才算正确？"],
            ),
            model="deepseek-v4-flash",
            input_tokens=50,
            output_tokens=20,
            cache_hit_tokens=None,
            cache_miss_tokens=50,
        )

    monkeypatch.setattr(
        "app.patient_chat.deepseek_query_planner_adapter.plan_retrieval_query",
        generic_rewrite,
    )
    assert _post(client, settings, "我想了解在家测量血压").status_code == 200
    response = _post(client, settings, "怎样才算测得对？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] is None
    with Session(engine) as db:
        events = db.scalars(select(ChatbotEvent).order_by(ChatbotEvent.occurred_at)).all()
        assert events[-1].rescue_trigger == "ambiguous"
        assert events[-1].rescue_outcome == "improved"


def test_grounded_answer_maps_citations_and_records_only_metadata(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    message = "血压高时，平时记录血压有什么作用？"

    response = _post(client, settings, message)

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback_code"] is None
    assert payload["evidence_decision"] == "sufficient"
    assert payload["grounding_mode"] == "approved_evidence"
    assert payload["model_version"] is None
    assert len(payload["answer_sections"]) == 3
    assert payload["sources"][0]["passage_id"].startswith("KBPASS-SYNTHETIC-")
    with Session(engine) as db:
        event = db.scalar(select(ChatbotEvent))
        assert event is not None
        assert event.query_length == len(message)
        assert message not in str(event.__dict__)
        assert event.provider_input_tokens == 120
        assert event.model_version == "deepseek-v4-flash"


def test_revoked_transmission_rights_fail_before_provider_call(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        for rights in db.scalars(select(KbRightsRecord)):
            rights.model_provider_transmission_allowed = False
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "血压高时，平时记录血压有什么作用？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "authorization_denied"
    assert adapter.calls == 0


def test_diagnosis_seeking_prompt_gets_bounded_symptom_guidance(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "我的血压持续偏高，我得了什么病？")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["fallback_code"] is None
    assert payload["safety_code"] == "permitted_symptom_guidance"
    assert payload["uncertainties"] == ["现有症状和资料不足以确认诊断。"]
    assert "prepare_symptom_summary" in payload["suggested_action_codes"]
    assert adapter.calls == 1


def test_confident_diagnostic_assertion_is_not_shown(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter(first_section_text="你肯定得了高血压。")
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "我的血压持续偏高，我得了什么病？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "policy_validation_failed"
    assert response.json()["sources"] == []
    assert adapter.calls == 1


def test_new_page_creates_retained_thread_and_follow_up_reuses_it(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter()
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)
    headers = _patient_headers(client, settings)

    first = client.post(
        "/api/v1/patient/chat/messages",
        headers=headers,
        json={"message": "血压记录有什么作用？", "language": "zh-Hans"},
    )
    assert first.status_code == 200
    thread_id = first.json()["session_id"]
    assert first.json()["follow_up_question"] is not None
    assert "ask_clarifying_question" in first.json()["suggested_action_codes"]

    second = client.post(
        "/api/v1/patient/chat/messages",
        headers=headers,
        json={
            "message": "那我应该记录多久？",
            "language": "zh-Hans",
            "session_id": thread_id,
        },
    )
    assert second.status_code == 200
    assert second.json()["session_id"] == thread_id
    assert len(adapter.conversations[1]) == 2
    assert adapter.conversations[1][0].content == "血压记录有什么作用？"

    listed = client.get("/api/v1/patient/chat/threads", headers=headers)
    assert listed.status_code == 200
    assert [item["thread_id"] for item in listed.json()["items"]] == [thread_id]

    history = client.get(f"/api/v1/patient/chat/threads/{thread_id}", headers=headers)
    assert history.status_code == 200
    assert [message["role"] for message in history.json()["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    unrelated = login(
        client,
        "unrelated.patient@example.com",
        settings.seed_unrelated_patient_password.get_secret_value(),
    )
    denied = client.post(
        "/api/v1/patient/chat/messages",
        headers=auth_header(unrelated["access_token"]),
        json={
            "message": "这个对话不属于我",
            "language": "zh-Hans",
            "session_id": thread_id,
        },
    )
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "not_found"
    with Session(engine) as db:
        thread = db.get(ChatThread, thread_id)
        assert thread is not None
        assert thread.retention_until is not None
        assert thread.last_message_at is not None
        assert (thread.retention_until - thread.last_message_at).days >= 59
        assistant_messages = db.scalars(
            select(ChatMessage).where(
                ChatMessage.thread_id == thread.id,
                ChatMessage.role == "assistant",
            )
        ).all()
        assert all(message.actor_user_id is None for message in assistant_messages)


def test_relevant_patient_measurement_is_bounded_attributed_and_visible(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter(use_context=True)
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "我的血压记录对日常观察有什么意义？")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback_code"] is None
    assert payload["context_used"] == [
        {
            "category": "measurements",
            "provenance": "patient_profile",
            "recorded_on": "2026-07-16",
        }
    ]
    assert adapter.patient_context is not None
    context_values = [item.value for item in adapter.patient_context.items]
    assert any("138/86 mmHg" in value for value in context_values)
    assert all("Demo Patient" not in value for value in context_values)


def test_future_real_context_mode_uses_same_broker_contract(settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
        profile = db.scalar(
            select(PatientProfile).where(PatientProfile.synthetic_identifier == "SYN-PATIENT-001")
        )
        assert profile is not None
        real_context_settings = Settings(
            chatbot_data_mode="approved_real_context",
            chatbot_external_provider_real_context_enabled=True,
            chatbot_external_provider_allowed_context_fields=["measurements"],
            chatbot_external_provider_no_training_contract_verified=True,
            chatbot_external_provider_no_retention_contract_verified=True,
            chatbot_external_provider_privacy_review_id="future-review",
            chatbot_external_provider_legal_review_id="future-legal",
            chatbot_external_provider_product_approval_id="future-product-approval",
        )

        context = select_patient_context(
            db,
            profile=profile,
            message="What do my blood pressure and medication records mean?",
            settings=real_context_settings,
        )

    assert context.items
    assert {item.category.value for item in context.items} == {"measurements"}
    assert any("138/86 mmHg" in item.value for item in context.items)


def test_unsupported_model_citation_returns_reviewed_source_fallback(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter(passage_id="invented-passage")
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "血压高时，平时记录血压有什么作用？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "unsupported_citation"
    assert response.json()["grounding_mode"] == "approved_evidence"
    assert response.json()["sources"]
    assert all(source["passage_id"] != "invented-passage" for source in response.json()["sources"])


def test_valid_but_unrelated_citation_returns_reviewed_source_fallback(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    adapter = FakeGroundedAdapter(first_section_text="保持充足睡眠可以改善整体健康。")
    monkeypatch.setattr("app.patient_chat.deepseek_chat_adapter", adapter)

    response = _post(client, settings, "血压高时，平时记录血压有什么作用？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "unsupported_citation"
    assert response.json()["grounding_mode"] == "approved_evidence"
    assert response.json()["sources"]
    with Session(engine) as db:
        event = db.scalar(select(ChatbotEvent).order_by(ChatbotEvent.occurred_at.desc()))
        assert event is not None
        assert event.provider_error_code == "claim_support_insufficient_semantic_overlap"


def test_generation_policy_requests_bounded_longer_answers(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    monkeypatch.setattr(settings, "deepseek_api_key", SecretStr("test-key-not-sent"))
    captured: dict[str, object] = {}

    def fake_request(self, request_body, request_settings):
        del self, request_settings
        captured.update(request_body)
        user_payload = json.loads(request_body["messages"][1]["content"])
        passage_ids = [item["passage_id"] for item in user_payload["evidence"]]
        content = {
            "answer_language": "zh-Hans",
            "answer_sections": [
                {
                    "text": "定期测量可以记录血压随时间的变化。",
                    "supporting_passage_ids": [passage_ids[0]],
                },
                {
                    "text": "这些记录可以帮助医生结合多次规范测量评估管理情况。",
                    "supporting_passage_ids": [passage_ids[1]],
                },
                {
                    "text": "你可以记录测量时间和结果，并在复诊时带给医生查看。",
                    "supporting_passage_ids": [passage_ids[0]],
                },
            ],
            "uses_patient_context": False,
            "patient_context_attribution": None,
            "uncertainties": [],
            "next_action_code": "contact_connected_doctor",
            "refusal_code": None,
        }
        return {
            "model": "deepseek-v4-flash",
            "choices": [{"message": {"content": json.dumps(content, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 200, "completion_tokens": 100},
        }

    monkeypatch.setattr(DeepSeekChatAdapter, "_request", fake_request)

    response = _post(client, settings, "高血压为什么需要定期测量血压？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] is None
    assert len(response.json()["answer_sections"]) == 3
    assert captured["max_tokens"] == 1400
    system_prompt = captured["messages"][0]["content"]
    assert "intent-adaptive length" in system_prompt
    assert "Routine education should use 2 to 3 non-repetitive" in system_prompt
    assert "closely paraphrase" in system_prompt
    assert "numeric claim unless that exact value appears verbatim" in system_prompt
    user_payload = json.loads(captured["messages"][1]["content"])
    assert user_payload["urgency_route"] == "routine_education"
    assert "call_120" not in user_payload["response_policy"]["allowed_next_actions"]
    assert user_payload["response_policy"]["section_count"] == "2-3"
    assert user_payload["response_policy"]["target_length"] == ("350-700 Chinese characters")
    assert (
        user_payload["response_policy"]["numeric_claims_require_exact_verbatim_cited_evidence"]
        is True
    )


def test_malformed_provider_output_is_repaired_once(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    monkeypatch.setattr(settings, "deepseek_api_key", SecretStr("test-key-not-sent"))
    calls: list[dict[str, object]] = []

    def fake_request(self, request_body, request_settings):
        del self, request_settings
        calls.append(request_body)
        if len(calls) == 1:
            return {
                "model": "deepseek-v4-flash",
                "choices": [{"message": {"content": '{"answer_language":"zh-Hans"}'}}],
            }
        user_payload = json.loads(request_body["messages"][1]["content"])
        passage_ids = [item["passage_id"] for item in user_payload["evidence"]]
        content = {
            "answer_language": "zh-Hans",
            "answer_sections": [
                {
                    "text": "定期测量可以记录血压随时间的变化。",
                    "supporting_passage_ids": [passage_ids[0]],
                },
                {
                    "text": "这些记录有助于医生结合多次规范测量进行评估。",
                    "supporting_passage_ids": [passage_ids[1]],
                },
                {
                    "text": "记录测量时间和结果，复诊时带给医生查看。",
                    "supporting_passage_ids": [passage_ids[0]],
                },
            ],
            "uses_patient_context": False,
            "patient_context_attribution": None,
            "used_patient_context_ids": [],
            "uncertainties": [],
            "next_action_code": "contact_connected_doctor",
            "refusal_code": None,
        }
        return {
            "model": "deepseek-v4-flash",
            "choices": [{"message": {"content": json.dumps(content, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 220, "completion_tokens": 110},
        }

    monkeypatch.setattr(DeepSeekChatAdapter, "_request", fake_request)

    response = _post(client, settings, "高血压为什么需要定期测量血压？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] is None
    assert len(calls) == 2
    repair_payload = json.loads(calls[1]["messages"][-1]["content"])
    assert repair_payload["task"].startswith("Repair the preceding response")
    assert repair_payload["validation_issues"]
    assert repair_payload["json_schema"]["title"] == "StructuredModelOutput"
    with Session(engine) as db:
        event = db.scalar(select(ChatbotEvent))
        assert event is not None
        assert event.provider_attempt_count == 2
        assert event.provider_error_code is None


def test_repeated_malformed_output_records_content_free_subtype(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    monkeypatch.setattr(settings, "deepseek_api_key", SecretStr("test-key-not-sent"))
    calls = 0

    def fake_request(self, request_body, request_settings):
        nonlocal calls
        del self, request_body, request_settings
        calls += 1
        return {
            "model": "deepseek-v4-flash",
            "choices": [{"message": {"content": "not valid json"}}],
        }

    monkeypatch.setattr(DeepSeekChatAdapter, "_request", fake_request)

    response = _post(client, settings, "高血压为什么需要定期测量血压？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "malformed_model_output"
    assert calls == 2
    with Session(engine) as db:
        event = db.scalar(select(ChatbotEvent))
        assert event is not None
        assert event.provider_error_code == "provider_content_invalid_json"
        assert event.provider_attempt_count == 2
        assert "not valid json" not in str(event.__dict__)


def test_repeated_schema_mismatch_records_field_specific_subtype(
    client: TestClient, settings, monkeypatch, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    monkeypatch.setattr(settings, "deepseek_api_key", SecretStr("test-key-not-sent"))
    calls: list[dict[str, object]] = []

    def fake_request(self, request_body, request_settings):
        del self, request_settings
        calls.append(request_body)
        content = {
            "answer_language": "zh-Hans",
            "answer_sections": [],
            "uses_patient_context": False,
            "next_action_code": "go_to_er",
        }
        return {
            "model": "deepseek-v4-flash",
            "choices": [{"message": {"content": json.dumps(content)}}],
        }

    monkeypatch.setattr(DeepSeekChatAdapter, "_request", fake_request)

    response = _post(client, settings, "高血压为什么需要定期测量血压？")

    assert response.status_code == 200
    assert response.json()["fallback_code"] == "malformed_model_output"
    assert len(calls) == 2
    repair_payload = json.loads(calls[1]["messages"][-1]["content"])
    assert any(
        issue.startswith("answer_sections:") for issue in repair_payload["validation_issues"]
    )
    assert "json_schema" in repair_payload
    with Session(engine) as db:
        event = db.scalar(select(ChatbotEvent))
        assert event is not None
        assert event.provider_error_code is not None
        assert event.provider_error_code.startswith("provider_schema_answer_sections_")
        assert event.provider_attempt_count == 2
