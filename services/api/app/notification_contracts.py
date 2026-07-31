"""Bounded, privacy-safe notification vocabulary and localized templates."""

from dataclasses import dataclass
from typing import Literal

NotificationEventType = Literal[
    "medication_reminder",
    "refill_reminder",
    "recovery_task_due",
    "follow_up_milestone",
    "consultation_milestone",
    "care_service_milestone",
    "imaging_action_available",
    "missing_information_warning",
    "incomplete_allocation_warning",
    "payer_clarification_requested",
    "adherence_evidence_available",
    "imaging_status_warning",
    "consultation_follow_up_warning",
    "payer_request_submitted",
    "payer_doctor_response_added",
    "payer_manual_review_transition",
    "payer_final_outcome",
    "payer_request_closed",
    "cost_variance_warning",
]
NotificationSeverity = Literal["information", "action", "warning"]
NotificationRole = Literal["patient", "doctor", "payer"]
NotificationChannel = Literal["in_app", "apns", "android_emas", "web_push"]
PrivacyClass = Literal["generic", "private_in_app"]

EVENT_CONTRACTS: dict[str, dict[str, object]] = {
    "medication_reminder": {
        "roles": {"patient"},
        "source_category": "medication_reminder",
        "severity": "action",
        "deep_link": "patient_medications",
        "expiry_hours": 24,
    },
    "refill_reminder": {
        "roles": {"patient"},
        "source_category": "medication_reminder",
        "severity": "action",
        "deep_link": "patient_medications",
        "expiry_hours": 168,
    },
    "recovery_task_due": {
        "roles": {"patient"},
        "source_category": "recovery_task",
        "severity": "action",
        "deep_link": "patient_recovery",
        "expiry_hours": 72,
    },
    "follow_up_milestone": {
        "roles": {"patient"},
        "source_category": "clinical_event",
        "severity": "action",
        "deep_link": "patient_dashboard",
        "expiry_hours": 168,
    },
    "consultation_milestone": {
        "roles": {"patient"},
        "source_category": "consultation",
        "severity": "action",
        "deep_link": "patient_consultations",
        "expiry_hours": 168,
    },
    "care_service_milestone": {
        "roles": {"patient"},
        "source_category": "clinical_service",
        "severity": "action",
        "deep_link": "patient_medical_service",
        "expiry_hours": 168,
    },
    "imaging_action_available": {
        "roles": {"patient"},
        "source_category": "medical_imaging_asset",
        "severity": "action",
        "deep_link": "patient_imaging",
        "expiry_hours": 168,
    },
    "missing_information_warning": {
        "roles": {"doctor"},
        "source_category": "payer_request",
        "severity": "warning",
        "deep_link": "doctor_payer_request",
        "expiry_hours": 720,
    },
    "incomplete_allocation_warning": {
        "roles": {"doctor"},
        "source_category": "payer_request",
        "severity": "warning",
        "deep_link": "doctor_payer_request",
        "expiry_hours": 720,
    },
    "payer_clarification_requested": {
        "roles": {"doctor"},
        "source_category": "payer_request",
        "severity": "warning",
        "deep_link": "doctor_payer_request",
        "expiry_hours": 720,
    },
    "adherence_evidence_available": {
        "roles": {"doctor"},
        "source_category": "clinical_event_update",
        "severity": "information",
        "deep_link": "doctor_patient_care",
        "expiry_hours": 168,
    },
    "imaging_status_warning": {
        "roles": {"doctor"},
        "source_category": "medical_imaging_asset",
        "severity": "information",
        "deep_link": "doctor_patient_care",
        "expiry_hours": 168,
    },
    "consultation_follow_up_warning": {
        "roles": {"doctor"},
        "source_category": "consultation",
        "severity": "information",
        "deep_link": "doctor_patient_care",
        "expiry_hours": 168,
    },
    "payer_request_submitted": {
        "roles": {"payer"},
        "source_category": "payer_request",
        "severity": "action",
        "deep_link": "payer_request",
        "expiry_hours": 720,
    },
    "payer_doctor_response_added": {
        "roles": {"payer"},
        "source_category": "payer_request",
        "severity": "action",
        "deep_link": "payer_request",
        "expiry_hours": 720,
    },
    "payer_manual_review_transition": {
        "roles": {"doctor", "patient"},
        "source_category": "payer_request",
        "severity": "information",
        "deep_links": {
            "doctor": "doctor_payer_request",
            "patient": "patient_care_cost",
        },
        "expiry_hours": 720,
    },
    "payer_final_outcome": {
        "roles": {"doctor", "patient"},
        "source_category": "payer_request",
        "severity": "information",
        "deep_links": {
            "doctor": "doctor_payer_request",
            "patient": "patient_care_cost",
        },
        "expiry_hours": 720,
    },
    "payer_request_closed": {
        "roles": {"doctor", "patient"},
        "source_category": "payer_request",
        "severity": "information",
        "deep_links": {
            "doctor": "doctor_payer_request",
            "patient": "patient_care_cost",
        },
        "expiry_hours": 168,
    },
    "cost_variance_warning": {
        "roles": {"doctor"},
        "source_category": "expected_care_comparison",
        "severity": "warning",
        "deep_link": "doctor_expected_care",
        "expiry_hours": 720,
    },
}

DEEP_LINK_CODES = {
    "patient_medications",
    "patient_recovery",
    "payer_request",
    "doctor_payer_request",
    "doctor_expected_care",
    "patient_care_cost",
    "patient_dashboard",
    "patient_consultations",
    "patient_medical_service",
    "patient_imaging",
    "doctor_patient_care",
}

