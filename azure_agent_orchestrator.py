"""
Azure AI Foundry Multi-Agent Orchestrator with Advanced RAG
Simple orchestrator: Master + 4 sub-agents + RAG with parent-child chunking
"""

import asyncio
import json
import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Optional
import aiohttp
import websockets

@dataclass
class Config:
    # Agent Foundry (South India)
    agent_endpoint: str
    agent_key: str
    project_id: str
    # Model Endpoint (East US)
    model_endpoint: str
    model_key: str
    model_name: str
    # WebSocket
    ws_endpoint: str
    ws_key: str


# ============ ADVANCED RAG SYSTEM ============

@dataclass
class Chunk:
    """A chunk with unique ID, tags, and parent-child relationships."""
    id: str
    content: str
    tags: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class RAGSystem:
    """Advanced RAG with parent-child chunking, tagging, and top-k retrieval."""

    def __init__(self, parent_chunk_size: int = 1000, child_chunk_size: int = 200, top_k: int = 5):
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.top_k = top_k
        self.chunks: dict[str, Chunk] = {}  # id -> Chunk
        self.embeddings_cache: dict[str, list[float]] = {}

    def _generate_id(self, content: str) -> str:
        """Generate unique ID based on content hash + UUID."""
        content_hash = hashlib.md5(content[:100].encode()).hexdigest()[:8]
        return f"{content_hash}-{uuid.uuid4().hex[:8]}"

    def _split_text(self, text: str, chunk_size: int) -> list[str]:
        """Split text into chunks of specified size."""
        words = text.split()
        chunks = []
        current = []
        current_len = 0

        for word in words:
            if current_len + len(word) > chunk_size and current:
                chunks.append(" ".join(current))
                current = [word]
                current_len = len(word)
            else:
                current.append(word)
                current_len += len(word) + 1

        if current:
            chunks.append(" ".join(current))
        return chunks

    def add_document(self, text: str, tags: list[str] = None, metadata: dict = None) -> list[str]:
        """
        Add document with parent-child chunking.
        Returns list of parent chunk IDs.
        """
        tags = tags or []
        metadata = metadata or {}
        parent_ids = []

        # Create parent chunks
        parent_texts = self._split_text(text, self.parent_chunk_size)

        for parent_text in parent_texts:
            parent_id = self._generate_id(parent_text)
            parent_chunk = Chunk(
                id=parent_id,
                content=parent_text,
                tags=tags.copy(),
                metadata={**metadata, "type": "parent"}
            )

            # Create child chunks for this parent
            child_texts = self._split_text(parent_text, self.child_chunk_size)
            for child_text in child_texts:
                child_id = self._generate_id(child_text)
                child_chunk = Chunk(
                    id=child_id,
                    content=child_text,
                    tags=tags.copy(),
                    parent_id=parent_id,
                    metadata={**metadata, "type": "child"}
                )
                self.chunks[child_id] = child_chunk
                parent_chunk.children_ids.append(child_id)

            self.chunks[parent_id] = parent_chunk
            parent_ids.append(parent_id)

        return parent_ids

    def tag_chunk(self, chunk_id: str, tags: list[str]):
        """Add tags to a specific chunk."""
        if chunk_id in self.chunks:
            self.chunks[chunk_id].tags.extend(tags)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Simple cosine similarity."""
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    async def set_embedding(self, chunk_id: str, embedding: list[float]):
        """Set embedding for a chunk (call your embedding API externally)."""
        if chunk_id in self.chunks:
            self.chunks[chunk_id].embedding = embedding

    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int = None,
        filter_tags: list[str] = None,
        return_parent: bool = True
    ) -> list[Chunk]:
        """
        Retrieve top-k relevant chunks.

        Args:
            query_embedding: Query vector
            top_k: Number of results (default: self.top_k)
            filter_tags: Only return chunks with these tags
            return_parent: If child matches, return parent chunk instead
        """
        top_k = top_k or self.top_k

        # Score all chunks
        scored = []
        for chunk in self.chunks.values():
            # Filter by tags
            if filter_tags and not any(t in chunk.tags for t in filter_tags):
                continue

            score = self._cosine_similarity(query_embedding, chunk.embedding)
            scored.append((score, chunk))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Get top-k, optionally returning parents
        results = []
        seen_ids = set()

        for score, chunk in scored[:top_k * 2]:  # Get extra in case of parent dedup
            if len(results) >= top_k:
                break

            # If child and return_parent, get parent
            if return_parent and chunk.parent_id and chunk.parent_id in self.chunks:
                target = self.chunks[chunk.parent_id]
            else:
                target = chunk

            if target.id not in seen_ids:
                seen_ids.add(target.id)
                results.append(target)

        return results

    def get_context(self, chunks: list[Chunk]) -> str:
        """Format chunks as context string for LLM."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            tags_str = f" [tags: {', '.join(chunk.tags)}]" if chunk.tags else ""
            context_parts.append(f"[{i}]{tags_str}\n{chunk.content}")
        return "\n\n---\n\n".join(context_parts)


# ============ AGENT ORCHESTRATOR ============

