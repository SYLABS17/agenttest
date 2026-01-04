"""Confidence-based routing for translation and search."""

from dataclasses import dataclass
from typing import Literal

import structlog

from src.config import get_settings
from src.translation.judge import TranslationJudge

logger = structlog.get_logger(__name__)


@dataclass
class RoutingDecision:
    """Result of routing decision."""

    index: str  # "english_unified" or "{lang}_native"
    query: str  # Query to use for search
    original_query: str
    response_language: str
    confidence: float
    routing_reason: str


class TranslationRouter:
    """
    Confidence-based router for query processing.

    Routes queries to either:
    1. English unified index (when translation confidence >= 75%)
    2. Native language index (when translation confidence < 75%)

    Critical for handling:
    - Scientific/mathematical content → typically English index
    - Literature, poetry, regional content → typically native index
    """

    def __init__(
        self,
        confidence_threshold: float = 0.75,
        judge: TranslationJudge | None = None,
    ):
        """
        Initialize the translation router.

        Args:
            confidence_threshold: Minimum confidence for English routing (default: 0.75)
            judge: Translation quality judge (created if not provided)
        """
        self.settings = get_settings()
        self.threshold = confidence_threshold
        self.judge = judge or TranslationJudge()

        # Content types that typically route to native indices
        self.native_routing_indicators = [
            # Literature and poetry
            "poem", "poetry", "kavitha", "kavya",
            "literature", "sahitya",
            # Regional history and culture
            "local history", "regional", "folklore",
            # Classical texts
            "classical", "ancient", "vedic",
            # Language-specific grammar
            "grammar", "vyakaran",
        ]

    def route(
        self,
        original_query: str,
        source_lang: str,
        translated_query: str,
        translation_confidence: float,
    ) -> RoutingDecision:
        """
        Determine routing based on translation confidence.

        Args:
            original_query: Query in source language
            source_lang: Source language code
            translated_query: Query translated to English
            translation_confidence: Confidence from translation service

        Returns:
            RoutingDecision with index and query to use
        """
        # English queries always route to English index
        if source_lang == "en":
            return RoutingDecision(
                index="english_unified",
                query=original_query,
                original_query=original_query,
                response_language="en",
                confidence=1.0,
                routing_reason="source_is_english",
            )

        # Check for content that should route to native
        if self._should_force_native_routing(original_query, translated_query):
            return RoutingDecision(
                index=f"{source_lang}_native",
                query=original_query,
                original_query=original_query,
                response_language=source_lang,
                confidence=translation_confidence,
                routing_reason="content_type_requires_native",
            )

        # Use confidence threshold for routing decision
        if translation_confidence >= self.threshold:
            return RoutingDecision(
                index="english_unified",
                query=translated_query,
                original_query=original_query,
                response_language=source_lang,
                confidence=translation_confidence,
                routing_reason="high_confidence_translation",
            )
        else:
            return RoutingDecision(
                index=f"{source_lang}_native",
                query=original_query,
                original_query=original_query,
                response_language=source_lang,
                confidence=translation_confidence,
                routing_reason="low_confidence_fallback",
            )

    def _should_force_native_routing(
        self, original_query: str, translated_query: str
    ) -> bool:
        """
        Check if content type requires native language routing.

        Certain content types (literature, poetry, regional history)
        should always use native indices regardless of translation confidence.

        Args:
            original_query: Original query
            translated_query: Translated query

        Returns:
            True if native routing should be forced
        """
        query_lower = translated_query.lower()

        for indicator in self.native_routing_indicators:
            if indicator in query_lower:
                logger.debug(
                    "forcing_native_routing",
                    indicator=indicator,
                    query=translated_query[:100],
                )
                return True

        return False

    async def route_with_evaluation(
        self,
        original_query: str,
        source_lang: str,
        translated_query: str,
    ) -> RoutingDecision:
        """
        Route with full LLM-based translation evaluation.

        More accurate but slower than simple confidence routing.
        Use for queries where accuracy is critical.

        Args:
            original_query: Query in source language
            source_lang: Source language code
            translated_query: Query translated to English

        Returns:
            RoutingDecision with detailed evaluation
        """
        # Get detailed evaluation from judge
        judgment = await self.judge.evaluate_translation(
            original=original_query,
            translated=translated_query,
            source_lang=source_lang,
            target_lang="en",
        )

        # Use weighted average of scores for routing
        weighted_confidence = (
            judgment.semantic_preservation * 0.5
            + judgment.term_accuracy * 0.3
            + judgment.fluency * 0.2
        )

        return self.route(
            original_query=original_query,
            source_lang=source_lang,
            translated_query=translated_query,
            translation_confidence=weighted_confidence,
        )

    def get_fallback_rate_stats(self) -> dict:
        """
        Return statistics about fallback routing.

        For monitoring and optimization. Target: ~12% fallback rate.
        """
        # This would typically query metrics storage
        return {
            "target_fallback_rate": 0.12,
            "description": "Approximately 12% of queries route to native indices",
        }

    def get_available_indices(self) -> list[str]:
        """Return list of available search indices."""
        indices = ["english_unified"]
        for lang in self.settings.supported_languages:
            if lang != "en":
                indices.append(f"{lang}_native")
        return indices
