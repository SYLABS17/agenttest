"""
Azure AI Foundry Multi-Agent Orchestrator
==========================================
A simple, production-ready orchestrator for connecting multiple agents
with cross-region model endpoint support.

Usage:
    orchestrator = AgentOrchestrator(config)
    orchestrator.register_agent("agent_id", role="specialist")
    response = await orchestrator.execute("Your task here")
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import aiohttp
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentOrchestrator")


class AgentRole(Enum):
    """Defines the role of each agent in the orchestration."""
    MASTER = "master"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    agent_id: str
    role: AgentRole
    description: str = ""
    enabled: bool = True


@dataclass
class FoundryConfig:
    """Azure AI Foundry configuration with cross-region support."""
    # Agent Foundry Resource (South India)
    agent_endpoint: str
    agent_api_key: str
    agent_project_id: str

    # Model Endpoint (East US) - separate resource
    model_endpoint: str
    model_api_key: str
    model_deployment_name: str

    # WebSocket configuration
    websocket_endpoint: str
    websocket_api_key: str

    # Optional settings
    api_version: str = "2024-12-01-preview"
    timeout_seconds: int = 120
    max_retries: int = 3


@dataclass
class OrchestratorConfig:
    """Main orchestrator configuration."""
    foundry: FoundryConfig
    master_agent_id: str
    sub_agent_ids: list = field(default_factory=list)


class AgentOrchestrator:
    """
    Multi-agent orchestrator for Azure AI Foundry.

    Connects a master agent with up to 4 sub-agents,
    supporting cross-region model endpoints via WebSocket.
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.agents: dict[str, AgentConfig] = {}
        self.master_agent: Optional[AgentConfig] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws_connection = None

    async def __aenter__(self):
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _init_session(self):
        """Initialize HTTP session with proper headers."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.foundry.timeout_seconds)
            )

    async def close(self):
        """Clean up resources."""
        if self._ws_connection:
            await self._ws_connection.close()
        if self._session:
            await self._session.close()
            self._session = None

    def register_agent(
        self,
        agent_id: str,
        role: AgentRole,
        description: str = "",
        is_master: bool = False
    ) -> None:
        """
        Register an agent with the orchestrator.

        Args:
            agent_id: The Azure AI Foundry agent ID
            role: The role this agent plays
            description: Human-readable description
            is_master: Whether this is the master coordinating agent
        """
        agent = AgentConfig(
            agent_id=agent_id,
            role=role,
            description=description
        )

        if is_master:
            self.master_agent = agent
            logger.info(f"Registered master agent: {agent_id}")
        else:
            if len(self.agents) >= 4:
                raise ValueError("Maximum 4 sub-agents allowed")
            self.agents[agent_id] = agent
            logger.info(f"Registered sub-agent: {agent_id} with role {role.value}")

    def _get_agent_headers(self) -> dict:
        """Get headers for Agent Foundry API calls."""
        return {
            "Authorization": f"Bearer {self.config.foundry.agent_api_key}",
            "Content-Type": "application/json",
            "api-version": self.config.foundry.api_version
        }

    def _get_model_headers(self) -> dict:
        """Get headers for Model endpoint API calls."""
        return {
            "Authorization": f"Bearer {self.config.foundry.model_api_key}",
            "Content-Type": "application/json",
            "api-version": self.config.foundry.api_version
        }

    async def _connect_websocket(self) -> None:
        """Establish WebSocket connection to the model endpoint."""
        ws_url = self.config.foundry.websocket_endpoint
        headers = {"Authorization": f"Bearer {self.config.foundry.websocket_api_key}"}

        try:
            self._ws_connection = await websockets.connect(
                ws_url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )
            logger.info("WebSocket connection established")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def _send_ws_message(self, message: dict) -> dict:
        """Send message via WebSocket and await response."""
        if not self._ws_connection:
            await self._connect_websocket()

        await self._ws_connection.send(json.dumps(message))
        response = await self._ws_connection.recv()
        return json.loads(response)

    async def _call_agent(self, agent_id: str, task: str, context: dict = None) -> dict:
        """
        Call a specific agent with a task.

        Uses the Agent Foundry endpoint (South India) for agent management
        and routes inference through the Model endpoint (East US).
        """
        await self._init_session()

        # Create thread for agent conversation
        thread_url = (
            f"{self.config.foundry.agent_endpoint}"
            f"/projects/{self.config.foundry.agent_project_id}"
            f"/agents/{agent_id}/threads"
        )

        try:
            # Create a new thread
            async with self._session.post(
                thread_url,
                headers=self._get_agent_headers(),
                json={}
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Failed to create thread: {error_text}")
                thread_data = await resp.json()
                thread_id = thread_data.get("id")

            # Add message to thread
            message_url = f"{thread_url}/{thread_id}/messages"
            message_payload = {
                "role": "user",
                "content": task
            }
            if context:
                message_payload["metadata"] = context

            async with self._session.post(
                message_url,
                headers=self._get_agent_headers(),
                json=message_payload
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Failed to add message: {error_text}")

            # Run the agent with model from East US endpoint
            run_url = f"{thread_url}/{thread_id}/runs"
            run_payload = {
                "assistant_id": agent_id,
                "model_endpoint": self.config.foundry.model_endpoint,
                "model_deployment": self.config.foundry.model_deployment_name
            }

            async with self._session.post(
                run_url,
                headers=self._get_agent_headers(),
                json=run_payload
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Failed to run agent: {error_text}")
                run_data = await resp.json()
                run_id = run_data.get("id")

            # Poll for completion
            result = await self._wait_for_run(thread_url, thread_id, run_id)
            return result

        except Exception as e:
            logger.error(f"Agent call failed for {agent_id}: {e}")
            raise

    async def _wait_for_run(
        self,
        thread_url: str,
        thread_id: str,
        run_id: str,
        poll_interval: float = 1.0
    ) -> dict:
        """Poll until agent run completes."""
        status_url = f"{thread_url}/{thread_id}/runs/{run_id}"
        max_polls = self.config.foundry.timeout_seconds

        for _ in range(max_polls):
            async with self._session.get(
                status_url,
                headers=self._get_agent_headers()
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get run status")
                run_data = await resp.json()
                status = run_data.get("status")

                if status == "completed":
                    # Fetch messages
                    messages_url = f"{thread_url}/{thread_id}/messages"
                    async with self._session.get(
                        messages_url,
                        headers=self._get_agent_headers()
                    ) as msg_resp:
                        return await msg_resp.json()

                elif status in ("failed", "cancelled", "expired"):
                    raise Exception(f"Run ended with status: {status}")

            await asyncio.sleep(poll_interval)

        raise TimeoutError("Agent run timed out")

    async def _stream_via_websocket(self, task: str, agent_id: str):
        """Stream responses via WebSocket for real-time output."""
        message = {
            "type": "agent_request",
            "agent_id": agent_id,
            "task": task,
            "model_endpoint": self.config.foundry.model_endpoint,
            "model_deployment": self.config.foundry.model_deployment_name
        }

        if not self._ws_connection:
            await self._connect_websocket()

        await self._ws_connection.send(json.dumps(message))

        # Stream response chunks
        full_response = []
        async for message in self._ws_connection:
            data = json.loads(message)
            if data.get("type") == "content":
                full_response.append(data.get("content", ""))
                yield data.get("content", "")
            elif data.get("type") == "done":
                break
            elif data.get("type") == "error":
                raise Exception(data.get("message", "Unknown error"))

    async def execute(
        self,
        task: str,
        use_websocket: bool = False,
        parallel_sub_agents: bool = True
    ) -> dict:
        """
        Execute a task through the agent orchestration.

        The master agent coordinates the work, delegating to sub-agents
        as needed based on the task requirements.

        Args:
            task: The task to execute
            use_websocket: Use WebSocket for streaming responses
            parallel_sub_agents: Run sub-agents in parallel when possible

        Returns:
            Orchestrated response from all agents
        """
        if not self.master_agent:
            raise ValueError("No master agent registered")

        logger.info(f"Executing task with master agent: {self.master_agent.agent_id}")

        # Step 1: Master agent analyzes task and creates plan
        planning_prompt = f"""
        Analyze this task and determine which sub-agents should handle parts of it.
        Available sub-agents: {json.dumps([
            {"id": a.agent_id, "role": a.role.value, "desc": a.description}
            for a in self.agents.values()
        ])}

        Task: {task}

        Respond with a JSON plan specifying which agents to use and what subtasks to assign.
        """

        if use_websocket:
            plan_response = ""
            async for chunk in self._stream_via_websocket(
                planning_prompt,
                self.master_agent.agent_id
            ):
                plan_response += chunk
        else:
            plan_result = await self._call_agent(
                self.master_agent.agent_id,
                planning_prompt
            )
            plan_response = self._extract_content(plan_result)

        # Step 2: Execute sub-agent tasks
        try:
            plan = json.loads(self._extract_json(plan_response))
        except json.JSONDecodeError:
            # If master didn't return valid JSON, use all agents
            plan = {"agents": [
                {"id": a.agent_id, "subtask": task}
                for a in self.agents.values()
            ]}

        sub_results = {}

        if parallel_sub_agents:
            # Run sub-agents in parallel
            tasks = []
            for agent_task in plan.get("agents", []):
                agent_id = agent_task.get("id")
                subtask = agent_task.get("subtask", task)
                if agent_id in self.agents:
                    tasks.append(self._call_agent(agent_id, subtask))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, agent_task in enumerate(plan.get("agents", [])):
                agent_id = agent_task.get("id")
                if i < len(results):
                    if isinstance(results[i], Exception):
                        sub_results[agent_id] = {"error": str(results[i])}
                    else:
                        sub_results[agent_id] = results[i]
        else:
            # Run sub-agents sequentially
            for agent_task in plan.get("agents", []):
                agent_id = agent_task.get("id")
                subtask = agent_task.get("subtask", task)
                if agent_id in self.agents:
                    try:
                        result = await self._call_agent(agent_id, subtask)
                        sub_results[agent_id] = result
                    except Exception as e:
                        sub_results[agent_id] = {"error": str(e)}

        # Step 3: Master agent synthesizes results
        synthesis_prompt = f"""
        Original task: {task}

        Sub-agent results:
        {json.dumps(sub_results, indent=2)}

        Synthesize these results into a final comprehensive response.
        """

        if use_websocket:
            final_response = ""
            async for chunk in self._stream_via_websocket(
                synthesis_prompt,
                self.master_agent.agent_id
            ):
                final_response += chunk
        else:
            final_result = await self._call_agent(
                self.master_agent.agent_id,
                synthesis_prompt
            )
            final_response = self._extract_content(final_result)

        return {
            "task": task,
            "plan": plan,
            "sub_agent_results": sub_results,
            "final_response": final_response
        }

    def _extract_content(self, result: dict) -> str:
        """Extract text content from agent response."""
        messages = result.get("data", [])
        for msg in messages:
            if msg.get("role") == "assistant":
                content = msg.get("content", [])
                if isinstance(content, list):
                    return " ".join(
                        c.get("text", "") for c in content
                        if c.get("type") == "text"
                    )
                return str(content)
        return ""

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text response."""
        # Find JSON block
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return text[start:end]
        return "{}"


