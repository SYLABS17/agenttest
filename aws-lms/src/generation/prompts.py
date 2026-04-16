"""Prompt templates for grounded response generation."""


class PromptTemplates:
    """
    Prompt templates for educational response generation.

    All prompts enforce strict grounding in retrieved content
    to minimize hallucination risk.
    """

    SYSTEM_PROMPT = """You are an educational assistant for students, helping with
curriculum-aligned learning across all subjects and grade levels.

CRITICAL RULES:
1. ONLY use information from the provided context chunks
2. CITE sources using [Source: X] format for every claim
3. If the context doesn't contain the answer, say "I don't have enough information to answer this question based on the available curriculum materials."
4. Use curriculum-aligned terminology appropriate for the student's grade level
5. Respond in the student's language (specified below)
6. Never make up facts or provide information not in the context

You are serving students. Accuracy is paramount."""

    GENERATION_PROMPT = """Answer the following question based ONLY on the provided context.

## CONTEXT CHUNKS
{context_chunks}

## STUDENT INFORMATION
- Language: {target_language}
- Grade Level: {grade_level}
- Subject: {subject}

## ORIGINAL QUESTION ({source_language}):
{original_query}

## TRANSLATED QUESTION (English):
{translated_query}

## INSTRUCTIONS
1. Ground your answer strictly in the provided chunks
2. Cite which chunk(s) support each claim using [Source: X]
3. Respond in {target_language} (the student's language)
4. Use age-appropriate explanations for {grade_level}
5. If context is insufficient, clearly state that

Provide a comprehensive, grounded answer:"""

    CONTEXT_CHUNK_TEMPLATE = """[Source {index}]
Content: {content}
From: {source_type} - {board} {subject} {grade_level}
{additional_info}
---"""

    VIDEO_REFERENCE_TEMPLATE = """
Additionally, you can watch this video segment for visual explanation:
- Video: {title} by {instructor}
- Segment: {start_timestamp} - {end_timestamp}
- Topic: {excerpt}
"""

    FOLLOW_UP_PROMPT = """Based on the previous answer and context, address this follow-up question:

## PREVIOUS CONTEXT
{previous_context}

## PREVIOUS ANSWER
{previous_answer}

## FOLLOW-UP QUESTION ({source_language}):
{follow_up_query}

Continue providing grounded, cited responses:"""

    NO_CONTEXT_RESPONSE = """I apologize, but I don't have enough information in the
available curriculum materials to accurately answer your question about "{topic}".

This could be because:
1. The topic is not covered in the indexed curriculum for your grade level
2. The question requires information beyond the current course materials
3. The topic may be covered in a different subject area

Would you like me to help with a related topic, or could you rephrase your question?"""

    @classmethod
    def format_context_chunks(
        cls,
        chunks: list,
        include_video: bool = True,
    ) -> str:
        """
        Format context chunks for the prompt.

        Args:
            chunks: List of ChunkWithContext objects
            include_video: Whether to include video references

        Returns:
            Formatted context string
        """
        formatted = []

        for i, chunk in enumerate(chunks, 1):
            # Get the context text (parent if available, else matched)
            content = chunk.context_text if hasattr(chunk, 'context_text') else chunk.matched_chunk.content
            metadata = chunk.matched_chunk.metadata

            additional_info = ""
            if metadata.chapter:
                additional_info += f"Chapter: {metadata.chapter}\n"
            if metadata.page_number:
                additional_info += f"Page: {metadata.page_number}\n"
            if metadata.video_id and include_video:
                additional_info += f"Video: {metadata.start_timestamp} - {metadata.end_timestamp}\n"

            formatted.append(
                cls.CONTEXT_CHUNK_TEMPLATE.format(
                    index=i,
                    content=content,
                    source_type=metadata.source_type,
                    board=metadata.board,
                    subject=metadata.subject,
                    grade_level=metadata.grade_level,
                    additional_info=additional_info.strip(),
                )
            )

        return "\n".join(formatted)

    @classmethod
    def format_video_references(cls, video_segments: list) -> str:
        """
        Format video segment references.

        Args:
            video_segments: List of VideoSegment objects

        Returns:
            Formatted video references
        """
        if not video_segments:
            return ""

        refs = []
        for segment in video_segments:
            refs.append(
                cls.VIDEO_REFERENCE_TEMPLATE.format(
                    title=segment.title,
                    instructor=segment.instructor,
                    start_timestamp=segment.start_timestamp,
                    end_timestamp=segment.end_timestamp,
                    excerpt=segment.transcript_excerpt[:100] + "...",
                )
            )

        return "\n".join(refs)

    @classmethod
    def build_generation_prompt(
        cls,
        context_chunks: list,
        original_query: str,
        translated_query: str,
        source_language: str,
        target_language: str,
        grade_level: str = "unknown",
        subject: str = "unknown",
        video_segments: list = None,
    ) -> str:
        """
        Build complete generation prompt.

        Args:
            context_chunks: Retrieved and reranked chunks
            original_query: Query in source language
            translated_query: Query translated to English
            source_language: Source language code
            target_language: Language for response
            grade_level: Student's grade level
            subject: Subject area
            video_segments: Optional video segments

        Returns:
            Complete formatted prompt
        """
        context_str = cls.format_context_chunks(context_chunks)

        if video_segments:
            context_str += "\n\n## VIDEO RESOURCES\n"
            context_str += cls.format_video_references(video_segments)

        return cls.GENERATION_PROMPT.format(
            context_chunks=context_str,
            original_query=original_query,
            translated_query=translated_query,
            source_language=source_language,
            target_language=target_language,
            grade_level=grade_level,
            subject=subject,
        )
