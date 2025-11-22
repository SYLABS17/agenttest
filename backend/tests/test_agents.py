"""Tests for agent modules."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents import ManagerAgent, BingSearchAgent, AISearchAgent
from backend.agents.base_agent import AgentMessage, AgentStatus


@pytest.mark.asyncio
async def test_bing_search_agent_dummy_mode():
    """Test BingSearchAgent in dummy mode."""
    agent = BingSearchAgent()
    assert agent.dummy_mode == True  # Should default to dummy mode
    
    # Test search functionality
    query = "renewable energy in Africa"
    results = await agent.search(query)
    
    assert isinstance(results, list)
    assert len(results) > 0
    assert all('title' in r and 'url' in r for r in results)


@pytest.mark.asyncio
async def test_ai_search_agent_dummy_mode():
    """Test AISearchAgent in dummy mode."""
    agent = AISearchAgent()
    assert agent.dummy_mode == True
    
    # Test search functionality
    query = "generative AI journalism"
    results = await agent.search(query)
    
    assert isinstance(results, list)
    assert len(results) > 0
    assert all('title' in r and 'content' in r for r in results)


@pytest.mark.asyncio
async def test_manager_agent_orchestration():
    """Test ManagerAgent orchestration capabilities."""
    manager = ManagerAgent()
    
    # Test orchestration
    query = "Impact of AI on healthcare"
    chat_history, report = await manager.orchestrate_research(query)
    
    assert isinstance(chat_history, list)
    assert len(chat_history) > 0
    assert isinstance(report, str)
    assert len(report) > 0
    assert query in report


@pytest.mark.asyncio
async def test_agent_message_creation():
    """Test AgentMessage creation and serialization."""
    message = AgentMessage(
        agent_name="TestAgent",
        content="Test content",
        metadata={"test": "value"}
    )
    
    assert message.agent_name == "TestAgent"
    assert message.content == "Test content"
    assert message.metadata == {"test": "value"}
    assert message.id is not None
    assert message.timestamp is not None
    
    # Test serialization
    msg_dict = message.to_dict()
    assert msg_dict["agent_name"] == "TestAgent"
    assert msg_dict["content"] == "Test content"
    assert msg_dict["metadata"] == {"test": "value"}


@pytest.mark.asyncio
async def test_agent_metrics():
    """Test agent metrics tracking."""
    agent = BingSearchAgent()
    
    # Initial state
    assert agent.get_metrics()["total_queries"] == 0
    assert agent.get_metrics()["successful_queries"] == 0
    
    # Execute a query
    await agent.execute("test query")
    
    # Check metrics updated
    metrics = agent.get_metrics()
    assert metrics["total_queries"] == 1
    assert metrics["successful_queries"] == 1
    assert metrics["average_latency_ms"] > 0


@pytest.mark.asyncio
async def test_agent_health_check():
    """Test agent health check functionality."""
    agent = AISearchAgent()
    health = await agent.health_check()
    
    assert "agent" in health
    assert "status" in health
    assert "healthy" in health
    assert "metrics" in health
    assert health["agent"] == "AISearchAgent"


@pytest.mark.asyncio
async def test_manager_agent_health_check():
    """Test manager agent comprehensive health check."""
    manager = ManagerAgent()
    health = await manager.health_check()
    
    assert "overall_healthy" in health
    assert "agents" in health
    assert "manager" in health["agents"]
    assert "bing_agent" in health["agents"]
    assert "ai_search_agent" in health["agents"]


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in agent execution."""
    agent = BingSearchAgent()
    
    # Mock search to raise an error
    with patch.object(agent, 'search', side_effect=Exception("Test error")):
        result = await agent.execute("test query")
        
        assert result.metadata["status"] == "error"
        assert "Test error" in result.content
        assert agent.get_metrics()["failed_queries"] == 1


@pytest.mark.asyncio
async def test_parallel_agent_execution():
    """Test parallel execution of multiple agents."""
    manager = ManagerAgent()
    
    # Time the execution to ensure it's parallel
    import time
    start = time.time()
    
    query = "test parallel execution"
    chat_history, report = await manager.orchestrate_research(query)
    
    elapsed = time.time() - start
    
    # Both agents should execute in parallel, so total time should be
    # close to the slowest agent, not the sum
    assert elapsed < 3.0  # Should be much less than sequential execution
    assert len(chat_history) > 2  # Should have responses from multiple agents


@pytest.mark.asyncio
async def test_conversation_history():
    """Test conversation history maintenance."""
    agent = BingSearchAgent()
    
    # Execute multiple queries
    queries = ["query1", "query2", "query3"]
    for q in queries:
        await agent.execute(q)
    
    # Check history
    assert len(agent.conversation_history) == 3
    assert all(isinstance(m, AgentMessage) for m in agent.conversation_history)
    
    # Test clear history
    agent.clear_history()
    assert len(agent.conversation_history) == 0