"""Term extraction utilities for academic content."""

import re
from dataclasses import dataclass
from typing import Optional

import structlog

from src.glossary.academic_glossary import AcademicGlossary

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedTerm:
    """Represents an extracted academic term."""

    term: str
    english_equivalent: str
    start_pos: int
    end_pos: int
    confidence: float
    subject: Optional[str] = None


class TermExtractor:
    """
    Extract and identify academic terms from text in any supported language.

    Used for:
    1. Pre-processing queries before translation
    2. Identifying topics for search filtering
    3. Logging glossary misses for expansion
    """

    def __init__(self, glossary: Optional[AcademicGlossary] = None):
        """Initialize term extractor with optional glossary."""
        self.glossary = glossary or AcademicGlossary()
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for term detection."""
        # Common academic term indicators
        self.term_indicators = {
            "en": [
                r"what is (?:the |a )?(.+?)\??$",
                r"define (.+?)\.?$",
                r"explain (.+?)\.?$",
                r"(.+?) (?:is|are|means?)",
            ],
            "hi": [
                r"(.+?) क्या है",
                r"(.+?) की परिभाषा",
                r"(.+?) को समझाइए",
            ],
            "ta": [
                r"(.+?) என்றால் என்ன",
                r"(.+?) விளக்கம்",
            ],
        }

    def extract_terms(
        self, text: str, language: str
    ) -> list[ExtractedTerm]:
        """
        Extract academic terms from text.

        Args:
            text: Input text
            language: ISO language code

        Returns:
            List of extracted terms with metadata
        """
        extracted = []

        # Find terms from glossary
        found_terms = self.glossary.find_terms_in_text(text, language)

        for term_info in found_terms:
            # Find position in text
            term = term_info["term"]
            match = re.search(re.escape(term), text, re.IGNORECASE)

            if match:
                extracted.append(
                    ExtractedTerm(
                        term=term,
                        english_equivalent=term_info["english"],
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=1.0,  # Glossary match = high confidence
                        subject=self._infer_subject(term_info["english"]),
                    )
                )

        # Sort by position
        extracted.sort(key=lambda x: x.start_pos)

        logger.debug(
            "terms_extracted",
            language=language,
            count=len(extracted),
            terms=[t.english_equivalent for t in extracted],
        )

        return extracted

    def extract_question_focus(
        self, question: str, language: str
    ) -> Optional[str]:
        """
        Extract the main topic/focus of a question.

        Args:
            question: The question text
            language: ISO language code

        Returns:
            Main topic term if identified, None otherwise
        """
        # Try pattern matching first
        patterns = self.term_indicators.get(language, [])
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                # Check if it's a known term
                english = self.glossary.get_english_term(topic, language)
                if english:
                    return english
                return topic

        # Fall back to extracted terms
        terms = self.extract_terms(question, language)
        if terms:
            # Return the term with highest confidence
            return max(terms, key=lambda t: t.confidence).english_equivalent

        return None

    def log_unknown_term(
        self, term: str, language: str, context: str
    ) -> None:
        """
        Log a potential term that's not in the glossary for future review.

        Args:
            term: The unknown term
            language: Source language
            context: Surrounding text for context
        """
        logger.info(
            "glossary_miss",
            term=term,
            language=language,
            context=context[:200],  # Truncate for logging
        )

    def _infer_subject(self, english_term: str) -> Optional[str]:
        """Infer the subject area from a term."""
        # Simple keyword-based classification
        subject_keywords = {
            "biology": [
                "photosynthesis", "chlorophyll", "mitochondria", "cell",
                "nucleus", "chromosome", "dna", "enzyme", "protein",
                "respiration", "digestion", "nervous",
            ],
            "mathematics": [
                "equation", "polynomial", "derivative", "integral",
                "trigonometry", "logarithm", "probability", "statistics",
                "algebra", "geometry", "calculus",
            ],
            "physics": [
                "velocity", "acceleration", "momentum", "gravity",
                "electromagnetism", "thermodynamics", "force", "energy",
                "wave", "optics", "quantum",
            ],
            "chemistry": [
                "reaction", "periodic", "oxidation", "reduction",
                "bond", "ionic", "covalent", "acid", "base", "salt",
            ],
            "computer_science": [
                "algorithm", "data structure", "recursion", "variable",
                "function", "loop", "array", "database",
            ],
        }

        term_lower = english_term.lower()
        for subject, keywords in subject_keywords.items():
            for keyword in keywords:
                if keyword in term_lower:
                    return subject

        return None

    def get_subject_terms(self, subject: str, language: str) -> list[str]:
        """
        Get all terms for a specific subject in a language.

        Args:
            subject: Subject area (biology, mathematics, etc.)
            language: ISO language code

        Returns:
            List of terms in the specified language
        """
        terms = []
        for english_term, translations in self.glossary.terms.items():
            if self._infer_subject(english_term) == subject:
                if language in translations:
                    terms.append(translations[language])
                elif language == "en":
                    terms.append(english_term)
        return terms
