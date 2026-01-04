"""Main evaluation framework for LMS quality assurance."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import structlog

from src.config import get_settings
from src.evaluation.metrics import MetricsCollector, QueryMetrics
from src.evaluation.parity import RetrievalParityChecker
from src.generation.generator import GeneratedResponse
from src.chunking.models import ChunkWithContext

logger = structlog.get_logger(__name__)


@dataclass
class EvaluationResult:
    """Complete evaluation result for a query-response pair."""

    query_id: str
    timestamp: datetime
    groundedness_score: float
    retrieval_relevance: float
    language_quality: float
    factual_accuracy: Optional[float]  # Only if ground truth available
    overall_score: float
    flags: list[str]  # Warning flags if any


class EvaluationFramework:
    """
    Four-layer evaluation framework for LMS quality assurance.

    Layers:
    1. Automated Quality Signals - Real-time metrics
    2. Human Evaluation (SME Review) - Sampled expert review
    3. Cross-Validation - Same question in different languages
    4. User Feedback Signals - Thumbs up/down, retry patterns
    """

    # Thresholds for quality alerts
    GROUNDEDNESS_THRESHOLD = 0.7
    RELEVANCE_THRESHOLD = 0.6
    PARITY_THRESHOLD = 0.90

    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        parity_checker: Optional[RetrievalParityChecker] = None,
    ):
        """
        Initialize evaluation framework.

        Args:
            metrics_collector: Metrics collection service
            parity_checker: Retrieval parity checker
        """
        self.settings = get_settings()
        self.metrics = metrics_collector or MetricsCollector()
        self.parity = parity_checker or RetrievalParityChecker()

    async def evaluate_response(
        self,
        query_id: str,
        query: str,
        response: GeneratedResponse,
        context_chunks: list[ChunkWithContext],
        ground_truth: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Evaluate a generated response.

        Args:
            query_id: Unique query identifier
            query: Original query text
            response: Generated response
            context_chunks: Retrieved context chunks
            ground_truth: Optional ground truth answer for accuracy check

        Returns:
            EvaluationResult with detailed scores
        """
        logger.debug("evaluating_response", query_id=query_id)

        flags = []

        # 1. Groundedness score
        groundedness = self._compute_groundedness(response, context_chunks)
        if groundedness < self.GROUNDEDNESS_THRESHOLD:
            flags.append("low_groundedness")

        # 2. Retrieval relevance
        relevance = self._compute_retrieval_relevance(query, context_chunks)
        if relevance < self.RELEVANCE_THRESHOLD:
            flags.append("low_relevance")

        # 3. Language quality
        language_quality = await self._evaluate_language_quality(
            response.answer, response.language
        )

        # 4. Factual accuracy (if ground truth available)
        factual_accuracy = None
        if ground_truth:
            factual_accuracy = self._compute_factual_accuracy(
                response.answer, ground_truth
            )
            if factual_accuracy < 0.8:
                flags.append("low_accuracy")

        # Overall score
        scores = [groundedness, relevance, language_quality]
        if factual_accuracy is not None:
            scores.append(factual_accuracy)
        overall = sum(scores) / len(scores)

        result = EvaluationResult(
            query_id=query_id,
            timestamp=datetime.utcnow(),
            groundedness_score=groundedness,
            retrieval_relevance=relevance,
            language_quality=language_quality,
            factual_accuracy=factual_accuracy,
            overall_score=overall,
            flags=flags,
        )

        if flags:
            logger.warning(
                "quality_flags_raised",
                query_id=query_id,
                flags=flags,
                overall_score=overall,
            )

        return result

    def _compute_groundedness(
        self,
        response: GeneratedResponse,
        chunks: list[ChunkWithContext],
    ) -> float:
        """
        Compute groundedness score.

        Measures how well the response is grounded in source chunks.
        """
        if not chunks:
            return 0.0

        # Check for source citations
        import re
        citations = re.findall(r'\[Source[:\s]+\d+\]', response.answer, re.IGNORECASE)
        citation_score = min(1.0, len(citations) / 3)  # Expect ~3 citations

        # Check content overlap
        chunk_content = " ".join(c.matched_chunk.content.lower() for c in chunks)
        answer_words = set(response.answer.lower().split())
        content_words = set(chunk_content.split())

        if not answer_words:
            return 0.0

        overlap = len(answer_words & content_words)
        overlap_score = overlap / len(answer_words)

        # Weighted combination
        return 0.4 * citation_score + 0.6 * overlap_score

    def _compute_retrieval_relevance(
        self,
        query: str,
        chunks: list[ChunkWithContext],
    ) -> float:
        """
        Compute retrieval relevance score.

        Measures how relevant the retrieved chunks are to the query.
        """
        if not chunks:
            return 0.0

        # Use average of reranker scores if available
        scores = [c.relevance_score for c in chunks if c.relevance_score > 0]
        if scores:
            return sum(scores) / len(scores)

        # Fallback: simple keyword overlap
        query_words = set(query.lower().split())
        chunk_content = " ".join(c.matched_chunk.content.lower() for c in chunks)
        content_words = set(chunk_content.split())

        overlap = len(query_words & content_words)
        return min(1.0, overlap / len(query_words)) if query_words else 0.0

    async def _evaluate_language_quality(
        self,
        text: str,
        language: str,
    ) -> float:
        """
        Evaluate language quality of response.

        In production, would use LLM evaluation or language-specific metrics.
        """
        # Simple heuristics for now
        if not text:
            return 0.0

        score = 0.7  # Base score

        # Check sentence structure
        sentences = text.split('.')
        if len(sentences) >= 2:
            score += 0.1

        # Check for complete response
        if len(text) > 100:
            score += 0.1

        # Penalize very short responses
        if len(text) < 50:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _compute_factual_accuracy(
        self,
        answer: str,
        ground_truth: str,
    ) -> float:
        """
        Compute factual accuracy against ground truth.

        Simple implementation - production would use more sophisticated comparison.
        """
        # Normalize texts
        answer_lower = answer.lower()
        truth_lower = ground_truth.lower()

        # Simple word overlap metric
        answer_words = set(answer_lower.split())
        truth_words = set(truth_lower.split())

        if not truth_words:
            return 1.0

        overlap = len(answer_words & truth_words)
        recall = overlap / len(truth_words)

        return recall

    async def run_automated_checks(
        self,
        query_id: str,
        response: GeneratedResponse,
        chunks: list[ChunkWithContext],
    ) -> dict:
        """
        Run automated quality checks on a response.

        Returns dict of check results for monitoring.
        """
        checks = {
            "query_id": query_id,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }

        # Check 1: Groundedness
        groundedness = self._compute_groundedness(response, chunks)
        checks["checks"]["groundedness"] = {
            "score": groundedness,
            "threshold": self.GROUNDEDNESS_THRESHOLD,
            "passed": groundedness >= self.GROUNDEDNESS_THRESHOLD,
        }

        # Check 2: Empty result
        checks["checks"]["has_content"] = {
            "passed": bool(chunks) and len(response.answer) > 20,
        }

        # Check 3: Source citations
        import re
        citations = re.findall(r'\[Source[:\s]+\d+\]', response.answer, re.IGNORECASE)
        checks["checks"]["has_citations"] = {
            "count": len(citations),
            "passed": len(citations) > 0,
        }

        # Check 4: Response confidence
        checks["checks"]["confidence"] = {
            "score": response.confidence,
            "threshold": 0.5,
            "passed": response.confidence >= 0.5,
        }

        # Overall pass
        all_passed = all(
            c.get("passed", True) for c in checks["checks"].values()
        )
        checks["overall_passed"] = all_passed

        if not all_passed:
            logger.warning("automated_checks_failed", query_id=query_id, checks=checks)

        return checks

    def get_quality_dashboard(self) -> dict:
        """
        Get quality dashboard data for monitoring.

        Returns comprehensive quality metrics.
        """
        aggregate = self.metrics.get_aggregate_metrics(24)
        language_breakdown = self.metrics.get_language_breakdown()

        return {
            "period": "24h",
            "total_queries": aggregate.total_queries,
            "latency": {
                "avg_ms": aggregate.avg_latency_ms,
                "p95_ms": aggregate.p95_latency_ms,
                "target_p95_ms": 3000,  # 3 second target
                "within_target": aggregate.p95_latency_ms < 3000,
            },
            "quality": {
                "avg_groundedness": aggregate.avg_groundedness,
                "avg_confidence": aggregate.avg_confidence,
                "groundedness_target": self.GROUNDEDNESS_THRESHOLD,
            },
            "routing": {
                "english_rate": aggregate.english_route_rate,
                "native_rate": aggregate.native_route_rate,
                "target_native_rate": 0.12,  # ~12% should route to native
            },
            "user_feedback": {
                "positive_rate": aggregate.positive_feedback_rate,
                "target_positive_rate": 0.67,  # 67% return rate target
            },
            "by_language": language_breakdown,
        }
