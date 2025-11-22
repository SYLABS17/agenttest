"""
Main FastAPI application for AI Research System
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import settings
from .agents import ManagerAgent, BingSearchAgent, AISearchAgent
from .services import ObservabilityService, setup_observability, EvaluationService
from .services.observability import observability_service

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


# Request/Response Models
class ResearchRequest(BaseModel):
    """Research query request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="Research query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")
    evaluate: bool = Field(default=True, description="Whether to evaluate performance")
    timeout_seconds: Optional[int] = Field(default=30, description="Request timeout in seconds")


class ResearchResponse(BaseModel):
    """Research query response model"""
    request_id: str
    query: str
    status: str
    report: Optional[Dict[str, Any]] = None
    evaluation: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    environment: str
    version: str
    timestamp: str
    services: Dict[str, str]


class MetricsResponse(BaseModel):
    """Metrics response"""
    observability_metrics: Dict[str, Any]
    evaluation_summary: Dict[str, Any]
    agent_metrics: List[Dict[str, Any]]


# Global instances
manager_agent: Optional[ManagerAgent] = None
evaluation_service: Optional[EvaluationService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting AI Research System...")
    
    # Initialize agents
    global manager_agent, evaluation_service
    
    bing_agent = BingSearchAgent()
    ai_search_agent = AISearchAgent()
    manager_agent = ManagerAgent(worker_agents=[bing_agent, ai_search_agent])
    
    # Initialize services
    evaluation_service = EvaluationService()
    
    # Setup observability
    setup_observability(app)
    
    logger.info("AI Research System started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Research System...")
    
    # Flush telemetry
    observability_service.flush()
    
    logger.info("AI Research System shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="AI Research System",
    description="Multi-agent AI research system with Azure integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    observability_service.log_event(
        "warning",
        f"HTTP Exception: {exc.status_code}",
        path=request.url.path,
        detail=exc.detail
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    observability_service.log_exception(
        exc,
        context={"path": request.url.path, "method": request.method}
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Research System API",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {
        "manager_agent": "healthy" if manager_agent else "unavailable",
        "evaluation_service": "healthy" if evaluation_service else "unavailable",
        "observability": "healthy" if observability_service.is_configured else "degraded",
        "azure_configured": "healthy" if settings.azure_configured else "not_configured"
    }
    
    overall_status = "healthy" if all(
        s == "healthy" for s in list(services_status.values())[:3]
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        environment=settings.app_env,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat(),
        services=services_status
    )


@app.post("/research", response_model=ResearchResponse)
async def conduct_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Conduct research using multi-agent system
    """
    import uuid
    import time
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Log request
        observability_service.log_event(
            "info",
            "Research request received",
            request_id=request_id,
            query=request.query[:100]
        )
        
        if not manager_agent:
            raise HTTPException(status_code=503, detail="Manager agent not initialized")
        
        # Execute research with timeout
        research_task = manager_agent.execute(request.query, request.context)
        
        if request.timeout_seconds:
            response = await asyncio.wait_for(research_task, timeout=request.timeout_seconds)
        else:
            response = await research_task
        
        # Process response
        if response.status.value == "failed":
            raise HTTPException(status_code=500, detail=f"Research failed: {response.error}")
        
        # Extract report
        report = response.content if isinstance(response.content, dict) else {"content": response.content}
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Perform evaluation if requested
        evaluation = None
        if request.evaluate and evaluation_service:
            # Get all agent responses from manager's worker agents
            agent_responses = []
            for agent in manager_agent.worker_agents:
                # Get last response from each agent (simplified)
                if hasattr(agent, 'last_response'):
                    agent_responses.append(agent.last_response)
            
            if agent_responses:
                system_eval = await evaluation_service.evaluate_system(
                    request.query,
                    agent_responses,
                    report
                )
                evaluation = system_eval.to_dict()
        
        # Log success
        observability_service.log_event(
            "info",
            "Research completed successfully",
            request_id=request_id,
            processing_time_ms=processing_time_ms,
            evaluation_score=evaluation.get("overall_score") if evaluation else None
        )
        
        return ResearchResponse(
            request_id=request_id,
            query=request.query,
            status="completed",
            report=report,
            evaluation=evaluation,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except asyncio.TimeoutError:
        observability_service.log_event(
            "error",
            "Research request timed out",
            request_id=request_id,
            timeout_seconds=request.timeout_seconds
        )
        raise HTTPException(status_code=408, detail="Request timeout")
        
    except Exception as e:
        observability_service.log_exception(
            e,
            context={"request_id": request_id, "query": request.query}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", response_model=List[Dict[str, Any]])
async def list_agents():
    """List all available agents and their status"""
    if not manager_agent:
        return []
    
    agents_info = []
    
    # Add manager agent info
    agents_info.append({
        "id": manager_agent.id,
        "name": manager_agent.name,
        "role": manager_agent.role.value,
        "status": manager_agent.status.value,
        "metrics": manager_agent.get_metrics()
    })
    
    # Add worker agents info
    for agent in manager_agent.worker_agents:
        agents_info.append({
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value,
            "status": agent.status.value,
            "metrics": agent.get_metrics()
        })
    
    return agents_info


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics and performance data"""
    
    # Get observability metrics
    obs_metrics = observability_service.get_metrics_summary()
    
    # Get evaluation summary
    eval_summary = evaluation_service.get_evaluation_summary() if evaluation_service else {}
    
    # Get agent metrics
    agent_metrics = []
    if manager_agent:
        agent_metrics.append(manager_agent.get_metrics())
        for agent in manager_agent.worker_agents:
            agent_metrics.append(agent.get_metrics())
    
    return MetricsResponse(
        observability_metrics=obs_metrics,
        evaluation_summary=eval_summary,
        agent_metrics=agent_metrics
    )


@app.get("/evaluation/history")
async def get_evaluation_history(limit: int = 10):
    """Get evaluation history"""
    if not evaluation_service:
        return {"message": "Evaluation service not available"}
    
    history = evaluation_service.evaluation_history[-limit:]
    
    return {
        "total_evaluations": len(evaluation_service.evaluation_history),
        "returned": len(history),
        "evaluations": [eval.to_dict() for eval in history]
    }


@app.post("/evaluation/export")
async def export_evaluation(evaluation_id: int, format: str = "json"):
    """Export a specific evaluation"""
    if not evaluation_service:
        raise HTTPException(status_code=503, detail="Evaluation service not available")
    
    if evaluation_id >= len(evaluation_service.evaluation_history):
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = evaluation_service.evaluation_history[evaluation_id]
    exported = evaluation_service.export_evaluation(evaluation, format)
    
    return Response(
        content=exported,
        media_type="application/json" if format == "json" else "text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=evaluation_{evaluation_id}.{format}"
        }
    )


@app.post("/agents/reset")
async def reset_agents():
    """Reset all agents to initial state"""
    if not manager_agent:
        raise HTTPException(status_code=503, detail="Manager agent not initialized")
    
    # Reset manager
    await manager_agent.reset()
    
    # Reset workers
    for agent in manager_agent.worker_agents:
        await agent.reset()
    
    observability_service.log_event("info", "All agents reset successfully")
    
    return {"message": "All agents reset successfully"}


@app.get("/config")
async def get_configuration():
    """Get current configuration (non-sensitive)"""
    return {
        "environment": settings.app_env,
        "version": settings.app_version,
        "debug": settings.app_debug,
        "evaluation_enabled": settings.evaluation_enabled,
        "evaluation_metrics": settings.evaluation_metrics,
        "agent_timeout": settings.agent_timeout_seconds,
        "max_retries": settings.agent_max_retries,
        "manager_max_iterations": settings.manager_max_iterations,
        "observability_configured": settings.observability_configured,
        "azure_configured": settings.azure_configured
    }


# Dummy data endpoints for testing
@app.get("/test/queries")
async def get_test_queries():
    """Get sample test queries"""
    return {
        "queries": [
            "Future of renewable energy in Africa",
            "Impact of generative AI on journalism",
            "Best practices for cloud-native application development",
            "Quantum computing applications in drug discovery",
            "Sustainable urban planning strategies for 2030",
            "Blockchain adoption in supply chain management",
            "Mental health support systems using AI",
            "Edge computing in autonomous vehicles"
        ]
    }


@app.post("/test/simulate")
async def simulate_research(query_index: int = 0):
    """Simulate a research request with predefined query"""
    queries = (await get_test_queries())["queries"]
    
    if query_index >= len(queries):
        raise HTTPException(status_code=400, detail="Invalid query index")
    
    request = ResearchRequest(
        query=queries[query_index],
        evaluate=True
    )
    
    return await conduct_research(request, BackgroundTasks())


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level=settings.log_level.lower()
    )