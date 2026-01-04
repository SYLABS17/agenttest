"""Cross-encoder reranking implementation."""

from dataclasses import dataclass
from typing import Optional

import structlog

from src.config import get_settings
from src.search.hybrid_search import SearchResult
from src.chunking.models import Chunk, ChunkWithContext

logger = structlog.get_logger(__name__)


@dataclass
class RerankResult:
    """Result from reranking operation."""

    chunk: Chunk
    original_score: float
    rerank_score: float
    combined_score: float
    parent_chunk: Optional[Chunk] = None


class CrossEncoderReranker:
    """
    Cross-encoder reranking for improved search relevance.

    Uses a cross-encoder model (e.g., ms-marco-MiniLM) to score
    query-document pairs for more accurate relevance ranking.

    Benefits over bi-encoder (embedding) search:
    - Considers full interaction between query and document
    - More accurate for nuanced relevance
    - Better at detecting subtle semantic matches
    """

    # Supported model names
    MODELS = {
        "ms-marco": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "ms-marco-large": "cross-encoder/ms-marco-MiniLM-L-12-v2",
        "bge": "BAAI/bge-reranker-base",
        "bge-large": "BAAI/bge-reranker-large",
    }

    def __init__(
        self,
        model_name: str = "ms-marco",
        device: str = "cpu",
        batch_size: int = 32,
    ):
        """
        Initialize cross-encoder reranker.

        Args:
            model_name: Name of the cross-encoder model
            device: Device for inference ("cpu" or "cuda")
            batch_size: Batch size for reranking
        """
        self.settings = get_settings()
        self.model_name = self.MODELS.get(model_name, model_name)
        self.device = device
        self.batch_size = batch_size
        self._model = None

    @property
    def model(self):
        """Lazy-load cross-encoder model."""
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self):
        """Load the cross-encoder model."""
        try:
            from sentence_transformers import CrossEncoder

            logger.info("loading_reranker", model=self.model_name)
            model = CrossEncoder(self.model_name, device=self.device)
            logger.info("reranker_loaded", model=self.model_name)
            return model
        except ImportError:
            logger.warning("sentence_transformers_not_available")
            return None
        except Exception as e:
            logger.error("reranker_load_failed", error=str(e))
            return None

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 7,
        score_threshold: float = 0.0,
    ) -> list[RerankResult]:
        """
        Rerank search results using cross-encoder.

        Args:
            query: Original search query
            results: Search results to rerank
            top_k: Number of top results to return
            score_threshold: Minimum score threshold

        Returns:
            Reranked results sorted by relevance
        """
        if not results:
            return []

        logger.debug(
            "reranking",
            query=query[:100],
            result_count=len(results),
            top_k=top_k,
        )

        # If model not available, return original order with scores
        if self.model is None:
            logger.warning("using_original_ranking")
            return self._passthrough_rerank(results, top_k)

        try:
            # Prepare query-document pairs
            pairs = [[query, r.chunk.content] for r in results]

            # Score all pairs
            scores = self.model.predict(pairs, batch_size=self.batch_size)

            # Combine with original scores
            reranked = []
            for result, rerank_score in zip(results, scores):
                # Weighted combination of original and rerank scores
                combined = self._combine_scores(
                    original=result.score,
                    rerank=float(rerank_score),
                )

                if combined >= score_threshold:
                    reranked.append(
                        RerankResult(
                            chunk=result.chunk,
                            original_score=result.score,
                            rerank_score=float(rerank_score),
                            combined_score=combined,
                        )
                    )

            # Sort by combined score
            reranked.sort(key=lambda x: x.combined_score, reverse=True)

            # Take top_k
            result = reranked[:top_k]

            logger.info(
                "reranking_complete",
                input_count=len(results),
                output_count=len(result),
            )

            return result

        except Exception as e:
            logger.error("reranking_failed", error=str(e))
            return self._passthrough_rerank(results, top_k)

    def rerank_with_context(
        self,
        query: str,
        results: list[SearchResult],
        parent_fetcher: callable,
        top_k: int = 7,
    ) -> list[ChunkWithContext]:
        """
        Rerank and expand with parent context.

        Args:
            query: Search query
            results: Search results
            parent_fetcher: Function to fetch parent chunks
            top_k: Number of results

        Returns:
            List of chunks with parent context
        """
        # First rerank
        reranked = self.rerank(query, results, top_k=top_k)

        # Expand with parent context
        expanded = []
        for result in reranked:
            parent = None
            if result.chunk.parent_id:
                parent = parent_fetcher(result.chunk.parent_id)

            expanded.append(
                ChunkWithContext(
                    matched_chunk=result.chunk,
                    parent_chunk=parent,
                    relevance_score=result.combined_score,
                )
            )

        return expanded

    def _combine_scores(
        self,
        original: float,
        rerank: float,
        original_weight: float = 0.3,
    ) -> float:
        """
        Combine original search score with rerank score.

        Args:
            original: Original search score (typically 0-1 or higher)
            rerank: Reranker score (can be negative for cross-encoders)
            original_weight: Weight for original score

        Returns:
            Combined score
        """
        # Normalize rerank score to 0-1 range using sigmoid
        import math
        normalized_rerank = 1 / (1 + math.exp(-rerank))

        # Normalize original score (assuming 0-10 range from Azure)
        normalized_original = min(1.0, original / 10.0)

        # Weighted combination
        return (
            original_weight * normalized_original +
            (1 - original_weight) * normalized_rerank
        )

    def _passthrough_rerank(
        self,
        results: list[SearchResult],
        top_k: int,
    ) -> list[RerankResult]:
        """Return results in original order when reranker unavailable."""
        return [
            RerankResult(
                chunk=r.chunk,
                original_score=r.score,
                rerank_score=r.score,
                combined_score=r.score,
            )
            for r in results[:top_k]
        ]

    async def async_rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 7,
    ) -> list[RerankResult]:
        """
        Async wrapper for reranking.

        Useful for integration with async pipelines.
        """
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.rerank(query, results, top_k)
        )

    def get_model_info(self) -> dict:
        """Return information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "loaded": self.model is not None,
            "batch_size": self.batch_size,
        }


class CohereReranker:
    """
    Alternative reranker using Cohere's rerank API.

    Higher quality but requires API calls and has associated costs.
    Use for production or when local models are insufficient.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Cohere reranker.

        Args:
            api_key: Cohere API key (from environment if not provided)
        """
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy-load Cohere client."""
        if self._client is None:
            try:
                import cohere
                self._client = cohere.Client(self.api_key)
            except Exception as e:
                logger.warning("cohere_init_failed", error=str(e))
        return self._client

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 7,
        model: str = "rerank-english-v3.0",
    ) -> list[RerankResult]:
        """
        Rerank using Cohere API.

        Args:
            query: Search query
            results: Results to rerank
            top_k: Number of results
            model: Cohere model name

        Returns:
            Reranked results
        """
        if self.client is None:
            logger.warning("cohere_unavailable")
            return []

        try:
            documents = [r.chunk.content for r in results]

            response = self.client.rerank(
                query=query,
                documents=documents,
                top_n=top_k,
                model=model,
            )

            reranked = []
            for item in response.results:
                original_result = results[item.index]
                reranked.append(
                    RerankResult(
                        chunk=original_result.chunk,
                        original_score=original_result.score,
                        rerank_score=item.relevance_score,
                        combined_score=item.relevance_score,
                    )
                )

            return reranked

        except Exception as e:
            logger.error("cohere_rerank_failed", error=str(e))
            return []
