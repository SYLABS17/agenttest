"""Metrics collection for LMS monitoring."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import time

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query."""

    query_id: str
    timestamp: datetime
    source_language: str
    target_language: str
    translation_confidence: float
    route_used: str  # "english_unified" or "{lang}_native"
    retrieval_count: int
    rerank_count: int
    groundedness_score: float
    response_confidence: float
    latency_ms: float
    tokens_used: int
    user_feedback: Optional[str] = None  # "positive", "negative", None


@dataclass
class AggregateMetrics:
    """Aggregated metrics over time period."""

    period_start: datetime
    period_end: datetime
    total_queries: int
    queries_by_language: dict[str, int]
    avg_latency_ms: float
    p95_latency_ms: float
    avg_groundedness: float
    avg_confidence: float
    english_route_rate: float
    native_route_rate: float
    positive_feedback_rate: float
    retry_rate: float  # User rephrasing = failed first attempt


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring.

    Key metrics tracked:
    - Latency (P50, P95, P99)
    - Groundedness scores
    - Translation confidence
    - Routing decisions
    - User feedback signals
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._query_metrics: list[QueryMetrics] = []
        self._start_times: dict[str, float] = {}

    def start_query(self, query_id: str) -> None:
        """Start timing a query."""
        self._start_times[query_id] = time.time()

    def end_query(
        self,
        query_id: str,
        source_language: str,
        target_language: str,
        translation_confidence: float,
        route_used: str,
        retrieval_count: int,
        rerank_count: int,
        groundedness_score: float,
        response_confidence: float,
        tokens_used: int,
    ) -> QueryMetrics:
        """
        Complete query timing and record metrics.

        Args:
            query_id: Unique query identifier
            source_language: Source language code
            target_language: Target language code
            translation_confidence: Translation quality score
            route_used: Index route used
            retrieval_count: Number of chunks retrieved
            rerank_count: Number of chunks after reranking
            groundedness_score: Groundedness of response
            response_confidence: Overall response confidence
            tokens_used: LLM tokens consumed

        Returns:
            QueryMetrics object
        """
        start_time = self._start_times.pop(query_id, time.time())
        latency_ms = (time.time() - start_time) * 1000

        metrics = QueryMetrics(
            query_id=query_id,
            timestamp=datetime.utcnow(),
            source_language=source_language,
            target_language=target_language,
            translation_confidence=translation_confidence,
            route_used=route_used,
            retrieval_count=retrieval_count,
            rerank_count=rerank_count,
            groundedness_score=groundedness_score,
            response_confidence=response_confidence,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
        )

        self._query_metrics.append(metrics)
        self._emit_metrics(metrics)

        return metrics

    def record_feedback(
        self,
        query_id: str,
        feedback: str,
    ) -> None:
        """
        Record user feedback for a query.

        Args:
            query_id: Query identifier
            feedback: "positive" or "negative"
        """
        for metrics in reversed(self._query_metrics):
            if metrics.query_id == query_id:
                metrics.user_feedback = feedback
                logger.info(
                    "feedback_recorded",
                    query_id=query_id,
                    feedback=feedback,
                    language=metrics.source_language,
                )
                break

    def get_aggregate_metrics(
        self,
        period_hours: int = 24,
    ) -> AggregateMetrics:
        """
        Get aggregated metrics for a time period.

        Args:
            period_hours: Number of hours to aggregate

        Returns:
            AggregateMetrics object
        """
        now = datetime.utcnow()
        cutoff = datetime.utcnow().replace(
            hour=now.hour - period_hours if now.hour >= period_hours else 0
        )

        recent = [m for m in self._query_metrics if m.timestamp >= cutoff]

        if not recent:
            return AggregateMetrics(
                period_start=cutoff,
                period_end=now,
                total_queries=0,
                queries_by_language={},
                avg_latency_ms=0,
                p95_latency_ms=0,
                avg_groundedness=0,
                avg_confidence=0,
                english_route_rate=0,
                native_route_rate=0,
                positive_feedback_rate=0,
                retry_rate=0,
            )

        # Calculate aggregates
        latencies = sorted([m.latency_ms for m in recent])
        p95_index = int(len(latencies) * 0.95)

        queries_by_lang = {}
        for m in recent:
            queries_by_lang[m.source_language] = queries_by_lang.get(m.source_language, 0) + 1

        english_routes = sum(1 for m in recent if m.route_used == "english_unified")
        with_feedback = [m for m in recent if m.user_feedback]
        positive = sum(1 for m in with_feedback if m.user_feedback == "positive")

        return AggregateMetrics(
            period_start=cutoff,
            period_end=now,
            total_queries=len(recent),
            queries_by_language=queries_by_lang,
            avg_latency_ms=sum(latencies) / len(latencies),
            p95_latency_ms=latencies[p95_index] if latencies else 0,
            avg_groundedness=sum(m.groundedness_score for m in recent) / len(recent),
            avg_confidence=sum(m.response_confidence for m in recent) / len(recent),
            english_route_rate=english_routes / len(recent),
            native_route_rate=1 - (english_routes / len(recent)),
            positive_feedback_rate=positive / len(with_feedback) if with_feedback else 0,
            retry_rate=0,  # Would need session tracking
        )

    def _emit_metrics(self, metrics: QueryMetrics) -> None:
        """Emit metrics to monitoring system."""
        logger.info(
            "query_metrics",
            query_id=metrics.query_id,
            language=metrics.source_language,
            route=metrics.route_used,
            latency_ms=round(metrics.latency_ms, 2),
            groundedness=round(metrics.groundedness_score, 3),
            confidence=round(metrics.response_confidence, 3),
        )

    def get_language_breakdown(self) -> dict[str, dict]:
        """Get metrics broken down by language."""
        breakdown = {}

        for metrics in self._query_metrics:
            lang = metrics.source_language
            if lang not in breakdown:
                breakdown[lang] = {
                    "count": 0,
                    "total_latency": 0,
                    "total_groundedness": 0,
                    "positive_feedback": 0,
                    "negative_feedback": 0,
                }

            breakdown[lang]["count"] += 1
            breakdown[lang]["total_latency"] += metrics.latency_ms
            breakdown[lang]["total_groundedness"] += metrics.groundedness_score

            if metrics.user_feedback == "positive":
                breakdown[lang]["positive_feedback"] += 1
            elif metrics.user_feedback == "negative":
                breakdown[lang]["negative_feedback"] += 1

        # Calculate averages
        for lang, data in breakdown.items():
            count = data["count"]
            data["avg_latency_ms"] = data["total_latency"] / count if count else 0
            data["avg_groundedness"] = data["total_groundedness"] / count if count else 0

        return breakdown

    def export_to_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        aggregate = self.get_aggregate_metrics(24)

        lines.append(f"lms_total_queries {{period=\"24h\"}} {aggregate.total_queries}")
        lines.append(f"lms_avg_latency_ms {{period=\"24h\"}} {aggregate.avg_latency_ms:.2f}")
        lines.append(f"lms_p95_latency_ms {{period=\"24h\"}} {aggregate.p95_latency_ms:.2f}")
        lines.append(f"lms_avg_groundedness {{period=\"24h\"}} {aggregate.avg_groundedness:.3f}")
        lines.append(f"lms_english_route_rate {{period=\"24h\"}} {aggregate.english_route_rate:.3f}")

        return "\n".join(lines)
