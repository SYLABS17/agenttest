"""Vertex AI embedding service."""

from typing import Optional
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings

logger = structlog.get_logger(__name__)


class VertexAIEmbeddingService:
    """Embedding service using Vertex AI text-embedding-005 or Gemini Embedding."""

    def __init__(self):
        self.settings = get_settings()
        self._model = None
        self.embedding_dimension = 768  # text-embedding-005 dimension

    @property
    def model(self):
        """Lazy-load Vertex AI embedding model."""
        if self._model is None:
            self._model = self._create_model()
        return self._model

    def _create_model(self):
        """Create Vertex AI embedding model."""
        try:
            import vertexai
            from vertexai.language_models import TextEmbeddingModel

            vertexai.init(
                project=self.settings.google_cloud_project,
                location=self.settings.vertex_ai_location,
            )
            return TextEmbeddingModel.from_pretrained(self.settings.embedding_model)
        except Exception as e:
            logger.warning("vertex_ai_embedding_init_failed", error=str(e))
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text using Vertex AI."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        text = text[:20000]  # Truncate if too long

        if self.model is None:
            logger.warning("using_mock_embedding")
            return [0.0] * self.embedding_dimension

        try:
            embeddings = self.model.get_embeddings([text])
            return embeddings[0].values
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
            batch = [t[:20000] for t in texts[i:i + batch_size]]

            if self.model is None:
                embeddings.extend([[0.0] * self.embedding_dimension] * len(batch))
            else:
                try:
                    batch_embeddings = self.model.get_embeddings(batch)
                    embeddings.extend([e.values for e in batch_embeddings])
                except Exception as e:
                    logger.error("batch_embedding_failed", error=str(e))
                    raise

        return embeddings

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self.embedding_dimension
