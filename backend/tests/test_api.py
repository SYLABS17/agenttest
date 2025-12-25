from fastapi.testclient import TestClient

from backend.config import AppConfig
from backend.main import create_app


def build_client():
    config = AppConfig(enable_mock_latency=False)
    app = create_app(config)
    return TestClient(app)


def test_health_endpoint_returns_ok():
    with build_client() as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"


def test_research_endpoint_returns_report():
    with build_client() as client:
        payload = {"query": "Future of renewable energy in Africa"}
        response = client.post("/api/research", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["final_report"]["key_insights"]
        assert "evaluation" in data
        assert "latency" in data


def test_logs_endpoint_returns_recent_entries():
    with build_client() as client:
        client.post("/api/research", json={"query": "Impact of generative AI on journalism"})
        logs_response = client.get("/api/logs")
        assert logs_response.status_code == 200
        logs = logs_response.json()["logs"]
        assert isinstance(logs, list)
