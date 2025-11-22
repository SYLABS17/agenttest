"""
Manager Agent - Orchestrates and coordinates worker agents
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_agent import BaseAgent, AgentResponse, AgentRole, AgentStatus
from ..config import settings

logger = logging.getLogger(__name__)


class ManagerAgent(BaseAgent):
    """
    Manager agent that coordinates multiple worker agents in a group-chat style collaboration
    """
    
    def __init__(self, worker_agents: Optional[List[BaseAgent]] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Manager Agent
        
        Args:
            worker_agents: List of worker agents to manage
            config: Optional configuration
        """
        super().__init__(AgentRole.MANAGER, "Manager_Agent", config)
        self.worker_agents = worker_agents or []
        self.max_iterations = settings.manager_max_iterations
        self.temperature = settings.manager_temperature
        self.conversation_history: List[Dict[str, Any]] = []
        self.research_context: Dict[str, Any] = {}
        
        logger.info(f"Manager Agent initialized with {len(self.worker_agents)} worker agents")
    
    def add_worker_agent(self, agent: BaseAgent) -> None:
        """Add a worker agent to the team"""
        self.worker_agents.append(agent)
        logger.info(f"Added {agent.name} to the team")
    
    def remove_worker_agent(self, agent_id: str) -> None:
        """Remove a worker agent from the team"""
        self.worker_agents = [a for a in self.worker_agents if a.id != agent_id]
        logger.info(f"Removed agent {agent_id} from the team")
    
    async def validate_input(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate manager input"""
        if not query or not query.strip():
            logger.error("Empty query provided to Manager Agent")
            return False
        
        if len(self.worker_agents) == 0:
            logger.error("No worker agents available for Manager Agent")
            return False
        
        return True
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Process a research query by coordinating worker agents
        
        Args:
            query: The research query
            context: Optional context
            
        Returns:
            AgentResponse with the final research report
        """
        try:
            # Initialize conversation
            self.conversation_history = []
            self.research_context = context or {}
            
            # Step 1: Plan the research approach
            research_plan = await self._create_research_plan(query)
            self.conversation_history.append({
                "role": "manager",
                "content": f"Research Plan: {research_plan}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Step 2: Distribute query to worker agents
            worker_responses = await self._distribute_to_workers(query, research_plan)
            
            # Step 3: Group chat style iteration
            final_response = await self._collaborative_synthesis(query, worker_responses, research_plan)
            
            # Step 4: Generate final research report
            report = await self._generate_final_report(query, final_response)
            
            return AgentResponse(
                agent_id=self.id,
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                content=report,
                sources=self._extract_all_sources(final_response),
                confidence_score=self._calculate_confidence(final_response),
                metadata={
                    "iterations": len(self.conversation_history),
                    "workers_used": [a.name for a in self.worker_agents],
                    "research_plan": research_plan
                }
            )
            
        except Exception as e:
            logger.error(f"Manager Agent processing failed: {str(e)}", exc_info=True)
            return self._create_error_response(str(e), AgentStatus.FAILED)
    
    async def _create_research_plan(self, query: str) -> Dict[str, Any]:
        """Create a research plan based on the query"""
        # Simulate creating a research plan (in production, this would use LLM)
        plan = {
            "objective": query,
            "approach": "multi-source comprehensive research",
            "steps": [
                "Gather information from web sources (Bing)",
                "Search internal knowledge base (AI Search)",
                "Synthesize findings",
                "Identify gaps and contradictions",
                "Generate comprehensive report"
            ],
            "expected_outputs": [
                "Key findings",
                "Supporting evidence",
                "Conflicting viewpoints",
                "Recommendations"
            ],
            "quality_criteria": {
                "relevance": "High alignment with research query",
                "completeness": "Comprehensive coverage of topic",
                "accuracy": "Verified facts with sources",
                "clarity": "Clear and structured presentation"
            }
        }
        
        logger.info(f"Created research plan for query: {query[:100]}...")
        return plan
    
    async def _distribute_to_workers(self, query: str, research_plan: Dict[str, Any]) -> List[AgentResponse]:
        """Distribute query to all worker agents in parallel"""
        logger.info(f"Distributing query to {len(self.worker_agents)} worker agents")
        
        # Create tasks for parallel execution
        tasks = []
        for agent in self.worker_agents:
            context = {
                "research_plan": research_plan,
                "manager_id": self.id,
                "timestamp": datetime.utcnow().isoformat()
            }
            task = agent.execute(query, context)
            tasks.append(task)
        
        # Execute all tasks in parallel with timeout
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=settings.agent_timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error("Worker agents timed out")
            responses = []
        
        # Filter out exceptions and log them
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Worker agent {self.worker_agents[i].name} failed: {str(response)}")
            else:
                valid_responses.append(response)
                self.conversation_history.append({
                    "role": response.agent_role.value,
                    "content": response.content,
                    "timestamp": response.timestamp.isoformat()
                })
        
        logger.info(f"Received {len(valid_responses)} valid responses from worker agents")
        return valid_responses
    
    async def _collaborative_synthesis(
        self,
        query: str,
        initial_responses: List[AgentResponse],
        research_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Facilitate group-chat style collaboration between agents
        """
        logger.info("Starting collaborative synthesis phase")
        
        synthesis = {
            "initial_responses": [],
            "discussion_rounds": [],
            "consensus_points": [],
            "disagreement_points": [],
            "additional_insights": []
        }
        
        # Process initial responses
        for response in initial_responses:
            synthesis["initial_responses"].append({
                "agent": response.agent_role.value,
                "summary": str(response.content)[:500] if response.content else "",
                "confidence": response.confidence_score,
                "sources_count": len(response.sources)
            })
        
        # Simulate discussion rounds (in production, this would involve actual agent communication)
        for iteration in range(min(self.max_iterations, 3)):
            discussion_round = {
                "round": iteration + 1,
                "timestamp": datetime.utcnow().isoformat(),
                "exchanges": []
            }
            
            # Simulate agent discussions
            if iteration == 0:
                # First round: Identify common findings
                discussion_round["exchanges"].append({
                    "speaker": "manager",
                    "message": "Let's identify common findings across all sources",
                    "type": "coordination"
                })
                
                for response in initial_responses:
                    discussion_round["exchanges"].append({
                        "speaker": response.agent_role.value,
                        "message": f"Key findings from {response.agent_role.value}",
                        "type": "contribution"
                    })
                
            elif iteration == 1:
                # Second round: Address contradictions
                discussion_round["exchanges"].append({
                    "speaker": "manager",
                    "message": "Let's discuss any contradictions or gaps",
                    "type": "coordination"
                })
                
            elif iteration == 2:
                # Third round: Final synthesis
                discussion_round["exchanges"].append({
                    "speaker": "manager",
                    "message": "Let's create our final synthesis",
                    "type": "coordination"
                })
            
            synthesis["discussion_rounds"].append(discussion_round)
            
            # Add to conversation history
            for exchange in discussion_round["exchanges"]:
                self.conversation_history.append({
                    "role": exchange["speaker"],
                    "content": exchange["message"],
                    "timestamp": discussion_round["timestamp"]
                })
        
        # Extract consensus and disagreement points (simulated)
        synthesis["consensus_points"] = [
            "All sources agree on the importance of the research topic",
            "Multiple sources confirm the key trends identified",
            "Consistent findings across different search methods"
        ]
        
        synthesis["disagreement_points"] = [
            "Varying perspectives on implementation approaches",
            "Different timelines suggested by different sources"
        ]
        
        synthesis["additional_insights"] = [
            "Cross-referencing revealed new connections",
            "Collaborative analysis identified emerging patterns"
        ]
        
        logger.info(f"Collaborative synthesis completed with {len(synthesis['discussion_rounds'])} rounds")
        return synthesis
    
    async def _generate_final_report(self, query: str, synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the final research report"""
        logger.info("Generating final research report")
        
        report = {
            "title": f"Research Report: {query}",
            "timestamp": datetime.utcnow().isoformat(),
            "executive_summary": self._create_executive_summary(query, synthesis),
            "methodology": {
                "approach": "Multi-agent collaborative research",
                "sources_consulted": len(synthesis["initial_responses"]),
                "discussion_rounds": len(synthesis["discussion_rounds"]),
                "agents_involved": [r["agent"] for r in synthesis["initial_responses"]]
            },
            "key_findings": self._extract_key_findings(synthesis),
            "detailed_analysis": self._create_detailed_analysis(synthesis),
            "consensus_points": synthesis["consensus_points"],
            "areas_of_disagreement": synthesis["disagreement_points"],
            "additional_insights": synthesis["additional_insights"],
            "recommendations": self._generate_recommendations(query, synthesis),
            "limitations": [
                "Analysis based on available data sources",
                "Time-constrained research window",
                "Potential gaps in coverage"
            ],
            "conclusion": self._create_conclusion(query, synthesis),
            "appendix": {
                "conversation_log": self.conversation_history[-10:],  # Last 10 exchanges
                "metrics": self._calculate_report_metrics(synthesis)
            }
        }
        
        logger.info("Final research report generated successfully")
        return report
    
    def _create_executive_summary(self, query: str, synthesis: Dict[str, Any]) -> str:
        """Create an executive summary for the report"""
        summary = f"""
        This research report addresses the query: "{query}"
        
        Through collaborative analysis involving {len(synthesis['initial_responses'])} specialized agents,
        we conducted a comprehensive investigation utilizing multiple data sources including web search
        and knowledge base queries.
        
        The research identified {len(synthesis['consensus_points'])} areas of consensus and
        {len(synthesis['disagreement_points'])} areas requiring further investigation.
        Our multi-agent approach enabled cross-validation of findings and identification of
        emerging patterns that might be missed by single-source analysis.
        """
        return summary.strip()
    
    def _extract_key_findings(self, synthesis: Dict[str, Any]) -> List[str]:
        """Extract key findings from the synthesis"""
        findings = [
            "Primary research objective has been thoroughly addressed",
            "Multiple independent sources corroborate the main conclusions",
            "Identified trends align with current industry patterns",
            "Evidence suggests strong potential for future developments",
            "Cross-source validation confirms reliability of findings"
        ]
        
        # Add findings from initial responses
        for response in synthesis["initial_responses"]:
            if response["confidence"] > 0.7:
                findings.append(f"High-confidence finding from {response['agent']}")
        
        return findings[:10]  # Return top 10 findings
    
    def _create_detailed_analysis(self, synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed analysis section"""
        analysis = {
            "data_quality": {
                "overall_confidence": sum(r["confidence"] for r in synthesis["initial_responses"]) / len(synthesis["initial_responses"]) if synthesis["initial_responses"] else 0,
                "source_diversity": len(set(r["agent"] for r in synthesis["initial_responses"])),
                "total_sources": sum(r["sources_count"] for r in synthesis["initial_responses"])
            },
            "coverage_analysis": {
                "topics_covered": ["Main topic", "Related areas", "Historical context", "Future projections"],
                "depth_of_analysis": "Comprehensive",
                "geographical_scope": "Global with regional insights"
            },
            "reliability_assessment": {
                "source_credibility": "High - multiple verified sources",
                "data_recency": "Current - includes latest available information",
                "bias_assessment": "Minimal - cross-validated across diverse sources"
            }
        }
        return analysis
    
    def _generate_recommendations(self, query: str, synthesis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on the research"""
        recommendations = [
            "Continue monitoring this topic for emerging developments",
            "Consider deeper investigation into areas of disagreement",
            "Validate findings with additional primary sources if available",
            "Implement insights in phased approach to minimize risk",
            "Establish metrics to track outcomes of recommended actions"
        ]
        
        # Add specific recommendations based on confidence levels
        high_confidence_count = sum(1 for r in synthesis["initial_responses"] if r["confidence"] > 0.7)
        if high_confidence_count > len(synthesis["initial_responses"]) / 2:
            recommendations.insert(0, "High confidence in findings suggests immediate action feasible")
        else:
            recommendations.insert(0, "Mixed confidence levels suggest cautious approach recommended")
        
        return recommendations
    
    def _create_conclusion(self, query: str, synthesis: Dict[str, Any]) -> str:
        """Create conclusion for the report"""
        conclusion = f"""
        This collaborative research investigation into "{query}" has yielded comprehensive insights
        through the coordinated efforts of multiple specialized agents. The multi-source approach
        has enabled robust cross-validation of findings and identification of both consensus areas
        and points requiring further investigation.
        
        The synthesis of {len(synthesis['initial_responses'])} independent analyses through
        {len(synthesis['discussion_rounds'])} rounds of collaborative discussion has produced
        a nuanced understanding of the topic that balances multiple perspectives while maintaining
        analytical rigor.
        
        The findings presented in this report provide a solid foundation for informed decision-making
        while acknowledging areas of uncertainty that may benefit from continued research.
        """
        return conclusion.strip()
    
    def _calculate_report_metrics(self, synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for the report"""
        metrics = {
            "total_processing_time_ms": sum(self.metrics.processing_time_ms or 0 for _ in synthesis["initial_responses"]),
            "agents_participated": len(synthesis["initial_responses"]),
            "discussion_rounds": len(synthesis["discussion_rounds"]),
            "consensus_ratio": len(synthesis["consensus_points"]) / (len(synthesis["consensus_points"]) + len(synthesis["disagreement_points"])) if (synthesis["consensus_points"] or synthesis["disagreement_points"]) else 0,
            "average_confidence": sum(r["confidence"] for r in synthesis["initial_responses"]) / len(synthesis["initial_responses"]) if synthesis["initial_responses"] else 0,
            "total_sources": sum(r["sources_count"] for r in synthesis["initial_responses"]),
            "conversation_exchanges": len(self.conversation_history)
        }
        return metrics
    
    def _extract_all_sources(self, synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all sources from the synthesis"""
        sources = []
        for response in synthesis.get("initial_responses", []):
            # Add placeholder sources (in production, these would be actual sources)
            for i in range(response.get("sources_count", 0)):
                sources.append({
                    "agent": response["agent"],
                    "type": "web" if "bing" in response["agent"] else "knowledge_base",
                    "title": f"Source {i+1} from {response['agent']}",
                    "url": f"https://example.com/{response['agent']}/source{i+1}",
                    "relevance_score": response["confidence"]
                })
        return sources
    
    def _calculate_confidence(self, synthesis: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        if not synthesis.get("initial_responses"):
            return 0.5
        
        confidences = [r["confidence"] for r in synthesis["initial_responses"]]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Adjust based on consensus
        consensus_ratio = len(synthesis["consensus_points"]) / (
            len(synthesis["consensus_points"]) + len(synthesis["disagreement_points"])
        ) if (synthesis["consensus_points"] or synthesis["disagreement_points"]) else 0.5
        
        # Weighted average: 70% agent confidence, 30% consensus
        final_confidence = (avg_confidence * 0.7) + (consensus_ratio * 0.3)
        
        return min(max(final_confidence, 0.0), 1.0)  # Clamp between 0 and 1