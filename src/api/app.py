"""FastAPI application for National LMS API."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

from src.config import get_settings
from src.pipeline import NationalLMSPipeline, QueryRequest, QueryResponse
from src.pipeline.models import UserContext

logger = structlog.get_logger(__name__)

# Global pipeline instance
_pipeline: Optional[NationalLMSPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global _pipeline
    logger.info("starting_application")
    _pipeline = NationalLMSPipeline()
    yield
    logger.info("shutting_down_application")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="National LMS API",
        description="Multi-modal RAG API serving 500 million students across 15+ Indian languages",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(query_router)
    app.include_router(health_router)
    app.include_router(feedback_router)

    return app


# Request/Response Models
class QueryRequestModel(BaseModel):
    """API request model for queries."""

    query: str = Field(..., min_length=1, max_length=2000, description="The question to answer")
    language: str = Field(default="en", description="Source language code (e.g., 'hi', 'ta', 'en')")
    grade_level: str = Field(default="class_10", description="Student grade level")
    board: str = Field(default="NCERT", description="Education board")
    subjects: list[str] = Field(default=[], description="Relevant subjects")
    include_video: bool = Field(default=True, description="Include video segment references")
    max_chunks: int = Field(default=7, ge=1, le=20, description="Maximum context chunks")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is photosynthesis?",
                "language": "hi",
                "grade_level": "class_10",
                "board": "NCERT",
                "subjects": ["biology"],
                "include_video": True,
            }
        }


class QueryResponseModel(BaseModel):
    """API response model for queries."""

    query_id: str
    answer: str
    language: str
    sources: list[dict]
    video_segments: list[dict]
    confidence: float
    metadata: dict

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "abc123",
                "answer": "Photosynthesis is the process...",
                "language": "hi",
                "sources": [
                    {
                        "source_type": "textbook",
                        "board": "NCERT",
                        "subject": "biology",
                        "chapter": "Life Processes",
                    }
                ],
                "video_segments": [],
                "confidence": 0.85,
                "metadata": {
                    "latency_ms": 1500,
                    "grounded": True,
                },
            }
        }


class FeedbackRequest(BaseModel):
    """User feedback request."""

    query_id: str = Field(..., description="Query ID to provide feedback for")
    feedback: str = Field(..., pattern="^(positive|negative)$", description="Feedback type")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    components: dict
    metrics: dict


# Routers
from fastapi import APIRouter

query_router = APIRouter(prefix="/api/v1", tags=["queries"])
health_router = APIRouter(prefix="/health", tags=["health"])
feedback_router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@query_router.post("/query", response_model=QueryResponseModel)
async def answer_query(request: QueryRequestModel):
    """
    Answer a student's educational query.

    Processes the query through:
    - Translation (if non-English)
    - Hybrid search across curriculum content
    - Reranking for relevance
    - Grounded response generation

    Returns curriculum-aligned answer with source citations.
    """
    if _pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not initialized",
        )

    try:
        # Build pipeline request
        pipeline_request = QueryRequest(
            query=request.query,
            source_language=request.language,
            user_context=UserContext(
                grade_level=request.grade_level,
                board=request.board,
                subjects=request.subjects,
                language=request.language,
            ),
            include_video=request.include_video,
            max_chunks=request.max_chunks,
        )

        # Process query
        response = await _pipeline.answer_query(pipeline_request)

        return QueryResponseModel(
            query_id=response.query_id,
            answer=response.answer,
            language=response.language,
            sources=[
                {
                    "source_type": s.source_type,
                    "board": s.board,
                    "subject": s.subject,
                    "grade_level": s.grade_level,
                    "chapter": s.chapter,
                    "page_number": s.page_number,
                }
                for s in response.sources
            ],
            video_segments=[
                {
                    "video_id": v.video_id,
                    "title": v.title,
                    "instructor": v.instructor,
                    "segment": f"{v.start_timestamp} - {v.end_timestamp}",
                    "url": v.url,
                }
                for v in response.video_segments
            ],
            confidence=response.confidence,
            metadata={
                "route_used": response.route_used,
                "translation_confidence": response.translation_confidence,
                "grounded": response.grounded,
                "latency_ms": response.latency_ms,
                "tokens_used": response.tokens_used,
            },
        )

    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}",
        )


@feedback_router.post("/")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback for a query."""
    if _pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not initialized",
        )

    await _pipeline.record_feedback(request.query_id, request.feedback)
    return {"status": "recorded", "query_id": request.query_id}


@health_router.get("/", response_model=HealthResponse)
async def health_check():
    """Check health status of all components."""
    if _pipeline is None:
        return HealthResponse(
            status="unhealthy",
            components={},
            metrics={},
        )

    health = _pipeline.get_health_status()
    return HealthResponse(
        status=health["status"],
        components=health["components"],
        metrics=health["metrics"],
    )


@health_router.get("/ready")
async def readiness_check():
    """Check if service is ready to accept requests."""
    if _pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
        )
    return {"ready": True}


@health_router.get("/live")
async def liveness_check():
    """Check if service is alive."""
    return {"alive": True}


# Create default app instance
app = create_app()
