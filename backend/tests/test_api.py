"""
Tests for the FastAPI application endpoints
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from agents.base_agent import AgentResponse, AgentRole, AgentStatus


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_manager_response():
    """Create mock manager agent response"""
    return AgentResponse(
        agent_id="test-manager-001",
        agent_role=AgentRole.MANAGER,
        status=AgentStatus.COMPLETED,
        content={
            "title": "Test Research Report",
            "executive_summary": "This is a test summary",
            "key_findings": ["Finding 1", "Finding 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        },
        sources=[
            {"title": "Source 1", "url": "http://example.com/1"},
            {"title": "Source 2", "url": "http://example.com/2"}
        ],
        confidence_score=0.85,
        processing_time_ms=1500.0
    )


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "environment" in data
        assert "version" in data
        assert "services" in data
    
    def test_health_check_structure(self, client):
        """Test health check response structure"""
        response = client.get("/healthz")
        data = response.json()
        assert data["version"] == "1.0.0"
        assert "manager_agent" in data["services"]
        assert "evaluation_service" in data["services"]
        assert "observability" in data["services"]


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AI Research System API"
        assert data["version"] == "1.0.0"
        assert data["documentation"] == "/docs"


class TestResearchEndpoint:
    """Test research endpoint"""
    
    @patch('main.manager_agent')
    def test_research_success(self, mock_manager, client, mock_manager_response):
        """Test successful research request"""
        # Setup mock
        mock_manager.execute = AsyncMock(return_value=mock_manager_response)
        
        # Make request
        response = client.post("/research", json={
            "query": "Test research query",
            "evaluate": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["query"] == "Test research query"
        assert data["status"] == "completed"
        assert "report" in data
        assert data["report"]["title"] == "Test Research Report"
    
    def test_research_invalid_query(self, client):
        """Test research with invalid query"""
        response = client.post("/research", json={
            "query": "",  # Empty query
            "evaluate": True
        })
        assert response.status_code == 422  # Validation error
    
    def test_research_with_timeout(self, client):
        """Test research with custom timeout"""
        response = client.post("/research", json={
            "query": "Test query with timeout",
            "timeout_seconds": 5
        })
        # Will fail if manager not initialized, which is expected in test
        assert response.status_code in [200, 503]
    
    @patch('main.manager_agent', None)
    def test_research_no_manager(self, client):
        """Test research when manager agent is not initialized"""
        response = client.post("/research", json={
            "query": "Test query",
            "evaluate": False
        })
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "not initialized" in data["detail"]


class TestAgentsEndpoint:
    """Test agents endpoints"""
    
    def test_list_agents_empty(self, client):
        """Test listing agents when none available"""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('main.manager_agent')
    def test_list_agents_with_data(self, mock_manager, client):
        """Test listing agents with mock data"""
        # Setup mock agents
        mock_agent = Mock()
        mock_agent.id = "test-agent-001"
        mock_agent.name = "Test Agent"
        mock_agent.role.value = "test_role"
        mock_agent.status.value = "idle"
        mock_agent.get_metrics.return_value = {
            "total_requests": 10,
            "success_rate": 0.9
        }
        
        mock_manager.id = "manager-001"
        mock_manager.name = "Manager"
        mock_manager.role.value = "manager"
        mock_manager.status.value = "idle"
        mock_manager.get_metrics.return_value = {}
        mock_manager.worker_agents = [mock_agent]
        
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Manager + worker
        assert data[0]["name"] == "Manager"
        assert data[1]["name"] == "Test Agent"
    
    @patch('main.manager_agent', None)
    def test_reset_agents_no_manager(self, client):
        """Test resetting agents when manager not initialized"""
        response = client.post("/agents/reset")
        assert response.status_code == 503


class TestMetricsEndpoint:
    """Test metrics endpoint"""
    
    def test_get_metrics(self, client):
        """Test getting system metrics"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "observability_metrics" in data
        assert "evaluation_summary" in data
        assert "agent_metrics" in data
        assert isinstance(data["agent_metrics"], list)


class TestEvaluationEndpoints:
    """Test evaluation-related endpoints"""
    
    def test_get_evaluation_history_empty(self, client):
        """Test getting evaluation history when empty"""
        response = client.get("/evaluation/history")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "evaluations" in data
    
    def test_get_evaluation_history_with_limit(self, client):
        """Test getting evaluation history with limit parameter"""
        response = client.get("/evaluation/history?limit=5")
        assert response.status_code == 200
    
    def test_export_evaluation_not_found(self, client):
        """Test exporting non-existent evaluation"""
        response = client.post("/evaluation/export?evaluation_id=999")
        assert response.status_code in [404, 503]


class TestConfigEndpoint:
    """Test configuration endpoint"""
    
    def test_get_config(self, client):
        """Test getting configuration"""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "version" in data
        assert "debug" in data
        assert "evaluation_enabled" in data
        assert "agent_timeout" in data
        assert "observability_configured" in data
        assert "azure_configured" in data


class TestTestEndpoints:
    """Test the test/demo endpoints"""
    
    def test_get_test_queries(self, client):
        """Test getting test queries"""
        response = client.get("/test/queries")
        assert response.status_code == 200
        data = response.json()
        assert "queries" in data
        assert isinstance(data["queries"], list)
        assert len(data["queries"]) > 0
        assert "Future of renewable energy in Africa" in data["queries"]
    
    @patch('main.manager_agent')
    def test_simulate_research(self, mock_manager, client, mock_manager_response):
        """Test simulating research with test query"""
        mock_manager.execute = AsyncMock(return_value=mock_manager_response)
        
        response = client.post("/test/simulate?query_index=0")
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "status" in data
    
    def test_simulate_research_invalid_index(self, client):
        """Test simulating research with invalid index"""
        response = client.post("/test/simulate?query_index=999")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid query index" in data["detail"]


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method"""
        response = client.get("/research")  # Should be POST
        assert response.status_code == 405
    
    def test_validation_error(self, client):
        """Test validation error for malformed request"""
        response = client.post("/research", json={
            "invalid_field": "value"
        })
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])