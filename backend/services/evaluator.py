"""
Evaluation Service - Evaluates agent performance and research quality
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json
import hashlib

from ..config import settings
from ..agents.base_agent import AgentResponse, AgentRole

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of evaluation metrics"""
    ACCURACY = "accuracy"
    LATENCY = "latency"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    COVERAGE = "coverage"
    CONFIDENCE = "confidence"
    QUALITY = "quality"


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    metric_type: MetricType
    score: float  # 0.0 to 1.0
    raw_value: Optional[Any] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_type": self.metric_type.value,
            "score": self.score,
            "raw_value": self.raw_value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentEvaluation:
    """Evaluation results for a single agent"""
    agent_id: str
    agent_role: AgentRole
    query: str
    metrics: List[EvaluationMetrics]
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_role": self.agent_role.value,
            "query": self.query,
            "metrics": [m.to_dict() for m in self.metrics],
            "overall_score": self.overall_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SystemEvaluation:
    """Evaluation results for the entire system"""
    query: str
    agent_evaluations: List[AgentEvaluation]
    system_metrics: List[EvaluationMetrics]
    overall_score: float
    agent_agreement_score: float
    quality_assessment: str
    improvement_areas: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "agent_evaluations": [e.to_dict() for e in self.agent_evaluations],
            "system_metrics": [m.to_dict() for m in self.system_metrics],
            "overall_score": self.overall_score,
            "agent_agreement_score": self.agent_agreement_score,
            "quality_assessment": self.quality_assessment,
            "improvement_areas": self.improvement_areas,
            "timestamp": self.timestamp.isoformat()
        }


