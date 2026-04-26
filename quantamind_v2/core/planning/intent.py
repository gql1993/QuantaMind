from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlanningIntent(str, Enum):
    SHORTCUT_QUERY = "shortcut_query"
    MULTI_AGENT_ANALYSIS = "multi_agent_analysis"
    STATUS_CHECK = "status_check"
    GENERAL_REQUEST = "general_request"


@dataclass(slots=True)
class IntentSignal:
    intent: PlanningIntent
    confidence: float
    reason: str


def detect_intent(message: str) -> IntentSignal:
    text = (message or "").strip().lower()
    if not text:
        return IntentSignal(
            intent=PlanningIntent.GENERAL_REQUEST,
            confidence=0.35,
            reason="empty message defaults to general request",
        )
    if any(token in text for token in ("协同", "多智能体", "联合", "跨团队")):
        return IntentSignal(
            intent=PlanningIntent.MULTI_AGENT_ANALYSIS,
            confidence=0.9,
            reason="message contains multi-agent collaboration signals",
        )
    if any(token in text for token in ("状态", "健康", "检查", "诊断")):
        return IntentSignal(
            intent=PlanningIntent.STATUS_CHECK,
            confidence=0.75,
            reason="message suggests status/health checking",
        )
    if any(token in text for token in ("日报", "报告", "今天情报", "今日日报")):
        return IntentSignal(
            intent=PlanningIntent.SHORTCUT_QUERY,
            confidence=0.7,
            reason="message resembles high-frequency report request",
        )
    return IntentSignal(
        intent=PlanningIntent.GENERAL_REQUEST,
        confidence=0.55,
        reason="no explicit high-confidence pattern found",
    )
