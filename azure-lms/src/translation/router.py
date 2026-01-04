"""Confidence-based routing for Azure implementation."""

from dataclasses import dataclass
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class RoutingDecision:
    """Result of routing decision."""

    index: str
    query: str
    original_query: str
    response_language: str
    confidence: float
    routing_reason: str


class TranslationRouter:
    """Confidence-based router for Azure AI Search indices."""

    def __init__(self, confidence_threshold: float = 0.75):
        self.settings = get_settings()
        self.threshold = confidence_threshold
        self.native_routing_indicators = [
            "poem", "poetry", "kavitha", "literature", "sahitya",
            "classical", "ancient", "grammar", "vyakaran",
        ]

    def route(
        self,
        original_query: str,
        source_lang: str,
        translated_query: str,
        translation_confidence: float,
    ) -> RoutingDecision:
        """Determine routing based on translation confidence."""
        if source_lang == "en":
            return RoutingDecision(
                index="english_unified",
                query=original_query,
                original_query=original_query,
                response_language="en",
                confidence=1.0,
                routing_reason="source_is_english",
            )

        if self._should_force_native_routing(translated_query):
            return RoutingDecision(
                index=f"{source_lang}_native",
                query=original_query,
                original_query=original_query,
                response_language=source_lang,
                confidence=translation_confidence,
                routing_reason="content_type_requires_native",
            )

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

    def _should_force_native_routing(self, query: str) -> bool:
        """Check if content type requires native routing."""
        query_lower = query.lower()
        for indicator in self.native_routing_indicators:
            if indicator in query_lower:
                return True
        return False
