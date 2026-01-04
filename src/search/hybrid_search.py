"""Hybrid search combining vector and BM25 keyword search."""

from dataclasses import dataclass
from typing import Optional

import structlog

from src.config import get_settings
from src.chunking.models import Chunk, ChunkMetadata
from src.search.embeddings import EmbeddingService

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Result from hybrid search."""

    chunk: Chunk
    score: float
    vector_score: float
    keyword_score: float
    semantic_caption: Optional[str] = None
    highlights: Optional[list[str]] = None


@dataclass
class SearchFilters:
    """Filters for search queries."""

    subjects: Optional[list[str]] = None
    grade_levels: Optional[list[str]] = None
    boards: Optional[list[str]] = None
    source_types: Optional[list[str]] = None
    language: Optional[str] = None

    def to_odata_filter(self) -> Optional[str]:
        """Convert filters to OData filter expression for Azure AI Search."""
        conditions = []

        if self.subjects:
            subjects_filter = " or ".join([f"subject eq '{s}'" for s in self.subjects])
            conditions.append(f"({subjects_filter})")

        if self.grade_levels:
            grades_filter = " or ".join([f"grade_level eq '{g}'" for g in self.grade_levels])
            conditions.append(f"({grades_filter})")

        if self.boards:
            boards_filter = " or ".join([f"board eq '{b}'" for b in self.boards])
            conditions.append(f"({boards_filter})")

        if self.source_types:
            types_filter = " or ".join([f"source_type eq '{t}'" for t in self.source_types])
            conditions.append(f"({types_filter})")

        if self.language:
            conditions.append(f"language eq '{self.language}'")

        return " and ".join(conditions) if conditions else None


class HybridSearchService:
    """
    Hybrid search service combining vector and BM25 search.

    Uses Azure AI Search with:
    - Vector search: Semantic similarity using embeddings
    - BM25 keyword search: Exact term matching

    The combination provides:
    - Conceptual understanding (vector)
    - Precise term matching (BM25)
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        search_client: Optional[object] = None,
    ):
        """
        Initialize hybrid search service.

        Args:
            embedding_service: Service for generating embeddings
            search_client: Azure AI Search client (injected for testing)
        """
        self.settings = get_settings()
        self.embedding_service = embedding_service or EmbeddingService()
        self._client = search_client

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
            logger.warning("search_client_init_failed", error=str(e))
            return None

    async def hybrid_search(
        self,
        query: str,
        index: str = "english_unified",
        filters: Optional[SearchFilters] = None,
        top: int = 50,
        include_vector: bool = True,
        include_semantic: bool = True,
    ) -> list[SearchResult]:
        """
        Perform hybrid search combining vector and keyword search.

        Args:
            query: Search query
            index: Index to search (english_unified or {lang}_native)
            filters: Optional filters to apply
            top: Maximum number of results
            include_vector: Whether to include vector search
            include_semantic: Whether to include semantic ranking

        Returns:
            List of search results sorted by relevance
        """
        logger.debug(
            "hybrid_search",
            query=query[:100],
            index=index,
            top=top,
        )

        if self.client is None:
            logger.warning("using_mock_search")
            return self._mock_search(query, top)

        try:
            # Generate query embedding
            query_embedding = None
            if include_vector:
                query_embedding = await self.embedding_service.embed(query)

            # Build search request
            from azure.search.documents.models import VectorizedQuery

            vector_queries = []
            if query_embedding:
                vector_queries.append(
                    VectorizedQuery(
                        vector=query_embedding,
                        k_nearest_neighbors=top,
                        fields="content_vector",
                    )
                )

            # Execute search
            results = self.client.search(
                search_text=query,
                vector_queries=vector_queries if vector_queries else None,
                query_type="semantic" if include_semantic else "simple",
                semantic_configuration_name=self.settings.search_semantic_config,
                filter=filters.to_odata_filter() if filters else None,
                top=top,
                select=[
                    "id", "content", "parent_id", "is_parent",
                    "source_type", "subject", "grade_level", "board",
                    "chapter", "section", "page_number", "language",
                    "video_id", "start_timestamp", "end_timestamp",
                ],
                include_total_count=True,
            )

            # Process results
            search_results = []
            for result in results:
                chunk = self._result_to_chunk(result)
                search_results.append(
                    SearchResult(
                        chunk=chunk,
                        score=result.get("@search.score", 0.0),
                        vector_score=result.get("@search.vector_score", 0.0),
                        keyword_score=result.get("@search.score", 0.0),
                        semantic_caption=self._extract_caption(result),
                        highlights=result.get("@search.highlights", {}).get("content", []),
                    )
                )

            logger.info(
                "search_completed",
                query=query[:50],
                result_count=len(search_results),
            )

            return search_results

        except Exception as e:
            logger.error("search_failed", error=str(e))
            raise

    async def keyword_search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top: int = 50,
    ) -> list[SearchResult]:
        """
        Perform BM25 keyword-only search.

        Useful for exact term matching when semantic search isn't needed.
        """
        return await self.hybrid_search(
            query=query,
            filters=filters,
            top=top,
            include_vector=False,
            include_semantic=False,
        )

    async def vector_search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top: int = 50,
    ) -> list[SearchResult]:
        """
        Perform vector-only search.

        Useful for conceptual similarity without term matching.
        """
        return await self.hybrid_search(
            query=query,
            filters=filters,
            top=top,
            include_vector=True,
            include_semantic=False,
        )

    async def search_by_embedding(
        self,
        embedding: list[float],
        filters: Optional[SearchFilters] = None,
        top: int = 50,
    ) -> list[SearchResult]:
        """
        Search using a pre-computed embedding vector.

        Args:
            embedding: Pre-computed embedding vector
            filters: Optional filters
            top: Maximum results

        Returns:
            List of search results
        """
        if self.client is None:
            return []

        from azure.search.documents.models import VectorizedQuery

        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top,
            fields="content_vector",
        )

        results = self.client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=filters.to_odata_filter() if filters else None,
            top=top,
            select=[
                "id", "content", "parent_id", "is_parent",
                "source_type", "subject", "grade_level", "board",
                "chapter", "section", "page_number", "language",
                "video_id", "start_timestamp", "end_timestamp",
            ],
        )

        return [
            SearchResult(
                chunk=self._result_to_chunk(r),
                score=r.get("@search.score", 0.0),
                vector_score=r.get("@search.score", 0.0),
                keyword_score=0.0,
            )
            for r in results
        ]

    def _result_to_chunk(self, result: dict) -> Chunk:
        """Convert search result to Chunk object."""
        metadata = ChunkMetadata(
            source_type=result.get("source_type", "unknown"),
            subject=result.get("subject", "unknown"),
            grade_level=result.get("grade_level", "unknown"),
            board=result.get("board", "unknown"),
            chapter=result.get("chapter"),
            section=result.get("section"),
            page_number=result.get("page_number"),
            language=result.get("language", "en"),
            video_id=result.get("video_id"),
            start_timestamp=result.get("start_timestamp"),
            end_timestamp=result.get("end_timestamp"),
        )

        return Chunk(
            id=result.get("id", ""),
            content=result.get("content", ""),
            parent_id=result.get("parent_id"),
            is_parent=result.get("is_parent", False),
            metadata=metadata,
        )

    def _extract_caption(self, result: dict) -> Optional[str]:
        """Extract semantic caption from search result."""
        captions = result.get("@search.captions", [])
        if captions and len(captions) > 0:
            return captions[0].get("text")
        return None

    def _mock_search(self, query: str, top: int) -> list[SearchResult]:
        """Return mock results for development."""
        mock_chunk = Chunk(
            id="mock-1",
            content=f"Mock result for: {query}",
            metadata=ChunkMetadata(
                source_type="mock",
                subject="test",
                grade_level="test",
                board="mock",
            ),
        )
        return [
            SearchResult(
                chunk=mock_chunk,
                score=0.9,
                vector_score=0.85,
                keyword_score=0.9,
            )
        ]

    def build_user_context_filters(
        self,
        user_context: dict,
    ) -> SearchFilters:
        """
        Build search filters from user context.

        Args:
            user_context: Dict with user preferences (grade, board, subjects)

        Returns:
            SearchFilters configured for the user
        """
        return SearchFilters(
            subjects=user_context.get("subjects"),
            grade_levels=[user_context.get("grade_level")] if user_context.get("grade_level") else None,
            boards=[user_context.get("board")] if user_context.get("board") else None,
            language=user_context.get("language"),
        )
