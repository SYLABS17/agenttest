from __future__ import annotations

import random
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List

from backend.services.observability import ObservabilityService


@dataclass
class AgentEvaluationResult:
    agent_name: str
    accuracy: float
    latency_ms: float
    agreement: float


class AgentEvaluator:
    """Scores agent outputs using simple heuristics to mimic evaluation."""

    def __init__(self, observability: ObservabilityService):
        self.observability = observability

    def evaluate(self, agent_payloads: List[Dict]) -> Dict[str, AgentEvaluationResult]:
        results: Dict[str, AgentEvaluationResult] = {}
        for payload in agent_payloads:
            agent_name = payload.get("agent")
            latency_ms = payload.get("latency_ms", 0.0)
            accuracy = self._score_accuracy(payload)
            agreement = self._score_agreement(payload, agent_payloads)
            result = AgentEvaluationResult(agent_name, accuracy, latency_ms, agreement)
            results[agent_name] = result
            self._log_evaluation(result, payload.get("query", ""))
        return results

    def _score_accuracy(self, payload: Dict) -> float:
        insights = payload.get("insights", [])
        base_score = min(len(insights) * 0.1, 0.9)
        noise = random.uniform(0.05, 0.1)
        return round(min(base_score + noise, 1.0), 2)

    def _score_agreement(self, payload: Dict, all_payloads: List[Dict]) -> float:
        target_topics = set(payload.get("topics", []))
        if not target_topics:
            return 0.5
        overlap_scores = []
        for other in all_payloads:
            if other is payload:
                continue
            other_topics = set(other.get("topics", []))
            if not other_topics:
                continue
            overlap = len(target_topics & other_topics) / max(len(target_topics | other_topics), 1)
            overlap_scores.append(overlap)
        if not overlap_scores:
            return 0.5
        return round(statistics.mean(overlap_scores), 2)

    def _log_evaluation(self, result: AgentEvaluationResult, query: str) -> None:
        self.observability.log_event(
            "agent_evaluation",
            agent=result.agent_name,
            accuracy=result.accuracy,
            latencyMs=result.latency_ms,
            agreement=result.agreement,
            query=query,
            evaluatedAt=time.time(),
        )