# =============================================================================
# Example Usage and Configuration
# =============================================================================

def create_config_from_env() -> OrchestratorConfig:
    """
    Create configuration from environment variables.

    Required environment variables:
        AZURE_AGENT_ENDPOINT - Agent Foundry endpoint (South India)
        AZURE_AGENT_API_KEY - Agent API key
        AZURE_AGENT_PROJECT_ID - Project ID
        AZURE_MODEL_ENDPOINT - Model endpoint (East US)
        AZURE_MODEL_API_KEY - Model API key
        AZURE_MODEL_DEPLOYMENT - Model deployment name
        AZURE_WS_ENDPOINT - WebSocket endpoint
        AZURE_WS_API_KEY - WebSocket API key
        MASTER_AGENT_ID - Master agent ID
    """
    import os

    return OrchestratorConfig(
        foundry=FoundryConfig(
            # Agent in South India
            agent_endpoint=os.environ["AZURE_AGENT_ENDPOINT"],
            agent_api_key=os.environ["AZURE_AGENT_API_KEY"],
            agent_project_id=os.environ["AZURE_AGENT_PROJECT_ID"],
            # Model in East US
            model_endpoint=os.environ["AZURE_MODEL_ENDPOINT"],
            model_api_key=os.environ["AZURE_MODEL_API_KEY"],
            model_deployment_name=os.environ["AZURE_MODEL_DEPLOYMENT"],
            # WebSocket
            websocket_endpoint=os.environ["AZURE_WS_ENDPOINT"],
            websocket_api_key=os.environ["AZURE_WS_API_KEY"]
        ),
        master_agent_id=os.environ["MASTER_AGENT_ID"]
    )


