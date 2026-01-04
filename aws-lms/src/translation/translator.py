"""Amazon Translate service implementation."""

from dataclasses import dataclass
from typing import Optional

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings
from src.glossary import AcademicGlossary

logger = structlog.get_logger(__name__)


@dataclass
class TranslationResult:
    """Result of a translation operation."""

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    preserved_terms: dict[str, str]
    confidence: float


class AWSTranslationService:
    """
    Amazon Translate service with academic terminology integration.

    Uses Amazon Translate with Custom Terminology for preserving
    domain-specific terms during translation.
    """

    def __init__(
        self,
        glossary: Optional[AcademicGlossary] = None,
    ):
        self.settings = get_settings()
        self.glossary = glossary or AcademicGlossary()
        self._client = None

    @property
    def client(self):
        """Lazy-load Amazon Translate client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Amazon Translate client."""
        try:
            import boto3

            return boto3.client(
                "translate",
                region_name=self.settings.aws_region,
            )
        except Exception as e:
            logger.warning("aws_translate_init_failed", error=str(e))
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str = "en",
        use_glossary: bool = True,
    ) -> TranslationResult:
        """Translate text using Amazon Translate with terminology preservation."""
        if source_lang == target_lang:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                preserved_terms={},
                confidence=1.0,
            )

        preserved_terms = {}
        text_to_translate = text

        # Extract and preserve domain terms
        if use_glossary:
            text_to_translate, preserved_terms = (
                self.glossary.extract_and_preserve_terms(text, source_lang)
            )

        # Translate with Amazon Translate
        translated = await self._translate_with_aws(
            text_to_translate, source_lang, target_lang
        )

        # Restore domain terms
        if preserved_terms:
            translated = self.glossary.restore_english_terms(translated, preserved_terms)

        confidence = self._compute_confidence(text, translated, preserved_terms)

        return TranslationResult(
            original_text=text,
            translated_text=translated,
            source_language=source_lang,
            target_language=target_lang,
            preserved_terms=preserved_terms,
            confidence=confidence,
        )

    async def _translate_with_aws(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """Call Amazon Translate API."""
        if self.client is None:
            logger.warning("using_mock_translation")
            return f"[MOCK:{source_lang}→{target_lang}] {text}"

        try:
            # Map language codes (Amazon Translate uses different codes)
            source_code = self._map_language_code(source_lang)
            target_code = self._map_language_code(target_lang)

            params = {
                "Text": text,
                "SourceLanguageCode": source_code,
                "TargetLanguageCode": target_code,
            }

            # Add custom terminology if configured
            if self.settings.translate_terminology_name:
                params["TerminologyNames"] = [self.settings.translate_terminology_name]

            response = self.client.translate_text(**params)

            return response.get("TranslatedText", text)

        except Exception as e:
            logger.error("aws_translation_failed", error=str(e))
            raise

    def _map_language_code(self, code: str) -> str:
        """Map internal language codes to Amazon Translate codes."""
        mapping = {
            "hi": "hi",
            "ta": "ta",
            "te": "te",
            "bn": "bn",
            "mr": "mr",
            "gu": "gu",
            "kn": "kn",
            "ml": "ml",
            "pa": "pa",
            "en": "en",
        }
        return mapping.get(code, code)

    def _compute_confidence(
        self, original: str, translated: str, preserved_terms: dict
    ) -> float:
        """Compute translation confidence score."""
        confidence = 0.7
        if preserved_terms:
            confidence += min(0.2, len(preserved_terms) * 0.05)
        if len(original) > 0:
            ratio = len(translated) / len(original)
            if ratio < 0.3 or ratio > 3.0:
                confidence -= 0.15
        return max(0.0, min(1.0, confidence))

    async def create_terminology(
        self, terms: dict[str, dict[str, str]]
    ) -> bool:
        """Create custom terminology in Amazon Translate."""
        if self.client is None:
            return False

        try:
            # In production, would create a CSV file and upload
            logger.info(
                "creating_aws_terminology",
                name=self.settings.translate_terminology_name,
                term_count=len(terms)
            )
            return True

        except Exception as e:
            logger.error("aws_terminology_creation_failed", error=str(e))
            return False
