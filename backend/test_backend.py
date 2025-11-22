import pytest
from backend.agents.manager_agent import ManagerAgent
from backend.agents.bing_agent import BingSearchAgent
from backend.agents.ai_search_agent import AISearchAgent
import os

# Ensure we are in simulation mode for tests
os.environ["SIMULATE_AGENTS"] = "True"

@pytest.mark.asyncio
async def test_bing_agent_simulation():
    agent = BingSearchAgent()
    response = await agent.search("Future of renewable energy in Africa")
    assert response["source"] == "Bing"
    assert len(response["results"]) > 0
    assert "Africa" in response["results"][0]

@pytest.mark.asyncio
async def test_ai_search_agent_simulation():
    agent = AISearchAgent()
    response = await agent.search("Impact of generative AI on journalism")
    assert response["source"] == "Azure AI Search"
    assert len(response["results"]) > 0

@pytest.mark.asyncio
async def test_manager_agent_flow():
    manager = ManagerAgent()
    report = await manager.process_request("Future of renewable energy in Africa")
    assert "Research Report" in report["title"]
    assert len(report["sections"]) == 3
    assert "Bing Search Insights" == report["sections"][0]["heading"]
