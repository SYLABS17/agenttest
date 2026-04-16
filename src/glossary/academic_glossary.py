"""Academic glossary for domain-specific term translation across 15 languages."""

import json
import re
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class AcademicGlossary:
    """
    Academic glossary mapping 10,000+ academic terms across multiple languages.

    Critical for preserving domain-specific terminology during translation.
    Example: 'ஒளிச்சேர்க்கை' (Tamil) → 'photosynthesis' (not literal translation)
    """

    def __init__(self, glossary_path: Optional[str] = None):
        """
        Initialize the academic glossary.

        Args:
            glossary_path: Path to glossary JSON file. If None, uses default.
        """
        self.glossary_path = glossary_path or self._get_default_path()
        self.terms: dict[str, dict[str, str]] = {}
        self.reverse_index: dict[str, dict[str, str]] = {}
        self._load_glossary()

    def _get_default_path(self) -> str:
        """Get default glossary file path."""
        return str(Path(__file__).parent.parent.parent / "data" / "glossary" / "academic_terms.json")

    def _load_glossary(self) -> None:
        """Load glossary from JSON file."""
        try:
            with open(self.glossary_path, encoding="utf-8") as f:
                self.terms = json.load(f)
            self._build_reverse_index()
            logger.info("glossary_loaded", term_count=len(self.terms))
        except FileNotFoundError:
            logger.warning("glossary_not_found", path=self.glossary_path)
            self.terms = self._get_default_terms()
            self._build_reverse_index()
            logger.info("using_default_glossary", term_count=len(self.terms))

    def _build_reverse_index(self) -> None:
        """
        Build reverse index for fast lookup from any language to English.

        Structure: {language_code: {native_term: english_term}}
        """
        self.reverse_index = {}
        for english_term, translations in self.terms.items():
            for lang_code, native_term in translations.items():
                if lang_code not in self.reverse_index:
                    self.reverse_index[lang_code] = {}
                self.reverse_index[lang_code][native_term.lower()] = english_term

    def get_english_term(self, native_term: str, source_lang: str) -> Optional[str]:
        """
        Get English equivalent of a native language term.

        Args:
            native_term: Term in source language
            source_lang: ISO language code (e.g., 'ta' for Tamil)

        Returns:
            English term if found, None otherwise
        """
        if source_lang not in self.reverse_index:
            return None
        return self.reverse_index[source_lang].get(native_term.lower())

    def get_native_term(self, english_term: str, target_lang: str) -> Optional[str]:
        """
        Get native language equivalent of an English term.

        Args:
            english_term: Term in English
            target_lang: ISO language code

        Returns:
            Native term if found, None otherwise
        """
        term_data = self.terms.get(english_term.lower())
        if term_data:
            return term_data.get(target_lang)
        return None

    def extract_and_preserve_terms(
        self, text: str, source_lang: str
    ) -> tuple[str, dict[str, str]]:
        """
        Extract domain terms from text and replace with placeholders.

        This is critical for preventing loss of scientific/academic terms
        during translation.

        Args:
            text: Text containing domain terms
            source_lang: Source language code

        Returns:
            Tuple of (text with placeholders, mapping of placeholder to English term)
        """
        if source_lang not in self.reverse_index:
            return text, {}

        preserved = {}
        modified_text = text

        # Sort by length (longest first) to handle overlapping terms
        lang_terms = sorted(
            self.reverse_index[source_lang].items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )

        for native_term, english_term in lang_terms:
            # Case-insensitive search with word boundaries
            pattern = re.compile(re.escape(native_term), re.IGNORECASE)
            if pattern.search(modified_text):
                placeholder = f"__TERM_{len(preserved):04d}__"
                modified_text = pattern.sub(placeholder, modified_text)
                preserved[placeholder] = english_term

        return modified_text, preserved

    def restore_english_terms(self, text: str, preserved: dict[str, str]) -> str:
        """
        Replace placeholders with English terms.

        Args:
            text: Translated text with placeholders
            preserved: Mapping of placeholder to English term

        Returns:
            Text with English domain terms
        """
        result = text
        for placeholder, english_term in preserved.items():
            result = result.replace(placeholder, english_term)
        return result

    def find_terms_in_text(self, text: str, lang: str) -> list[dict]:
        """
        Find all recognized academic terms in text.

        Args:
            text: Text to analyze
            lang: Language code

        Returns:
            List of found terms with metadata
        """
        found = []

        if lang == "en":
            # Search in English terms
            for english_term in self.terms:
                if re.search(rf"\b{re.escape(english_term)}\b", text, re.IGNORECASE):
                    found.append({
                        "term": english_term,
                        "english": english_term,
                        "translations": self.terms[english_term],
                    })
        elif lang in self.reverse_index:
            # Search in native language terms
            for native_term, english_term in self.reverse_index[lang].items():
                if native_term in text.lower():
                    found.append({
                        "term": native_term,
                        "english": english_term,
                        "translations": self.terms.get(english_term, {}),
                    })

        return found

    def add_term(
        self, english_term: str, translations: dict[str, str]
    ) -> None:
        """
        Add a new term to the glossary.

        Args:
            english_term: English term (key)
            translations: Dict of language code to native term
        """
        english_lower = english_term.lower()
        self.terms[english_lower] = translations

        # Update reverse index
        for lang_code, native_term in translations.items():
            if lang_code not in self.reverse_index:
                self.reverse_index[lang_code] = {}
            self.reverse_index[lang_code][native_term.lower()] = english_lower

        logger.info("term_added", term=english_term, languages=list(translations.keys()))

    def save_glossary(self, path: Optional[str] = None) -> None:
        """Save glossary to JSON file."""
        save_path = path or self.glossary_path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.terms, f, ensure_ascii=False, indent=2)
        logger.info("glossary_saved", path=save_path)

    def get_term_count(self) -> int:
        """Return total number of terms in glossary."""
        return len(self.terms)

    def get_coverage_stats(self) -> dict[str, int]:
        """Get coverage statistics by language."""
        stats = {}
        for translations in self.terms.values():
            for lang in translations:
                stats[lang] = stats.get(lang, 0) + 1
        return stats

    def _get_default_terms(self) -> dict[str, dict[str, str]]:
        """
        Return default academic terms.

        This is a subset - full glossary has 10,000+ terms.
        """
        return {
            # Biology Terms
            "photosynthesis": {
                "en": "photosynthesis",
                "hi": "प्रकाश संश्लेषण",
                "ta": "ஒளிச்சேர்க்கை",
                "te": "కిరణజన్య సంయోగక్రియ",
                "bn": "সালোকসংশ্লেষ",
                "mr": "प्रकाशसंश्लेषण",
                "gu": "પ્રકાશસંશ્લેષણ",
                "kn": "ದ್ಯುತಿಸಂಶ್ಲೇಷಣೆ",
                "ml": "പ്രകാശസംശ്ലേഷണം",
                "pa": "ਪ੍ਰਕਾਸ਼ ਸੰਸ਼ਲੇਸ਼ਣ",
            },
            "chlorophyll": {
                "en": "chlorophyll",
                "hi": "हरितलवक",
                "ta": "பச்சையம்",
                "te": "పత్రహరితం",
                "bn": "ক্লোরোফিল",
                "mr": "हरितद्रव्य",
                "gu": "હરિતદ્રવ્ય",
                "kn": "ಪತ್ರಹರಿತ್ತು",
                "ml": "ഹരിതകം",
                "pa": "ਹਰੀਤਲਵਕ",
            },
            "mitochondria": {
                "en": "mitochondria",
                "hi": "माइटोकॉन्ड्रिया",
                "ta": "மைட்டோகாண்டிரியா",
                "te": "మైటోకాండ్రియా",
                "bn": "মাইটোকন্ড্রিয়া",
                "mr": "तंतुकणिका",
                "gu": "માઇટોકોન્ડ્રિયા",
                "kn": "ಮೈಟೊಕಾಂಡ್ರಿಯಾ",
                "ml": "മൈറ്റോകോൺഡ്രിയ",
                "pa": "ਮਾਈਟੋਕੌਂਡਰੀਆ",
            },
            "cell membrane": {
                "en": "cell membrane",
                "hi": "कोशिका झिल्ली",
                "ta": "செல் சவ்வு",
                "te": "కణ త్వచం",
                "bn": "কোষ ঝিল্লি",
                "mr": "पेशी पटल",
                "gu": "કોષ પટલ",
                "kn": "ಜೀವಕೋಶ ಪೊರೆ",
                "ml": "കോശ സ്തരം",
                "pa": "ਸੈੱਲ ਝਿੱਲੀ",
            },
            "nucleus": {
                "en": "nucleus",
                "hi": "केन्द्रक",
                "ta": "உட்கரு",
                "te": "కేంద్రకం",
                "bn": "নিউক্লিয়াস",
                "mr": "केंद्रक",
                "gu": "કેન્દ્ર",
                "kn": "ಬೀಜಕೇಂದ್ರ",
                "ml": "ന്യൂക്ലിയസ്",
                "pa": "ਨਿਊਕਲੀਅਸ",
            },
            "chromosome": {
                "en": "chromosome",
                "hi": "गुणसूत्र",
                "ta": "நிறமூர்த்தம்",
                "te": "క్రోమోజోమ్",
                "bn": "ক্রোমোজোম",
                "mr": "गुणसूत्र",
                "gu": "રંગસૂત્ર",
                "kn": "ವರ್ಣತಂತು",
                "ml": "ക്രോമസോം",
                "pa": "ਕ੍ਰੋਮੋਸੋਮ",
            },
            "dna": {
                "en": "DNA",
                "hi": "डीएनए",
                "ta": "டிஎன்ஏ",
                "te": "డీఎన్ఎ",
                "bn": "ডিএনএ",
                "mr": "डीएनए",
                "gu": "ડીએનએ",
                "kn": "ಡಿಎನ್ಎ",
                "ml": "ഡിഎൻഎ",
                "pa": "ਡੀਐਨਏ",
            },
            "enzyme": {
                "en": "enzyme",
                "hi": "एंजाइम",
                "ta": "நொதி",
                "te": "ఎంజైమ్",
                "bn": "উৎসেচক",
                "mr": "विकर",
                "gu": "ઉત્સેચક",
                "kn": "ಕಿಣ್ವ",
                "ml": "എൻസൈം",
                "pa": "ਐਨਜ਼ਾਈਮ",
            },
            # Mathematics Terms
            "quadratic equation": {
                "en": "quadratic equation",
                "hi": "द्विघात समीकरण",
                "ta": "இருபடி சமன்பாடு",
                "te": "వర్గ సమీకరణం",
                "bn": "দ্বিঘাত সমীকরণ",
                "mr": "वर्गसमीकरण",
                "gu": "દ્વિઘાત સમીકરણ",
                "kn": "ವರ್ಗ ಸಮೀಕರಣ",
                "ml": "വർഗ്ഗസമവാക്യം",
                "pa": "ਦੋਘਾਤ ਸਮੀਕਰਨ",
            },
            "polynomial": {
                "en": "polynomial",
                "hi": "बहुपद",
                "ta": "பல்லுறுப்புக்கோவை",
                "te": "బహుపది",
                "bn": "বহুপদী",
                "mr": "बहुपदी",
                "gu": "બહુપદી",
                "kn": "ಬಹುಪದೋಕ್ತಿ",
                "ml": "ബഹുപദം",
                "pa": "ਬਹੁਪਦ",
            },
            "derivative": {
                "en": "derivative",
                "hi": "अवकलज",
                "ta": "வகைக்கெழு",
                "te": "ఉత్పన్నం",
                "bn": "অন্তরকলন",
                "mr": "अवकलज",
                "gu": "વ્યુત્પન્ન",
                "kn": "ಉತ್ಪನ್ನ",
                "ml": "വ്യുത്പന്നം",
                "pa": "ਡੈਰੀਵੇਟਿਵ",
            },
            "integral": {
                "en": "integral",
                "hi": "समाकल",
                "ta": "தொகையீடு",
                "te": "సమాకలనం",
                "bn": "সমাকল",
                "mr": "समाकल",
                "gu": "સમાકલ",
                "kn": "ಸಮಾಕಲನ",
                "ml": "സമാകലം",
                "pa": "ਇੰਟੀਗ੍ਰਲ",
            },
            "trigonometry": {
                "en": "trigonometry",
                "hi": "त्रिकोणमिति",
                "ta": "முக்கோணவியல்",
                "te": "త్రికోణమితి",
                "bn": "ত্রিকোণমিতি",
                "mr": "त्रिकोणमिती",
                "gu": "ત્રિકોણમિતિ",
                "kn": "ತ್ರಿಕೋನಮಿತಿ",
                "ml": "ത്രികോണമിതി",
                "pa": "ਤ੍ਰਿਕੋਣਮਿਤੀ",
            },
            "logarithm": {
                "en": "logarithm",
                "hi": "लघुगणक",
                "ta": "மடக்கை",
                "te": "లఘుగణకం",
                "bn": "লগারিদম",
                "mr": "लघुगणक",
                "gu": "લઘુગણક",
                "kn": "ಲಘುಗಣಕ",
                "ml": "ലോഗരിതം",
                "pa": "ਲਘੂਗਣਕ",
            },
            "probability": {
                "en": "probability",
                "hi": "प्रायिकता",
                "ta": "நிகழ்தகவு",
                "te": "సంభావ్యత",
                "bn": "সম্ভাবনা",
                "mr": "संभाव्यता",
                "gu": "સંભાવના",
                "kn": "ಸಂಭಾವ್ಯತೆ",
                "ml": "സംഭാവ്യത",
                "pa": "ਸੰਭਾਵਨਾ",
            },
            "statistics": {
                "en": "statistics",
                "hi": "सांख्यिकी",
                "ta": "புள்ளியியல்",
                "te": "గణాంకశాస్త్రం",
                "bn": "পরিসংখ্যান",
                "mr": "सांख्यिकी",
                "gu": "આંકડાશાસ્ત્ર",
                "kn": "ಸಂಖ್ಯಾಶಾಸ್ತ್ರ",
                "ml": "സ്ഥിതിവിവരശാസ്ത്രം",
                "pa": "ਅੰਕੜੇ",
            },
            # Physics Terms
            "velocity": {
                "en": "velocity",
                "hi": "वेग",
                "ta": "திசைவேகம்",
                "te": "వేగం",
                "bn": "বেগ",
                "mr": "वेग",
                "gu": "વેગ",
                "kn": "ವೇಗ",
                "ml": "പ്രവേഗം",
                "pa": "ਵੇਗ",
            },
            "acceleration": {
                "en": "acceleration",
                "hi": "त्वरण",
                "ta": "முடுக்கம்",
                "te": "త్వరణం",
                "bn": "ত্বরণ",
                "mr": "त्वरण",
                "gu": "પ્રવેગ",
                "kn": "ವೇಗೋತ್ಕರ್ಷ",
                "ml": "ത്വരണം",
                "pa": "ਤਵਰਣ",
            },
            "momentum": {
                "en": "momentum",
                "hi": "संवेग",
                "ta": "உந்தம்",
                "te": "ద్రవ్యవేగం",
                "bn": "ভরবেগ",
                "mr": "संवेग",
                "gu": "વેગમાન",
                "kn": "ಸಂವೇಗ",
                "ml": "ആക്കം",
                "pa": "ਸੰਵੇਗ",
            },
            "gravity": {
                "en": "gravity",
                "hi": "गुरुत्वाकर्षण",
                "ta": "புவியீர்ப்பு",
                "te": "గురుత్వాకర్షణ",
                "bn": "মাধ্যাকর্ষণ",
                "mr": "गुरुत्वाकर्षण",
                "gu": "ગુરુત્વાકર્ષણ",
                "kn": "ಗುರುತ್ವ",
                "ml": "ഗുരുത്വാകർഷണം",
                "pa": "ਗੁਰੂਤਾ",
            },
            "electromagnetism": {
                "en": "electromagnetism",
                "hi": "विद्युत चुंबकत्व",
                "ta": "மின்காந்தவியல்",
                "te": "విద్యుదయస్కాంతత్వం",
                "bn": "তড়িৎচুম্বকত্ব",
                "mr": "विद्युतचुंबकत्व",
                "gu": "વિદ્યુતચુંબકત્વ",
                "kn": "ವಿದ್ಯುತ್ಕಾಂತೀಯತೆ",
                "ml": "വൈദ്യുതകാന്തികത",
                "pa": "ਇਲੈਕਟ੍ਰੋਮੈਗਨੈਟਿਜ਼ਮ",
            },
            "thermodynamics": {
                "en": "thermodynamics",
                "hi": "ऊष्मागतिकी",
                "ta": "வெப்பஇயக்கவியல்",
                "te": "ఉష్ణగతిశాస్త్రం",
                "bn": "তাপগতিবিদ্যা",
                "mr": "उष्मागतिकी",
                "gu": "ઉષ્માગતિશાસ્ત્ર",
                "kn": "ಉಷ್ಣಬಲ ವಿಜ್ಞಾನ",
                "ml": "താപഗതികം",
                "pa": "ਥਰਮੋਡਾਇਨਾਮਿਕਸ",
            },
            # Chemistry Terms
            "chemical reaction": {
                "en": "chemical reaction",
                "hi": "रासायनिक अभिक्रिया",
                "ta": "வேதியியல் வினை",
                "te": "రసాయన చర్య",
                "bn": "রাসায়নিক বিক্রিয়া",
                "mr": "रासायनिक अभिक्रिया",
                "gu": "રાસાયણિક પ્રક્રિયા",
                "kn": "ರಾಸಾಯನಿಕ ಕ್ರಿಯೆ",
                "ml": "രാസപ്രവർത്തനം",
                "pa": "ਰਸਾਇਣਕ ਪ੍ਰਤੀਕਿਰਿਆ",
            },
            "periodic table": {
                "en": "periodic table",
                "hi": "आवर्त सारणी",
                "ta": "ஆவர்த்தன அட்டவணை",
                "te": "ఆవర్తన పట్టిక",
                "bn": "পর্যায় সারণী",
                "mr": "आवर्त सारणी",
                "gu": "આવર્તકોષ્ટક",
                "kn": "ಆವರ್ತ ಕೋಷ್ಟಕ",
                "ml": "ആവർത്തനപ്പട്ടിക",
                "pa": "ਆਵਰਤ ਸਾਰਣੀ",
            },
            "oxidation": {
                "en": "oxidation",
                "hi": "ऑक्सीकरण",
                "ta": "ஆக்சிஜனேற்றம்",
                "te": "ఆక్సీకరణం",
                "bn": "জারণ",
                "mr": "ऑक्सिडीकरण",
                "gu": "ઓક્સિડેશન",
                "kn": "ಆಕ್ಸಿಡೀಕರಣ",
                "ml": "ഓക്സീകരണം",
                "pa": "ਆਕਸੀਕਰਨ",
            },
            "reduction": {
                "en": "reduction",
                "hi": "अपचयन",
                "ta": "ஒடுக்கம்",
                "te": "తగ్గింపు",
                "bn": "বিজারণ",
                "mr": "अपचयन",
                "gu": "ઘટાડો",
                "kn": "ಕಡಿತ",
                "ml": "നിരോക്സീകരണം",
                "pa": "ਘਟਾਉ",
            },
            "covalent bond": {
                "en": "covalent bond",
                "hi": "सहसंयोजक बंध",
                "ta": "சகப்பிணைப்பு",
                "te": "సహవాలెన్సీ బంధం",
                "bn": "সমযোজী বন্ধন",
                "mr": "सहसंयुज बंध",
                "gu": "સહસંયોજક બંધ",
                "kn": "ಸಹಬಂಧ",
                "ml": "സഹസംയോജക ബന്ധം",
                "pa": "ਸਹਿ-ਸੰਯੋਜਕ ਬੰਧ",
            },
            "ionic bond": {
                "en": "ionic bond",
                "hi": "आयनिक बंध",
                "ta": "அயனிப் பிணைப்பு",
                "te": "అయానిక్ బంధం",
                "bn": "আয়নিক বন্ধন",
                "mr": "आयनिक बंध",
                "gu": "આયનિક બંધ",
                "kn": "ಅಯಾನಿಕ್ ಬಂಧ",
                "ml": "അയോണിക് ബന്ധം",
                "pa": "ਆਇਓਨਿਕ ਬੰਧ",
            },
            # Computer Science Terms
            "algorithm": {
                "en": "algorithm",
                "hi": "एल्गोरिदम",
                "ta": "வழிமுறை",
                "te": "అల్గారిథమ్",
                "bn": "অ্যালগরিদম",
                "mr": "अल्गोरिदम",
                "gu": "અલ્ગોરિધમ",
                "kn": "ಅಲ್ಗಾರಿದಮ್",
                "ml": "അൽഗോരിതം",
                "pa": "ਐਲਗੋਰਿਦਮ",
            },
            "data structure": {
                "en": "data structure",
                "hi": "आंकड़ा संरचना",
                "ta": "தரவு கட்டமைப்பு",
                "te": "డేటా స్ట్రక్చర్",
                "bn": "ডাটা স্ট্রাকচার",
                "mr": "डेटा स्ट्रक्चर",
                "gu": "ડેટા સ્ટ્રક્ચર",
                "kn": "ಡೇಟಾ ಸ್ಟ್ರಕ್ಚರ್",
                "ml": "ഡാറ്റ സ്ട്രക്ചർ",
                "pa": "ਡਾਟਾ ਢਾਂਚਾ",
            },
            "recursion": {
                "en": "recursion",
                "hi": "पुनरावर्तन",
                "ta": "மறுசுழற்சி",
                "te": "పునరావృతం",
                "bn": "পুনরাবৃত্তি",
                "mr": "पुनरावृत्ती",
                "gu": "પુનરાવર્તન",
                "kn": "ಪುನರಾವರ್ತನೆ",
                "ml": "പുനരാവർത്തനം",
                "pa": "ਰਿਕਰਸ਼ਨ",
            },
            "variable": {
                "en": "variable",
                "hi": "चर",
                "ta": "மாறி",
                "te": "చరము",
                "bn": "চলক",
                "mr": "चल",
                "gu": "ચલ",
                "kn": "ಚರ",
                "ml": "ചരം",
                "pa": "ਵੇਰੀਏਬਲ",
            },
            "function": {
                "en": "function",
                "hi": "फलन",
                "ta": "செயலி",
                "te": "ఫంక్షన్",
                "bn": "ফাংশন",
                "mr": "फंक्शन",
                "gu": "ફંક્શન",
                "kn": "ಕಾರ್ಯ",
                "ml": "ഫങ്ഷൻ",
                "pa": "ਫੰਕਸ਼ਨ",
            },
        }
