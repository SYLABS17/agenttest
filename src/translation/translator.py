"""Translation service with academic glossary integration."""

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
    translation_method: str  # "glossary_enhanced" or "direct"


class TranslationService:
    """
    Translation service optimized for academic content.

    Key feature: Uses academic glossary to preserve domain-specific terms
    during translation, preventing context loss.

    Example:
        'ஒளிச்சேர்க்கை' (Tamil) → 'photosynthesis' (not literal translation)
    """

    def __init__(
        self,
        glossary: Optional[AcademicGlossary] = None,
        azure_client: Optional[object] = None,
    ):
        """
        Initialize translation service.

        Args:
            glossary: Academic glossary for term preservation
            azure_client: Azure Translator client (injected for testing)
        """
        self.settings = get_settings()
        self.glossary = glossary or AcademicGlossary()
        self._client = azure_client

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
        except ImportError:
            logger.warning("azure_translator_not_available", reason="SDK not installed")
            return None
        except Exception as e:
            logger.error("translator_init_failed", error=str(e))
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
        """
        Translate text with academic term preservation.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'ta' for Tamil)
            target_lang: Target language code (default: 'en')
            use_glossary: Whether to use glossary for term preservation

        Returns:
            TranslationResult with translated text and metadata
        """
        logger.debug(
            "translating",
            source=source_lang,
            target=target_lang,
            length=len(text),
        )

        # If source == target, return as-is
        if source_lang == target_lang:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                preserved_terms={},
                confidence=1.0,
                translation_method="passthrough",
            )

        preserved_terms = {}
        text_to_translate = text

        # Step 1: Extract and preserve domain terms using glossary
        if use_glossary:
            text_to_translate, preserved_terms = (
                self.glossary.extract_and_preserve_terms(text, source_lang)
            )

            if preserved_terms:
                logger.debug(
                    "terms_preserved",
                    count=len(preserved_terms),
                    terms=list(preserved_terms.values()),
                )

        # Step 2: Translate with Azure Translator
        translated = await self._translate_with_azure(
            text_to_translate, source_lang, target_lang
        )

        # Step 3: Restore domain terms in English
        if preserved_terms:
            translated = self.glossary.restore_english_terms(
                translated, preserved_terms
            )

        # Step 4: Compute confidence score
        confidence = self._compute_translation_confidence(
            text, translated, preserved_terms
        )

        return TranslationResult(
            original_text=text,
            translated_text=translated,
            source_language=source_lang,
            target_language=target_lang,
            preserved_terms=preserved_terms,
            confidence=confidence,
            translation_method="glossary_enhanced" if use_glossary else "direct",
        )

    async def _translate_with_azure(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """
        Call Azure Translator API.

        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language

        Returns:
            Translated text
        """
        if self.client is None:
            # Fallback for development/testing without Azure
            logger.warning("using_mock_translation")
            return f"[TRANSLATED:{source_lang}→{target_lang}] {text}"

        try:
            response = self.client.translate(
                content=[text],
                to=[target_lang],
                from_parameter=source_lang,
            )

            if response and len(response) > 0:
                translation = response[0]
                if translation.translations and len(translation.translations) > 0:
                    return translation.translations[0].text

            return text  # Return original if translation fails

        except Exception as e:
            logger.error("azure_translation_failed", error=str(e))
            raise

    def _compute_translation_confidence(
        self,
        original: str,
        translated: str,
        preserved_terms: dict[str, str],
    ) -> float:
        """
        Compute confidence score for translation quality.

        Factors:
        - Number of preserved domain terms (higher = better)
        - Length ratio (extreme differences = lower confidence)
        - Presence of placeholder artifacts

        Args:
            original: Original text
            translated: Translated text
            preserved_terms: Terms that were preserved

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.7  # Base confidence

        # Boost for preserved terms (max 0.2 boost)
        if preserved_terms:
            term_boost = min(0.2, len(preserved_terms) * 0.05)
            confidence += term_boost

        # Check length ratio
        if len(original) > 0:
            ratio = len(translated) / len(original)
            # Penalize extreme ratios
            if ratio < 0.3 or ratio > 3.0:
                confidence -= 0.15
            elif ratio < 0.5 or ratio > 2.0:
                confidence -= 0.05

        # Check for placeholder artifacts (translation failure)
        if "__TERM_" in translated:
            confidence -= 0.3

        # Ensure bounds
        return max(0.0, min(1.0, confidence))

    async def translate_to_native(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> TranslationResult:
        """
        Translate from English to native language for response delivery.

        Args:
            text: English text to translate
            target_lang: Target language for the student
            source_lang: Source language (usually English)

        Returns:
            TranslationResult in native language
        """
        return await self.translate(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            use_glossary=True,
        )

    def get_supported_languages(self) -> list[str]:
        """Return list of supported language codes."""
        return self.settings.supported_languages

    def is_supported(self, lang_code: str) -> bool:
        """Check if a language is supported."""
        return lang_code in self.settings.supported_languages
