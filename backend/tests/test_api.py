from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_healthz_endpoint():
  response = client.get("/healthz")
  assert response.status_code == 200
  payload = response.json()
  assert payload["status"] == "ok"


def test_research_endpoint_generates_report():
  response = client.post("/api/research", json={"query": "Future of renewable energy in Africa"})
  assert response.status_code == 200
  payload = response.json()
  assert "finalReport" in payload
  assert payload["evaluation"]["overall"] >= 0
