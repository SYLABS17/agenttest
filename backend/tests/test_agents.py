from pathlib import Path

from backend.agents.ai_search_agent import AISearchAgent
from backend.agents.bing_agent import BingSearchAgent
from backend.agents.manager_agent import ManagerAgent
from backend.config import AppConfig
from backend.services.evaluator import AgentEvaluator
from backend.services.observability import ObservabilityService


def build_config(**overrides):
    return AppConfig(enable_mock_latency=False, **overrides)


def build_observability(config: AppConfig):
    return ObservabilityService(config)


def test_bing_agent_returns_insights(tmp_path):
    config = build_config()
    obs = build_observability(config)
    agent = BingSearchAgent(config, obs)
    response = agent.run("Future of renewable energy in Africa")
    assert response.agent == "bing-search"
    assert response.insights
    assert response.latency_ms >= 0


def test_manager_agent_generates_report(tmp_path):
    config = build_config(reports_dir=tmp_path)
    obs = build_observability(config)
    bing_agent = BingSearchAgent(config, obs)
    ai_agent = AISearchAgent(config, obs)
    evaluator = AgentEvaluator(obs)
    manager = ManagerAgent(config, obs, bing_agent, ai_agent, evaluator)

    output = manager.run_research("Impact of generative AI on journalism")
    assert output["final_report"]["title"].startswith("Research Brief")
    assert len(output["conversation"]) >= 3
    assert Path(output["report_path"]).exists()
    assert "evaluation" in output
