"""Evaluator service for agent performance assessment."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics
import json
from pathlib import Path

import structlog
import pandas as pd

from ..config import DATA_DIR


class EvaluatorService:
    """Service for evaluating agent performance."""
    
    def __init__(self):
        """Initialize evaluator service."""
        self.logger = structlog.get_logger()
        self.evaluation_history: List[Dict[str, Any]] = []
        self.evaluation_metrics = {
            "accuracy": [],
            "latency": [],
            "relevance": [],
            "completeness": [],
            "agreement": []
        }
        
        # Load evaluation criteria
        self.criteria = {
            "accuracy": {
                "weight": 0.3,
                "description": "How accurate and factual are the results"
            },
            "latency": {
                "weight": 0.2,
                "description": "Response time performance"
            },
            "relevance": {
                "weight": 0.25,
                "description": "How relevant are the results to the query"
            },
            "completeness": {
                "weight": 0.15,
                "description": "How comprehensive is the coverage"
            },
            "agreement": {
                "weight": 0.1,
                "description": "Consistency between different agents"
            }
        }
        
    async def evaluate_agent_response(
        self,
        agent_name: str,
        query: str,
        response: Dict[str, Any],
        latency_ms: float
    ) -> Dict[str, Any]:
        """Evaluate a single agent response.
        
        Args:
            agent_name: Name of the agent
            query: Original query
            response: Agent response
            latency_ms: Response latency in milliseconds
            
        Returns:
            Evaluation results
        """
        evaluation = {
            "agent_name": agent_name,
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
            "scores": {}
        }
        
        # Calculate scores (using dummy logic for demonstration)
        # In production, these would use ML models or more sophisticated metrics
        
        # Accuracy score (dummy - based on result count and metadata)
        result_count = response.get("result_count", 0)
        has_sources = bool(response.get("results", []))
        accuracy_score = min(1.0, (result_count * 0.1 + (0.5 if has_sources else 0)))
        evaluation["scores"]["accuracy"] = accuracy_score
        
        # Latency score (lower is better, normalized)
        if latency_ms < 500:
            latency_score = 1.0
        elif latency_ms < 1000:
            latency_score = 0.8
        elif latency_ms < 2000:
            latency_score = 0.6
        elif latency_ms < 5000:
            latency_score = 0.4
        else:
            latency_score = 0.2
        evaluation["scores"]["latency"] = latency_score
        
        # Relevance score (dummy - based on query terms in results)
        query_terms = set(query.lower().split())
        results = response.get("results", [])
        relevance_scores = []
        
        for result in results[:5]:  # Check top 5 results
            content = f"{result.get('title', '')} {result.get('snippet', '')} {result.get('content', '')}".lower()
            matching_terms = sum(1 for term in query_terms if term in content)
            relevance_scores.append(matching_terms / len(query_terms) if query_terms else 0)
            
        relevance_score = statistics.mean(relevance_scores) if relevance_scores else 0.5
        evaluation["scores"]["relevance"] = min(1.0, relevance_score * 1.5)  # Boost and cap
        
        # Completeness score (based on result diversity and count)
        completeness_score = min(1.0, result_count * 0.2)
        if results:
            # Check for diversity in sources/categories
            sources = set(r.get("source", "") for r in results)
            categories = set(r.get("category", "") for r in results)
            diversity_bonus = (len(sources) + len(categories)) * 0.1
            completeness_score = min(1.0, completeness_score + diversity_bonus)
        evaluation["scores"]["completeness"] = completeness_score
        
        # Calculate overall score
        overall_score = sum(
            score * self.criteria[metric]["weight"]
            for metric, score in evaluation["scores"].items()
            if metric in self.criteria
        )
        evaluation["overall_score"] = overall_score
        
        # Store in history
        self.evaluation_history.append(evaluation)
        
        # Update metrics
        for metric, score in evaluation["scores"].items():
            if metric in self.evaluation_metrics:
                self.evaluation_metrics[metric].append(score)
        
        self.logger.info(
            "Agent evaluated",
            agent=agent_name,
            overall_score=f"{overall_score:.2f}",
            latency_ms=latency_ms
        )
        
        return evaluation
    
    async def evaluate_multi_agent_agreement(
        self,
        agents_responses: List[Dict[str, Any]]
    ) -> float:
        """Evaluate agreement between multiple agents.
        
        Args:
            agents_responses: List of agent responses
            
        Returns:
            Agreement score (0-1)
        """
        if len(agents_responses) < 2:
            return 1.0  # Perfect agreement if only one agent
            
        # Extract results from each agent
        all_results = []
        for response in agents_responses:
            results = response.get("results", [])
            # Create normalized result signatures
            signatures = set()
            for r in results:
                # Use title and domain as signature
                title = r.get("title", "").lower()
                url = r.get("url", "")
                if url:
                    domain = url.split("/")[2] if "/" in url else url
                    signatures.add(f"{title}:{domain}")
                else:
                    signatures.add(title)
            all_results.append(signatures)
        
        # Calculate Jaccard similarity between all pairs
        similarities = []
        for i in range(len(all_results)):
            for j in range(i + 1, len(all_results)):
                set1, set2 = all_results[i], all_results[j]
                if set1 or set2:
                    intersection = len(set1 & set2)
                    union = len(set1 | set2)
                    similarity = intersection / union if union > 0 else 0
                    similarities.append(similarity)
        
        # Average similarity is our agreement score
        agreement_score = statistics.mean(similarities) if similarities else 0.5
        
        self.evaluation_metrics["agreement"].append(agreement_score)
        
        return agreement_score
    
    async def generate_evaluation_report(
        self,
        query: str,
        evaluations: List[Dict[str, Any]],
        agreement_score: float
    ) -> Dict[str, Any]:
        """Generate comprehensive evaluation report.
        
        Args:
            query: Research query
            evaluations: List of agent evaluations
            agreement_score: Multi-agent agreement score
            
        Returns:
            Evaluation report
        """
        report = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_evaluations": evaluations,
            "agreement_score": agreement_score,
            "summary": {}
        }
        
        # Calculate summary statistics
        if evaluations:
            # Per-metric summaries
            for metric in self.criteria.keys():
                scores = [e["scores"].get(metric, 0) for e in evaluations]
                if scores:
                    report["summary"][metric] = {
                        "mean": statistics.mean(scores),
                        "median": statistics.median(scores),
                        "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
                        "min": min(scores),
                        "max": max(scores)
                    }
            
            # Overall performance
            overall_scores = [e.get("overall_score", 0) for e in evaluations]
            report["summary"]["overall"] = {
                "mean": statistics.mean(overall_scores),
                "median": statistics.median(overall_scores),
                "best_agent": max(evaluations, key=lambda x: x.get("overall_score", 0))["agent_name"],
                "agreement_score": agreement_score
            }
            
            # Latency analysis
            latencies = [e.get("latency_ms", 0) for e in evaluations]
            report["summary"]["latency"] = {
                "mean_ms": statistics.mean(latencies),
                "median_ms": statistics.median(latencies),
                "total_ms": sum(latencies)
            }
        
        # Generate recommendations
        recommendations = []
        
        if report["summary"].get("overall", {}).get("mean", 0) < 0.7:
            recommendations.append("Overall performance is below optimal. Consider tuning agent parameters.")
            
        if report["summary"].get("latency", {}).get("mean_ms", 0) > 2000:
            recommendations.append("High latency detected. Consider implementing caching or parallel processing.")
            
        if agreement_score < 0.5:
            recommendations.append("Low agreement between agents. Review search strategies for consistency.")
            
        report["recommendations"] = recommendations
        
        # Save report to file
        report_file = DATA_DIR / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(
            "Evaluation report generated",
            report_file=str(report_file),
            overall_score=f"{report['summary'].get('overall', {}).get('mean', 0):.2f}"
        )
        
        return report
    
    def get_historical_metrics(self) -> Dict[str, Any]:
        """Get historical evaluation metrics.
        
        Returns:
            Historical metrics summary
        """
        summary = {
            "total_evaluations": len(self.evaluation_history),
            "metrics": {}
        }
        
        for metric, scores in self.evaluation_metrics.items():
            if scores:
                summary["metrics"][metric] = {
                    "count": len(scores),
                    "mean": statistics.mean(scores),
                    "median": statistics.median(scores),
                    "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
                    "trend": "improving" if len(scores) > 5 and scores[-5:] > scores[:5] else "stable"
                }
        
        return summary
    
    def export_metrics_to_csv(self, filepath: Optional[Path] = None) -> Path:
        """Export evaluation metrics to CSV.
        
        Args:
            filepath: Optional output path
            
        Returns:
            Path to exported file
        """
        if not filepath:
            filepath = DATA_DIR / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        if self.evaluation_history:
            df = pd.DataFrame(self.evaluation_history)
            
            # Flatten scores dictionary
            scores_df = pd.json_normalize(df["scores"])
            df = pd.concat([df.drop("scores", axis=1), scores_df], axis=1)
            
            df.to_csv(filepath, index=False)
            
            self.logger.info("Metrics exported", filepath=str(filepath))
        else:
            # Create empty CSV with headers
            df = pd.DataFrame(columns=["agent_name", "query", "timestamp", "latency_ms", "overall_score"])
            df.to_csv(filepath, index=False)
            
        return filepath


# Global evaluator service instance
evaluator_service = EvaluatorService()