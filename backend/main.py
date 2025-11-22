from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.agents.manager_agent import ManagerAgent
from backend.services.evaluator import Evaluator
from backend.services.observability import setup_logging
import uvicorn
import os

app = FastAPI(title="AI Research System")
logger = setup_logging()
manager = ManagerAgent()
evaluator = Evaluator()

class ResearchRequest(BaseModel):
    query: str

@app.get("/healthz")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/research")
async def research(request: ResearchRequest):
    logger.info(f"Received research request: {request.query}")
    try:
        report = await manager.process_request(request.query)
        evaluation = evaluator.evaluate_response(request.query, report)
        
        response = {
            "report": report,
            "evaluation": evaluation
        }
        logger.info("Research completed successfully")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
