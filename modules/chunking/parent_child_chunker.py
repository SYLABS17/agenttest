"""
Parent-Child Chunker with Unique IDs and Semantic Ranking
==========================================================
Advanced RAG chunking strategy for hierarchical document processing.

Features:
- Parent chunks (large context) with child chunks (precise retrieval)
- Unique deterministic IDs based on content hash + position
- Semantic ranking integration
- Overlap handling between chunks
- Metadata preservation across hierarchy
"""

import hashlib
import re
import json
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


class ChunkType(Enum):
    """Type of chunk in the hierarchy."""
    PARENT = "parent"
    CHILD = "child"


class SplitStrategy(Enum):
    """Strategy for splitting text into chunks."""
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"  # Requires embedding model


@dataclass
class ChunkingConfig:
    """Configuration for chunking behavior."""
    # Parent chunk settings
    parent_chunk_size: int = 2000       # Characters
    parent_overlap: int = 200           # Overlap between parents

    # Child chunk settings
    child_chunk_size: int = 400         # Characters
    child_overlap: int = 50             # Overlap between children
    children_per_parent: int = 5        # Max children per parent

    # Strategy
    split_strategy: SplitStrategy = SplitStrategy.SENTENCE

    # ID generation
    id_prefix: str = "chunk"            # Prefix for chunk IDs
    include_position_in_id: bool = True # Include position in ID hash

    # Metadata
    preserve_metadata: bool = True      # Pass metadata to children


@dataclass
class Chunk:
    """A single chunk (parent or child)."""
    chunk_id: str                       # Unique deterministic ID
    content: str                        # Chunk text content
    chunk_type: ChunkType               # Parent or child
    parent_id: Optional[str] = None     # Parent chunk ID (for children)
    document_id: str = ""               # Source document ID
    position: int = 0                   # Position in document (0-indexed)
    start_char: int = 0                 # Start character position
    end_char: int = 0                   # End character position
    metadata: dict = field(default_factory=dict)
    embedding: list = field(default_factory=list)  # Optional embedding
    semantic_score: float = 0.0         # Semantic ranking score


@dataclass
class ChunkHierarchy:
    """Complete hierarchy of parent and child chunks."""
    document_id: str
    parent_chunks: list                 # List of parent Chunks
    child_chunks: list                  # List of child Chunks
    total_parents: int = 0
    total_children: int = 0
    metadata: dict = field(default_factory=dict)

    def get_parent(self, parent_id: str) -> Optional[Chunk]:
        """Get parent chunk by ID."""
        for p in self.parent_chunks:
            if p.chunk_id == parent_id:
                return p
        return None

    def get_children(self, parent_id: str) -> list:
        """Get all children for a parent."""
        return [c for c in self.child_chunks if c.parent_id == parent_id]

    def to_search_documents(self) -> list:
        """Convert to Azure AI Search document format."""
        docs = []

        # Parents with their children content for context
        for parent in self.parent_chunks:
            children = self.get_children(parent.chunk_id)
            child_content = " ".join([c.content for c in children])

            docs.append({
                "id": parent.chunk_id,
                "content": parent.content,
                "child_content": child_content,
                "chunk_type": "parent",
                "document_id": self.document_id,
                "position": parent.position,
                "metadata": json.dumps(parent.metadata),
                "embedding": parent.embedding if parent.embedding else None
            })

        # Children with parent reference
        for child in self.child_chunks:
            docs.append({
                "id": child.chunk_id,
                "content": child.content,
                "parent_id": child.parent_id,
                "chunk_type": "child",
                "document_id": self.document_id,
                "position": child.position,
                "metadata": json.dumps(child.metadata),
                "embedding": child.embedding if child.embedding else None
            })

        return docs


