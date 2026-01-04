"""Azure AI Search hybrid search implementation."""

from dataclasses import dataclass
from typing import Optional
import structlog

from src.config import get_settings
from src.search.embeddings import AzureEmbeddingService

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Result from Azure AI Search."""

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

    def to_odata_filter(self) -> Optional[str]:
        """Convert to Azure OData filter expression."""
        conditions = []
        if self.subjects:
            conditions.append(f"({' or '.join([f\"subject eq '{s}'\" for s in self.subjects])})")
        if self.grade_levels:
            conditions.append(f"({' or '.join([f\"grade_level eq '{g}'\" for g in self.grade_levels])})")
        if self.boards:
            conditions.append(f"({' or '.join([f\"board eq '{b}'\" for b in self.boards])})")
        if self.language:
            conditions.append(f"language eq '{self.language}'")
        return " and ".join(conditions) if conditions else None


class AzureHybridSearchService:
    """Azure AI Search with hybrid vector and BM25 search."""

    def __init__(self, embedding_service: Optional[AzureEmbeddingService] = None):
        self.settings = get_settings()
        self.embedding_service = embedding_service or AzureEmbeddingService()
        self._client = None

    @property
    def client(self):
        """Lazy-load Azure AI Search client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Azure AI Search client."""
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            return SearchClient(
                endpoint=self.settings.azure_search_endpoint,
                index_name=self.settings.azure_search_index_name,
                credential=AzureKeyCredential(self.settings.azure_search_api_key),
            )
        except Exception as e:
            logger.warning("azure_search_init_failed", error=str(e))
            return None

    async def hybrid_search(
        self,
        query: str,
        index: str = "english_unified",
        filters: Optional[SearchFilters] = None,
        top: int = 50,
    ) -> list[SearchResult]:
        """Perform hybrid search combining vector and keyword search."""
        logger.debug("azure_hybrid_search", query=query[:100], top=top)

        if self.client is None:
            return self._mock_search(query)

        try:
            from azure.search.documents.models import VectorizedQuery

            # Generate query embedding
            query_embedding = await self.embedding_service.embed(query)

            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top,
                fields="content_vector",
            )

            results = self.client.search(
                search_text=query,
                vector_queries=[vector_query],
                query_type="semantic",
                semantic_configuration_name=self.settings.search_semantic_config,
                filter=filters.to_odata_filter() if filters else None,
                top=top,
                select=["id", "content", "parent_id", "source_type", "subject",
                       "grade_level", "board", "chapter", "video_id",
                       "start_timestamp", "end_timestamp"],
            )

            return [
                SearchResult(
                    id=r.get("id", ""),
                    content=r.get("content", ""),
                    score=r.get("@search.score", 0.0),
                    metadata={
                        "source_type": r.get("source_type"),
                        "subject": r.get("subject"),
                        "grade_level": r.get("grade_level"),
                        "board": r.get("board"),
                        "chapter": r.get("chapter"),
                        "video_id": r.get("video_id"),
                        "start_timestamp": r.get("start_timestamp"),
                        "end_timestamp": r.get("end_timestamp"),
                    },
                    vector_score=r.get("@search.vector_score"),
                )
                for r in results
            ]

        except Exception as e:
            logger.error("azure_search_failed", error=str(e))
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
