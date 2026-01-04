"""Tests for translation service."""

import pytest
from src.translation import TranslationService, TranslationRouter, TranslationJudge


class TestTranslationService:
    """Tests for TranslationService."""

    @pytest.mark.asyncio
    async def test_passthrough_same_language(self):
        """Test that same-language translation passes through."""
        translator = TranslationService()
        result = await translator.translate(
            text="Hello world",
            source_lang="en",
            target_lang="en",
        )

        assert result.translated_text == "Hello world"
        assert result.confidence == 1.0
        assert result.translation_method == "passthrough"

    @pytest.mark.asyncio
    async def test_translation_with_glossary(self):
        """Test translation with glossary term preservation."""
        translator = TranslationService()
        result = await translator.translate(
            text="प्रकाश संश्लेषण क्या है?",
            source_lang="hi",
            target_lang="en",
            use_glossary=True,
        )

        # Should have preserved the academic term
        assert result.translation_method == "glossary_enhanced"
        assert len(result.preserved_terms) > 0 or result.confidence > 0

    def test_supported_languages(self):
        """Test that all 15 languages are supported."""
        translator = TranslationService()
        languages = translator.get_supported_languages()

        assert len(languages) >= 15
        assert "hi" in languages
        assert "ta" in languages
        assert "en" in languages


class TestTranslationRouter:
    """Tests for TranslationRouter."""

    def test_english_query_routes_to_english_index(self):
        """Test that English queries route to English index."""
        router = TranslationRouter()
        decision = router.route(
            original_query="What is photosynthesis?",
            source_lang="en",
            translated_query="What is photosynthesis?",
            translation_confidence=1.0,
        )

        assert decision.index == "english_unified"
        assert decision.routing_reason == "source_is_english"

    def test_high_confidence_routes_to_english(self):
        """Test high confidence translation routes to English index."""
        router = TranslationRouter()
        decision = router.route(
            original_query="प्रकाश संश्लेषण क्या है?",
            source_lang="hi",
            translated_query="What is photosynthesis?",
            translation_confidence=0.85,
        )

        assert decision.index == "english_unified"
        assert decision.confidence >= 0.75

    def test_low_confidence_routes_to_native(self):
        """Test low confidence translation routes to native index."""
        router = TranslationRouter()
        decision = router.route(
            original_query="कविता का अर्थ क्या है?",
            source_lang="hi",
            translated_query="What is the meaning of poetry?",
            translation_confidence=0.60,
        )

        assert decision.index == "hi_native"
        assert decision.routing_reason == "low_confidence_fallback"

    def test_content_type_forces_native(self):
        """Test that certain content types force native routing."""
        router = TranslationRouter()
        decision = router.route(
            original_query="तमिल कविता क्या है?",
            source_lang="hi",
            translated_query="What is Tamil poetry?",
            translation_confidence=0.90,
        )

        # Poetry should route to native despite high confidence
        assert decision.routing_reason == "content_type_requires_native"


class TestTranslationJudge:
    """Tests for TranslationJudge."""

    def test_heuristic_evaluation(self):
        """Test heuristic evaluation when LLM unavailable."""
        judge = TranslationJudge()
        result = judge._heuristic_evaluation(
            original="प्रकाश संश्लेषण क्या है?",
            translated="What is photosynthesis?",
            source_lang="hi",
            target_lang="en",
        )

        assert 0 <= result.fidelity_score <= 1.0
        assert result.reasoning != ""

    def test_score_method(self):
        """Test quick scoring method."""
        judge = TranslationJudge()
        score = judge.score(
            original="Hello world",
            translated="Hello world",
            source_lang="en",
        )

        assert 0 <= score <= 1.0
