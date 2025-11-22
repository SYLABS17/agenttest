import asyncio
from dataclasses import dataclass
from pathlib import Path

import pytest

from backend.agents import AgentResponse
from backend.agents.manager_agent import ManagerAgent
from backend.services.evaluator import AgentEvaluator
from backend.services.observability import ObservabilityService


@dataclass
class StubAgent:
  name: str

  async def run(self, query: str) -> AgentResponse:
    await asyncio.sleep(0)
    return AgentResponse(
        agent=self.name,
        query=query,
        summary=f"{self.name} summary for {query}",
        citations=[f"https://example.com/{self.name}"],
        latency_ms=10,
        relevance=0.9,
    )


@pytest.mark.asyncio
async def test_manager_returns_final_report(tmp_path):
  observability = ObservabilityService(connection_string=None, environment="test", log_dir=tmp_path)
  evaluator = AgentEvaluator(observability)
  manager = ManagerAgent([StubAgent("bing"), StubAgent("ai")], evaluator, observability)

  result = await manager.handle_query("Impact of generative AI on journalism")
  assert "finalReport" in result
  assert len(result["workerResponses"]) == 2
  assert result["evaluation"]["overall"] > 0
