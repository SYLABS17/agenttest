"""Translation quality judge using LLM evaluation."""

from dataclasses import dataclass
from typing import Optional

import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class JudgmentResult:
    """Result of translation quality judgment."""

    original_text: str
    translated_text: str
    fidelity_score: float  # 0.0 to 1.0
    semantic_preservation: float
    term_accuracy: float
    fluency: float
    reasoning: str
    recommendations: list[str]


class TranslationJudge:
    """
    LLM-based judge for evaluating translation quality.

    Used for confidence-based routing decisions:
    - Score >= 0.75 → Route to English unified index
    - Score < 0.75 → Route to native language index

    The judge evaluates:
    1. Semantic preservation (is meaning intact?)
    2. Term accuracy (are academic terms correct?)
    3. Fluency (is the translation natural?)
    """

    JUDGE_PROMPT = """You are a translation quality evaluator for an educational system.
Evaluate the translation quality from {source_lang} to {target_lang}.

ORIGINAL TEXT ({source_lang}):
{original_text}

TRANSLATED TEXT ({target_lang}):
{translated_text}

ACADEMIC TERMS IDENTIFIED:
{terms}

Evaluate on a scale of 0.0 to 1.0:

1. SEMANTIC PRESERVATION: Is the core meaning preserved?
   - 1.0: Perfect preservation of all meaning
   - 0.7: Minor nuances lost but main idea intact
   - 0.5: Some meaning lost or distorted
   - 0.3: Significant meaning loss
   - 0.0: Complete meaning loss

2. TERM ACCURACY: Are academic/technical terms translated correctly?
   - 1.0: All terms are correctly translated or properly preserved
   - 0.7: Minor term issues that don't affect understanding
   - 0.5: Some terms incorrectly translated
   - 0.3: Multiple critical terms wrong
   - 0.0: Terms completely wrong

3. FLUENCY: Is the translation natural and readable?
   - 1.0: Native-like fluency
   - 0.7: Minor awkwardness but clear
   - 0.5: Understandable but noticeably translated
   - 0.3: Difficult to read
   - 0.0: Incomprehensible

Respond in JSON format:
{{
    "semantic_preservation": <float>,
    "term_accuracy": <float>,
    "fluency": <float>,
    "overall_fidelity": <float>,
    "reasoning": "<brief explanation>",
    "recommendations": ["<any suggestions for improvement>"]
}}
"""

    def __init__(self, llm_client: Optional[object] = None):
        """
        Initialize the translation judge.

        Args:
            llm_client: LLM client for evaluation (Azure OpenAI or similar)
        """
        self.settings = get_settings()
        self._client = llm_client

    @property
    def client(self):
        """Lazy-load LLM client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Azure OpenAI client for judgment."""
        try:
            from openai import AzureOpenAI

            return AzureOpenAI(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
            )
        except Exception as e:
            logger.warning("llm_client_init_failed", error=str(e))
            return None

    async def evaluate_translation(
        self,
        original: str,
        translated: str,
        source_lang: str,
        target_lang: str,
        identified_terms: Optional[list[str]] = None,
    ) -> JudgmentResult:
        """
        Evaluate translation quality using LLM.

        Args:
            original: Original text
            translated: Translated text
            source_lang: Source language code
            target_lang: Target language code
            identified_terms: List of academic terms in the text

        Returns:
            JudgmentResult with detailed scores
        """
        logger.debug(
            "evaluating_translation",
            source_lang=source_lang,
            target_lang=target_lang,
        )

        # If no LLM client available, use heuristic scoring
        if self.client is None:
            return self._heuristic_evaluation(
                original, translated, source_lang, target_lang
            )

        # Prepare prompt
        terms_str = ", ".join(identified_terms) if identified_terms else "None identified"
        prompt = self.JUDGE_PROMPT.format(
            source_lang=source_lang,
            target_lang=target_lang,
            original_text=original,
            translated_text=translated,
            terms=terms_str,
        )

        try:
            # Call LLM for evaluation
            response = self.client.chat.completions.create(
                model=self.settings.azure_openai_chat_deployment,
                messages=[
                    {"role": "system", "content": "You are a translation quality evaluator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistent evaluation
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            # Parse response
            import json
            result = json.loads(response.choices[0].message.content)

            return JudgmentResult(
                original_text=original,
                translated_text=translated,
                fidelity_score=result.get("overall_fidelity", 0.7),
                semantic_preservation=result.get("semantic_preservation", 0.7),
                term_accuracy=result.get("term_accuracy", 0.7),
                fluency=result.get("fluency", 0.7),
                reasoning=result.get("reasoning", ""),
                recommendations=result.get("recommendations", []),
            )

        except Exception as e:
            logger.error("llm_evaluation_failed", error=str(e))
            return self._heuristic_evaluation(
                original, translated, source_lang, target_lang
            )

    def _heuristic_evaluation(
        self,
        original: str,
        translated: str,
        source_lang: str,
        target_lang: str,
    ) -> JudgmentResult:
        """
        Fallback heuristic-based evaluation when LLM is unavailable.

        Uses simple metrics like length ratio, character analysis, etc.
        """
        # Length ratio check
        length_ratio = len(translated) / len(original) if len(original) > 0 else 1.0

        # Penalize extreme ratios
        if 0.5 <= length_ratio <= 2.0:
            ratio_score = 0.8
        elif 0.3 <= length_ratio <= 3.0:
            ratio_score = 0.6
        else:
            ratio_score = 0.4

        # Check for placeholder artifacts (translation failures)
        artifact_penalty = 0.0
        if "__TERM_" in translated or "TRANSLATED" in translated:
            artifact_penalty = 0.2

        # Base score with adjustments
        base_score = 0.75
        fidelity = base_score * ratio_score - artifact_penalty

        return JudgmentResult(
            original_text=original,
            translated_text=translated,
            fidelity_score=max(0.0, min(1.0, fidelity)),
            semantic_preservation=ratio_score,
            term_accuracy=0.7,  # Default when no LLM
            fluency=0.7,
            reasoning="Heuristic evaluation (LLM unavailable)",
            recommendations=[],
        )

    def score(
        self,
        original: str,
        translated: str,
        source_lang: str,
    ) -> float:
        """
        Quick synchronous scoring for routing decisions.

        Args:
            original: Original text
            translated: Translated text
            source_lang: Source language

        Returns:
            Fidelity score between 0.0 and 1.0
        """
        # Use heuristic for quick sync scoring
        result = self._heuristic_evaluation(
            original, translated, source_lang, "en"
        )
        return result.fidelity_score
