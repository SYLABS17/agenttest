"""
Tests for agent implementations
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentResponse, AgentRole, AgentStatus, AgentMetrics
from agents.manager_agent import ManagerAgent
from agents.bing_agent import BingSearchAgent
from agents.ai_search_agent import AISearchAgent


class TestBaseAgent:
    """Test base agent functionality"""
    
    class ConcreteAgent(BaseAgent):
        """Concrete implementation for testing"""
        
        async def process(self, query: str, context=None):
            return AgentResponse(
                agent_id=self.id,
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                content=f"Processed: {query}",
                confidence_score=0.8
            )
        
        async def validate_input(self, query: str, context=None):
            return bool(query and query.strip())
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization"""
        agent = self.ConcreteAgent(AgentRole.MANAGER, "TestAgent")
        assert agent.role == AgentRole.MANAGER
        assert agent.name == "TestAgent"
        assert agent.status == AgentStatus.IDLE
        assert agent.id is not None
    
    @pytest.mark.asyncio
    async def test_agent_execute_success(self):
        """Test successful agent execution"""
        agent = self.ConcreteAgent(AgentRole.MANAGER)
        response = await agent.execute("Test query")
        
        assert response.status == AgentStatus.COMPLETED
        assert response.content == "Processed: Test query"
        assert response.confidence_score == 0.8
        assert response.processing_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_agent_execute_invalid_input(self):
        """Test agent execution with invalid input"""
        agent = self.ConcreteAgent(AgentRole.MANAGER)
        response = await agent.execute("")  # Empty query
        
        assert response.status == AgentStatus.FAILED
        assert response.error is not None
        assert "Invalid input" in response.error
    
    @pytest.mark.asyncio
    async def test_agent_metrics(self):
        """Test agent metrics tracking"""
        agent = self.ConcreteAgent(AgentRole.MANAGER)
        
        # Execute multiple requests
        await agent.execute("Query 1")
        await agent.execute("Query 2")
        await agent.execute("")  # This should fail
        
        metrics = agent.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["successful_requests"] == 2
        assert metrics["failed_requests"] == 1
        assert metrics["success_rate"] == 2/3
    
    @pytest.mark.asyncio
    async def test_agent_reset(self):
        """Test agent reset functionality"""
        agent = self.ConcreteAgent(AgentRole.MANAGER)
        await agent.execute("Test query")
        
        # Reset agent
        await agent.reset()
        
        assert agent.status == AgentStatus.IDLE
        assert len(agent.message_history) == 0
        assert agent.current_task_id is None


