from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agents.ai_search_agent import AISearchAgent
from backend.agents.bing_agent import BingSearchAgent
from backend.agents.manager_agent import ManagerAgent
from backend.config import ROOT_DIR, Settings, get_settings
from backend.services.evaluator import AgentEvaluator
from backend.services.observability import ObservabilityService


settings: Settings = get_settings()
observability = ObservabilityService(
    connection_string=settings.appinsights_connection_string,
    environment=settings.environment,
    log_dir=ROOT_DIR / "backend" / "logs",
)

bing_agent = BingSearchAgent(settings.bing_fixture_path, observability)
ai_agent = AISearchAgent(settings.ai_search_fixture_path, observability)
evaluator = AgentEvaluator(observability)
manager = ManagerAgent([bing_agent, ai_agent], evaluator, observability)


class ResearchRequest(BaseModel):
  query: str
  context: str | None = None


class ResearchResponse(BaseModel):
  query: str
  finalReport: str
  messages: list[Dict[str, Any]]
  evaluation: Dict[str, Any]
  latencyMs: int


app = FastAPI(
    title="Azure AI Research Orchestrator",
    description="Manager agent coordinating Bing + Azure AI Search workers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> Dict[str, Any]:
  return {
      "status": "ok",
      "environment": settings.environment,
      "timestamp": dt.datetime.utcnow().isoformat() + "Z",
  }


@app.post("/api/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest) -> ResearchResponse:
  if not request.query.strip():
    raise HTTPException(status_code=400, detail="Query must not be empty.")

  result = await manager.handle_query(request.query.strip())
  _persist_report(request.query, result["finalReport"])
  return ResearchResponse(**result)


@app.get("/api/logs")
async def fetch_logs(limit: int = 100) -> Dict[str, Any]:
  log_file = ROOT_DIR / "backend" / "logs" / "app.log"
  if not log_file.exists():
    return {"entries": [], "message": "Log file not created yet."}

  with log_file.open("r", encoding="utf-8") as handle:
    lines = handle.readlines()
  return {"entries": lines[-limit:]}


def _persist_report(query: str, report: str) -> None:
  reports_dir: Path = settings.reports_dir
  reports_dir.mkdir(parents=True, exist_ok=True)
  safe_name = query.lower().replace(" ", "-")[:40]
  file_path = reports_dir / f"{safe_name or 'report'}-{dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
  file_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
  uvicorn.run("backend.main:app", host=settings.api_host, port=settings.api_port, reload=True)
