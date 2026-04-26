from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PlanningHeuristicResult:
    complexity: str
    owner_agents: list[str]
    risk_level: str
    reasoning: str
    requested_priority: str
    effective_priority: str
    budget_seconds: float | None
    budget_risk: str

    def to_dict(self) -> dict:
        return {
            "complexity": self.complexity,
            "owner_agents": list(self.owner_agents),
            "risk_level": self.risk_level,
            "reasoning": self.reasoning,
            "requested_priority": self.requested_priority,
            "effective_priority": self.effective_priority,
            "budget_seconds": self.budget_seconds,
            "budget_risk": self.budget_risk,
        }


def _normalize_priority(priority: str) -> str:
    normalized = (priority or "normal").strip().lower()
    if normalized not in {"low", "normal", "high"}:
        return "normal"
    return normalized


def _resolve_budget_risk(budget_seconds: float | None) -> str:
    if budget_seconds is None:
        return "unknown"
    if budget_seconds <= 15:
        return "high"
    if budget_seconds <= 45:
        return "medium"
    return "low"


def _build_result(
    *,
    complexity: str,
    owner_agents: list[str],
    risk_level: str,
    reasoning: str,
    requested_priority: str,
    budget_seconds: float | None,
) -> PlanningHeuristicResult:
    budget_risk = _resolve_budget_risk(budget_seconds)
    effective_priority = requested_priority
    if requested_priority == "normal" and budget_risk == "high":
        effective_priority = "high"
    return PlanningHeuristicResult(
        complexity=complexity,
        owner_agents=owner_agents,
        risk_level=risk_level,
        reasoning=reasoning,
        requested_priority=requested_priority,
        effective_priority=effective_priority,
        budget_seconds=budget_seconds,
        budget_risk=budget_risk,
    )


def evaluate_message_heuristics(
    message: str,
    *,
    priority: str = "normal",
    budget_seconds: float | None = None,
) -> PlanningHeuristicResult:
    text = (message or "").strip().lower()
    normalized_priority = _normalize_priority(priority)
    normalized_budget = float(budget_seconds) if budget_seconds is not None else None
    owner_agents: list[str] = []
    if any(token in text for token in ("设计", "工艺")):
        owner_agents.extend(["design_specialist", "process_engineer"])
    if any(token in text for token in ("仿真", "模拟")):
        owner_agents.append("simulation_specialist")
    if any(token in text for token in ("数据库", "数据")):
        owner_agents.append("data_analyst")
    if any(token in text for token in ("系统", "网关", "状态")):
        owner_agents.append("system")
    if any(token in text for token in ("情报", "日报", "报告")):
        owner_agents.append("intel_officer")
    deduped = list(dict.fromkeys(owner_agents)) or ["default"]

    multi_signals = ("协同", "多智能体", "跨团队", "联合", "并行")
    if any(token in text for token in multi_signals):
        return _build_result(
            complexity="high",
            owner_agents=deduped,
            risk_level="medium",
            reasoning="multi-agent signals found, split and merge flow recommended",
            requested_priority=normalized_priority,
            budget_seconds=normalized_budget,
        )
    if len(text) > 120 or len(deduped) >= 3:
        return _build_result(
            complexity="medium",
            owner_agents=deduped,
            risk_level="low",
            reasoning="request has moderate breadth or multiple owner candidates",
            requested_priority=normalized_priority,
            budget_seconds=normalized_budget,
        )
    return _build_result(
        complexity="low",
        owner_agents=deduped,
        risk_level="low",
        reasoning="short and focused request, single-path execution is sufficient",
        requested_priority=normalized_priority,
        budget_seconds=normalized_budget,
    )
