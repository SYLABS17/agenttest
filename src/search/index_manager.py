"""Index management for Azure AI Search."""

from typing import Optional

import structlog

from src.config import get_settings
from src.chunking.models import Chunk
from src.search.embeddings import EmbeddingService

logger = structlog.get_logger(__name__)


class IndexManager:
    """
    Manages Azure AI Search indices for the LMS.

    Handles:
    - Index creation with proper schema
    - Document indexing with embeddings
    - Index updates and maintenance
    """

    # Index schema for curriculum content
    INDEX_SCHEMA = {
        "name": "curriculum-index",
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "searchable": False},
            {"name": "content", "type": "Edm.String", "searchable": True, "analyzer": "en.microsoft"},
            {"name": "content_vector", "type": "Collection(Edm.Single)", "dimensions": 1536,
             "vectorSearchProfile": "vector-profile"},
            {"name": "parent_id", "type": "Edm.String", "searchable": False, "filterable": True},
            {"name": "is_parent", "type": "Edm.Boolean", "filterable": True},
            {"name": "source_type", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "subject", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "grade_level", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "board", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "chapter", "type": "Edm.String", "searchable": True},
            {"name": "section", "type": "Edm.String", "searchable": True},
            {"name": "page_number", "type": "Edm.Int32", "sortable": True},
            {"name": "language", "type": "Edm.String", "filterable": True},
            {"name": "video_id", "type": "Edm.String", "filterable": True},
            {"name": "start_timestamp", "type": "Edm.String", "sortable": True},
            {"name": "end_timestamp", "type": "Edm.String", "sortable": True},
        ],
        "vectorSearch": {
            "algorithms": [
                {
                    "name": "hnsw-config",
                    "kind": "hnsw",
                    "hnswParameters": {
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                }
            ],
            "profiles": [
                {"name": "vector-profile", "algorithm": "hnsw-config"}
            ]
        },
        "semantic": {
            "configurations": [
                {
                    "name": "curriculum-config",
                    "prioritizedFields": {
                        "contentFields": [{"fieldName": "content"}],
                        "titleFields": [{"fieldName": "chapter"}],
                        "keywordsFields": [{"fieldName": "subject"}]
                    }
                }
            ]
        }
    }

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        admin_client: Optional[object] = None,
        search_client: Optional[object] = None,
    ):
        """
        Initialize index manager.

        Args:
            embedding_service: Service for generating embeddings
            admin_client: Azure Search Index Admin Client
            search_client: Azure Search Client for document operations
        """
        self.settings = get_settings()
        self.embedding_service = embedding_service or EmbeddingService()
        self._admin_client = admin_client
        self._search_client = search_client

    @property
    def admin_client(self):
        """Lazy-load admin client."""
        if self._admin_client is None:
            self._admin_client = self._create_admin_client()
        return self._admin_client

    @property
    def search_client(self):
        """Lazy-load search client."""
        if self._search_client is None:
            self._search_client = self._create_search_client()
        return self._search_client

    def _create_admin_client(self):
        """Create Azure Search Index Admin Client."""
        try:
            from azure.search.documents.indexes import SearchIndexClient
            from azure.core.credentials import AzureKeyCredential

            return SearchIndexClient(
                endpoint=self.settings.azure_search_endpoint,
                credential=AzureKeyCredential(self.settings.azure_search_api_key),
            )
        except Exception as e:
            logger.warning("admin_client_init_failed", error=str(e))
            return None

    def _create_search_client(self):
        """Create Azure Search Client for document operations."""
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

    async def create_index(self, index_name: Optional[str] = None) -> bool:
        """
        Create search index with proper schema.

        Args:
            index_name: Name for the index (default from settings)

        Returns:
            True if created successfully
        """
        if self.admin_client is None:
            logger.warning("cannot_create_index", reason="admin client unavailable")
            return False

        name = index_name or self.settings.azure_search_index_name

        try:
            from azure.search.documents.indexes.models import (
                SearchIndex,
                SearchField,
                VectorSearch,
                HnswAlgorithmConfiguration,
                VectorSearchProfile,
                SemanticConfiguration,
                SemanticPrioritizedFields,
                SemanticField,
                SemanticSearch,
            )

            # Build fields
            fields = [
                SearchField(name="id", type="Edm.String", key=True),
                SearchField(name="content", type="Edm.String", searchable=True, analyzer_name="en.microsoft"),
                SearchField(
                    name="content_vector",
                    type="Collection(Edm.Single)",
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="vector-profile",
                ),
                SearchField(name="parent_id", type="Edm.String", filterable=True),
                SearchField(name="is_parent", type="Edm.Boolean", filterable=True),
                SearchField(name="source_type", type="Edm.String", filterable=True, facetable=True),
                SearchField(name="subject", type="Edm.String", filterable=True, facetable=True),
                SearchField(name="grade_level", type="Edm.String", filterable=True, facetable=True),
                SearchField(name="board", type="Edm.String", filterable=True, facetable=True),
                SearchField(name="chapter", type="Edm.String", searchable=True),
                SearchField(name="section", type="Edm.String", searchable=True),
                SearchField(name="page_number", type="Edm.Int32", sortable=True),
                SearchField(name="language", type="Edm.String", filterable=True),
                SearchField(name="video_id", type="Edm.String", filterable=True),
                SearchField(name="start_timestamp", type="Edm.String", sortable=True),
                SearchField(name="end_timestamp", type="Edm.String", sortable=True),
            ]

            # Vector search config
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="hnsw-config",
                        parameters={"m": 4, "efConstruction": 400, "efSearch": 500, "metric": "cosine"},
                    )
                ],
                profiles=[
                    VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")
                ],
            )

            # Semantic config
            semantic_config = SemanticConfiguration(
                name="curriculum-config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")],
                    title_field=SemanticField(field_name="chapter"),
                    keywords_fields=[SemanticField(field_name="subject")],
                ),
            )

            # Create index
            index = SearchIndex(
                name=name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=SemanticSearch(configurations=[semantic_config]),
            )

            self.admin_client.create_or_update_index(index)
            logger.info("index_created", name=name)
            return True

        except Exception as e:
            logger.error("index_creation_failed", error=str(e))
            return False

    async def index_chunks(
        self,
        chunks: list[Chunk],
        batch_size: int = 100,
    ) -> dict:
        """
        Index chunks with embeddings.

        Args:
            chunks: List of chunks to index
            batch_size: Number of documents per batch

        Returns:
            Dict with success/failure counts
        """
        if self.search_client is None:
            logger.warning("cannot_index", reason="search client unavailable")
            return {"indexed": 0, "failed": len(chunks)}

        logger.info("indexing_chunks", count=len(chunks))

        # Generate embeddings for all chunks
        contents = [c.content for c in chunks]
        embeddings = await self.embedding_service.embed_batch(contents, batch_size)

        # Prepare documents
        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            doc = chunk.to_dict()
            doc["content_vector"] = embedding
            documents.append(doc)

        # Index in batches
        indexed = 0
        failed = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            try:
                result = self.search_client.upload_documents(documents=batch)
                for r in result:
                    if r.succeeded:
                        indexed += 1
                    else:
                        failed += 1
                        logger.warning("document_index_failed", key=r.key, error=r.error_message)
            except Exception as e:
                logger.error("batch_index_failed", error=str(e))
                failed += len(batch)

        logger.info("indexing_complete", indexed=indexed, failed=failed)
        return {"indexed": indexed, "failed": failed}

    async def delete_documents(self, document_ids: list[str]) -> int:
        """
        Delete documents from index.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            Number of documents deleted
        """
        if self.search_client is None:
            return 0

        try:
            documents = [{"id": doc_id} for doc_id in document_ids]
            result = self.search_client.delete_documents(documents=documents)
            deleted = sum(1 for r in result if r.succeeded)
            logger.info("documents_deleted", count=deleted)
            return deleted
        except Exception as e:
            logger.error("delete_failed", error=str(e))
            return 0

    async def get_document(self, document_id: str) -> Optional[Chunk]:
        """
        Retrieve a specific document by ID.

        Args:
            document_id: Document ID

        Returns:
            Chunk if found, None otherwise
        """
        if self.search_client is None:
            return None

        try:
            result = self.search_client.get_document(key=document_id)
            return Chunk.from_dict(result)
        except Exception as e:
            logger.warning("document_not_found", id=document_id, error=str(e))
            return None

    async def get_parent_chunk(self, child_chunk: Chunk) -> Optional[Chunk]:
        """
        Retrieve parent chunk for a child chunk.

        Args:
            child_chunk: Child chunk

        Returns:
            Parent chunk if exists
        """
        if child_chunk.parent_id is None:
            return None

        return await self.get_document(child_chunk.parent_id)

    def get_index_stats(self) -> dict:
        """Get index statistics."""
        if self.admin_client is None:
            return {}

        try:
            index = self.admin_client.get_index(self.settings.azure_search_index_name)
            return {
                "name": index.name,
                "field_count": len(index.fields),
            }
        except Exception as e:
            logger.warning("stats_failed", error=str(e))
            return {}
