"""Azure OpenAI embedding service."""

from typing import Optional
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings

logger = structlog.get_logger(__name__)


class AzureEmbeddingService:
    """Embedding service using Azure OpenAI text-embedding-ada-002."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None
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
            logger.warning("azure_openai_init_failed", error=str(e))
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text using Azure OpenAI."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        text = text[:30000]  # Truncate if too long

        if self.client is None:
            logger.warning("using_mock_embedding")
            return [0.0] * self.embedding_dimension

        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.settings.azure_openai_embedding_deployment,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("embedding_failed", error=str(e))
            raise

    async def embed_batch(
        self, texts: list[str], batch_size: int = 100
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = [t[:30000] for t in texts[i:i + batch_size]]

            if self.client is None:
                embeddings.extend([[0.0] * self.embedding_dimension] * len(batch))
            else:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.settings.azure_openai_embedding_deployment,
                )
                embeddings.extend([d.embedding for d in response.data])

        return embeddings

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self.embedding_dimension
