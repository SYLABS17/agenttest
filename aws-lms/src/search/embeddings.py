"""Amazon Bedrock embedding service."""

from typing import Optional
import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings

logger = structlog.get_logger(__name__)


class BedrockEmbeddingService:
    """Embedding service using Amazon Bedrock Titan Embeddings."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self.embedding_dimension = 1024  # Titan Embeddings v2 dimension

    @property
    def client(self):
        """Lazy-load Bedrock Runtime client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Bedrock Runtime client."""
        try:
            import boto3

            return boto3.client(
                "bedrock-runtime",
                region_name=self.settings.aws_region,
            )
        except Exception as e:
            logger.warning("bedrock_client_init_failed", error=str(e))
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text using Bedrock Titan Embeddings."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        text = text[:8000]  # Titan limit

        if self.client is None:
            logger.warning("using_mock_embedding")
            return [0.0] * self.embedding_dimension

        try:
            body = json.dumps({
                "inputText": text,
            })

            response = self.client.invoke_model(
                modelId=self.settings.bedrock_embedding_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            return response_body.get("embedding", [0.0] * self.embedding_dimension)

        except Exception as e:
            logger.error("embedding_failed", error=str(e))
            raise

    async def embed_batch(
        self, texts: list[str], batch_size: int = 25
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        embeddings = []
        for text in texts:
            embedding = await self.embed(text[:8000])
            embeddings.append(embedding)

        return embeddings

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self.embedding_dimension
