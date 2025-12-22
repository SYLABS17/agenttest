"""
Azure AI Search Semantic Pipeline with Foundry IQ Integration
==============================================================
Ingest semantic models as separate indexes and connect to Foundry IQ agents.

Usage:
    pipeline = SemanticSearchPipeline(config)
    await pipeline.create_index("products", schema)
    await pipeline.ingest_documents("products", docs)

    agent = FoundryIQAgent(config, pipeline)
    response = await agent.query("Find similar products")
"""

import asyncio
import json
import aiohttp
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchConfig:
    """Azure AI Search configuration."""
    endpoint: str           # https://<name>.search.windows.net
    api_key: str
    api_version: str = "2024-07-01"


@dataclass
class FoundryConfig:
    """Azure AI Foundry IQ configuration."""
    endpoint: str           # Foundry endpoint
    api_key: str
    project_id: str
    model_deployment: str = "gpt-4o"


@dataclass
class PipelineConfig:
    """Combined pipeline configuration."""
    search: SearchConfig
    foundry: FoundryConfig
    indexes: list = field(default_factory=list)  # List of semantic model index names


# =============================================================================
# SEMANTIC MODEL INDEX SCHEMAS
# =============================================================================

SEMANTIC_SCHEMAS = {
    "default": {
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
            {"name": "content", "type": "Edm.String", "searchable": True},
            {"name": "title", "type": "Edm.String", "searchable": True, "filterable": True},
            {"name": "embedding", "type": "Collection(Edm.Single)", "searchable": True,
             "dimensions": 1536, "vectorSearchProfile": "semantic-profile"},
            {"name": "metadata", "type": "Edm.String", "filterable": True},
            {"name": "category", "type": "Edm.String", "filterable": True, "facetable": True}
        ],
        "vectorSearch": {
            "profiles": [{"name": "semantic-profile", "algorithm": "semantic-hnsw"}],
            "algorithms": [{"name": "semantic-hnsw", "kind": "hnsw",
                          "parameters": {"m": 4, "efConstruction": 400, "efSearch": 500}}]
        },
        "semantic": {
            "configurations": [{
                "name": "semantic-config",
                "prioritizedFields": {
                    "contentFields": [{"fieldName": "content"}],
                    "titleField": {"fieldName": "title"}
                }
            }]
        }
    }
}


# =============================================================================
# SEMANTIC SEARCH PIPELINE
# =============================================================================

