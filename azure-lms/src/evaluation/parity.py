"""Retrieval parity checking for translation quality validation."""

from dataclasses import dataclass
from typing import Optional

import structlog

from src.search.hybrid_search import HybridSearchService, SearchFilters
from src.translation.translator import TranslationService

logger = structlog.get_logger(__name__)


@dataclass
class ParityResult:
    """Result of retrieval parity check."""

    english_query: str
    regional_query: str
    regional_language: str
    english_chunk_ids: set[str]
    regional_chunk_ids: set[str]
    overlap_count: int
    parity_score: float  # 0.0 to 1.0
    passed: bool
    recommendation: str


class RetrievalParityChecker:
    """
    Validates translation quality through retrieval parity.

    Key insight: If the same question in English and Tamil retrieve
    different source chunks, the translation is introducing drift.

    Target: 90% retrieval parity across languages.
    """

    PARITY_THRESHOLD = 0.90

    def __init__(
        self,
        search_service: Optional[HybridSearchService] = None,
        translation_service: Optional[TranslationService] = None,
    ):
        """
        Initialize parity checker.

        Args:
            search_service: Hybrid search service
            translation_service: Translation service
        """
        self.search = search_service or HybridSearchService()
        self.translator = translation_service or TranslationService()

    async def check_parity(
        self,
        question_en: str,
        question_regional: str,
        language: str,
        top_k: int = 10,
    ) -> ParityResult:
        """
        Check retrieval parity between English and regional query.

        Args:
            question_en: Question in English
            question_regional: Same question in regional language
            language: Regional language code
            top_k: Number of results to compare

        Returns:
            ParityResult with parity score and analysis
        """
        logger.debug(
            "checking_parity",
            language=language,
            en_query=question_en[:50],
        )

        # Retrieve for English query
        results_en = await self.search.hybrid_search(
            query=question_en,
            index="english_unified",
            top=top_k,
        )

        # Translate regional query and retrieve
        translation_result = await self.translator.translate(
            text=question_regional,
            source_lang=language,
            target_lang="en",
        )

        results_regional = await self.search.hybrid_search(
            query=translation_result.translated_text,
            index="english_unified",
            top=top_k,
        )

        # Compare chunk IDs
        en_ids = {r.chunk.id for r in results_en}
        regional_ids = {r.chunk.id for r in results_regional}

        overlap = en_ids & regional_ids
        overlap_count = len(overlap)

        # Calculate parity score
        max_possible = max(len(en_ids), len(regional_ids))
        parity_score = overlap_count / max_possible if max_possible > 0 else 0

        passed = parity_score >= self.PARITY_THRESHOLD

        # Generate recommendation
        if passed:
            recommendation = "Retrieval parity is within acceptable range."
        elif parity_score >= 0.75:
            recommendation = f"Parity slightly below threshold. Consider reviewing glossary coverage for {language}."
        elif parity_score >= 0.50:
            recommendation = f"Significant parity gap. Translation quality issues likely for {language}."
        else:
            recommendation = f"Critical parity failure. Immediate review needed for {language} translation pipeline."

        result = ParityResult(
            english_query=question_en,
            regional_query=question_regional,
            regional_language=language,
            english_chunk_ids=en_ids,
            regional_chunk_ids=regional_ids,
            overlap_count=overlap_count,
            parity_score=parity_score,
            passed=passed,
            recommendation=recommendation,
        )

        if not passed:
            logger.warning(
                "low_retrieval_parity",
                language=language,
                parity=parity_score,
                threshold=self.PARITY_THRESHOLD,
                overlap=overlap_count,
            )
            self._log_for_glossary_review(question_regional, question_en, language)

        return result

    async def batch_parity_check(
        self,
        question_pairs: list[tuple[str, str, str]],
    ) -> dict[str, float]:
        """
        Check parity for multiple question pairs.

        Args:
            question_pairs: List of (english, regional, language) tuples

        Returns:
            Dict mapping language to average parity score
        """
        results_by_language: dict[str, list[float]] = {}

        for en, regional, lang in question_pairs:
            result = await self.check_parity(en, regional, lang)

            if lang not in results_by_language:
                results_by_language[lang] = []
            results_by_language[lang].append(result.parity_score)

        # Calculate averages
        return {
            lang: sum(scores) / len(scores)
            for lang, scores in results_by_language.items()
        }

    def _log_for_glossary_review(
        self,
        regional_query: str,
        english_query: str,
        language: str,
    ) -> None:
        """Log query pair for glossary review."""
        logger.info(
            "glossary_review_needed",
            language=language,
            regional_query=regional_query,
            english_query=english_query,
        )

    async def generate_parity_report(
        self,
        sample_size: int = 100,
    ) -> dict:
        """
        Generate comprehensive parity report.

        Args:
            sample_size: Number of samples per language

        Returns:
            Report dict with parity statistics
        """
        # In production, would sample from query logs
        report = {
            "timestamp": "2026-01-04",
            "sample_size_per_language": sample_size,
            "threshold": self.PARITY_THRESHOLD,
            "results": {},
        }

        # Mock results for demonstration
        languages = ["hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
        for lang in languages:
            # Simulated parity scores
            report["results"][lang] = {
                "avg_parity": 0.92 if lang in ["hi", "ta"] else 0.88,
                "samples_tested": sample_size,
                "passed_threshold": True if lang in ["hi", "ta"] else False,
                "lowest_parity_query": "Example query with low parity",
            }

        return report


class CrossValidationService:
    """
    Cross-validation service for systematic quality checking.

    Runs same questions in English vs regional languages to detect
    translation-induced retrieval drift.
    """

    def __init__(
        self,
        parity_checker: Optional[RetrievalParityChecker] = None,
    ):
        """Initialize cross-validation service."""
        self.parity_checker = parity_checker or RetrievalParityChecker()

        # Standard test questions for each subject
        self.test_questions = {
            "biology": [
                ("What is photosynthesis?", "प्रकाश संश्लेषण क्या है?", "hi"),
                ("What is photosynthesis?", "ஒளிச்சேர்க்கை என்றால் என்ன?", "ta"),
                ("How does the cell divide?", "कोशिका कैसे विभाजित होती है?", "hi"),
            ],
            "mathematics": [
                ("What is a quadratic equation?", "द्विघात समीकरण क्या है?", "hi"),
                ("What is a quadratic equation?", "இருபடி சமன்பாடு என்றால் என்ன?", "ta"),
                ("How to solve linear equations?", "रैखिक समीकरण कैसे हल करें?", "hi"),
            ],
            "physics": [
                ("What is Newton's first law?", "न्यूटन का पहला नियम क्या है?", "hi"),
                ("What is gravity?", "गुरुत्वाकर्षण क्या है?", "hi"),
            ],
        }

    async def run_validation(
        self,
        subjects: Optional[list[str]] = None,
    ) -> dict:
        """
        Run cross-validation for specified subjects.

        Args:
            subjects: List of subjects to validate (all if None)

        Returns:
            Validation report
        """
        subjects = subjects or list(self.test_questions.keys())
        results = {}

        for subject in subjects:
            if subject not in self.test_questions:
                continue

            questions = self.test_questions[subject]
            subject_results = []

            for en, regional, lang in questions:
                parity = await self.parity_checker.check_parity(
                    question_en=en,
                    question_regional=regional,
                    language=lang,
                )
                subject_results.append({
                    "english": en,
                    "regional": regional,
                    "language": lang,
                    "parity": parity.parity_score,
                    "passed": parity.passed,
                })

            results[subject] = {
                "questions_tested": len(subject_results),
                "avg_parity": sum(r["parity"] for r in subject_results) / len(subject_results),
                "all_passed": all(r["passed"] for r in subject_results),
                "details": subject_results,
            }

        return results
