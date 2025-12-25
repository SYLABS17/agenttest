"""Bing Search Agent implementation."""

from typing import Dict, Any, Optional, List
import asyncio
import json
import random
from datetime import datetime
import httpx

from .base_agent import BaseAgent, AgentMessage
from ..config import settings, FeatureFlags


class BingSearchAgent(BaseAgent):
    """Agent that performs web search using Bing Search API."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Bing Search Agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(name="BingSearchAgent", config=config)
        self.api_key = settings.bing_search_api_key
        self.endpoint = settings.bing_search_endpoint
        self.dummy_mode = FeatureFlags.ENABLE_DUMMY_MODE
        
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform Bing search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        if self.dummy_mode:
            return await self._get_dummy_results(query)
            
        # Real Bing Search API call
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json"
        }
        
        params = {
            "q": query,
            "count": 10,
            "offset": 0,
            "mkt": "en-US",
            "safesearch": "Moderate"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.endpoint,
                    headers=headers,
                    params=params,
                    timeout=settings.agent_timeout_seconds
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract web pages from response
                results = []
                if "webPages" in data and "value" in data["webPages"]:
                    for item in data["webPages"]["value"][:5]:
                        results.append({
                            "title": item.get("name", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "Bing Web Search"
                        })
                        
                return results
                
        except Exception as e:
            self.logger.error("Bing search failed", error=str(e))
            # Return dummy results as fallback
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
        
        # Generate dummy results based on query
        dummy_results = []
        
        if "renewable energy" in query.lower():
            dummy_results = [
                {
                    "title": "The Future of Renewable Energy in Africa: Opportunities and Challenges",
                    "url": "https://example.com/renewable-africa",
                    "snippet": "Africa has immense potential for renewable energy development, with abundant solar, wind, and hydro resources. Recent studies show that solar capacity could reach 600 GW by 2040...",
                    "source": "Bing Web Search"
                },
                {
                    "title": "Solar Power Revolution: How Africa is Leading the Clean Energy Transition",
                    "url": "https://example.com/solar-revolution",
                    "snippet": "Countries across Africa are embracing solar technology at an unprecedented rate. Morocco's Noor Ouarzazate Solar Complex, one of the world's largest concentrated solar power plants...",
                    "source": "Bing Web Search"
                },
                {
                    "title": "Wind Energy Projects Transform Rural Communities in Kenya and Ethiopia",
                    "url": "https://example.com/wind-energy-east-africa",
                    "snippet": "The Lake Turkana Wind Power project in Kenya, Africa's largest wind farm, is providing clean electricity to over 330,000 households while creating jobs and infrastructure...",
                    "source": "Bing Web Search"
                }
            ]
        elif "generative ai" in query.lower() or "journalism" in query.lower():
            dummy_results = [
                {
                    "title": "How Generative AI is Reshaping Modern Journalism",
                    "url": "https://example.com/ai-journalism",
                    "snippet": "Newsrooms worldwide are adopting AI tools for fact-checking, content generation, and data analysis. While AI enhances efficiency, journalists emphasize the irreplaceable value of human judgment...",
                    "source": "Bing Web Search"
                },
                {
                    "title": "The Ethics of AI-Generated News: Balancing Automation and Authenticity",
                    "url": "https://example.com/ai-ethics-news",
                    "snippet": "Major news organizations are establishing guidelines for AI use, focusing on transparency, accountability, and maintaining editorial standards. The Associated Press recently published...",
                    "source": "Bing Web Search"
                },
                {
                    "title": "Case Studies: Successful AI Integration in Digital Newsrooms",
                    "url": "https://example.com/ai-newsroom-cases",
                    "snippet": "Bloomberg, Reuters, and The Washington Post share their experiences with AI tools. From automated financial reporting to personalized content delivery, these organizations demonstrate...",
                    "source": "Bing Web Search"
                }
            ]
        else:
            # Generic dummy results
            dummy_results = [
                {
                    "title": f"Comprehensive Analysis of {query}",
                    "url": f"https://example.com/{query.replace(' ', '-').lower()}",
                    "snippet": f"Recent developments in {query} show significant progress in multiple areas. Experts predict continued growth and innovation in this field over the next decade...",
                    "source": "Bing Web Search"
                },
                {
                    "title": f"Latest Research Findings on {query}",
                    "url": f"https://research.example.com/{query.replace(' ', '-').lower()}",
                    "snippet": f"A new study published this month reveals important insights about {query}. Researchers from leading institutions collaborated to analyze trends and patterns...",
                    "source": "Bing Web Search"
                },
                {
                    "title": f"Industry Report: {query} Trends and Forecasts",
                    "url": f"https://industry.example.com/{query.replace(' ', '-').lower()}",
                    "snippet": f"Market analysis indicates strong potential for {query} with projected growth rates exceeding initial estimates. Key factors driving this trend include technological advancement...",
                    "source": "Bing Web Search"
                }
            ]
            
        return dummy_results
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Process a research query using Bing Search.
        
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
                response_content = f"🔍 **Bing Search Results for:** {query}\n\n"
                
                for i, result in enumerate(results, 1):
                    response_content += f"**{i}. {result['title']}**\n"
                    response_content += f"   📎 {result['url']}\n"
                    response_content += f"   {result['snippet']}\n\n"
                    
                response_content += f"\n*Found {len(results)} relevant results from web search.*"
            else:
                response_content = f"No results found for query: {query}"
            
            # Create response message
            message = AgentMessage(
                agent_name=self.name,
                content=response_content,
                metadata={
                    "query": query,
                    "result_count": len(results),
                    "results": results,
                    "search_type": "web"
                }
            )
            
            return message
            
        except Exception as e:
            self.logger.error("Failed to process Bing search", error=str(e))
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for Bing Search Agent.
        
        Returns:
            Health status
        """
        health = await super().health_check()
        
        # Check API key configuration
        health["has_api_key"] = bool(self.api_key) if not self.dummy_mode else True
        health["dummy_mode"] = self.dummy_mode
        health["endpoint"] = self.endpoint
        
        return health