class TestManagerAgent:
    """Test manager agent functionality"""
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test manager agent initialization"""
        worker1 = Mock()
        worker2 = Mock()
        manager = ManagerAgent(worker_agents=[worker1, worker2])
        
        assert manager.role == AgentRole.MANAGER
        assert len(manager.worker_agents) == 2
        assert manager.max_iterations > 0
    
    @pytest.mark.asyncio
    async def test_manager_add_remove_workers(self):
        """Test adding and removing worker agents"""
        manager = ManagerAgent()
        assert len(manager.worker_agents) == 0
        
        # Add worker
        worker = Mock()
        worker.id = "worker-001"
        manager.add_worker_agent(worker)
        assert len(manager.worker_agents) == 1
        
        # Remove worker
        manager.remove_worker_agent("worker-001")
        assert len(manager.worker_agents) == 0
    
    @pytest.mark.asyncio
    async def test_manager_validate_input(self):
        """Test manager input validation"""
        manager = ManagerAgent()
        
        # Empty query
        assert not await manager.validate_input("")
        
        # No workers
        assert not await manager.validate_input("Valid query")
        
        # Valid input
        manager.add_worker_agent(Mock())
        assert await manager.validate_input("Valid query")
    
    @pytest.mark.asyncio
    @patch('agents.manager_agent.ManagerAgent._distribute_to_workers')
    @patch('agents.manager_agent.ManagerAgent._collaborative_synthesis')
    @patch('agents.manager_agent.ManagerAgent._generate_final_report')
    async def test_manager_process(self, mock_report, mock_synthesis, mock_distribute):
        """Test manager processing pipeline"""
        # Setup mocks
        mock_distribute.return_value = [
            AgentResponse(
                agent_id="worker-001",
                agent_role=AgentRole.BING_SEARCH,
                status=AgentStatus.COMPLETED,
                content="Bing results",
                sources=[],
                confidence_score=0.8
            )
        ]
        mock_synthesis.return_value = {
            "initial_responses": [],
            "discussion_rounds": [],
            "consensus_points": [],
            "disagreement_points": []
        }
        mock_report.return_value = {
            "title": "Test Report",
            "executive_summary": "Summary"
        }
        
        worker = Mock()
        manager = ManagerAgent(worker_agents=[worker])
        
        response = await manager.process("Test query")
        
        assert response.status == AgentStatus.COMPLETED
        assert response.content is not None
        assert mock_distribute.called
        assert mock_synthesis.called
        assert mock_report.called


class TestBingSearchAgent:
    """Test Bing search agent functionality"""
    
    @pytest.mark.asyncio
    async def test_bing_agent_initialization(self):
        """Test Bing agent initialization"""
        agent = BingSearchAgent()
        assert agent.role == AgentRole.BING_SEARCH
        assert agent.max_results > 0
        assert "web" in agent.search_types
    
    @pytest.mark.asyncio
    async def test_bing_agent_validate_input(self):
        """Test Bing agent input validation"""
        agent = BingSearchAgent()
        
        # Valid query
        assert await agent.validate_input("Valid search query")
        
        # Empty query
        assert not await agent.validate_input("")
        
        # Too long query
        assert not await agent.validate_input("x" * 1001)
    
    @pytest.mark.asyncio
    @patch('agents.bing_agent.BingSearchAgent._perform_search')
    async def test_bing_agent_process(self, mock_search):
        """Test Bing agent processing"""
        mock_search.return_value = [
            {
                "type": "web",
                "title": "Test Result",
                "url": "http://example.com",
                "snippet": "Test snippet",
                "relevance_score": 0.9
            }
        ]
        
        agent = BingSearchAgent()
        response = await agent.process("Test query")
        
        assert response.status == AgentStatus.COMPLETED
        assert response.content is not None
        assert "summary" in response.content
        assert "detailed_results" in response.content
        assert len(response.sources) > 0
        assert response.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_bing_generate_results(self):
        """Test Bing result generation"""
        agent = BingSearchAgent()
        
        # Test web results
        web_results = agent._generate_web_results("test query", 3)
        assert len(web_results) == 3
        assert all(r["type"] == "web" for r in web_results)
        
        # Test news results
        news_results = agent._generate_news_results("test query", 2)
        assert len(news_results) == 2
        assert all(r["type"] == "news" for r in news_results)
        
        # Test academic results
        academic_results = agent._generate_academic_results("test query", 1)
        assert len(academic_results) == 1
        assert all(r["type"] == "academic" for r in academic_results)


class TestAISearchAgent:
    """Test AI Search agent functionality"""
    
    @pytest.mark.asyncio
    async def test_ai_search_initialization(self):
        """Test AI Search agent initialization"""
        agent = AISearchAgent()
        assert agent.role == AgentRole.AI_SEARCH
        assert agent.max_results > 0
        assert "semantic" in agent.search_modes
        assert len(agent.kb_categories) > 0
    
    @pytest.mark.asyncio
    async def test_ai_search_validate_input(self):
        """Test AI Search input validation"""
        agent = AISearchAgent()
        
        # Valid query
        assert await agent.validate_input("Valid search query")
        
        # Empty query
        assert not await agent.validate_input("")
        
        # Too long query
        assert not await agent.validate_input("x" * 1001)
    
    @pytest.mark.asyncio
    @patch('agents.ai_search_agent.AISearchAgent._perform_semantic_search')
    @patch('agents.ai_search_agent.AISearchAgent._perform_vector_search')
    async def test_ai_search_process(self, mock_vector, mock_semantic):
        """Test AI Search processing"""
        mock_semantic.return_value = [
            {
                "id": "doc-001",
                "title": "Test Document",
                "category": "research_papers",
                "content": "Test content",
                "relevance_score": 0.95,
                "semantic_score": 0.93
            }
        ]
        mock_vector.return_value = []
        
        agent = AISearchAgent()
        response = await agent.process("Test query")
        
        assert response.status == AgentStatus.COMPLETED
        assert response.content is not None
        assert "summary" in response.content
        assert "insights" in response.content
        assert response.confidence_score > 0
        assert mock_semantic.called
        assert mock_vector.called
    
    @pytest.mark.asyncio
    async def test_ai_search_combine_results(self):
        """Test combining search results"""
        agent = AISearchAgent()
        
        semantic_results = [
            {"id": "doc-1", "relevance_score": 0.9, "search_type": "semantic"},
            {"id": "doc-2", "relevance_score": 0.8, "search_type": "semantic"}
        ]
        
        vector_results = [
            {"id": "doc-2", "relevance_score": 0.85, "search_type": "vector"},
            {"id": "doc-3", "relevance_score": 0.7, "search_type": "vector"}
        ]
        
        combined = agent._combine_search_results(semantic_results, vector_results)
        
        # Should have 3 unique documents
        assert len(combined) == 3
        # doc-2 should have both search methods
        doc2 = next(d for d in combined if d["id"] == "doc-2")
        assert "semantic" in doc2["search_methods"]
        assert "vector" in doc2["search_methods"]
    
    @pytest.mark.asyncio
    async def test_ai_search_generate_insights(self):
        """Test insight generation"""
        agent = AISearchAgent()
        
        results = [
            {
                "category": "research_papers",
                "tags": ["ai", "research"],
                "combined_score": 0.9
            },
            {
                "category": "best_practices",
                "tags": ["implementation", "guide"],
                "combined_score": 0.8
            }
        ]
        
        insights = await agent._generate_insights(results, "test query")
        
        assert "key_themes" in insights
        assert "consensus_areas" in insights
        assert "knowledge_gaps" in insights
        assert "actionable_recommendations" in insights
        assert "confidence_level" in insights


class TestAgentIntegration:
    """Test agent integration and collaboration"""
    
    @pytest.mark.asyncio
    async def test_manager_with_workers_integration(self):
        """Test manager coordinating with worker agents"""
        # Create worker agents
        bing_agent = BingSearchAgent()
        ai_search_agent = AISearchAgent()
        
        # Create manager with workers
        manager = ManagerAgent(worker_agents=[bing_agent, ai_search_agent])
        
        # Mock the worker responses to avoid actual API calls
        with patch.object(bing_agent, 'execute') as mock_bing:
            with patch.object(ai_search_agent, 'execute') as mock_ai:
                mock_bing.return_value = AgentResponse(
                    agent_id="bing-001",
                    agent_role=AgentRole.BING_SEARCH,
                    status=AgentStatus.COMPLETED,
                    content={"summary": "Bing results"},
                    sources=[],
                    confidence_score=0.8
                )
                mock_ai.return_value = AgentResponse(
                    agent_id="ai-001",
                    agent_role=AgentRole.AI_SEARCH,
                    status=AgentStatus.COMPLETED,
                    content={"summary": "AI Search results"},
                    sources=[],
                    confidence_score=0.9
                )
                
                # Execute research
                response = await manager.execute("Integration test query")
                
                assert response.status == AgentStatus.COMPLETED
                assert response.content is not None
                assert mock_bing.called
                assert mock_ai.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])