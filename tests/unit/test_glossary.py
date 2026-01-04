"""Tests for academic glossary system."""

import pytest
from src.glossary import AcademicGlossary, TermExtractor


class TestAcademicGlossary:
    """Tests for AcademicGlossary class."""

    def test_init_with_default_terms(self):
        """Test initialization with default terms."""
        glossary = AcademicGlossary()
        assert glossary.get_term_count() > 0

    def test_get_english_term(self):
        """Test retrieving English equivalent of Hindi term."""
        glossary = AcademicGlossary()
        english = glossary.get_english_term("प्रकाश संश्लेषण", "hi")
        assert english == "photosynthesis"

    def test_get_native_term(self):
        """Test retrieving native language term from English."""
        glossary = AcademicGlossary()
        tamil = glossary.get_native_term("photosynthesis", "ta")
        assert tamil == "ஒளிச்சேர்க்கை"

    def test_extract_and_preserve_terms(self):
        """Test term extraction and placeholder replacement."""
        glossary = AcademicGlossary()
        text = "प्रकाश संश्लेषण में क्या होता है?"

        modified, preserved = glossary.extract_and_preserve_terms(text, "hi")

        assert "__TERM_" in modified
        assert "photosynthesis" in preserved.values()

    def test_restore_english_terms(self):
        """Test restoring English terms from placeholders."""
        glossary = AcademicGlossary()
        text = "What happens in __TERM_0000__?"
        preserved = {"__TERM_0000__": "photosynthesis"}

        restored = glossary.restore_english_terms(text, preserved)
        assert "photosynthesis" in restored
        assert "__TERM_" not in restored

    def test_find_terms_in_text(self):
        """Test finding academic terms in text."""
        glossary = AcademicGlossary()
        text = "The process of photosynthesis uses chlorophyll."

        found = glossary.find_terms_in_text(text, "en")

        assert len(found) >= 2
        terms = [t["english"] for t in found]
        assert "photosynthesis" in terms
        assert "chlorophyll" in terms

    def test_add_term(self):
        """Test adding a new term to glossary."""
        glossary = AcademicGlossary()
        initial_count = glossary.get_term_count()

        glossary.add_term("test_term", {"hi": "परीक्षा शब्द", "ta": "சோதனை சொல்"})

        assert glossary.get_term_count() == initial_count + 1
        assert glossary.get_native_term("test_term", "hi") == "परीक्षा शब्द"

    def test_coverage_stats(self):
        """Test getting coverage statistics."""
        glossary = AcademicGlossary()
        stats = glossary.get_coverage_stats()

        assert "hi" in stats
        assert "ta" in stats
        assert stats["hi"] > 0


class TestTermExtractor:
    """Tests for TermExtractor class."""

    def test_extract_terms(self):
        """Test extracting terms from text."""
        extractor = TermExtractor()
        terms = extractor.extract_terms(
            "The quadratic equation uses polynomial expressions.",
            "en"
        )

        assert len(terms) >= 1
        english_terms = [t.english_equivalent for t in terms]
        assert "quadratic equation" in english_terms or "polynomial" in english_terms

    def test_extract_question_focus(self):
        """Test extracting main topic from question."""
        extractor = TermExtractor()
        focus = extractor.extract_question_focus(
            "What is photosynthesis?",
            "en"
        )

        assert focus is not None
        assert "photosynthesis" in focus.lower()

    def test_infer_subject(self):
        """Test subject inference from terms."""
        extractor = TermExtractor()
        subject = extractor._infer_subject("photosynthesis")
        assert subject == "biology"

        subject = extractor._infer_subject("quadratic equation")
        assert subject == "mathematics"