class AgentOrchestrator:
    def __init__(self, config: Config, master_id: str, rag: RAGSystem = None):
        self.config = config
        self.master_id = master_id
        self.agents: dict[str, str] = {}
        self.rag = rag or RAGSystem()
        self._session = None
        self._ws = None

    async def connect(self):
        self._session = aiohttp.ClientSession()
        return self

    async def close(self):
        if self._ws: await self._ws.close()
        if self._session: await self._session.close()

    def add_agent(self, agent_id: str, role: str):
        """Add sub-agent (max 4)."""
        if len(self.agents) >= 4:
            raise ValueError("Max 4 sub-agents")
        self.agents[agent_id] = role

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding from model endpoint."""
        url = f"{self.config.model_endpoint}/embeddings"
        headers = {"Authorization": f"Bearer {self.config.model_key}", "Content-Type": "application/json"}
        async with self._session.post(url, headers=headers, json={"input": text}) as resp:
            result = await resp.json()
            return result.get("data", [{}])[0].get("embedding", [])

    async def call_agent(self, agent_id: str, task: str, context: str = "") -> str:
        """Call an agent via REST API with optional RAG context."""
        url = f"{self.config.agent_endpoint}/projects/{self.config.project_id}/agents/{agent_id}/runs"
        headers = {"Authorization": f"Bearer {self.config.agent_key}", "Content-Type": "application/json"}

        full_task = f"Context:\n{context}\n\nTask: {task}" if context else task
        payload = {
            "task": full_task,
            "model_endpoint": self.config.model_endpoint,
            "model_deployment": self.config.model_name
        }
        async with self._session.post(url, headers=headers, json=payload) as resp:
            result = await resp.json()
            return result.get("response", str(result))

    async def call_via_ws(self, agent_id: str, task: str, context: str = "") -> str:
        """Call agent via WebSocket."""
        if not self._ws:
            headers = {"Authorization": f"Bearer {self.config.ws_key}"}
            self._ws = await websockets.connect(self.config.ws_endpoint, additional_headers=headers)

        full_task = f"Context:\n{context}\n\nTask: {task}" if context else task
        await self._ws.send(json.dumps({"agent_id": agent_id, "task": full_task}))

        response = ""
        async for msg in self._ws:
            data = json.loads(msg)
            if data.get("type") == "done": break
            response += data.get("content", "")
        return response

    async def execute(
        self,
        task: str,
        use_ws: bool = False,
        use_rag: bool = True,
        rag_top_k: int = 5,
        rag_tags: list[str] = None
    ) -> dict:
        """Execute task with RAG-enhanced context."""
        call = self.call_via_ws if use_ws else self.call_agent
        context = ""

        # RAG retrieval
        if use_rag and self.rag.chunks:
            query_emb = await self.get_embedding(task)
            relevant = self.rag.retrieve(query_emb, top_k=rag_top_k, filter_tags=rag_tags)
            context = self.rag.get_context(relevant)

        # 1. Master plans
        plan = await call(self.master_id, f"Plan for agents {list(self.agents.items())}: {task}", context)

        # 2. Sub-agents execute in parallel
        tasks = [call(aid, f"{task} (role: {role})", context) for aid, role in self.agents.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sub_results = {aid: str(r) for aid, r in zip(self.agents.keys(), results)}

        # 3. Master synthesizes
        synthesis = await call(self.master_id, f"Synthesize for '{task}': {json.dumps(sub_results)}", context)

        return {"task": task, "context_chunks": len(context.split("---")), "sub_results": sub_results, "final": synthesis}


# ============ USAGE EXAMPLE ============
async def main():
    config = Config(
        agent_endpoint="https://your-foundry.southindia.api.azureml.ms",
        agent_key="YOUR_AGENT_KEY",
        project_id="YOUR_PROJECT_ID",
        model_endpoint="https://your-model.eastus.api.azureml.ms",
        model_key="YOUR_MODEL_KEY",
        model_name="gpt-4o",
        ws_endpoint="wss://your-ws.eastus.api.azureml.ms/ws",
        ws_key="YOUR_WS_KEY"
    )

    # Initialize RAG with custom settings
    rag = RAGSystem(
        parent_chunk_size=1000,  # Parent chunks ~1000 chars
        child_chunk_size=200,    # Child chunks ~200 chars
        top_k=5                  # Default top-k retrieval
    )

    # Add documents with tags
    doc1 = "Your large document text here about market analysis..."
    parent_ids = rag.add_document(
        doc1,
        tags=["market", "analysis", "2024"],
        metadata={"source": "report.pdf", "date": "2024-01"}
    )
    print(f"Added document with {len(parent_ids)} parent chunks")

    # Tag specific chunks
    for pid in parent_ids:
        rag.tag_chunk(pid, ["priority"])

    # Initialize orchestrator with RAG
    orch = AgentOrchestrator(config, master_id="asst_master_001", rag=rag)
    await orch.connect()

    # Set embeddings (normally you'd batch this)
    for chunk_id in rag.chunks:
        emb = await orch.get_embedding(rag.chunks[chunk_id].content)
        await rag.set_embedding(chunk_id, emb)

    # Register agents
    orch.add_agent("asst_researcher_001", "researcher")
    orch.add_agent("asst_analyst_001", "analyst")
    orch.add_agent("asst_writer_001", "writer")
    orch.add_agent("asst_reviewer_001", "reviewer")

    # Execute with RAG
    result = await orch.execute(
        task="Analyze market trends",
        use_rag=True,
        rag_top_k=5,
        rag_tags=["market"]  # Filter by tags
    )
    print(json.dumps(result, indent=2))

    await orch.close()

if __name__ == "__main__":
    asyncio.run(main())
