from __future__ import annotations

import asyncio
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, List

from . import AgentResponse
from backend.services.observability import ObservabilityService


class AISearchAgent:
  """Simulates Azure AI Search grounding for research documents."""

  def __init__(
      self,
      data_file: Path,
      observability: ObservabilityService,
      latency_bounds: tuple[float, float] = (0.3, 1.5),
  ) -> None:
    self._data_file = data_file
    self._observability = observability
    self._latency_bounds = latency_bounds
    self._index = self._load_fixture(data_file)

  def _load_fixture(self, path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
      raise FileNotFoundError(f"Azure AI Search fixture missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
      payload = json.load(handle)
    return payload.get("results", [])

  def _lookup(self, query: str) -> Dict[str, Any]:
    normalized = query.lower()
    for entry in self._index:
      if normalized in entry.get("query", "").lower():
        return entry
    return {
        "query": query,
        "summary": "AI Search index did not match the query; returning default synthesis.",
        "citations": [],
        "facets": [],
    }

  async def run(self, query: str) -> AgentResponse:
    start = time.perf_counter()
    artificial_latency = random.uniform(*self._latency_bounds)
    await asyncio.sleep(artificial_latency)

    record = self._lookup(query)
    latency_ms = int((time.perf_counter() - start) * 1000)

    self._observability.log_event(
        "ai_search_agent.completed",
        query=query,
        latency_ms=latency_ms,
        doc_count=len(record.get("citations", [])),
    )

    metadata = {
        "facets": record.get("facets", []),
        "index": record.get("index", "research-index"),
        "agent": "azure-ai-search",
        "latencySeconds": artificial_latency,
    }

    return AgentResponse(
        agent="AISearchAgent",
        query=query,
        summary=record.get("summary", ""),
        citations=record.get("citations", []),
        latency_ms=latency_ms,
        relevance=record.get("relevance", 0.82),
        metadata=metadata,
    )
