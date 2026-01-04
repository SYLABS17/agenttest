"""Amazon OpenSearch hybrid search implementation."""

from dataclasses import dataclass
from typing import Optional
import structlog

from src.config import get_settings
from src.search.embeddings import BedrockEmbeddingService

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Result from OpenSearch."""

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

    def to_opensearch_query(self) -> dict:
        """Convert to OpenSearch query filter."""
        must = []
        if self.subjects:
            must.append({"terms": {"subject": self.subjects}})
        if self.grade_levels:
            must.append({"terms": {"grade_level": self.grade_levels}})
        if self.boards:
            must.append({"terms": {"board": self.boards}})
        if self.language:
            must.append({"term": {"language": self.language}})

        return {"bool": {"must": must}} if must else {"match_all": {}}


class OpenSearchService:
    """Amazon OpenSearch with hybrid vector and BM25 search."""

    def __init__(self, embedding_service: Optional[BedrockEmbeddingService] = None):
        self.settings = get_settings()
        self.embedding_service = embedding_service or BedrockEmbeddingService()
        self._client = None

    @property
    def client(self):
        """Lazy-load OpenSearch client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create OpenSearch client."""
        try:
            from opensearchpy import OpenSearch, RequestsHttpConnection
            from requests_aws4auth import AWS4Auth
            import boto3

            credentials = boto3.Session().get_credentials()
            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                self.settings.aws_region,
                "aoss",
                session_token=credentials.token,
            )

            return OpenSearch(
                hosts=[{"host": self.settings.opensearch_endpoint.replace("https://", ""), "port": 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
            )
        except Exception as e:
            logger.warning("opensearch_init_failed", error=str(e))
            return None

    async def hybrid_search(
        self,
        query: str,
        index: str = "english_unified",
        filters: Optional[SearchFilters] = None,
        top: int = 50,
    ) -> list[SearchResult]:
        """Perform hybrid search combining vector and keyword search."""
        logger.debug("opensearch_hybrid_search", query=query[:100], top=top)

        if self.client is None:
            return self._mock_search(query)

        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed(query)

            # Build hybrid query
            search_body = {
                "size": top,
                "query": {
                    "bool": {
                        "should": [
                            # BM25 text search
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["content^2", "chapter", "subject"],
                                }
                            },
                            # KNN vector search
                            {
                                "knn": {
                                    "content_vector": {
                                        "vector": query_embedding,
                                        "k": top,
                                    }
                                }
                            },
                        ],
                    }
                },
                "_source": [
                    "content", "source_type", "subject", "grade_level",
                    "board", "chapter", "video_id", "start_timestamp", "end_timestamp"
                ],
            }

            # Add filters
            if filters:
                search_body["query"]["bool"]["filter"] = filters.to_opensearch_query()

            response = self.client.search(
                index=self.settings.opensearch_index_name,
                body=search_body,
            )

            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                results.append(
                    SearchResult(
                        id=hit["_id"],
                        content=source.get("content", ""),
                        score=hit.get("_score", 0.0),
                        metadata={
                            "source_type": source.get("source_type"),
                            "subject": source.get("subject"),
                            "grade_level": source.get("grade_level"),
                            "board": source.get("board"),
                            "chapter": source.get("chapter"),
                            "video_id": source.get("video_id"),
                            "start_timestamp": source.get("start_timestamp"),
                            "end_timestamp": source.get("end_timestamp"),
                        },
                    )
                )

            return results

        except Exception as e:
            logger.error("opensearch_search_failed", error=str(e))
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