_COPY: dict[str, dict[str, tuple[str, str]]] = {
    "medication_reminder": {
        "en": ("Care reminder", "Open Dr. AI to review your scheduled care reminder."),
        "zh-Hans": ("护理提醒", "打开 Dr. AI 查看您的计划护理提醒。"),
    },
    "refill_reminder": {
        "en": ("Refill reminder", "Open Dr. AI to review a refill reminder."),
        "zh-Hans": ("续药提醒", "打开 Dr. AI 查看续药提醒。"),
    },
    "recovery_task_due": {
        "en": ("Recovery reminder", "Open Dr. AI to review a recovery task."),
        "zh-Hans": ("康复提醒", "打开 Dr. AI 查看康复任务。"),
    },
    "follow_up_milestone": {
        "en": ("Follow-up reminder", "Open Dr. AI to review a follow-up milestone."),
        "zh-Hans": ("随访提醒", "打开 Dr. AI 查看随访节点。"),
    },
    "consultation_milestone": {
        "en": ("Consultation update", "Open Dr. AI to review a consultation update."),
        "zh-Hans": ("会诊更新", "打开 Dr. AI 查看会诊更新。"),
    },
    "care_service_milestone": {
        "en": ("Care milestone", "Open Dr. AI to review a scheduled care milestone."),
        "zh-Hans": ("医疗服务节点", "打开 Dr. AI 查看计划医疗服务节点。"),
    },
    "imaging_action_available": {
        "en": ("Imaging update", "Open Dr. AI to review an available imaging action."),
        "zh-Hans": ("影像更新", "打开 Dr. AI 查看可执行的影像操作。"),
    },
    "missing_information_warning": {
        "en": ("Information needs review", "Required information has not been recorded."),
        "zh-Hans": ("信息需要审核", "尚未记录所需信息。"),
    },
    "incomplete_allocation_warning": {
        "en": (
            "Cost allocation incomplete",
            "A deterministic allocation check is incomplete. Review is recommended.",
        ),
        "zh-Hans": ("费用分配不完整", "确定性分配检查尚未完成，建议审核。"),
    },
    "payer_clarification_requested": {
        "en": ("Clarification requested", "Open Dr. AI to review the payer clarification request."),
        "zh-Hans": ("需要澄清", "打开 Dr. AI 查看付款方的澄清请求。"),
    },
    "adherence_evidence_available": {
        "en": (
            "Recorded care evidence updated",
            "Open Dr. AI to review newly recorded completion evidence.",
        ),
        "zh-Hans": ("护理记录已更新", "打开 Dr. AI 查看新记录的完成证据。"),
    },
    "imaging_status_warning": {
        "en": ("Imaging status updated", "Open Dr. AI to review the recorded imaging status."),
        "zh-Hans": ("影像状态已更新", "打开 Dr. AI 查看已记录的影像状态。"),
    },
    "consultation_follow_up_warning": {
        "en": ("Consultation status updated", "Open Dr. AI to review the consultation status."),
        "zh-Hans": ("会诊状态已更新", "打开 Dr. AI 查看会诊状态。"),
    },
    "payer_request_submitted": {
        "en": ("Review request available", "Open Dr. AI to review a newly submitted request."),
        "zh-Hans": ("有新的审核请求", "打开 Dr. AI 查看新提交的请求。"),
    },
    "payer_doctor_response_added": {
        "en": (
            "Additional information available",
            "Open Dr. AI to review an attributable response.",
        ),
        "zh-Hans": ("有补充信息", "打开 Dr. AI 查看可追溯的回复。"),
    },
    "payer_manual_review_transition": {
        "en": ("Request status updated", "Open Dr. AI to review the latest human review status."),
        "zh-Hans": ("请求状态已更新", "打开 Dr. AI 查看最新的人工审核状态。"),
    },
    "payer_final_outcome": {
        "en": ("Human review outcome recorded", "Open Dr. AI to review the recorded outcome."),
        "zh-Hans": ("已记录人工审核结果", "打开 Dr. AI 查看已记录的审核结果。"),
    },
    "payer_request_closed": {
        "en": ("Review request closed", "Open Dr. AI to review the closed request history."),
        "zh-Hans": ("审核请求已关闭", "打开 Dr. AI 查看已关闭请求的历史记录。"),
    },
    "cost_variance_warning": {
        "en": (
            "Cost comparison needs review",
            "A deterministic comparison is outside the published range. Review is recommended.",
        ),
        "zh-Hans": (
            "费用比较需要审核",
            "确定性比较结果超出已发布范围，建议进行审核。",
        ),
    },
}


@dataclass(frozen=True)
class RenderedNotification:
    title: str
    body: str
    locale: str
    template_code: str


def render_notification(event_type: str, locale: str) -> RenderedNotification:
    if event_type not in EVENT_CONTRACTS:
        raise ValueError("unsupported_notification_event_type")
    resolved_locale = "zh-Hans" if locale == "zh-Hans" else "en"
    title, body = _COPY[event_type][resolved_locale]
    return RenderedNotification(
        title=title,
        body=body,
        locale=resolved_locale,
        template_code=f"{event_type}_v1",
    )


def validate_contract(event_type: str, audience_role: str, deep_link_code: str) -> None:
    contract = EVENT_CONTRACTS.get(event_type)
    if contract is None:
        raise ValueError("unsupported_notification_event_type")
    if audience_role not in contract["roles"]:
        raise ValueError("notification_audience_role_mismatch")
    expected_link = (
        contract["deep_links"][audience_role] if "deep_links" in contract else contract["deep_link"]
    )
    if deep_link_code != expected_link or deep_link_code not in DEEP_LINK_CODES:
        raise ValueError("notification_deep_link_mismatch")
