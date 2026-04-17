"""FastAPI application for LMS with Azure AI Foundry and Voice Live."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
import structlog

from src.config.settings import get_settings
from src.foundry.client import AzureAIFoundryClient
from src.voice.speech import AzureVoiceLive

logger = structlog.get_logger(__name__)
settings = get_settings()

_foundry: Optional[AzureAIFoundryClient] = None
_voice: Optional[AzureVoiceLive] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global _foundry, _voice

    logger.info("initializing_services")
    _foundry = AzureAIFoundryClient(
        project_connection_string=settings.azure_ai_project_connection_string,
        search_index=settings.azure_search_index_name,
        chat_model=settings.chat_model,
    )
    await _foundry.initialize()

    _voice = AzureVoiceLive(
        speech_key=settings.azure_speech_key,
        speech_region=settings.azure_speech_region,
    )

    yield

    if _foundry:
        await _foundry.close()


app = FastAPI(
    title="LMS API",
    description="Learning Management System with Azure AI Foundry and Voice Live",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="en")


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: float


class SpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en")


@app.get("/health")
async def health():
    return {"status": "healthy" if _foundry else "unhealthy"}


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query using Azure AI Foundry RAG."""
    if not _foundry:
        raise HTTPException(status_code=503, detail="Not initialized")

    result = await _foundry.query(request.question, request.language)
    return QueryResponse(answer=result.answer, sources=result.sources, confidence=result.confidence)


@app.post("/api/v1/synthesize")
async def synthesize(request: SpeechRequest):
    """Text-to-speech using Azure Voice Live."""
    if not _voice:
        raise HTTPException(status_code=503, detail="Not initialized")

    audio = await _voice.synthesize_speech(request.text, request.language)
    if not audio:
        raise HTTPException(status_code=500, detail="Synthesis failed")

    return Response(content=audio, media_type="audio/wav")


@app.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    """Real-time voice WebSocket."""
    await websocket.accept()

    if not _voice or not _foundry:
        await websocket.close(code=1011)
        return

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "recognize":
                result = await _voice.recognize_once(data.get("language", "en"))
                await websocket.send_json({"type": "transcription", "text": result.text})

            elif data.get("type") == "query":
                result = await _foundry.query(data.get("text", ""), data.get("language", "en"))
                await websocket.send_json({"type": "answer", "text": result.answer})

            elif data.get("type") == "speak":
                audio = await _voice.synthesize_speech(data.get("text", ""), data.get("language", "en"))
                await websocket.send_bytes(audio)

    except WebSocketDisconnect:
        pass
