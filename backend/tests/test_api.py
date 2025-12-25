"""Tests for FastAPI application endpoints."""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI Research System"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"
    assert "timestamp" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "environment" in data
    assert "agents" in data
    assert "services" in data


def test_research_endpoint():
    """Test research endpoint with valid query."""
    payload = {
        "query": "Test research query",
        "include_evaluation": True
    }
    response = client.post("/api/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["query"] == "Test research query"
    assert "processing_time_ms" in data
    assert data["processing_time_ms"] > 0


def test_research_endpoint_empty_query():
    """Test research endpoint with empty query."""
    payload = {
        "query": "",
        "include_evaluation": False
    }
    response = client.post("/api/research", json=payload)
    assert response.status_code == 422  # Validation error


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "agents" in data
    assert "evaluations" in data
    assert "observability" in data


def test_agents_status_endpoint():
    """Test agents status endpoint."""
    response = client.get("/api/agents/status")
    assert response.status_code == 200
    data = response.json()
    assert "overall_healthy" in data
    assert "agents" in data


def test_evaluation_history_endpoint():
    """Test evaluation history endpoint."""
    response = client.get("/api/evaluation/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "evaluations" in data
    assert isinstance(data["evaluations"], list)


def test_logs_endpoint_dev_mode():
    """Test logs endpoint in development mode."""
    response = client.get("/api/logs?lines=10")
    # In test environment, should return 200 if in dev mode or 403 if not
    assert response.status_code in [200, 403]
    if response.status_code == 200:
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)


def test_dummy_query_endpoint():
    """Test dummy query endpoint."""
    response = client.post("/api/test/dummy-query")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "query" in data
    assert "report" in data
    assert "chat_history" in data


def test_cors_headers():
    """Test CORS headers are properly set."""
    response = client.options("/api/research")
    assert response.status_code == 200
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or "Access-Control-Allow-Origin" in response.headers


def test_invalid_endpoint():
    """Test invalid endpoint returns 404."""
    response = client.get("/api/invalid-endpoint")
    assert response.status_code == 404


def test_research_with_context():
    """Test research endpoint with context."""
    payload = {
        "query": "AI in healthcare",
        "context": {
            "focus": "diagnostics",
            "region": "North America"
        },
        "include_evaluation": False
    }
    response = client.post("/api/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["query"] == "AI in healthcare"


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling of concurrent requests."""
    import asyncio
    import httpx
    
    async def make_request():
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/research", json={
                "query": "concurrent test",
                "include_evaluation": False
            })
            return response.status_code
    
    # Make 5 concurrent requests
    tasks = [make_request() for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    # All should succeed
    assert all(status == 200 for status in results)