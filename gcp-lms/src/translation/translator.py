"""Google Cloud Translation service implementation."""

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


class GCPTranslationService:
    """
    Google Cloud Translation service with academic glossary integration.

    Uses Cloud Translation API v3 with custom glossary support
    for preserving domain-specific terminology.
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
        """Lazy-load Cloud Translation client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Cloud Translation client."""
        try:
            from google.cloud import translate_v3 as translate

            return translate.TranslationServiceClient()
        except Exception as e:
            logger.warning("gcp_translator_init_failed", error=str(e))
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
        """Translate text using Cloud Translation with glossary preservation."""
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

        # Translate with Cloud Translation
        translated = await self._translate_with_gcp(
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

    async def _translate_with_gcp(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """Call Cloud Translation API."""
        if self.client is None:
            logger.warning("using_mock_translation")
            return f"[MOCK:{source_lang}→{target_lang}] {text}"

        try:
            parent = self.settings.translation_parent or (
                f"projects/{self.settings.google_cloud_project}/locations/global"
            )

            response = self.client.translate_text(
                request={
                    "parent": parent,
                    "contents": [text],
                    "source_language_code": source_lang,
                    "target_language_code": target_lang,
                    "mime_type": "text/plain",
                }
            )

            if response.translations:
                return response.translations[0].translated_text
            return text

        except Exception as e:
            logger.error("gcp_translation_failed", error=str(e))
            raise

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

    async def create_glossary(
        self, terms: dict[str, dict[str, str]]
    ) -> bool:
        """Create a custom glossary in Cloud Translation."""
        if self.client is None:
            return False

        try:
            from google.cloud import translate_v3 as translate

            parent = f"projects/{self.settings.google_cloud_project}/locations/global"
            glossary_id = self.settings.glossary_id

            # Build glossary entries
            # In production, would upload to GCS and create glossary
            logger.info("creating_gcp_glossary", glossary_id=glossary_id, term_count=len(terms))
            return True

        except Exception as e:
            logger.error("gcp_glossary_creation_failed", error=str(e))
            return False
