"""Abstract interfaces for cloud service providers.

These interfaces define the contract that each cloud implementation
must fulfill, enabling seamless switching between Azure, GCP, and AWS.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class SearchResult:
    """Unified search result across cloud providers."""

    id: str
    content: str
    score: float
    metadata: dict
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None


@dataclass
class TranslationResult:
    """Unified translation result."""

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float


@dataclass
class GenerationResult:
    """Unified LLM generation result."""

    text: str
    tokens_used: int
    model: str
    finish_reason: str


class SearchProvider(ABC):
    """Abstract interface for vector/hybrid search services."""

    @abstractmethod
    async def search(
        self,
        query: str,
        index_name: str,
        top_k: int = 50,
        filters: Optional[dict] = None,
        include_vector: bool = True,
    ) -> list[SearchResult]:
        """Perform hybrid search."""
        pass

    @abstractmethod
    async def index_documents(
        self,
        documents: list[dict],
        index_name: str,
    ) -> dict:
        """Index documents with embeddings."""
        pass

    @abstractmethod
    async def delete_documents(
        self,
        document_ids: list[str],
        index_name: str,
    ) -> int:
        """Delete documents from index."""
        pass

    @abstractmethod
    async def create_index(
        self,
        index_name: str,
        schema: dict,
    ) -> bool:
        """Create a new search index."""
        pass


class EmbeddingProvider(ABC):
    """Abstract interface for embedding services."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for single text."""
        pass

    @abstractmethod
    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass


class TranslationProvider(ABC):
    """Abstract interface for translation services."""

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        glossary_id: Optional[str] = None,
    ) -> TranslationResult:
        """Translate text between languages."""
        pass

    @abstractmethod
    async def detect_language(self, text: str) -> str:
        """Detect language of text."""
        pass

    @abstractmethod
    async def create_glossary(
        self,
        glossary_id: str,
        terms: dict[str, dict[str, str]],
    ) -> bool:
        """Create a custom glossary for domain terms."""
        pass


class LLMProvider(ABC):
    """Abstract interface for LLM generation services."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> GenerationResult:
        """Generate text from prompt."""
        pass

    @abstractmethod
    async def generate_with_context(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> GenerationResult:
        """Generate with conversation context."""
        pass


class StorageProvider(ABC):
    """Abstract interface for object storage services."""

    @abstractmethod
    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload data and return URL."""
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """Download data from path."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete object at path."""
        pass

    @abstractmethod
    async def get_url(
        self,
        path: str,
        expiry_seconds: int = 3600,
    ) -> str:
        """Get signed URL for object."""
        pass


class VideoIndexerProvider(ABC):
    """Abstract interface for video indexing services."""

    @abstractmethod
    async def index_video(
        self,
        video_path: str,
        video_id: str,
    ) -> dict:
        """Index video and extract transcript."""
        pass

    @abstractmethod
    async def get_transcript(
        self,
        video_id: str,
    ) -> list[dict]:
        """Get transcript with timestamps."""
        pass


class CloudProvider(ABC):
    """
    Main cloud provider interface.

    Each cloud implementation must provide all service components.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Cloud provider name (azure, gcp, aws)."""
        pass

    @property
    @abstractmethod
    def search(self) -> SearchProvider:
        """Get search provider."""
        pass

    @property
    @abstractmethod
    def embeddings(self) -> EmbeddingProvider:
        """Get embedding provider."""
        pass

    @property
    @abstractmethod
    def translation(self) -> TranslationProvider:
        """Get translation provider."""
        pass

    @property
    @abstractmethod
    def llm(self) -> LLMProvider:
        """Get LLM provider."""
        pass

    @property
    @abstractmethod
    def storage(self) -> StorageProvider:
        """Get storage provider."""
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """Check health of all services."""
        pass
