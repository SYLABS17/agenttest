"""Azure Translator service implementation."""

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


class AzureTranslationService:
    """
    Azure Translator service with academic glossary integration.

    Uses Azure Cognitive Services Translator with custom glossary
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
        """Lazy-load Azure Translator client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Azure Translator client."""
        try:
            from azure.ai.translation.text import TextTranslationClient
            from azure.core.credentials import AzureKeyCredential

            credential = AzureKeyCredential(self.settings.azure_translator_key)
            return TextTranslationClient(
                endpoint=self.settings.azure_translator_endpoint,
                credential=credential,
                region=self.settings.azure_translator_region,
            )
        except Exception as e:
            logger.warning("azure_translator_init_failed", error=str(e))
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
        """Translate text using Azure Translator with glossary preservation."""
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

        # Translate with Azure
        translated = await self._translate_with_azure(
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

    async def _translate_with_azure(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """Call Azure Translator API."""
        if self.client is None:
            logger.warning("using_mock_translation")
            return f"[MOCK:{source_lang}→{target_lang}] {text}"

        try:
            response = self.client.translate(
                content=[text],
                to=[target_lang],
                from_parameter=source_lang,
            )

            if response and len(response) > 0:
                translation = response[0]
                if translation.translations:
                    return translation.translations[0].text
            return text

        except Exception as e:
            logger.error("azure_translation_failed", error=str(e))
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
