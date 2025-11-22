from __future__ import annotations

import asyncio
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, List

from . import AgentResponse
from backend.services.observability import ObservabilityService


class BingSearchAgent:
  """Simulated Bing Search worker that serves curated responses from fixture data."""

  def __init__(
      self,
      data_file: Path,
      observability: ObservabilityService,
      latency_bounds: tuple[float, float] = (0.25, 1.2),
  ) -> None:
    self._data_file = data_file
    self._observability = observability
    self._latency_bounds = latency_bounds
    self._results_index = self._load_fixture(data_file)

  def _load_fixture(self, path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
      raise FileNotFoundError(f"Bing Search fixture missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
      payload = json.load(handle)
    return payload.get("results", [])

  def _lookup(self, query: str) -> Dict[str, Any]:
    normalized = query.lower()
    for entry in self._results_index:
      if normalized in entry.get("query", "").lower():
        return entry
    return {
        "query": query,
        "summary": "Bing Search agent could not find curated data; returning synthesized placeholder.",
        "citations": [],
        "sources": [],
    }

  async def run(self, query: str) -> AgentResponse:
    start_time = time.perf_counter()
    artificial_latency = random.uniform(*self._latency_bounds)
    await asyncio.sleep(artificial_latency)

    record = self._lookup(query)
    summary = record.get("summary", "")
    citations = record.get("citations", [])

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    metadata = {
        "sources": record.get("sources", []),
        "agent": "bing-search",
        "latencySeconds": artificial_latency,
    }

    self._observability.log_event(
        "bing_search_agent.completed",
        query=query,
        latency_ms=latency_ms,
        citations=len(citations),
    )

    return AgentResponse(
        agent="BingSearchAgent",
        query=query,
        summary=summary,
        citations=citations,
        latency_ms=latency_ms,
        relevance=record.get("relevance", 0.75),
        metadata=metadata,
    )
