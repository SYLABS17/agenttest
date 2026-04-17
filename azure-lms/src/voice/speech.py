"""Azure Voice Live for real-time speech interactions."""

import asyncio
from typing import AsyncIterator, Callable, Optional
from dataclasses import dataclass

import azure.cognitiveservices.speech as speechsdk


@dataclass
class SpeechResult:
    """Result from speech recognition."""
    text: str
    language: str
    confidence: float


class AzureVoiceLive:
    """Real-time voice interactions using Azure Speech."""

    SUPPORTED_LANGUAGES = {
        "en": "en-US",
        "hi": "hi-IN",
        "ta": "ta-IN",
        "te": "te-IN",
        "bn": "bn-IN",
        "mr": "mr-IN",
        "gu": "gu-IN",
        "kn": "kn-IN",
        "ml": "ml-IN",
        "pa": "pa-IN",
        "or": "or-IN",
        "as": "as-IN",
        "ur": "ur-IN",
    }

    def __init__(self, speech_key: str, speech_region: str):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region,
        )
        self.speech_config.speech_recognition_language = "en-US"
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
            "Continuous"
        )

    def create_recognizer(
        self,
        language: str = "en",
        on_recognized: Optional[Callable[[SpeechResult], None]] = None,
    ) -> speechsdk.SpeechRecognizer:
        """Create a speech recognizer for real-time transcription."""
        lang_code = self.SUPPORTED_LANGUAGES.get(language, "en-US")
        self.speech_config.speech_recognition_language = lang_code

        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )

        if on_recognized:
            def handle_recognized(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    result = SpeechResult(
                        text=evt.result.text,
                        language=language,
                        confidence=0.9,
                    )
                    on_recognized(result)

            recognizer.recognized.connect(handle_recognized)

        return recognizer

    async def recognize_once(self, language: str = "en") -> SpeechResult:
        """Recognize a single utterance."""
        lang_code = self.SUPPORTED_LANGUAGES.get(language, "en-US")
        self.speech_config.speech_recognition_language = lang_code

        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )

        result = await asyncio.to_thread(recognizer.recognize_once)

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return SpeechResult(
                text=result.text,
                language=language,
                confidence=0.9,
            )
        return SpeechResult(text="", language=language, confidence=0.0)

    async def synthesize_speech(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> bytes:
        """Convert text to speech audio."""
        lang_code = self.SUPPORTED_LANGUAGES.get(language, "en-US")

        voice_name = voice or self._get_default_voice(lang_code)
        self.speech_config.speech_synthesis_voice_name = voice_name

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None,
        )

        result = await asyncio.to_thread(synthesizer.speak_text, text)

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        return b""

    def _get_default_voice(self, lang_code: str) -> str:
        """Get default voice for language."""
        voices = {
            "en-US": "en-US-JennyNeural",
            "hi-IN": "hi-IN-SwaraNeural",
            "ta-IN": "ta-IN-PallaviNeural",
            "te-IN": "te-IN-ShrutiNeural",
            "bn-IN": "bn-IN-TanishaaNeural",
            "mr-IN": "mr-IN-AarohiNeural",
            "gu-IN": "gu-IN-DhwaniNeural",
            "kn-IN": "kn-IN-SapnaNeural",
            "ml-IN": "ml-IN-SobhanaNeural",
        }
        return voices.get(lang_code, "en-US-JennyNeural")

    async def start_continuous_recognition(
        self,
        language: str = "en",
    ) -> AsyncIterator[SpeechResult]:
        """Start continuous speech recognition."""
        lang_code = self.SUPPORTED_LANGUAGES.get(language, "en-US")
        self.speech_config.speech_recognition_language = lang_code

        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )

        queue = asyncio.Queue()
        stop_event = asyncio.Event()

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                asyncio.run_coroutine_threadsafe(
                    queue.put(SpeechResult(
                        text=evt.result.text,
                        language=language,
                        confidence=0.9,
                    )),
                    asyncio.get_event_loop(),
                )

        def on_canceled(evt):
            stop_event.set()

        recognizer.recognized.connect(on_recognized)
        recognizer.canceled.connect(on_canceled)

        recognizer.start_continuous_recognition()

        try:
            while not stop_event.is_set():
                try:
                    result = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield result
                except asyncio.TimeoutError:
                    continue
        finally:
            recognizer.stop_continuous_recognition()