class SemanticSearchPipeline:
    """Pipeline for ingesting semantic models into Azure AI Search indexes."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self.indexes: dict = {}  # Track created indexes

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "api-key": self.config.search.api_key
        }

    def _url(self, path: str) -> str:
        return f"{self.config.search.endpoint}/{path}?api-version={self.config.search.api_version}"

    async def create_index(self, name: str, schema: dict = None) -> dict:
        """
        Create a semantic search index for a model.

        Args:
            name: Index name (e.g., "products", "documents", "knowledge")
            schema: Custom schema or use default semantic schema
        """
        schema = schema or SEMANTIC_SCHEMAS["default"]
        payload = {"name": name, **schema}

        async with self._session.put(
            self._url(f"indexes/{name}"),
            headers=self._headers(),
            json=payload
        ) as resp:
            result = await resp.json()
            if resp.status in (200, 201):
                self.indexes[name] = {"status": "active", "schema": schema}
            return {"status": resp.status, "result": result}

    async def delete_index(self, name: str) -> dict:
        """Delete an index."""
        async with self._session.delete(
            self._url(f"indexes/{name}"),
            headers=self._headers()
        ) as resp:
            if resp.status == 204:
                self.indexes.pop(name, None)
            return {"status": resp.status}

    async def ingest_documents(self, index_name: str, documents: list) -> dict:
        """
        Ingest documents into a semantic index.

        Args:
            index_name: Target index
            documents: List of documents with id, content, title, embedding, metadata
        """
        payload = {"value": [{"@search.action": "upload", **doc} for doc in documents]}

        async with self._session.post(
            self._url(f"indexes/{index_name}/docs/index"),
            headers=self._headers(),
            json=payload
        ) as resp:
            return {"status": resp.status, "result": await resp.json()}

    async def semantic_search(
        self,
        index_name: str,
        query: str,
        vector: list = None,
        top: int = 5,
        filters: str = None
    ) -> dict:
        """
        Perform semantic/hybrid search on an index.

        Args:
            index_name: Index to search
            query: Text query for semantic search
            vector: Optional embedding vector for hybrid search
            top: Number of results
            filters: OData filter expression
        """
        payload = {
            "search": query,
            "queryType": "semantic",
            "semanticConfiguration": "semantic-config",
            "top": top,
            "select": "id,title,content,category,metadata"
        }

        if vector:
            payload["vectorQueries"] = [{
                "kind": "vector",
                "vector": vector,
                "fields": "embedding",
                "k": top
            }]

        if filters:
            payload["filter"] = filters

        async with self._session.post(
            self._url(f"indexes/{index_name}/docs/search"),
            headers=self._headers(),
            json=payload
        ) as resp:
            return await resp.json()

    async def search_all_indexes(self, query: str, vector: list = None, top: int = 3) -> dict:
        """Search across all registered semantic indexes."""
        results = {}
        tasks = [
            self.semantic_search(idx, query, vector, top)
            for idx in self.indexes.keys()
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, resp in zip(self.indexes.keys(), responses):
            if isinstance(resp, Exception):
                results[idx] = {"error": str(resp)}
            else:
                results[idx] = resp.get("value", [])

        return results


# =============================================================================
# FOUNDRY IQ AGENT WITH SEARCH
# =============================================================================

class FoundryIQAgent:
    """
    Foundry IQ agent integrated with semantic search pipeline.
    No data agents needed - direct index access.
    """

    def __init__(self, config: PipelineConfig, pipeline: SemanticSearchPipeline):
        self.config = config
        self.pipeline = pipeline
        self._session: Optional[aiohttp.ClientSession] = None
        self.agent_id: Optional[str] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.foundry.api_key}"
        }

    def _url(self, path: str) -> str:
        return f"{self.config.foundry.endpoint}/projects/{self.config.foundry.project_id}/{path}"

    async def create_agent(self, name: str, instructions: str = None) -> str:
        """
        Create Foundry IQ agent with semantic search tool.
        """
        index_list = ", ".join(self.pipeline.indexes.keys()) or "none configured"

        default_instructions = f"""You are an AI assistant with access to semantic search across these indexes: {index_list}.

When users ask questions:
1. Determine which index(es) are relevant
2. Search for related information
3. Synthesize results into a helpful response

