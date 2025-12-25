from backend.services.evaluator import AgentEvaluator
from backend.services.observability import ObservabilityService
from backend.config import AppConfig


def test_evaluator_scores_agents():
    config = AppConfig(enable_mock_latency=False)
    obs = ObservabilityService(config)
    evaluator = AgentEvaluator(obs)
    payloads = [
        {"agent": "bing", "query": "test", "insights": ["a", "b"], "topics": ["solar", "finance"], "latency_ms": 120},
        {"agent": "ai-search", "query": "test", "insights": ["c"], "topics": ["solar"], "latency_ms": 180},
    ]

    results = evaluator.evaluate(payloads)
    assert "bing" in results
    assert 0 <= results["bing"].accuracy <= 1
    assert results["ai-search"].agreement >= 0
