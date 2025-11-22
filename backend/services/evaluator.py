from __future__ import annotations

import math
from typing import Dict, List

from backend.agents import AgentResponse
from backend.services.observability import ObservabilityService


class AgentEvaluator:
  """Scores agents with repeatable, dummy metrics for demo purposes."""

  def __init__(self, observability: ObservabilityService) -> None:
    self._observability = observability

  def evaluate(self, query: str, responses: List[AgentResponse]) -> Dict[str, object]:
    if not responses:
      return {"overall": 0.0, "explanation": "No agent responses available."}

    relevance_scores = [resp.relevance for resp in responses]
    latencies = [resp.latency_ms for resp in responses]
    agreement = self._compute_agreement(responses)

    overall = round((sum(relevance_scores) / len(relevance_scores) * 0.6) + (agreement * 0.4), 3)
    evaluation = {
        "overall": overall,
        "accuracy": round(sum(relevance_scores) / len(relevance_scores), 3),
        "latencyScore": round(1 / (1 + math.log1p(sum(latencies) / len(latencies))), 3),
        "agreement": round(agreement, 3),
        "agents": [
            {
                "agent": resp.agent,
                "latencyMs": resp.latency_ms,
                "relevance": resp.relevance,
            }
            for resp in responses
        ],
        "query": query,
    }

    self._observability.log_event("agent_evaluator.completed", query=query, overall=overall)
    return evaluation

  def _compute_agreement(self, responses: List[AgentResponse]) -> float:
    if len(responses) < 2:
      return 1.0
    reference = set(responses[0].citations)
    overlap = 0
    for response in responses[1:]:
      overlap += len(reference.intersection(response.citations))
    max_possible = sum(len(reference) for _ in responses[1:]) or 1
    return overlap / max_possible
