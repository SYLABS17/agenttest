import asyncio
from pathlib import Path

import pytest

from backend.agents.ai_search_agent import AISearchAgent
from backend.agents.bing_agent import BingSearchAgent
from backend.services.observability import ObservabilityService


ROOT = Path(__file__).resolve().parents[2]


def build_observability(tmp_path) -> ObservabilityService:
  return ObservabilityService(connection_string=None, environment="test", log_dir=tmp_path)


@pytest.mark.asyncio
async def test_bing_agent_returns_curated_summary(tmp_path):
  obs = build_observability(tmp_path)
  agent = BingSearchAgent(ROOT / "test" / "data" / "bing_results.json", obs, latency_bounds=(0, 0))
  response = await agent.run("Future of renewable energy in Africa")
  assert response.agent == "BingSearchAgent"
  assert "renewable" in response.summary.lower()


@pytest.mark.asyncio
async def test_ai_search_agent_handles_missing_query(tmp_path):
  obs = build_observability(tmp_path)
  agent = AISearchAgent(ROOT / "test" / "data" / "ai_search_results.json", obs, latency_bounds=(0, 0))
  response = await agent.run("Unknown query")
  assert response.summary.startswith("AI Search index")
