"""
Azure AI Foundry Multi-Agent Orchestrator
Simple orchestrator: Master agent + 4 sub-agents with cross-region support
"""

import asyncio
import json
import aiohttp
import websockets
from dataclasses import dataclass

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


class AgentOrchestrator:
    def __init__(self, config: Config, master_id: str):
        self.config = config
        self.master_id = master_id
        self.agents: dict[str, str] = {}  # id -> role
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

    async def call_agent(self, agent_id: str, task: str) -> str:
        """Call an agent via REST API."""
        url = f"{self.config.agent_endpoint}/projects/{self.config.project_id}/agents/{agent_id}/runs"
        headers = {"Authorization": f"Bearer {self.config.agent_key}", "Content-Type": "application/json"}
        payload = {
            "task": task,
            "model_endpoint": self.config.model_endpoint,
            "model_deployment": self.config.model_name
        }
        async with self._session.post(url, headers=headers, json=payload) as resp:
            result = await resp.json()
            return result.get("response", str(result))

    async def call_via_ws(self, agent_id: str, task: str) -> str:
        """Call agent via WebSocket for streaming."""
        if not self._ws:
            headers = {"Authorization": f"Bearer {self.config.ws_key}"}
            self._ws = await websockets.connect(self.config.ws_endpoint, additional_headers=headers)

        await self._ws.send(json.dumps({"agent_id": agent_id, "task": task}))
        response = ""
        async for msg in self._ws:
            data = json.loads(msg)
            if data.get("type") == "done": break
            response += data.get("content", "")
        return response

    async def execute(self, task: str, use_ws: bool = False) -> dict:
        """Execute task: master plans, sub-agents execute, master synthesizes."""
        call = self.call_via_ws if use_ws else self.call_agent

        # 1. Master creates plan
        plan_prompt = f"Plan this task for agents {list(self.agents.items())}: {task}"
        plan = await call(self.master_id, plan_prompt)

        # 2. Run sub-agents in parallel
        tasks = [call(aid, f"{task} (role: {role})") for aid, role in self.agents.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sub_results = {aid: str(r) for aid, r in zip(self.agents.keys(), results)}

        # 3. Master synthesizes
        synthesis = await call(self.master_id, f"Synthesize results for '{task}': {json.dumps(sub_results)}")

        return {"task": task, "sub_results": sub_results, "final": synthesis}


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

    orch = AgentOrchestrator(config, master_id="asst_master_001")
    await orch.connect()

    # Register 4 sub-agents
    orch.add_agent("asst_researcher_001", "researcher")
    orch.add_agent("asst_analyst_001", "analyst")
    orch.add_agent("asst_writer_001", "writer")
    orch.add_agent("asst_reviewer_001", "reviewer")

    result = await orch.execute("Create a market analysis report")
    print(json.dumps(result, indent=2))

    await orch.close()

if __name__ == "__main__":
    asyncio.run(main())
