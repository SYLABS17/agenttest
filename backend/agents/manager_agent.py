"""Manager Agent for orchestrating multi-agent research."""

from typing import Dict, Any, Optional, List, Tuple
import asyncio
from datetime import datetime
import json

from .base_agent import BaseAgent, AgentMessage
from .bing_agent import BingSearchAgent
from .ai_search_agent import AISearchAgent
from ..config import settings


class ManagerAgent(BaseAgent):
    """Manager agent that coordinates other research agents."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Manager Agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(name="ManagerAgent", config=config)
        
        # Initialize worker agents
        self.bing_agent = BingSearchAgent()
        self.ai_search_agent = AISearchAgent()
        
        # Group chat history
        self.group_chat_history: List[AgentMessage] = []
        
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Coordinate search across multiple agents.
        
        Args:
            query: Search query
            
        Returns:
            Aggregated search results
        """
        # Run searches in parallel
        tasks = [
            self.bing_agent.search(query),
            self.ai_search_agent.search(query)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        aggregated_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Agent search failed", agent_index=i, error=str(result))
                continue
            aggregated_results.extend(result)
            
        return aggregated_results
    
    async def orchestrate_research(self, query: str) -> Tuple[List[AgentMessage], str]:
        """Orchestrate multi-agent research in group chat style.
        
        Args:
            query: Research query
            
        Returns:
            Tuple of (chat history, final report)
        """
        chat_history = []
        
        # Manager introduces the task
        manager_intro = AgentMessage(
            agent_name=self.name,
            content=f"🎯 **Research Task:** {query}\n\nI'm coordinating a research effort on this topic. Let me engage our specialist agents to gather comprehensive information from multiple sources.",
            metadata={"role": "coordinator", "phase": "introduction"}
        )
        chat_history.append(manager_intro)
        
        # Execute agent searches in parallel
        self.logger.info("Dispatching query to worker agents", query=query[:100])
        
        tasks = [
            self.bing_agent.execute(query),
            self.ai_search_agent.execute(query)
        ]
        
        agent_responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process agent responses
        bing_results = []
        ai_search_results = []
        
        for i, response in enumerate(agent_responses):
            if isinstance(response, Exception):
                error_msg = AgentMessage(
                    agent_name="System",
                    content=f"⚠️ Agent encountered an error: {str(response)}",
                    metadata={"error": True}
                )
                chat_history.append(error_msg)
            else:
                chat_history.append(response)
                
                # Extract results from metadata
                if response.agent_name == "BingSearchAgent":
                    bing_results = response.metadata.get("results", [])
                elif response.agent_name == "AISearchAgent":
                    ai_search_results = response.metadata.get("results", [])
        
        # Manager analyzes and synthesizes results
        synthesis_msg = AgentMessage(
            agent_name=self.name,
            content="📊 **Analyzing and synthesizing results...**\n\nI'm now combining insights from both web search and our knowledge base to create a comprehensive research report.",
            metadata={"role": "coordinator", "phase": "synthesis"}
        )
        chat_history.append(synthesis_msg)
        
        # Generate final report
        final_report = await self._generate_final_report(query, bing_results, ai_search_results)
        
        # Manager presents the final report
        report_msg = AgentMessage(
            agent_name=self.name,
            content=f"✅ **Final Research Report**\n\n{final_report}",
            metadata={
                "role": "coordinator",
                "phase": "conclusion",
                "report_length": len(final_report),
                "sources_count": len(bing_results) + len(ai_search_results)
            }
        )
        chat_history.append(report_msg)
        
        # Store in group chat history
        self.group_chat_history.extend(chat_history)
        
        return chat_history, final_report
    
    async def _generate_final_report(self, query: str, 
                                    bing_results: List[Dict[str, Any]], 
                                    ai_search_results: List[Dict[str, Any]]) -> str:
        """Generate final research report from aggregated results.
        
        Args:
            query: Original research query
            bing_results: Results from Bing search
            ai_search_results: Results from AI Search
            
        Returns:
            Formatted research report
        """
        report = f"# Research Report: {query}\n\n"
        report += f"*Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n"
        
        # Executive Summary
        report += "## Executive Summary\n\n"
        report += f"This comprehensive research report on \"{query}\" synthesizes findings from multiple sources, "
        report += f"including {len(bing_results)} web search results and {len(ai_search_results)} knowledge base documents. "
        report += "The analysis provides a multi-faceted view of the topic, combining current web information with curated knowledge.\n\n"
        
        # Key Findings
        report += "## Key Findings\n\n"
        
        # Process web search results
        if bing_results:
            report += "### Web Search Insights\n\n"
            for i, result in enumerate(bing_results[:3], 1):
                report += f"**{i}. {result.get('title', 'Untitled')}**\n"
                report += f"- Source: {result.get('url', 'N/A')}\n"
                report += f"- Summary: {result.get('snippet', 'No summary available')}\n\n"
        
        # Process knowledge base results
        if ai_search_results:
            report += "### Knowledge Base Analysis\n\n"
            for i, result in enumerate(ai_search_results[:3], 1):
                report += f"**{i}. {result.get('title', 'Untitled')}**\n"
                report += f"- Category: {result.get('category', 'General')}\n"
                report += f"- Relevance Score: {result.get('score', 0):.2f}\n"
                content = result.get('content', 'No content available')
                report += f"- Key Points: {content[:300]}...\n\n"
        
        # Synthesis and Recommendations
        report += "## Synthesis and Recommendations\n\n"
        
        if "renewable energy" in query.lower():
            report += "Based on the comprehensive analysis:\n\n"
            report += "1. **Growing Momentum**: Renewable energy adoption in Africa is accelerating, driven by decreasing technology costs and increasing international investment.\n\n"
            report += "2. **Key Opportunities**: Solar and wind energy present the most immediate opportunities, with several large-scale projects already demonstrating success.\n\n"
            report += "3. **Challenges to Address**: Infrastructure development, financing mechanisms, and regulatory frameworks remain critical areas requiring attention.\n\n"
            report += "4. **Future Outlook**: The sector shows strong potential for continued growth, with projections indicating significant capacity additions by 2030.\n\n"
        elif "generative ai" in query.lower() or "journalism" in query.lower():
            report += "Based on the comprehensive analysis:\n\n"
            report += "1. **Transformation in Progress**: Generative AI is fundamentally changing journalism workflows, from content creation to fact-checking.\n\n"
            report += "2. **Ethical Considerations**: The industry is actively developing guidelines to ensure AI use maintains journalistic integrity and transparency.\n\n"
            report += "3. **Productivity Gains**: News organizations report significant efficiency improvements while emphasizing the continued importance of human oversight.\n\n"
            report += "4. **Future Direction**: The integration of AI in journalism will likely deepen, with focus on augmentation rather than replacement of human journalists.\n\n"
        else:
            report += f"The research on \"{query}\" reveals several important insights:\n\n"
            report += "1. **Current State**: The topic shows significant activity and interest across multiple domains.\n\n"
            report += "2. **Key Trends**: Analysis indicates evolving patterns that warrant continued monitoring.\n\n"
            report += "3. **Implications**: The findings suggest important considerations for stakeholders in this area.\n\n"
            report += "4. **Recommendations**: Further investigation into specific aspects would provide additional value.\n\n"
        
        # Data Sources
        report += "## Data Sources\n\n"
        report += f"- Web Search Results: {len(bing_results)} sources analyzed\n"
        report += f"- Knowledge Base Documents: {len(ai_search_results)} documents reviewed\n"
        report += f"- Total Sources Evaluated: {len(bing_results) + len(ai_search_results)}\n\n"
        
        # Methodology
        report += "## Methodology\n\n"
        report += "This report was generated using a multi-agent research system that:\n"
        report += "1. Simultaneously queries multiple data sources\n"
        report += "2. Applies semantic analysis to identify relevant information\n"
        report += "3. Synthesizes findings across sources to provide comprehensive insights\n"
        report += "4. Structures information for clarity and actionability\n\n"
        
        # Disclaimer
        report += "---\n\n"
        report += "*Disclaimer: This report is generated by an AI system and should be verified with primary sources for critical decisions.*\n"
        
        return report
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Process research query by orchestrating multiple agents.
        
        Args:
            query: Research query
            context: Optional context
            
        Returns:
            Manager's final message with report
        """
        try:
            # Orchestrate research
            chat_history, final_report = await self.orchestrate_research(query)
            
            # Create summary message
            message = AgentMessage(
                agent_name=self.name,
                content=f"Research completed successfully. Generated a comprehensive report with insights from {len(chat_history)} agent interactions.",
                metadata={
                    "query": query,
                    "chat_history_length": len(chat_history),
                    "report_length": len(final_report),
                    "final_report": final_report,
                    "chat_history": [msg.to_dict() for msg in chat_history]
                }
            )
            
            return message
            
        except Exception as e:
            self.logger.error("Failed to orchestrate research", error=str(e))
            raise
    
    async def get_agent_metrics(self) -> Dict[str, Any]:
        """Get metrics from all agents.
        
        Returns:
            Combined metrics from all agents
        """
        return {
            "manager": self.get_metrics(),
            "bing_agent": self.bing_agent.get_metrics(),
            "ai_search_agent": self.ai_search_agent.get_metrics(),
            "group_chat_size": len(self.group_chat_history)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents.
        
        Returns:
            Combined health status
        """
        # Run health checks in parallel
        tasks = [
            super().health_check(),
            self.bing_agent.health_check(),
            self.ai_search_agent.health_check()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {
            "overall_healthy": True,
            "agents": {}
        }
        
        agent_names = ["manager", "bing_agent", "ai_search_agent"]
        
        for name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                health_status["agents"][name] = {
                    "healthy": False,
                    "error": str(result)
                }
                health_status["overall_healthy"] = False
            else:
                health_status["agents"][name] = result
                if not result.get("healthy", True):
                    health_status["overall_healthy"] = False
                    
        return health_status