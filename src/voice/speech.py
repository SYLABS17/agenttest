"""Azure Voice Live for real-time speech interactions."""

import asyncio
from dataclasses import dataclass
from typing import Optional, Callable

import azure.cognitiveservices.speech as speechsdk


@dataclass
class SpeechResult:
    """Result from speech recognition."""
    text: str
    language: str
    confidence: float


class AzureVoiceLive:
    """Real-time voice using Azure Speech."""

    LANGUAGES = {
        "en": "en-US", "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN",
        "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN",
        "ml": "ml-IN", "pa": "pa-IN", "ur": "ur-IN",
    }

    VOICES = {
        "en-US": "en-US-JennyNeural", "hi-IN": "hi-IN-SwaraNeural",
        "ta-IN": "ta-IN-PallaviNeural", "te-IN": "te-IN-ShrutiNeural",
        "bn-IN": "bn-IN-TanishaaNeural", "mr-IN": "mr-IN-AarohiNeural",
    }

    def __init__(self, speech_key: str, speech_region: str):
        self.config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)

    async def recognize_once(self, language: str = "en") -> SpeechResult:
        """Recognize a single utterance."""
        lang_code = self.LANGUAGES.get(language, "en-US")
        self.config.speech_recognition_language = lang_code

        audio = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(speech_config=self.config, audio_config=audio)

        result = await asyncio.to_thread(recognizer.recognize_once)

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return SpeechResult(text=result.text, language=language, confidence=0.9)
        return SpeechResult(text="", language=language, confidence=0.0)

    async def synthesize_speech(self, text: str, language: str = "en") -> bytes:
        """Convert text to speech audio."""
        lang_code = self.LANGUAGES.get(language, "en-US")
        voice = self.VOICES.get(lang_code, "en-US-JennyNeural")
        self.config.speech_synthesis_voice_name = voice

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.config, audio_config=None)
        result = await asyncio.to_thread(synthesizer.speak_text, text)

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        return b""
