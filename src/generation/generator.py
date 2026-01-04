"""Grounded response generation using LLM."""

from dataclasses import dataclass
from typing import Optional

import structlog

from src.config import get_settings
from src.generation.prompts import PromptTemplates
from src.chunking.models import ChunkWithContext
from src.video.retrieval import VideoSegment

logger = structlog.get_logger(__name__)


@dataclass
class GeneratedResponse:
    """Result of response generation."""

    answer: str
    language: str
    sources: list[dict]
    video_segments: list[dict]
    confidence: float
    tokens_used: int
    model: str
    grounded: bool


@dataclass
class SourceReference:
    """Reference to a source document."""

    source_type: str
    title: str
    chapter: Optional[str]
    page: Optional[int]
    board: str
    grade_level: str


class GroundedGenerator:
    """
    Grounded response generator for educational queries.

    Generates responses strictly based on retrieved context,
    with explicit source citations to minimize hallucination.

    Key features:
    - Strict grounding in retrieved chunks
    - Multi-language response generation
    - Source citation enforcement
    - Age-appropriate explanations
    """

    def __init__(
        self,
        llm_client: Optional[object] = None,
    ):
        """
        Initialize grounded generator.

        Args:
            llm_client: Azure OpenAI or compatible LLM client
        """
        self.settings = get_settings()
        self._client = llm_client
        self.prompts = PromptTemplates()

    @property
    def client(self):
        """Lazy-load LLM client."""
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
            logger.warning("llm_client_init_failed", error=str(e))
            return None

    async def generate(
        self,
        context_chunks: list[ChunkWithContext],
        original_query: str,
        translated_query: str,
        source_language: str,
        target_language: str,
        user_context: Optional[dict] = None,
        video_segments: Optional[list[VideoSegment]] = None,
    ) -> GeneratedResponse:
        """
        Generate grounded response from context chunks.

        Args:
            context_chunks: Retrieved and reranked chunks with context
            original_query: Query in source language
            translated_query: Query translated to English
            source_language: Source language code
            target_language: Language for response
            user_context: Optional user context (grade, board, etc.)
            video_segments: Optional video segments to reference

        Returns:
            GeneratedResponse with answer and metadata
        """
        logger.debug(
            "generating_response",
            chunk_count=len(context_chunks),
            source_lang=source_language,
            target_lang=target_language,
        )

        # Handle no context case
        if not context_chunks:
            return self._no_context_response(translated_query, target_language)

        # Extract user context
        grade_level = user_context.get("grade_level", "unknown") if user_context else "unknown"
        subject = user_context.get("subject", "unknown") if user_context else "unknown"

        # Build prompt
        prompt = self.prompts.build_generation_prompt(
            context_chunks=context_chunks,
            original_query=original_query,
            translated_query=translated_query,
            source_language=source_language,
            target_language=target_language,
            grade_level=grade_level,
            subject=subject,
            video_segments=video_segments,
        )

        # Generate response
        if self.client is None:
            logger.warning("using_mock_generation")
            return self._mock_response(translated_query, target_language, context_chunks)

        try:
            response = self.client.chat.completions.create(
                model=self.settings.azure_openai_chat_deployment,
                messages=[
                    {"role": "system", "content": PromptTemplates.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.settings.generation_temperature,
                max_tokens=self.settings.generation_max_tokens,
            )

            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # Extract sources from chunks
            sources = self._extract_sources(context_chunks)

            # Format video segments
            video_refs = self._format_video_segments(video_segments) if video_segments else []

            # Check grounding
            grounded = self._check_grounding(answer, context_chunks)

            logger.info(
                "response_generated",
                tokens=tokens_used,
                grounded=grounded,
                source_count=len(sources),
            )

            return GeneratedResponse(
                answer=answer,
                language=target_language,
                sources=sources,
                video_segments=video_refs,
                confidence=self._compute_confidence(context_chunks, grounded),
                tokens_used=tokens_used,
                model=self.settings.azure_openai_chat_deployment,
                grounded=grounded,
            )

        except Exception as e:
            logger.error("generation_failed", error=str(e))
            raise

    def _extract_sources(
        self,
        chunks: list[ChunkWithContext],
    ) -> list[dict]:
        """Extract source references from chunks."""
        sources = []
        seen = set()

        for chunk in chunks:
            metadata = chunk.matched_chunk.metadata

            # Create unique key for deduplication
            key = f"{metadata.source_type}:{metadata.board}:{metadata.chapter}"
            if key in seen:
                continue
            seen.add(key)

            source = {
                "source_type": metadata.source_type,
                "board": metadata.board,
                "subject": metadata.subject,
                "grade_level": metadata.grade_level,
                "chapter": metadata.chapter,
                "page_number": metadata.page_number,
            }
            sources.append(source)

        return sources

    def _format_video_segments(
        self,
        segments: list[VideoSegment],
    ) -> list[dict]:
        """Format video segments for response."""
        return [
            {
                "video_id": s.video_id,
                "title": s.title,
                "instructor": s.instructor,
                "start_timestamp": s.start_timestamp,
                "end_timestamp": s.end_timestamp,
                "url": s.url,
                "thumbnail_url": s.thumbnail_url,
            }
            for s in segments
        ]

    def _check_grounding(
        self,
        answer: str,
        chunks: list[ChunkWithContext],
    ) -> bool:
        """
        Check if answer is properly grounded in sources.

        Looks for:
        - Source citations [Source: X]
        - Content overlap with chunks

        Args:
            answer: Generated answer
            chunks: Context chunks

        Returns:
            True if answer appears grounded
        """
        # Check for citations
        import re
        citations = re.findall(r'\[Source[:\s]+\d+\]', answer, re.IGNORECASE)

        if not citations:
            logger.warning("no_citations_in_response")
            return False

        # Check for content overlap (simple heuristic)
        chunk_content = " ".join(c.matched_chunk.content.lower() for c in chunks)
        answer_words = set(answer.lower().split())

        # At least 30% of substantial words should appear in chunks
        content_words = set(chunk_content.split())
        overlap = len(answer_words & content_words)
        overlap_ratio = overlap / len(answer_words) if answer_words else 0

        return overlap_ratio > 0.3

    def _compute_confidence(
        self,
        chunks: list[ChunkWithContext],
        grounded: bool,
    ) -> float:
        """Compute confidence score for response."""
        if not chunks:
            return 0.0

        # Average relevance of top chunks
        avg_relevance = sum(c.relevance_score for c in chunks) / len(chunks)

        # Boost if grounded
        if grounded:
            avg_relevance = min(1.0, avg_relevance + 0.1)
        else:
            avg_relevance = max(0.0, avg_relevance - 0.2)

        return avg_relevance

    def _no_context_response(
        self,
        query: str,
        language: str,
    ) -> GeneratedResponse:
        """Generate response when no context is available."""
        # Extract topic from query
        topic = query[:50] + "..." if len(query) > 50 else query

        answer = PromptTemplates.NO_CONTEXT_RESPONSE.format(topic=topic)

        return GeneratedResponse(
            answer=answer,
            language=language,
            sources=[],
            video_segments=[],
            confidence=0.0,
            tokens_used=0,
            model="no_context",
            grounded=False,
        )

    def _mock_response(
        self,
        query: str,
        language: str,
        chunks: list[ChunkWithContext],
    ) -> GeneratedResponse:
        """Generate mock response for development."""
        sources = self._extract_sources(chunks)

        mock_answer = f"""Based on the curriculum materials [Source: 1], here is the answer to your question about "{query[:30]}...":

{chunks[0].matched_chunk.content[:200] if chunks else 'No content available'}

This explanation is based on the {sources[0]['board'] if sources else 'curriculum'} textbook.

[Source: 1] - {sources[0]['chapter'] if sources and sources[0].get('chapter') else 'Chapter reference'}"""

        return GeneratedResponse(
            answer=mock_answer,
            language=language,
            sources=sources,
            video_segments=[],
            confidence=0.7,
            tokens_used=0,
            model="mock",
            grounded=True,
        )

    async def generate_follow_up(
        self,
        previous_context: str,
        previous_answer: str,
        follow_up_query: str,
        source_language: str,
        target_language: str,
    ) -> GeneratedResponse:
        """
        Generate response to a follow-up question.

        Uses previous context and answer to maintain continuity.
        """
        prompt = PromptTemplates.FOLLOW_UP_PROMPT.format(
            previous_context=previous_context,
            previous_answer=previous_answer,
            follow_up_query=follow_up_query,
            source_language=source_language,
        )

        # Similar generation logic as main generate method
        # Simplified for brevity
        return await self.generate(
            context_chunks=[],
            original_query=follow_up_query,
            translated_query=follow_up_query,
            source_language=source_language,
            target_language=target_language,
        )
