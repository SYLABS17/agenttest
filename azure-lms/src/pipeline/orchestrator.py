"""Azure LMS Pipeline Orchestrator."""

import time
from dataclasses import dataclass, field
from typing import Optional
import uuid
import structlog

from src.config import get_settings
from src.glossary import AcademicGlossary
from src.translation import AzureTranslationService, TranslationRouter
from src.search import AzureHybridSearchService, AzureEmbeddingService
from src.reranking import CrossEncoderReranker
from src.video import VideoRetriever
from src.generation import GroundedGenerator

logger = structlog.get_logger(__name__)


@dataclass
class QueryRequest:
    """Incoming query request."""

    query: str
    source_language: str = "en"
    grade_level: str = "class_10"
    board: str = "NCERT"
    subjects: list[str] = field(default_factory=list)
    include_video: bool = True
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class QueryResponse:
    """Response to a query."""

    query_id: str
    answer: str
    language: str
    sources: list[dict]
    video_segments: list[dict]
    confidence: float
    route_used: str
    latency_ms: float


class AzureLMSPipeline:
    """
    Azure LMS Pipeline Orchestrator.

    Processes queries through:
    1. Azure Translator (with glossary)
    2. Confidence-based routing
    3. Azure AI Search (hybrid)
    4. Cross-encoder reranking
    5. Azure OpenAI generation
    """

    def __init__(self):
        self.settings = get_settings()
        self.glossary = AcademicGlossary()
        self.translator = AzureTranslationService(glossary=self.glossary)
        self.router = TranslationRouter()
        self.search = AzureHybridSearchService()
        self.reranker = CrossEncoderReranker()
        self.video_retriever = VideoRetriever()
        self.generator = GroundedGenerator()

        logger.info("azure_pipeline_initialized")

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        """Process a student query through the Azure pipeline."""
        start_time = time.time()

        logger.info(
            "processing_query_azure",
            query_id=request.query_id,
            language=request.source_language,
        )

        try:
            # Step 1: Translate with Azure Translator
            translation = await self.translator.translate(
                text=request.query,
                source_lang=request.source_language,
                target_lang="en",
            )

            # Step 2: Route based on confidence
            route = self.router.route(
                original_query=request.query,
                source_lang=request.source_language,
                translated_query=translation.translated_text,
                translation_confidence=translation.confidence,
            )

            # Step 3: Azure AI Search
            search_results = await self.search.hybrid_search(
                query=route.query,
                index=route.index,
                top=self.settings.search_top_k,
            )

            # Step 4: Rerank
            reranked = self.reranker.rerank(
                query=route.query,
                results=search_results,
                top_k=self.settings.search_rerank_top_k,
            )

            # Step 5: Extract video segments
            video_segments = []
            if request.include_video:
                video_segments = self.video_retriever.retrieve_segments_from_results(
                    [r.chunk for r in reranked]
                )

            # Step 6: Generate with Azure OpenAI
            generated = await self.generator.generate(
                context_chunks=reranked,
                original_query=request.query,
                translated_query=translation.translated_text,
                source_language=request.source_language,
                target_language=request.source_language,
            )

            latency_ms = (time.time() - start_time) * 1000

            return QueryResponse(
                query_id=request.query_id,
                answer=generated.answer,
                language=request.source_language,
                sources=generated.sources,
                video_segments=[
                    {
                        "video_id": v.video_id,
                        "title": v.title,
                        "segment": f"{v.start_timestamp} - {v.end_timestamp}",
                        "url": v.url,
                    }
                    for v in video_segments
                ],
                confidence=generated.confidence,
                route_used=route.index,
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error("azure_query_failed", error=str(e))
            raise

    def get_health_status(self) -> dict:
        """Get health status of Azure services."""
        return {
            "status": "healthy",
            "cloud": "azure",
            "services": {
                "azure_search": self.search.client is not None,
                "azure_openai": True,
                "azure_translator": self.translator.client is not None,
            },
        }
