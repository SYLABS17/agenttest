"""Embedding service for vector search."""

from typing import Optional

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """
    Embedding generation service using Azure OpenAI.

    Uses text-embedding-ada-002 or text-embedding-3-large for
    high-quality vector representations of educational content.
    """

    def __init__(self, client: Optional[object] = None):
        """
        Initialize embedding service.

        Args:
            client: Azure OpenAI client (injected for testing)
        """
        self.settings = get_settings()
        self._client = client
        self.embedding_dimension = 1536  # ada-002 dimension

    @property
    def client(self):
        """Lazy-load Azure OpenAI client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Azure OpenAI client."""
        try:
            from openai import AzureOpenAI

            return AzureOpenAI(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
            )
        except Exception as e:
            logger.warning("embedding_client_init_failed", error=str(e))
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Truncate if too long (ada-002 has 8191 token limit)
        text = self._truncate_text(text, max_chars=30000)

        if self.client is None:
            # Return mock embedding for development
            logger.warning("using_mock_embedding")
            return [0.0] * self.embedding_dimension

        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.settings.azure_openai_embedding_deployment,
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error("embedding_failed", error=str(e), text_length=len(text))
            raise

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        logger.debug("embedding_batch", count=len(texts))

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch = [self._truncate_text(t, max_chars=30000) for t in batch]

            if self.client is None:
                # Mock embeddings for development
                batch_embeddings = [[0.0] * self.embedding_dimension] * len(batch)
            else:
                try:
                    response = self.client.embeddings.create(
                        input=batch,
                        model=self.settings.azure_openai_embedding_deployment,
                    )
                    batch_embeddings = [d.embedding for d in response.data]
                except Exception as e:
                    logger.error("batch_embedding_failed", error=str(e), batch_size=len(batch))
                    raise

            embeddings.extend(batch_embeddings)

        return embeddings

    def _truncate_text(self, text: str, max_chars: int) -> str:
        """Truncate text to maximum character length."""
        if len(text) <= max_chars:
            return text

        # Try to truncate at sentence boundary
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        if last_period > max_chars * 0.8:
            return truncated[:last_period + 1]
        return truncated

    def cosine_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between -1 and 1
        """
        import math

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
