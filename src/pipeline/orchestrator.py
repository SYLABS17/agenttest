"""Main query pipeline orchestrator for National LMS."""

import time
from typing import Optional
import uuid

import structlog

from src.config import get_settings
from src.glossary import AcademicGlossary
from src.translation import TranslationService, TranslationRouter
from src.search import HybridSearchService, SearchFilters
from src.search.index_manager import IndexManager
from src.reranking import CrossEncoderReranker
from src.video import VideoRetriever
from src.generation import GroundedGenerator
from src.evaluation import EvaluationFramework, MetricsCollector
from src.pipeline.models import (
    QueryRequest,
    QueryResponse,
    UserContext,
    SourceReference,
    VideoReference,
)

logger = structlog.get_logger(__name__)


class NationalLMSPipeline:
    """
    Main orchestrator for the National Learning Management System.

    Processes student queries through:
    1. Translation with glossary preservation
    2. Confidence-based routing
    3. Hybrid search (vector + BM25)
    4. Cross-encoder reranking
    5. Parent context expansion
    6. Grounded response generation
    7. Quality evaluation

    Designed for 120 million daily active users across 15+ languages.
    """

    def __init__(
        self,
        glossary: Optional[AcademicGlossary] = None,
        translator: Optional[TranslationService] = None,
        router: Optional[TranslationRouter] = None,
        search: Optional[HybridSearchService] = None,
        index_manager: Optional[IndexManager] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        video_retriever: Optional[VideoRetriever] = None,
        generator: Optional[GroundedGenerator] = None,
        evaluator: Optional[EvaluationFramework] = None,
        metrics: Optional[MetricsCollector] = None,
    ):
        """
        Initialize the pipeline with all components.

        Args:
            All components can be injected for testing, otherwise
            default implementations are created.
        """
        self.settings = get_settings()

        # Initialize components
        self.glossary = glossary or AcademicGlossary()
        self.translator = translator or TranslationService(glossary=self.glossary)
        self.router = router or TranslationRouter()
        self.search = search or HybridSearchService()
        self.index_manager = index_manager or IndexManager()
        self.reranker = reranker or CrossEncoderReranker()
        self.video_retriever = video_retriever or VideoRetriever()
        self.generator = generator or GroundedGenerator()
        self.evaluator = evaluator or EvaluationFramework()
        self.metrics = metrics or MetricsCollector()

        logger.info("pipeline_initialized")

    async def answer_query(
        self,
        request: QueryRequest,
    ) -> QueryResponse:
        """
        Process a student query through the complete pipeline.

        Args:
            request: QueryRequest with query and context

        Returns:
            QueryResponse with answer and metadata
        """
        start_time = time.time()
        self.metrics.start_query(request.query_id)

        logger.info(
            "processing_query",
            query_id=request.query_id,
            language=request.source_language,
            query=request.query[:50],
        )

        try:
            # Step 1: Translate query with glossary preservation
            translation_result = await self.translator.translate(
                text=request.query,
                source_lang=request.source_language,
                target_lang="en",
            )

            translated_query = translation_result.translated_text
            translation_confidence = translation_result.confidence

            # Step 2: Route based on confidence
            route = self.router.route(
                original_query=request.query,
                source_lang=request.source_language,
                translated_query=translated_query,
                translation_confidence=translation_confidence,
            )

            # Override routing if requested
            if request.force_native_index:
                route.index = f"{request.source_language}_native"
                route.query = request.query

            # Step 3: Build search filters from user context
            filters = self._build_filters(request.user_context)

            # Step 4: Hybrid search
            search_results = await self.search.hybrid_search(
                query=route.query,
                index=route.index,
                filters=filters,
                top=self.settings.search_top_k,
            )

            # Step 5: Rerank results
            reranked = self.reranker.rerank(
                query=route.query,
                results=search_results,
                top_k=request.max_chunks,
            )

            # Step 6: Expand with parent context
            async def fetch_parent(parent_id: str):
                return await self.index_manager.get_document(parent_id)

            chunks_with_context = self.reranker.rerank_with_context(
                query=route.query,
                results=search_results,
                parent_fetcher=lambda pid: None,  # Simplified for now
                top_k=request.max_chunks,
            )

            # Step 7: Extract video segments
            video_segments = []
            if request.include_video:
                video_segments = self.video_retriever.retrieve_segments_from_results(
                    chunks=[r.chunk for r in reranked],
                    max_segments=3,
                )

            # Step 8: Generate grounded response
            generated = await self.generator.generate(
                context_chunks=chunks_with_context,
                original_query=request.query,
                translated_query=translated_query,
                source_language=request.source_language,
                target_language=request.source_language,  # Respond in user's language
                user_context={
                    "grade_level": request.user_context.grade_level,
                    "subject": request.user_context.subjects[0] if request.user_context.subjects else "unknown",
                },
                video_segments=[vs.segment for vs in video_segments],
            )

            # Step 9: Build response
            latency_ms = (time.time() - start_time) * 1000

            response = QueryResponse(
                query_id=request.query_id,
                answer=generated.answer,
                language=generated.language,
                sources=[
                    SourceReference(
                        source_type=s["source_type"],
                        board=s["board"],
                        subject=s["subject"],
                        grade_level=s["grade_level"],
                        chapter=s.get("chapter"),
                        page_number=s.get("page_number"),
                    )
                    for s in generated.sources
                ],
                video_segments=[
                    VideoReference(
                        video_id=v["video_id"],
                        title=v["title"],
                        instructor=v["instructor"],
                        start_timestamp=v["start_timestamp"],
                        end_timestamp=v["end_timestamp"],
                        url=v["url"],
                        thumbnail_url=v["thumbnail_url"],
                    )
                    for v in generated.video_segments
                ],
                confidence=generated.confidence,
                route_used=route.index,
                translation_confidence=translation_confidence,
                grounded=generated.grounded,
                latency_ms=latency_ms,
                tokens_used=generated.tokens_used,
                model=generated.model,
            )

            # Step 10: Record metrics
            self.metrics.end_query(
                query_id=request.query_id,
                source_language=request.source_language,
                target_language=request.source_language,
                translation_confidence=translation_confidence,
                route_used=route.index,
                retrieval_count=len(search_results),
                rerank_count=len(reranked),
                groundedness_score=1.0 if generated.grounded else 0.5,
                response_confidence=generated.confidence,
                tokens_used=generated.tokens_used,
            )

            logger.info(
                "query_completed",
                query_id=request.query_id,
                latency_ms=round(latency_ms, 2),
                route=route.index,
                chunks=len(reranked),
                grounded=generated.grounded,
            )

            return response

        except Exception as e:
            logger.error(
                "query_failed",
                query_id=request.query_id,
                error=str(e),
            )
            raise

    def _build_filters(self, context: UserContext) -> SearchFilters:
        """Build search filters from user context."""
        return SearchFilters(
            subjects=context.subjects if context.subjects else None,
            grade_levels=[context.grade_level] if context.grade_level != "unknown" else None,
            boards=[context.board] if context.board else None,
            language=context.language,
        )

    async def answer_simple(
        self,
        query: str,
        language: str = "en",
        grade_level: str = "class_10",
    ) -> QueryResponse:
        """
        Simplified interface for quick queries.

        Args:
            query: Question text
            language: Language code
            grade_level: Grade level

        Returns:
            QueryResponse
        """
        request = QueryRequest(
            query=query,
            source_language=language,
            user_context=UserContext(
                grade_level=grade_level,
                language=language,
            ),
        )
        return await self.answer_query(request)

    async def record_feedback(
        self,
        query_id: str,
        feedback: str,
    ) -> None:
        """
        Record user feedback for a query.

        Args:
            query_id: Query identifier
            feedback: "positive" or "negative"
        """
        self.metrics.record_feedback(query_id, feedback)

    def get_health_status(self) -> dict:
        """Get health status of all pipeline components."""
        return {
            "status": "healthy",
            "components": {
                "glossary": {"terms": self.glossary.get_term_count()},
                "translator": {"available": True},
                "search": {"available": self.search.client is not None},
                "reranker": {"model": self.reranker.model_name},
                "generator": {"available": self.generator.client is not None},
            },
            "metrics": self.evaluator.get_quality_dashboard(),
        }


async def create_pipeline() -> NationalLMSPipeline:
    """Factory function to create a fully configured pipeline."""
    pipeline = NationalLMSPipeline()
    logger.info("pipeline_created")
    return pipeline