class EvaluationService:
    """
    Service for evaluating agent and system performance
    """
    
    def __init__(self):
        """Initialize evaluation service"""
        self.enabled = settings.evaluation_enabled
        self.metrics_config = settings.evaluation_metrics
        self.evaluation_history: List[SystemEvaluation] = []
        self.benchmarks = self._load_benchmarks()
        
        logger.info(f"Evaluation service initialized with metrics: {self.metrics_config}")
    
    def _load_benchmarks(self) -> Dict[str, Any]:
        """Load benchmark data for comparison"""
        # In production, this would load from a database or file
        return {
            "latency": {
                "excellent": 500,   # ms
                "good": 1000,
                "acceptable": 2000,
                "poor": 5000
            },
            "accuracy": {
                "excellent": 0.9,
                "good": 0.75,
                "acceptable": 0.6,
                "poor": 0.4
            },
            "relevance": {
                "excellent": 0.85,
                "good": 0.7,
                "acceptable": 0.5,
                "poor": 0.3
            },
            "completeness": {
                "excellent": 0.9,
                "good": 0.75,
                "acceptable": 0.6,
                "poor": 0.4
            }
        }
    
    async def evaluate_agent(self, agent_response: AgentResponse, query: str, 
                            ground_truth: Optional[Dict[str, Any]] = None) -> AgentEvaluation:
        """
        Evaluate a single agent's performance
        
        Args:
            agent_response: The agent's response
            query: The original query
            ground_truth: Optional ground truth for comparison
            
        Returns:
            AgentEvaluation with detailed metrics
        """
        metrics = []
        
        # Evaluate latency
        if agent_response.processing_time_ms:
            latency_metric = self._evaluate_latency(agent_response.processing_time_ms)
            metrics.append(latency_metric)
        
        # Evaluate relevance
        relevance_metric = self._evaluate_relevance(agent_response, query)
        metrics.append(relevance_metric)
        
        # Evaluate completeness
        completeness_metric = self._evaluate_completeness(agent_response)
        metrics.append(completeness_metric)
        
        # Evaluate accuracy (if ground truth available)
        if ground_truth:
            accuracy_metric = self._evaluate_accuracy(agent_response, ground_truth)
            metrics.append(accuracy_metric)
        
        # Evaluate confidence
        confidence_metric = self._evaluate_confidence(agent_response)
        metrics.append(confidence_metric)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)
        
        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(metrics)
        
        # Generate recommendations
        recommendations = self._generate_agent_recommendations(metrics, agent_response.agent_role)
        
        return AgentEvaluation(
            agent_id=agent_response.agent_id,
            agent_role=agent_response.agent_role,
            query=query,
            metrics=metrics,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    async def evaluate_system(self, query: str, agent_responses: List[AgentResponse],
                            final_report: Optional[Dict[str, Any]] = None) -> SystemEvaluation:
        """
        Evaluate the entire system's performance
        
        Args:
            query: The original query
            agent_responses: All agent responses
            final_report: The final generated report
            
        Returns:
            SystemEvaluation with comprehensive metrics
        """
        # Evaluate individual agents
        agent_evaluations = []
        for response in agent_responses:
            agent_eval = await self.evaluate_agent(response, query)
            agent_evaluations.append(agent_eval)
        
        # Calculate system-level metrics
        system_metrics = []
        
        # Overall quality metric
        quality_metric = self._evaluate_system_quality(agent_evaluations, final_report)
        system_metrics.append(quality_metric)
        
        # Coverage metric
        coverage_metric = self._evaluate_coverage(agent_responses, query)
        system_metrics.append(coverage_metric)
        
        # Consistency metric
        consistency_metric = self._evaluate_consistency(agent_responses)
        system_metrics.append(consistency_metric)
        
        # Calculate agent agreement score
        agent_agreement_score = self._calculate_agent_agreement(agent_responses)
        
        # Calculate overall system score
        overall_score = self._calculate_system_score(agent_evaluations, system_metrics)
        
        # Quality assessment
        quality_assessment = self._assess_quality_level(overall_score)
        
        # Identify improvement areas
        improvement_areas = self._identify_improvement_areas(agent_evaluations, system_metrics)
        
        evaluation = SystemEvaluation(
            query=query,
            agent_evaluations=agent_evaluations,
            system_metrics=system_metrics,
            overall_score=overall_score,
            agent_agreement_score=agent_agreement_score,
            quality_assessment=quality_assessment,
            improvement_areas=improvement_areas
        )
        
        # Store in history
        self.evaluation_history.append(evaluation)
        
        return evaluation
    
    def _evaluate_latency(self, processing_time_ms: float) -> EvaluationMetrics:
        """Evaluate latency performance"""
        benchmarks = self.benchmarks["latency"]
        
        if processing_time_ms <= benchmarks["excellent"]:
            score = 1.0
        elif processing_time_ms <= benchmarks["good"]:
            score = 0.8
        elif processing_time_ms <= benchmarks["acceptable"]:
            score = 0.6
        elif processing_time_ms <= benchmarks["poor"]:
            score = 0.4
        else:
            score = 0.2
        
        return EvaluationMetrics(
            metric_type=MetricType.LATENCY,
            score=score,
            raw_value=processing_time_ms,
            details={
                "processing_time_ms": processing_time_ms,
                "benchmark_category": self._get_benchmark_category(processing_time_ms, benchmarks)
            }
        )
    
    def _evaluate_relevance(self, response: AgentResponse, query: str) -> EvaluationMetrics:
        """Evaluate relevance of response to query"""
        # Simulate relevance scoring (in production, use NLP/embedding similarity)
        score = response.confidence_score * 0.8  # Use confidence as proxy
        
        # Adjust based on sources
        if response.sources:
            source_bonus = min(len(response.sources) * 0.02, 0.2)
            score = min(score + source_bonus, 1.0)
        
        return EvaluationMetrics(
            metric_type=MetricType.RELEVANCE,
            score=score,
            details={
                "confidence_score": response.confidence_score,
                "source_count": len(response.sources),
                "query_terms": query.split()[:5]
            }
        )
    
    def _evaluate_completeness(self, response: AgentResponse) -> EvaluationMetrics:
        """Evaluate completeness of response"""
        score = 0.5  # Base score
        
        # Check for content
        if response.content:
            score += 0.2
            
            # Check content structure (for dict responses)
            if isinstance(response.content, dict):
                if "summary" in response.content:
                    score += 0.1
                if "detailed_results" in response.content:
                    score += 0.1
                if "insights" in response.content or "search_metadata" in response.content:
                    score += 0.1
        
        # Check for sources
        if response.sources:
            score += min(len(response.sources) * 0.02, 0.1)
        
        # Check for metadata
        if response.metadata:
            score += 0.05
        
        return EvaluationMetrics(
            metric_type=MetricType.COMPLETENESS,
            score=min(score, 1.0),
            details={
                "has_content": bool(response.content),
                "has_sources": bool(response.sources),
                "has_metadata": bool(response.metadata),
                "source_count": len(response.sources)
            }
        )
    
    def _evaluate_accuracy(self, response: AgentResponse, ground_truth: Dict[str, Any]) -> EvaluationMetrics:
        """Evaluate accuracy against ground truth"""
        # Simplified accuracy evaluation
        # In production, this would involve sophisticated comparison
        score = 0.7  # Default moderate accuracy
        
        if response.confidence_score > 0.8:
            score += 0.1
        
        if response.sources and len(response.sources) > 3:
            score += 0.1
        
        return EvaluationMetrics(
            metric_type=MetricType.ACCURACY,
            score=min(score, 1.0),
            details={
                "ground_truth_available": True,
                "confidence_alignment": response.confidence_score
            }
        )
    
    def _evaluate_confidence(self, response: AgentResponse) -> EvaluationMetrics:
        """Evaluate confidence calibration"""
        confidence = response.confidence_score
        
        # Check if confidence is well-calibrated
        if 0.6 <= confidence <= 0.85:
            score = 0.9  # Well-calibrated confidence
        elif 0.5 <= confidence < 0.6 or 0.85 < confidence <= 0.95:
            score = 0.7  # Reasonable confidence
        else:
            score = 0.5  # Over or under confident
        
        return EvaluationMetrics(
            metric_type=MetricType.CONFIDENCE,
            score=score,
            raw_value=confidence,
            details={
                "confidence_level": confidence,
                "calibration": "well-calibrated" if score > 0.8 else "needs-adjustment"
            }
        )
    
    def _evaluate_system_quality(self, agent_evaluations: List[AgentEvaluation],
                                 final_report: Optional[Dict[str, Any]]) -> EvaluationMetrics:
        """Evaluate overall system quality"""
        # Calculate average agent scores
        avg_score = statistics.mean([e.overall_score for e in agent_evaluations])
        
        # Bonus for final report quality
        if final_report:
            if "executive_summary" in final_report:
                avg_score += 0.05
            if "recommendations" in final_report:
                avg_score += 0.05
        
        return EvaluationMetrics(
            metric_type=MetricType.QUALITY,
            score=min(avg_score, 1.0),
            details={
                "agent_count": len(agent_evaluations),
                "avg_agent_score": avg_score,
                "has_final_report": bool(final_report)
            }
        )
    
    def _evaluate_coverage(self, responses: List[AgentResponse], query: str) -> EvaluationMetrics:
        """Evaluate topic coverage"""
        total_sources = sum(len(r.sources) for r in responses)
        unique_sources = len(set(
            s.get("url", s.get("id", str(i)))
            for r in responses
            for i, s in enumerate(r.sources)
        ))
        
        # Score based on diversity and quantity
        score = min(0.3 + (unique_sources * 0.05), 1.0)
        
        # Bonus for multiple agent types
        agent_types = set(r.agent_role for r in responses)
        if len(agent_types) > 1:
            score = min(score + 0.1, 1.0)
        
        return EvaluationMetrics(
            metric_type=MetricType.COVERAGE,
            score=score,
            details={
                "total_sources": total_sources,
                "unique_sources": unique_sources,
                "agent_types": len(agent_types)
            }
        )
    
    def _evaluate_consistency(self, responses: List[AgentResponse]) -> EvaluationMetrics:
        """Evaluate consistency across agent responses"""
        if len(responses) < 2:
            return EvaluationMetrics(
                metric_type=MetricType.CONSISTENCY,
                score=1.0,
                details={"note": "Single agent, consistency not applicable"}
            )
        
        # Compare confidence scores
        confidences = [r.confidence_score for r in responses]
        confidence_std = statistics.stdev(confidences) if len(confidences) > 1 else 0
        
        # Lower standard deviation indicates higher consistency
        if confidence_std < 0.1:
            score = 0.9
        elif confidence_std < 0.2:
            score = 0.7
        elif confidence_std < 0.3:
            score = 0.5
        else:
            score = 0.3
        
        return EvaluationMetrics(
            metric_type=MetricType.CONSISTENCY,
            score=score,
            details={
                "confidence_std": confidence_std,
                "confidence_range": max(confidences) - min(confidences)
            }
        )
    
    def _calculate_overall_score(self, metrics: List[EvaluationMetrics]) -> float:
        """Calculate overall score from individual metrics"""
        if not metrics:
            return 0.5
        
        # Weighted average based on metric type
        weights = {
            MetricType.ACCURACY: 0.25,
            MetricType.RELEVANCE: 0.25,
            MetricType.COMPLETENESS: 0.2,
            MetricType.LATENCY: 0.15,
            MetricType.CONFIDENCE: 0.15,
            MetricType.CONSISTENCY: 0.1,
            MetricType.COVERAGE: 0.1,
            MetricType.QUALITY: 0.1
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for metric in metrics:
            weight = weights.get(metric.metric_type, 0.1)
            weighted_sum += metric.score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _calculate_system_score(self, agent_evaluations: List[AgentEvaluation],
                               system_metrics: List[EvaluationMetrics]) -> float:
        """Calculate overall system score"""
        # Average of agent scores
        agent_avg = statistics.mean([e.overall_score for e in agent_evaluations]) if agent_evaluations else 0.5
        
        # Average of system metrics
        system_avg = statistics.mean([m.score for m in system_metrics]) if system_metrics else 0.5
        
        # Weighted combination
        return (agent_avg * 0.6) + (system_avg * 0.4)
    
    def _calculate_agent_agreement(self, responses: List[AgentResponse]) -> float:
        """Calculate agreement score between agents"""
        if len(responses) < 2:
            return 1.0
        
        # Use confidence scores as proxy for agreement
        confidences = [r.confidence_score for r in responses]
        
        # Calculate coefficient of variation
        if statistics.mean(confidences) > 0:
            cv = statistics.stdev(confidences) / statistics.mean(confidences)
            # Convert CV to agreement score (lower CV = higher agreement)
            agreement = max(0, 1 - cv)
        else:
            agreement = 0.5
        
        return agreement
    
    def _identify_strengths_weaknesses(self, metrics: List[EvaluationMetrics]) -> Tuple[List[str], List[str]]:
        """Identify strengths and weaknesses from metrics"""
        strengths = []
        weaknesses = []
        
        for metric in metrics:
            if metric.score >= 0.8:
                strengths.append(f"Strong {metric.metric_type.value}: {metric.score:.2f}")
            elif metric.score < 0.5:
                weaknesses.append(f"Weak {metric.metric_type.value}: {metric.score:.2f}")
        
        if not strengths:
            strengths.append("Consistent moderate performance across metrics")
        
        if not weaknesses:
            weaknesses.append("No significant weaknesses identified")
        
        return strengths, weaknesses
    
    def _generate_agent_recommendations(self, metrics: List[EvaluationMetrics], 
                                       agent_role: AgentRole) -> List[str]:
        """Generate recommendations for agent improvement"""
        recommendations = []
        
        for metric in metrics:
            if metric.metric_type == MetricType.LATENCY and metric.score < 0.6:
                recommendations.append("Optimize processing pipeline to reduce latency")
            elif metric.metric_type == MetricType.RELEVANCE and metric.score < 0.7:
                recommendations.append("Improve query understanding and result filtering")
            elif metric.metric_type == MetricType.COMPLETENESS and metric.score < 0.7:
                recommendations.append("Enhance response detail and source coverage")
            elif metric.metric_type == MetricType.CONFIDENCE and metric.score < 0.6:
                recommendations.append("Calibrate confidence scoring mechanism")
        
        # Agent-specific recommendations
        if agent_role == AgentRole.BING_SEARCH and len(recommendations) == 0:
            recommendations.append("Consider expanding search query variations")
        elif agent_role == AgentRole.AI_SEARCH and len(recommendations) == 0:
            recommendations.append("Update knowledge base index for better coverage")
        elif agent_role == AgentRole.MANAGER and len(recommendations) == 0:
            recommendations.append("Enhance synthesis algorithm for better integration")
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _assess_quality_level(self, score: float) -> str:
        """Assess quality level based on score"""
        if score >= 0.9:
            return "Excellent - Exceeds expectations"
        elif score >= 0.75:
            return "Good - Meets expectations"
        elif score >= 0.6:
            return "Acceptable - Room for improvement"
        elif score >= 0.4:
            return "Below Average - Significant improvements needed"
        else:
            return "Poor - Major issues require attention"
    
    def _identify_improvement_areas(self, agent_evaluations: List[AgentEvaluation],
                                   system_metrics: List[EvaluationMetrics]) -> List[str]:
        """Identify system-wide improvement areas"""
        areas = []
        
        # Check agent performance
        low_performing_agents = [e for e in agent_evaluations if e.overall_score < 0.6]
        if low_performing_agents:
            areas.append(f"Improve performance of {len(low_performing_agents)} agent(s)")
        
        # Check system metrics
        for metric in system_metrics:
            if metric.score < 0.6:
                areas.append(f"Enhance system {metric.metric_type.value}")
        
        # Check consistency
        consistency_metrics = [m for m in system_metrics if m.metric_type == MetricType.CONSISTENCY]
        if consistency_metrics and consistency_metrics[0].score < 0.7:
            areas.append("Improve inter-agent coordination and consistency")
        
        # Check coverage
        coverage_metrics = [m for m in system_metrics if m.metric_type == MetricType.COVERAGE]
        if coverage_metrics and coverage_metrics[0].score < 0.7:
            areas.append("Expand information sources and coverage")
        
        if not areas:
            areas.append("Maintain current performance levels")
        
        return areas
    
    def _get_benchmark_category(self, value: float, benchmarks: Dict[str, float]) -> str:
        """Get benchmark category for a value"""
        if value <= benchmarks["excellent"]:
            return "excellent"
        elif value <= benchmarks["good"]:
            return "good"
        elif value <= benchmarks["acceptable"]:
            return "acceptable"
        elif value <= benchmarks["poor"]:
            return "poor"
        else:
            return "very_poor"
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary of evaluation history"""
        if not self.evaluation_history:
            return {"message": "No evaluations performed yet"}
        
        recent_evaluations = self.evaluation_history[-10:]  # Last 10 evaluations
        
        return {
            "total_evaluations": len(self.evaluation_history),
            "recent_evaluations": len(recent_evaluations),
            "average_score": statistics.mean([e.overall_score for e in recent_evaluations]),
            "best_score": max([e.overall_score for e in recent_evaluations]),
            "worst_score": min([e.overall_score for e in recent_evaluations]),
            "average_agreement": statistics.mean([e.agent_agreement_score for e in recent_evaluations]),
            "common_improvement_areas": self._get_common_improvement_areas(recent_evaluations)
        }
    
    def _get_common_improvement_areas(self, evaluations: List[SystemEvaluation]) -> List[str]:
        """Get common improvement areas across evaluations"""
        all_areas = []
        for evaluation in evaluations:
            all_areas.extend(evaluation.improvement_areas)
        
        # Count frequency
        area_counts = {}
        for area in all_areas:
            area_counts[area] = area_counts.get(area, 0) + 1
        
        # Sort by frequency
        sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [area for area, count in sorted_areas[:3]]  # Top 3 common areas
    
    def export_evaluation(self, evaluation: SystemEvaluation, format: str = "json") -> str:
        """Export evaluation in specified format"""
        if format == "json":
            return json.dumps(evaluation.to_dict(), indent=2)
        else:
            # Add other formats (CSV, HTML) as needed
            return json.dumps(evaluation.to_dict(), indent=2)