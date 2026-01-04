"""Vertex AI Search hybrid search implementation."""

from dataclasses import dataclass
from typing import Optional
import structlog

from src.config import get_settings
from src.search.embeddings import VertexAIEmbeddingService

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Result from Vertex AI Search."""

    id: str
    content: str
    score: float
    metadata: dict
    vector_score: Optional[float] = None


@dataclass
class SearchFilters:
    """Filters for search queries."""

    subjects: Optional[list[str]] = None
    grade_levels: Optional[list[str]] = None
    boards: Optional[list[str]] = None
    language: Optional[str] = None

    def to_filter_expression(self) -> Optional[str]:
        """Convert to Vertex AI Search filter expression."""
        conditions = []
        if self.subjects:
            conditions.append(f"subject: ANY(\"{'\", \"'.join(self.subjects)}\")")
        if self.grade_levels:
            conditions.append(f"grade_level: ANY(\"{'\", \"'.join(self.grade_levels)}\")")
        if self.boards:
            conditions.append(f"board: ANY(\"{'\", \"'.join(self.boards)}\")")
        if self.language:
            conditions.append(f"language = \"{self.language}\"")
        return " AND ".join(conditions) if conditions else None


class VertexAISearchService:
    """Vertex AI Search with hybrid vector and keyword search."""

    def __init__(self, embedding_service: Optional[VertexAIEmbeddingService] = None):
        self.settings = get_settings()
        self.embedding_service = embedding_service or VertexAIEmbeddingService()
        self._client = None

    @property
    def client(self):
        """Lazy-load Vertex AI Search client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Vertex AI Search client."""
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine

            return discoveryengine.SearchServiceClient()
        except Exception as e:
            logger.warning("vertex_search_init_failed", error=str(e))
            return None

    async def hybrid_search(
        self,
        query: str,
        index: str = "english_unified",
        filters: Optional[SearchFilters] = None,
        top: int = 50,
    ) -> list[SearchResult]:
        """Perform hybrid search combining vector and keyword search."""
        logger.debug("vertex_hybrid_search", query=query[:100], top=top)

        if self.client is None:
            return self._mock_search(query)

        try:
            from google.cloud import discoveryengine_v1 as discoveryengine

            serving_config = (
                f"projects/{self.settings.google_cloud_project}/"
                f"locations/{self.settings.vertex_search_location}/"
                f"collections/default_collection/"
                f"dataStores/{self.settings.vertex_search_datastore_id}/"
                f"servingConfigs/default_search"
            )

            # Build search request
            request = discoveryengine.SearchRequest(
                serving_config=serving_config,
                query=query,
                page_size=top,
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True,
                    ),
                    extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                        max_extractive_answer_count=3,
                    ),
                ),
            )

            if filters:
                filter_expr = filters.to_filter_expression()
                if filter_expr:
                    request.filter = filter_expr

            response = self.client.search(request=request)

            results = []
            for result in response.results:
                doc = result.document
                results.append(
                    SearchResult(
                        id=doc.id,
                        content=doc.derived_struct_data.get("content", ""),
                        score=result.relevance_score or 0.0,
                        metadata={
                            "source_type": doc.derived_struct_data.get("source_type"),
                            "subject": doc.derived_struct_data.get("subject"),
                            "grade_level": doc.derived_struct_data.get("grade_level"),
                            "board": doc.derived_struct_data.get("board"),
                            "chapter": doc.derived_struct_data.get("chapter"),
                            "video_id": doc.derived_struct_data.get("video_id"),
                        },
                    )
                )

            return results

        except Exception as e:
            logger.error("vertex_search_failed", error=str(e))
            raise

    def _mock_search(self, query: str) -> list[SearchResult]:
        """Return mock results for development."""
        return [
            SearchResult(
                id="mock-1",
                content=f"Mock result for: {query}",
                score=0.9,
                metadata={"source_type": "mock", "subject": "test"},
            )
        ]