class SemanticRanker:
    """
    Semantic ranking for chunks.
    Assigns scores based on content relevance.
    """

    def __init__(self, embedding_fn: Callable = None):
        """
        Initialize ranker.

        Args:
            embedding_fn: Function to generate embeddings (text -> list[float])
        """
        self.embedding_fn = embedding_fn

    async def compute_embeddings(self, chunks: list) -> list:
        """Compute embeddings for all chunks."""
        if not self.embedding_fn:
            return chunks

        for chunk in chunks:
            chunk.embedding = await self.embedding_fn(chunk.content)

        return chunks

    def rank_by_query(self, chunks: list, query_embedding: list) -> list:
        """
        Rank chunks by similarity to query.

        Args:
            chunks: List of Chunk objects with embeddings
            query_embedding: Query embedding vector

        Returns:
            Chunks sorted by semantic score (descending)
        """
        if not query_embedding:
            return chunks

        for chunk in chunks:
            if chunk.embedding:
                chunk.semantic_score = self._cosine_similarity(
                    chunk.embedding,
                    query_embedding
                )

        return sorted(chunks, key=lambda c: c.semantic_score, reverse=True)

    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class ParentChildChunker:
    """
    Hierarchical document chunker with parent-child relationships.

    Parents provide context, children provide precision.
    Each chunk gets a unique, deterministic ID.

    Usage:
        chunker = ParentChildChunker(config)
        hierarchy = chunker.chunk_document(doc_id, text, metadata)

        # Access chunks
        for parent in hierarchy.parent_chunks:
            children = hierarchy.get_children(parent.chunk_id)

        # Export for search
        search_docs = hierarchy.to_search_documents()
    """

    def __init__(self, config: ChunkingConfig = None):
        self.config = config or ChunkingConfig()
        self.ranker = SemanticRanker()

    def _generate_chunk_id(
        self,
        document_id: str,
        content: str,
        chunk_type: ChunkType,
        position: int,
        parent_id: str = None
    ) -> str:
        """
        Generate unique, deterministic chunk ID.

        ID format: {prefix}_{type}_{hash}
        Hash is based on: document_id + content + position
        """
        # Build hash input
        hash_input = f"{document_id}:{content[:100]}"

        if self.config.include_position_in_id:
            hash_input += f":{position}"

        if parent_id:
            hash_input += f":{parent_id}"

        # Generate hash
        content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]

        # Build ID
        type_prefix = "p" if chunk_type == ChunkType.PARENT else "c"
        chunk_id = f"{self.config.id_prefix}_{type_prefix}_{content_hash}"

        return chunk_id

    def _split_into_sentences(self, text: str) -> list:
        """Split text into sentences."""
        # Handle common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_into_paragraphs(self, text: str) -> list:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_fixed_size(self, text: str, size: int, overlap: int) -> list:
        """Split text into fixed-size chunks with overlap."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + size
            chunk = text[start:end]

            # Try to end at word boundary
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space

            chunks.append({
                "text": chunk.strip(),
                "start": start,
                "end": end
            })

            start = end - overlap
            if start < 0:
                start = 0

        return chunks

    def _create_parent_chunks(self, document_id: str, text: str, metadata: dict) -> list:
        """Create parent chunks from document."""
        parent_chunks = []

        raw_chunks = self._split_fixed_size(
            text,
            self.config.parent_chunk_size,
            self.config.parent_overlap
        )

        for i, chunk_data in enumerate(raw_chunks):
            chunk_id = self._generate_chunk_id(
                document_id,
                chunk_data["text"],
                ChunkType.PARENT,
                i
            )

            parent = Chunk(
                chunk_id=chunk_id,
                content=chunk_data["text"],
                chunk_type=ChunkType.PARENT,
                document_id=document_id,
                position=i,
                start_char=chunk_data["start"],
                end_char=chunk_data["end"],
                metadata=metadata.copy() if self.config.preserve_metadata else {}
            )
            parent_chunks.append(parent)

        return parent_chunks

    def _create_child_chunks(self, parent: Chunk) -> list:
        """Create child chunks from a parent chunk."""
        child_chunks = []

        # Split parent content into children
        if self.config.split_strategy == SplitStrategy.SENTENCE:
            sentences = self._split_into_sentences(parent.content)
            raw_chunks = self._merge_sentences(sentences, self.config.child_chunk_size)
        elif self.config.split_strategy == SplitStrategy.PARAGRAPH:
            raw_chunks = self._split_into_paragraphs(parent.content)
        else:
            raw_chunks = self._split_fixed_size(
                parent.content,
                self.config.child_chunk_size,
                self.config.child_overlap
            )
            raw_chunks = [c["text"] for c in raw_chunks]

        # Limit children per parent
        raw_chunks = raw_chunks[:self.config.children_per_parent]

        for i, content in enumerate(raw_chunks):
            if isinstance(content, dict):
                content = content.get("text", str(content))

            chunk_id = self._generate_chunk_id(
                parent.document_id,
                content,
                ChunkType.CHILD,
                i,
                parent.chunk_id
            )

            child = Chunk(
                chunk_id=chunk_id,
                content=content,
                chunk_type=ChunkType.CHILD,
                parent_id=parent.chunk_id,
                document_id=parent.document_id,
                position=i,
                metadata=parent.metadata.copy() if self.config.preserve_metadata else {}
            )
            child_chunks.append(child)

        return child_chunks

    def _merge_sentences(self, sentences: list, target_size: int) -> list:
        """Merge sentences into chunks of target size."""
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_size + sentence_len > target_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_len + 1  # +1 for space

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def chunk_document(
        self,
        document_id: str,
        text: str,
        metadata: dict = None
    ) -> ChunkHierarchy:
        """
        Chunk a document into parent-child hierarchy.

        Args:
            document_id: Unique document identifier
            text: Document text content
            metadata: Optional metadata to attach to chunks

        Returns:
            ChunkHierarchy with all parent and child chunks
        """
        metadata = metadata or {}

        # Create parents
        parent_chunks = self._create_parent_chunks(document_id, text, metadata)

        # Create children for each parent
        all_children = []
        for parent in parent_chunks:
            children = self._create_child_chunks(parent)
            all_children.extend(children)

        return ChunkHierarchy(
            document_id=document_id,
            parent_chunks=parent_chunks,
            child_chunks=all_children,
            total_parents=len(parent_chunks),
            total_children=len(all_children),
            metadata=metadata
        )

    async def chunk_with_embeddings(
        self,
        document_id: str,
        text: str,
        embedding_fn: Callable,
        metadata: dict = None
    ) -> ChunkHierarchy:
        """
        Chunk document and compute embeddings for all chunks.

        Args:
            document_id: Unique document identifier
            text: Document text content
            embedding_fn: Async function to generate embeddings
            metadata: Optional metadata

        Returns:
            ChunkHierarchy with embeddings populated
        """
        hierarchy = self.chunk_document(document_id, text, metadata)

        # Compute embeddings for all chunks
        self.ranker.embedding_fn = embedding_fn
        await self.ranker.compute_embeddings(hierarchy.parent_chunks)
        await self.ranker.compute_embeddings(hierarchy.child_chunks)

        return hierarchy


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_search_index_schema() -> dict:
    """
    Create Azure AI Search index schema for parent-child chunks.
    """
    return {
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
            {"name": "content", "type": "Edm.String", "searchable": True},
            {"name": "child_content", "type": "Edm.String", "searchable": True},
            {"name": "chunk_type", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "parent_id", "type": "Edm.String", "filterable": True},
            {"name": "document_id", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "position", "type": "Edm.Int32", "filterable": True, "sortable": True},
            {"name": "metadata", "type": "Edm.String", "searchable": False},
            {"name": "embedding", "type": "Collection(Edm.Single)",
             "searchable": True, "dimensions": 1536, "vectorSearchProfile": "parent-child-profile"}
        ],
        "vectorSearch": {
            "profiles": [{"name": "parent-child-profile", "algorithm": "hnsw-config"}],
            "algorithms": [{"name": "hnsw-config", "kind": "hnsw",
                          "parameters": {"m": 4, "efConstruction": 400, "efSearch": 500}}]
        },
        "semantic": {
            "configurations": [{
                "name": "parent-child-semantic",
                "prioritizedFields": {
                    "contentFields": [
                        {"fieldName": "content"},
                        {"fieldName": "child_content"}
                    ]
                }
            }]
        }
    }