Available indexes and their purposes will be provided in context."""

        payload = {
            "name": name,
            "model": self.config.foundry.model_deployment,
            "instructions": instructions or default_instructions,
            "tools": [{
                "type": "function",
                "function": {
                    "name": "semantic_search",
                    "description": "Search semantic indexes for relevant information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "string", "description": "Index name to search"},
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["index", "query"]
                    }
                }
            }]
        }

        async with self._session.post(
            self._url("agents"),
            headers=self._headers(),
            json=payload
        ) as resp:
            result = await resp.json()
            self.agent_id = result.get("id")
            return self.agent_id

    async def query(self, user_query: str, search_all: bool = True) -> dict:
        """
        Query the agent with automatic semantic search.

        Args:
            user_query: User's question
            search_all: Search all indexes for context
        """
        # Step 1: Get search context from indexes
        context = {}
        if search_all and self.pipeline.indexes:
            context = await self.pipeline.search_all_indexes(user_query, top=3)

        # Step 2: Build prompt with search context
        context_text = ""
        for idx, results in context.items():
            if results and not isinstance(results, dict):
                context_text += f"\n### Results from '{idx}' index:\n"
                for r in results[:3]:
                    context_text += f"- {r.get('title', 'Untitled')}: {r.get('content', '')[:200]}...\n"

        # Step 3: Call Foundry IQ agent
        payload = {
            "messages": [
                {"role": "system", "content": f"Search context:{context_text}" if context_text else "No search context available."},
                {"role": "user", "content": user_query}
            ],
            "model": self.config.foundry.model_deployment
        }

        async with self._session.post(
            self._url("chat/completions"),
            headers=self._headers(),
            json=payload
        ) as resp:
            result = await resp.json()
            return {
                "query": user_query,
                "search_context": context,
                "response": result.get("choices", [{}])[0].get("message", {}).get("content", "")
            }


# =============================================================================
# MASTER AGENT ORCHESTRATOR (No Data Agents)
# =============================================================================

class MasterAgent:
    """
    Master agent that orchestrates semantic search without data agents.
    Directly manages indexes and queries.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.pipeline: Optional[SemanticSearchPipeline] = None
        self.foundry_agent: Optional[FoundryIQAgent] = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize pipeline and agent."""
        self._session = aiohttp.ClientSession()
        self.pipeline = SemanticSearchPipeline(self.config)
        self.pipeline._session = self._session
        self.foundry_agent = FoundryIQAgent(self.config, self.pipeline)
        self.foundry_agent._session = self._session
        return self

    async def close(self):
        if self._session:
            await self._session.close()

    async def setup_semantic_indexes(self, index_configs: list) -> dict:
        """
        Set up multiple semantic model indexes.

        Args:
            index_configs: List of {"name": "...", "schema": {...}} dicts
        """
        results = {}
        for cfg in index_configs:
            name = cfg.get("name")
            schema = cfg.get("schema", SEMANTIC_SCHEMAS["default"])
            result = await self.pipeline.create_index(name, schema)
            results[name] = result
        return results

    async def ingest_semantic_model(self, index_name: str, model_data: list) -> dict:
        """Ingest semantic model data into an index."""
        return await self.pipeline.ingest_documents(index_name, model_data)

    async def execute(self, query: str) -> dict:
        """
        Execute query through master agent.

        1. Searches all semantic indexes
        2. Uses Foundry IQ to generate response
        3. Returns combined result
        """
        return await self.foundry_agent.query(query, search_all=True)


# =============================================================================
# SIMPLE FACTORY FUNCTIONS
# =============================================================================

def create_config(
    search_endpoint: str,
    search_key: str,
    foundry_endpoint: str,
    foundry_key: str,
    project_id: str,
    model: str = "gpt-4o"
) -> PipelineConfig:
    """Create pipeline config from parameters."""
    return PipelineConfig(
        search=SearchConfig(endpoint=search_endpoint, api_key=search_key),
        foundry=FoundryConfig(
            endpoint=foundry_endpoint,
            api_key=foundry_key,
            project_id=project_id,
            model_deployment=model
        )
    )


def create_config_from_env() -> PipelineConfig:
    """Create config from environment variables."""
    import os
    return create_config(
        search_endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        search_key=os.environ["AZURE_SEARCH_KEY"],
        foundry_endpoint=os.environ["AZURE_FOUNDRY_ENDPOINT"],
        foundry_key=os.environ["AZURE_FOUNDRY_KEY"],
        project_id=os.environ["AZURE_PROJECT_ID"],
        model=os.environ.get("AZURE_MODEL", "gpt-4o")
    )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def main():
    """Example: Set up semantic indexes and query via master agent."""

    config = create_config(
        search_endpoint="https://your-search.search.windows.net",
        search_key="your-search-key",
        foundry_endpoint="https://your-foundry.api.azureml.ms",
        foundry_key="your-foundry-key",
        project_id="your-project-id"
    )

    # Initialize master agent
    agent = MasterAgent(config)
    await agent.initialize()

    try:
        # Create semantic indexes for different models
        await agent.setup_semantic_indexes([
            {"name": "products"},      # Product semantic model
            {"name": "documents"},     # Document semantic model
            {"name": "knowledge"}      # Knowledge base model
        ])

        # Ingest sample data into product index
        await agent.ingest_semantic_model("products", [
            {
                "id": "prod-1",
                "title": "AI-Powered Analytics Suite",
                "content": "Enterprise analytics platform with ML capabilities",
                "category": "software",
                "embedding": [0.1] * 1536,  # Your actual embedding
                "metadata": json.dumps({"price": 999, "tier": "enterprise"})
            }
        ])

        # Query across all indexes
        result = await agent.execute("What AI analytics solutions do we have?")
        print(json.dumps(result, indent=2))

    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
