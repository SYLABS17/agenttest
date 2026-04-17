"""Azure AI Foundry client for RAG-based LMS."""

from typing import Optional
from dataclasses import dataclass

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AzureAISearchTool,
    ConnectionType,
)


@dataclass
class QueryResult:
    """Result from a RAG query."""
    answer: str
    sources: list[dict]
    confidence: float


class AzureAIFoundryClient:
    """Client for Azure AI Foundry RAG operations."""

    def __init__(
        self,
        project_connection_string: str,
        search_index: str = "lms-index",
        chat_model: str = "gpt-4o",
    ):
        self.credential = DefaultAzureCredential()
        self.project = AIProjectClient.from_connection_string(
            conn_str=project_connection_string,
            credential=self.credential,
        )
        self.search_index = search_index
        self.chat_model = chat_model
        self._agent = None

    async def initialize(self):
        """Initialize the AI agent with search tool."""
        search_connection = self.project.connections.get_default(
            connection_type=ConnectionType.AZURE_AI_SEARCH
        )

        search_tool = AzureAISearchTool(
            index_connection_id=search_connection.id,
            index_name=self.search_index,
        )

        self._agent = self.project.agents.create_agent(
            model=self.chat_model,
            name="lms-assistant",
            instructions="""You are a helpful learning management assistant.
Answer questions based on the educational content provided.
Always cite your sources and be accurate.""",
            tools=[search_tool],
        )

    async def query(
        self,
        question: str,
        language: str = "en",
        context: Optional[dict] = None,
    ) -> QueryResult:
        """Query the LMS using RAG."""
        if not self._agent:
            await self.initialize()

        thread = self.project.agents.create_thread()

        message = self.project.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=question,
        )

        run = self.project.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=self._agent.id,
        )

        messages = self.project.agents.list_messages(thread_id=thread.id)
        assistant_message = next(
            (m for m in messages if m.role == "assistant"),
            None
        )

        if not assistant_message:
            return QueryResult(
                answer="Unable to process your question.",
                sources=[],
                confidence=0.0,
            )

        answer_text = assistant_message.content[0].text.value
        citations = getattr(assistant_message.content[0].text, "annotations", [])

        sources = []
        for citation in citations:
            if hasattr(citation, "file_citation"):
                sources.append({
                    "title": citation.file_citation.file_id,
                    "quote": citation.text,
                })

        return QueryResult(
            answer=answer_text,
            sources=sources,
            confidence=0.9 if sources else 0.7,
        )

    async def close(self):
        """Cleanup resources."""
        if self._agent:
            self.project.agents.delete_agent(self._agent.id)