async def main():
    """Example usage of the AgentOrchestrator."""

    # Example configuration (replace with your actual values)
    config = OrchestratorConfig(
        foundry=FoundryConfig(
            # Agent Foundry in South India
            agent_endpoint="https://your-foundry.southindia.api.azureml.ms",
            agent_api_key="your-agent-api-key",
            agent_project_id="your-project-id",
            # Model endpoint in East US
            model_endpoint="https://your-model.eastus.api.azureml.ms",
            model_api_key="your-model-api-key",
            model_deployment_name="gpt-4o",
            # WebSocket endpoint
            websocket_endpoint="wss://your-ws-endpoint.eastus.api.azureml.ms/ws",
            websocket_api_key="your-ws-api-key"
        ),
        master_agent_id="asst_master_001"
    )

    async with AgentOrchestrator(config) as orchestrator:
        # Register master agent
        orchestrator.register_agent(
            agent_id="asst_master_001",
            role=AgentRole.MASTER,
            description="Coordinates tasks and synthesizes results",
            is_master=True
        )

        # Register 4 sub-agents
        orchestrator.register_agent(
            agent_id="asst_researcher_001",
            role=AgentRole.RESEARCHER,
            description="Researches topics and gathers information"
        )

        orchestrator.register_agent(
            agent_id="asst_analyst_001",
            role=AgentRole.ANALYST,
            description="Analyzes data and provides insights"
        )

        orchestrator.register_agent(
            agent_id="asst_writer_001",
            role=AgentRole.WRITER,
            description="Writes and formats content"
        )

        orchestrator.register_agent(
            agent_id="asst_reviewer_001",
            role=AgentRole.REVIEWER,
            description="Reviews and validates output quality"
        )

        # Execute a task
        result = await orchestrator.execute(
            task="Create a comprehensive market analysis report for AI services",
            use_websocket=False,
            parallel_sub_agents=True
        )

        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
