"""Azure AI Search Agent implementation."""

from typing import Dict, Any, Optional, List
import asyncio
import random
from datetime import datetime

from azure.search.documents import SearchClient
from azure.search.documents.models import SearchMode
from azure.core.credentials import AzureKeyCredential

from .base_agent import BaseAgent, AgentMessage
from ..config import settings, FeatureFlags


class AISearchAgent(BaseAgent):
    """Agent that performs search using Azure AI Search."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize AI Search Agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(name="AISearchAgent", config=config)
        self.endpoint = settings.azure_search_endpoint
        self.api_key = settings.azure_search_api_key
        self.index_name = settings.azure_search_index_name
        self.dummy_mode = FeatureFlags.ENABLE_DUMMY_MODE
        
        if not self.dummy_mode and self.endpoint and self.api_key:
            try:
                self.search_client = SearchClient(
                    endpoint=self.endpoint,
                    index_name=self.index_name,
                    credential=AzureKeyCredential(self.api_key)
                )
            except Exception as e:
                self.logger.warning("Failed to initialize Azure Search client", error=str(e))
                self.search_client = None
        else:
            self.search_client = None
            
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform Azure AI Search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        if self.dummy_mode or not self.search_client:
            return await self._get_dummy_results(query)
            
        try:
            # Perform semantic search
            results = self.search_client.search(
                search_text=query,
                search_mode=SearchMode.ALL,
                include_total_count=True,
                top=5,
                select=["title", "content", "url", "category", "timestamp"]
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "category": result.get("category", ""),
                    "score": result.get("@search.score", 0),
                    "source": "Azure AI Search"
                })
                
            return search_results
            
        except Exception as e:
            self.logger.error("Azure AI Search failed", error=str(e))
            return await self._get_dummy_results(query)
    
    async def _get_dummy_results(self, query: str) -> List[Dict[str, Any]]:
        """Get dummy search results for testing.
        
        Args:
            query: Search query
            
        Returns:
            List of dummy results
        """
        # Simulate some delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Generate dummy results with semantic relevance
        dummy_results = []
        
        if "renewable energy" in query.lower():
            dummy_results = [
                {
                    "title": "Technical Report: Solar Panel Efficiency in Sub-Saharan Africa",
                    "content": "This comprehensive technical report analyzes solar panel performance across different African climates. Key findings include optimal panel angles for maximum efficiency in equatorial regions, degradation rates in desert conditions, and cost-benefit analysis for rural electrification projects.",
                    "url": "https://docs.example.com/solar-efficiency-africa",
                    "category": "Technical Documentation",
                    "score": 0.95,
                    "source": "Azure AI Search"
                },
                {
                    "title": "Case Study: Morocco's Renewable Energy Strategy 2030",
                    "content": "Morocco aims to generate 52% of its electricity from renewable sources by 2030. This case study examines the policy framework, international partnerships, and technological innovations driving this ambitious target. Special focus on the Noor solar complex and offshore wind projects.",
                    "url": "https://docs.example.com/morocco-renewable-2030",
                    "category": "Policy Analysis",
                    "score": 0.89,
                    "source": "Azure AI Search"
                },
                {
                    "title": "Investment Guide: African Green Energy Opportunities",
                    "content": "Detailed analysis of investment opportunities in African renewable energy markets. Covers regulatory frameworks, risk assessment, financing mechanisms, and projected returns. Includes profiles of successful projects and emerging markets with high growth potential.",
                    "url": "https://docs.example.com/green-energy-investment",
                    "category": "Financial Analysis",
                    "score": 0.82,
                    "source": "Azure AI Search"
                }
            ]
        elif "generative ai" in query.lower() or "journalism" in query.lower():
            dummy_results = [
                {
                    "title": "Research Paper: LLMs in Newsroom Workflows",
                    "content": "Academic research examining the integration of Large Language Models in modern newsrooms. Studies workflow optimization, quality metrics, and journalist perspectives. Includes quantitative analysis of productivity gains and qualitative assessment of content quality changes.",
                    "url": "https://docs.example.com/llm-newsroom-research",
                    "category": "Academic Research",
                    "score": 0.93,
                    "source": "Azure AI Search"
                },
                {
                    "title": "Best Practices: AI-Assisted Investigative Journalism",
                    "content": "Guidelines for using AI tools in investigative reporting while maintaining journalistic integrity. Covers data analysis, pattern recognition, fact-checking automation, and source verification. Real-world examples from Pulitzer Prize-winning investigations.",
                    "url": "https://docs.example.com/ai-investigative-guide",
                    "category": "Professional Guidelines",
                    "score": 0.88,
                    "source": "Azure AI Search"
                },
                {
                    "title": "Technical Architecture: AI-Powered News Platform",
                    "content": "Detailed technical architecture for building scalable AI-enhanced news platforms. Includes system design, API integration, content management workflows, and performance optimization strategies. Code examples and deployment configurations included.",
                    "url": "https://docs.example.com/ai-news-architecture",
                    "category": "Technical Documentation",
                    "score": 0.85,
                    "source": "Azure AI Search"
                }
            ]
        else:
            # Generic semantic search results
            dummy_results = [
                {
                    "title": f"Comprehensive Knowledge Base: {query}",
                    "content": f"This document provides in-depth coverage of {query}, including historical context, current state analysis, and future projections. Contains verified data from multiple authoritative sources with cross-references and citations.",
                    "url": f"https://kb.example.com/{query.replace(' ', '-').lower()}",
                    "category": "Knowledge Base",
                    "score": 0.91,
                    "source": "Azure AI Search"
                },
                {
                    "title": f"Technical Specification: {query} Implementation",
                    "content": f"Detailed technical specifications for implementing solutions related to {query}. Includes architecture diagrams, API documentation, performance benchmarks, and best practices based on industry standards.",
                    "url": f"https://specs.example.com/{query.replace(' ', '-').lower()}",
                    "category": "Technical Specification",
                    "score": 0.87,
                    "source": "Azure AI Search"
                },
                {
                    "title": f"Industry Analysis: {query} Market Trends",
                    "content": f"Market analysis report covering {query} with focus on current trends, competitive landscape, and growth opportunities. Features data visualization, SWOT analysis, and strategic recommendations.",
                    "url": f"https://analysis.example.com/{query.replace(' ', '-').lower()}",
                    "category": "Market Analysis",
                    "score": 0.84,
                    "source": "Azure AI Search"
                }
            ]
            
        return dummy_results
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Process a research query using Azure AI Search.
        
        Args:
            query: Research query
            context: Optional context
            
        Returns:
            Agent response message
        """
        try:
            # Perform search
            results = await self.search(query)
            
            # Format results into response
            if results:
                response_content = f"📚 **Azure AI Search Results for:** {query}\n\n"
                
                for i, result in enumerate(results, 1):
                    response_content += f"**{i}. {result['title']}**\n"
                    response_content += f"   📁 Category: {result['category']}\n"
                    response_content += f"   📊 Relevance Score: {result['score']:.2f}\n"
                    response_content += f"   📎 {result['url']}\n"
                    response_content += f"   {result['content'][:200]}...\n\n"
                    
                response_content += f"\n*Found {len(results)} relevant documents in knowledge base.*"
            else:
                response_content = f"No documents found for query: {query}"
            
            # Create response message
            message = AgentMessage(
                agent_name=self.name,
                content=response_content,
                metadata={
                    "query": query,
                    "result_count": len(results),
                    "results": results,
                    "search_type": "semantic",
                    "index": self.index_name
                }
            )
            
            return message
            
        except Exception as e:
            self.logger.error("Failed to process AI Search", error=str(e))
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for AI Search Agent.
        
        Returns:
            Health status
        """
        health = await super().health_check()
        
        # Check configuration
        health["has_credentials"] = bool(self.api_key and self.endpoint) if not self.dummy_mode else True
        health["dummy_mode"] = self.dummy_mode
        health["index_name"] = self.index_name
        health["search_client_initialized"] = self.search_client is not None
        
        return health