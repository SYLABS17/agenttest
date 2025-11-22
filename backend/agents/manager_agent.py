from __future__ import annotations

import asyncio
import time
from dataclasses import asdict
from typing import Dict, Iterable, List

from . import AgentMessage, AgentResponse
from backend.services.evaluator import AgentEvaluator
from backend.services.observability import ObservabilityService


class ManagerAgent:
  """Coordinates Bing + Azure AI Search workers and synthesizes the report."""

  def __init__(
      self,
      workers: Iterable,
      evaluator: AgentEvaluator,
      observability: ObservabilityService,
  ) -> None:
    self._workers = list(workers)
    self._evaluator = evaluator
    self._observability = observability

  async def handle_query(self, query: str) -> Dict[str, object]:
    start = time.perf_counter()
    self._observability.log_event("manager_agent.received", query=query)

    with self._observability.start_trace("manager.handle_query", {"query": query}):
      worker_results = await self._execute_workers(query)
      messages = self._build_messages(query, worker_results)
      final_report = self._synthesize_report(query, worker_results)
      evaluation = self._evaluator.evaluate(query, worker_results)

    total_latency_ms = int((time.perf_counter() - start) * 1000)
    self._observability.log_event(
        "manager_agent.completed",
        query=query,
        worker_count=len(worker_results),
        latency_ms=total_latency_ms,
    )

    return {
        "query": query,
        "messages": [asdict(message) for message in messages],
        "workerResponses": [asdict(result) for result in worker_results],
        "finalReport": final_report,
        "evaluation": evaluation,
        "latencyMs": total_latency_ms,
    }

  async def _execute_workers(self, query: str) -> List[AgentResponse]:
    tasks = [asyncio.create_task(worker.run(query)) for worker in self._workers]
    results: List[AgentResponse] = []
    for task in asyncio.as_completed(tasks):
      try:
        response = await task
        results.append(response)
      except Exception as exc:  # pragma: no cover - logged for observability
        self._observability.log_exception("manager_agent.worker_failed", exc, query=query)
    return results

  def _build_messages(self, query: str, responses: List[AgentResponse]) -> List[AgentMessage]:
    messages: List[AgentMessage] = [
        AgentMessage(
            role="system",
            agent="ManagerAgent",
            content=f"ManagerAgent initialized research session for '{query}'.",
        )
    ]
    for response in responses:
      messages.append(
          AgentMessage(
              role="assistant",
              agent=response.agent,
              content=response.summary,
              citations=response.citations,
              latency_ms=response.latency_ms,
          )
      )

    synthesis = self._synthesize_report(query, responses)
    messages.append(
        AgentMessage(
            role="assistant",
            agent="ManagerAgent",
            content=synthesis,
            latency_ms=sum(resp.latency_ms for resp in responses),
        )
    )
    return messages

  def _synthesize_report(self, query: str, responses: List[AgentResponse]) -> str:
    if not responses:
      return f"No data available for '{query}'."

    bullets = "\n".join([f"- {response.summary}" for response in responses])
    citations = sorted({citation for resp in responses for citation in resp.citations})
    sources = "\n".join([f"  • {citation}" for citation in citations]) or "  • No citations provided"

    return (
        f"## Research Summary: {query}\n\n"
        f"{bullets}\n\n"
        f"### Sources\n{sources}"
    )
