"""Main FastAPI application for AI Research System."""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.services import ObservabilityService, EvaluatorService, setup_logging
from backend.agents import ManagerAgent


# Set up logging first
logger = setup_logging()

# Initialize services
observability = ObservabilityService()
evaluator = EvaluatorService()
manager_agent = ManagerAgent()


# Pydantic models
class ResearchQuery(BaseModel):
    """Research query request model."""
    query: str = Field(..., description="Research query to process")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")
    include_evaluation: bool = Field(default=True, description="Include evaluation metrics")


class ResearchResponse(BaseModel):
    """Research response model."""
    success: bool
    query: str
    report: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    evaluation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    environment: str
    agents: Dict[str, Any]
    services: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Metrics response model."""
    timestamp: str
    agents: Dict[str, Any]
    evaluations: Dict[str, Any]
    observability: Dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(
        "Starting AI Research System",
        environment=settings.api_env,
        host=settings.api_host,
        port=settings.api_port
    )
    
    # Warm up agents
    await manager_agent.health_check()
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Research System")
    
    # Clean up resources
    if observability.metrics_exporter:
        observability.metrics_exporter.close()


# Create FastAPI app
app = FastAPI(
    title="AI Research System",
    description="Multi-agent research system with Azure AI integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc)
    )
    
    observability.record_error(exc, {"path": request.url.path})
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An unexpected error occurred",
            "message": str(exc) if settings.is_development() else "Internal server error"
        }
    )


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "service": "AI Research System",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/healthz", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    # Check all agents
    agents_health = await manager_agent.health_check()
    
    # Check services
    services_health = {
        "observability": {
            "tracing_enabled": observability.tracer is not None,
            "metrics_enabled": observability.stats is not None,
            "has_app_insights": bool(settings.applicationinsights_connection_string)
        },
        "evaluator": {
            "total_evaluations": len(evaluator.evaluation_history),
            "criteria_count": len(evaluator.criteria)
        }
    }
    
    return HealthResponse(
        status="healthy" if agents_health.get("overall_healthy", False) else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        environment=settings.api_env,
        agents=agents_health,
        services=services_health
    )


@app.post("/api/research", response_model=ResearchResponse)
async def conduct_research(
    request: ResearchQuery,
    background_tasks: BackgroundTasks
):
    """Conduct research using multi-agent system."""
    start_time = datetime.utcnow()
    
    # Record request
    observability.record_request({"endpoint": "/api/research"})
    
    try:
        # Start tracing
        with observability.create_tracer("research_request").span(name="conduct_research") as span:
            span.add_attribute("query", request.query[:100])
            
            logger.info("Processing research query", query=request.query[:100])
            
            # Execute research
            result = await manager_agent.execute(request.query, request.context)
            
            # Extract data from result
            metadata = result.metadata
            final_report = metadata.get("final_report", "")
            chat_history = metadata.get("chat_history", [])
            
            # Calculate processing time
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Record latency
            observability.record_latency(processing_time_ms, {"agent": "manager"})
            
            # Perform evaluation if requested
            evaluation = None
            if request.include_evaluation:
                # Evaluate each agent's response
                evaluations = []
                
                # Extract individual agent responses from chat history
                for msg in chat_history:
                    if msg.get("agent_name") in ["BingSearchAgent", "AISearchAgent"]:
                        agent_eval = await evaluator.evaluate_agent_response(
                            agent_name=msg["agent_name"],
                            query=request.query,
                            response=msg.get("metadata", {}),
                            latency_ms=msg.get("metadata", {}).get("latency_ms", 0)
                        )
                        evaluations.append(agent_eval)
                
                # Calculate agreement score
                agent_responses = [
                    msg.get("metadata", {}) 
                    for msg in chat_history 
                    if msg.get("agent_name") in ["BingSearchAgent", "AISearchAgent"]
                ]
                agreement_score = await evaluator.evaluate_multi_agent_agreement(agent_responses)
                
                # Generate evaluation report
                if evaluations:
                    evaluation = await evaluator.generate_evaluation_report(
                        query=request.query,
                        evaluations=evaluations,
                        agreement_score=agreement_score
                    )
                    
                    # Log evaluation in background
                    background_tasks.add_task(
                        logger.info,
                        "Research evaluation completed",
                        overall_score=evaluation.get("summary", {}).get("overall", {}).get("mean", 0)
                    )
            
            logger.info(
                "Research completed",
                query=request.query[:50],
                processing_time_ms=processing_time_ms,
                report_length=len(final_report)
            )
            
            return ResearchResponse(
                success=True,
                query=request.query,
                report=final_report,
                chat_history=chat_history,
                evaluation=evaluation,
                processing_time_ms=processing_time_ms
            )
            
    except Exception as e:
        logger.error("Research failed", error=str(e), query=request.query)
        observability.record_error(e, {"endpoint": "/api/research"})
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ResearchResponse(
            success=False,
            query=request.query,
            error=str(e),
            processing_time_ms=processing_time_ms
        )


@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics."""
    return MetricsResponse(
        timestamp=datetime.utcnow().isoformat(),
        agents=await manager_agent.get_agent_metrics(),
        evaluations=evaluator.get_historical_metrics(),
        observability=observability.get_metrics_summary()
    )


@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents."""
    return await manager_agent.health_check()


@app.get("/api/evaluation/history")
async def get_evaluation_history(limit: int = 100):
    """Get evaluation history."""
    history = evaluator.evaluation_history[-limit:]
    return {
        "count": len(history),
        "evaluations": history
    }


@app.get("/api/evaluation/export")
async def export_evaluations():
    """Export evaluation metrics as CSV."""
    filepath = evaluator.export_metrics_to_csv()
    
    if filepath.exists():
        def iterfile():
            with open(filepath, mode="rb") as file_like:
                yield from file_like
                
        return StreamingResponse(
            iterfile(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=metrics_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    else:
        raise HTTPException(status_code=404, detail="No metrics to export")


@app.get("/api/logs")
async def get_recent_logs(lines: int = 100):
    """Get recent application logs (dev mode only)."""
    if not settings.is_development():
        raise HTTPException(status_code=403, detail="Logs only available in development mode")
        
    from backend.config import LOGS_DIR
    
    # Find most recent log file
    log_files = list(LOGS_DIR.glob("app_*.log"))
    if not log_files:
        return {"logs": []}
        
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    
    # Read last N lines
    with open(latest_log, "r") as f:
        all_lines = f.readlines()
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
    # Parse JSON logs
    logs = []
    for line in recent_lines:
        try:
            logs.append(json.loads(line.strip()))
        except:
            logs.append({"raw": line.strip()})
            
    return {
        "log_file": str(latest_log),
        "total_lines": len(all_lines),
        "returned_lines": len(logs),
        "logs": logs
    }


@app.post("/api/test/dummy-query")
async def test_dummy_query():
    """Test endpoint with dummy queries."""
    dummy_queries = [
        "Future of renewable energy in Africa",
        "Impact of generative AI on journalism",
        "Quantum computing applications in healthcare"
    ]
    
    import random
    query = random.choice(dummy_queries)
    
    return await conduct_research(
        ResearchQuery(query=query, include_evaluation=True),
        BackgroundTasks()
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development(),
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["default"],
            },
        }
    )