"""FastAPI application for AWS LMS."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

from src.pipeline import AWSLMSPipeline
from src.pipeline.orchestrator import QueryRequest

logger = structlog.get_logger(__name__)

_pipeline: Optional[AWSLMSPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global _pipeline
    logger.info("starting_aws_lms")
    _pipeline = AWSLMSPipeline()
    yield
    logger.info("shutting_down_aws_lms")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    application = FastAPI(
        title="LMS API - AWS",
        description="Multi-modal RAG API powered by Amazon Web Services",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = create_app()


class QueryRequestModel(BaseModel):
    """API request model."""

    query: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="en")
    grade_level: str = Field(default="class_10")
    board: str = Field(default="curriculum_board")
    subjects: list[str] = Field(default=[])
    include_video: bool = Field(default=True)


class QueryResponseModel(BaseModel):
    """API response model."""

    query_id: str
    answer: str
    language: str
    sources: list[dict]
    video_segments: list[dict]
    confidence: float
    metadata: dict


@app.post("/api/v1/query", response_model=QueryResponseModel)
async def answer_query(request: QueryRequestModel):
    """Answer a student's educational query using AWS services."""
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    try:
        pipeline_request = QueryRequest(
            query=request.query,
            source_language=request.language,
            grade_level=request.grade_level,
            board=request.board,
            subjects=request.subjects,
            include_video=request.include_video,
        )

        response = await _pipeline.answer_query(pipeline_request)

        return QueryResponseModel(
            query_id=response.query_id,
            answer=response.answer,
            language=response.language,
            sources=response.sources,
            video_segments=response.video_segments,
            confidence=response.confidence,
            metadata={
                "cloud": "aws",
                "route_used": response.route_used,
                "latency_ms": response.latency_ms,
            },
        )

    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Check health of AWS services."""
    if _pipeline is None:
        return {"status": "unhealthy", "cloud": "aws"}
    return _pipeline.get_health_status()


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe."""
    return {"ready": _pipeline is not None, "cloud": "aws"}


@app.get("/health/live")
async def liveness_check():
    """Liveness probe."""
    return {"alive": True, "cloud": "aws"}
