"""FastAPI application for LMS with Azure AI Foundry and Voice Live."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
import structlog

from azure_lms.src.config.settings import get_settings
from azure_lms.src.foundry.client import AzureAIFoundryClient
from azure_lms.src.voice.speech import AzureVoiceLive

logger = structlog.get_logger(__name__)
settings = get_settings()

_foundry_client: Optional[AzureAIFoundryClient] = None
_voice_client: Optional[AzureVoiceLive] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global _foundry_client, _voice_client

    logger.info("initializing_azure_ai_foundry")
    _foundry_client = AzureAIFoundryClient(
        project_connection_string=settings.azure_ai_project_connection_string,
        search_index=settings.azure_search_index_name,
        chat_model=settings.chat_model,
    )
    await _foundry_client.initialize()

    logger.info("initializing_voice_live")
    _voice_client = AzureVoiceLive(
        speech_key=settings.azure_speech_key,
        speech_region=settings.azure_speech_region,
    )

    yield

    logger.info("shutting_down")
    if _foundry_client:
        await _foundry_client.close()


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
    """Request for RAG query."""
    question: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="en")


class QueryResponse(BaseModel):
    """Response from RAG query."""
    answer: str
    sources: list[dict]
    confidence: float


class SpeechRequest(BaseModel):
    """Request for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if _foundry_client else "unhealthy",
        "service": "lms-azure-foundry",
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe."""
    return {"ready": _foundry_client is not None}


@app.get("/health/live")
async def liveness_check():
    """Liveness probe."""
    return {"alive": True}


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the LMS using Azure AI Foundry RAG."""
    if not _foundry_client:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = await _foundry_client.query(
            question=request.question,
            language=request.language,
        )

        return QueryResponse(
            answer=result.answer,
            sources=result.sources,
            confidence=result.confidence,
        )
    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/synthesize")
async def synthesize_speech(request: SpeechRequest):
    """Convert text to speech using Azure Voice Live."""
    if not _voice_client:
        raise HTTPException(status_code=503, detail="Voice service not initialized")

    try:
        audio_data = await _voice_client.synthesize_speech(
            text=request.text,
            language=request.language,
        )

        if not audio_data:
            raise HTTPException(status_code=500, detail="Speech synthesis failed")

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"},
        )
    except Exception as e:
        logger.error("synthesis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """WebSocket for real-time voice interactions."""
    await websocket.accept()

    if not _voice_client or not _foundry_client:
        await websocket.close(code=1011, reason="Services not initialized")
        return

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "recognize":
                result = await _voice_client.recognize_once(
                    language=data.get("language", "en")
                )
                await websocket.send_json({
                    "type": "transcription",
                    "text": result.text,
                    "confidence": result.confidence,
                })

            elif data.get("type") == "query":
                question = data.get("text", "")
                if question:
                    result = await _foundry_client.query(
                        question=question,
                        language=data.get("language", "en"),
                    )
                    await websocket.send_json({
                        "type": "answer",
                        "text": result.answer,
                        "sources": result.sources,
                    })

            elif data.get("type") == "speak":
                text = data.get("text", "")
                if text:
                    audio = await _voice_client.synthesize_speech(
                        text=text,
                        language=data.get("language", "en"),
                    )
                    await websocket.send_bytes(audio)

    except WebSocketDisconnect:
        logger.info("websocket_disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
