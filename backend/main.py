from __future__ import annotations

import functools
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.agents.ai_search_agent import AISearchAgent
from backend.agents.bing_agent import BingSearchAgent
from backend.agents.manager_agent import ManagerAgent
from backend.config import AppConfig, settings
from backend.services.evaluator import AgentEvaluator
from backend.services.observability import ObservabilityService

try:
    from azure.identity import DefaultAzureCredential  # type: ignore
    from azure.keyvault.secrets import SecretClient  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    DefaultAzureCredential = None
    SecretClient = None


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=5, description="The research question the agents should investigate.")


class HealthResponse(BaseModel):
    status: str
    environment: str
    app_name: str


class KeyVaultSecretProvider:
    """Simple wrapper that fetches secrets from Key Vault when configured."""

    def __init__(self, config: AppConfig):
        self.config = config
        self._client = None
        if config.key_vault_uri and DefaultAzureCredential and SecretClient:
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=config.key_vault_uri, credential=credential)

    def get_secret(self, name: str) -> Optional[str]:
        if not self._client:
            return None
        try:
            return self._client.get_secret(name).value
        except Exception:
            return None


def create_app(config: AppConfig = settings) -> FastAPI:
    app = FastAPI(title=config.app_name, version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event() -> None:
        obs = ObservabilityService(config)
        secret_provider = KeyVaultSecretProvider(config)
        azure_search_key = secret_provider.get_secret("azure-search-key") or config.azure_search_api_key
        app.state.settings = config
        app.state.observability = obs
        app.state.bing_agent = BingSearchAgent(config, obs)
        ai_agent = AISearchAgent(config, obs)
        if azure_search_key:
            obs.log_event("secret_resolved", secretName="azure-search-key", resolved=True)
        app.state.ai_search_agent = ai_agent
        evaluator = AgentEvaluator(obs)
        app.state.manager = ManagerAgent(
            settings=config,
            observability=obs,
            bing_agent=app.state.bing_agent,
            ai_search_agent=ai_agent,
            evaluator=evaluator,
        )
        obs.log_event("startup_complete", env=config.environment)

    def get_manager(agent: ManagerAgent = Depends(lambda: getattr(app.state, "manager", None))) -> ManagerAgent:
        manager = agent or getattr(app.state, "manager", None)
        if not manager:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Manager not ready")
        return manager

    def get_observability() -> ObservabilityService:
        obs = getattr(app.state, "observability", None)
        if not obs:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Observability not ready")
        return obs

    @app.post("/api/research")
    async def run_research(payload: ResearchRequest, manager: ManagerAgent = Depends(get_manager)):
        result = await _run_in_threadpool(manager.run_research, payload.query)
        return JSONResponse(content=result)

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz(config: AppConfig = Depends(lambda: settings)):
        return HealthResponse(status="ok", environment=config.environment, app_name=config.app_name)

    @app.get("/api/logs")
    async def get_logs(observability: ObservabilityService = Depends(get_observability)):
        return {"logs": list(observability.recent_logs())}

    return app


async def _run_in_threadpool(func, *args, **kwargs):
    from starlette.concurrency import run_in_threadpool

    return await run_in_threadpool(functools.partial(func, *args, **kwargs))


app = create_app()
