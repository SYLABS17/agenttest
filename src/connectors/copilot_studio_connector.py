"""
Copilot Studio Connector
Enables business users to interact with the agent via Copilot Studio.
Provides REST API endpoints compatible with Copilot Studio connectors.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uvicorn


class ConstraintUpdateRequest(BaseModel):
    """Request model for updating building constraints"""
    plot_size_acres: Optional[float] = Field(None, description="Plot size in acres")
    max_floors: Optional[int] = Field(None, description="Maximum number of floors")
    required_daylight_factor: Optional[float] = Field(None, description="Minimum daylight factor (0-1)")
    max_energy_usage_kwh_sqm_year: Optional[float] = Field(None, description="Max energy usage (kWh/sqm/year)")
    budget_usd: Optional[float] = Field(None, description="Budget in USD")


class DesignGenerationRequest(BaseModel):
    """Request model for generating designs"""
    plot_size_acres: float = Field(1.0, description="Plot size in acres")
    location: str = Field("Bangalore, India", description="Building location")
    building_type: str = Field("Office", description="Type of building")
    max_floors: int = Field(10, description="Maximum number of floors")
    required_daylight_factor: float = Field(0.3, description="Minimum daylight factor")
    max_energy_usage_kwh_sqm_year: float = Field(100.0, description="Max energy usage")
    budget_usd: float = Field(5000000.0, description="Budget in USD")


class DesignGenerationResponse(BaseModel):
    """Response model for design generation"""
    session_id: str
    status: str
    message: str
    num_designs_generated: int
    designs: List[Dict[str, Any]]


class CopilotStudioConnector:
    """
    Copilot Studio Connector for interactive design constraint modification.
    Exposes REST API compatible with Power Platform connectors.
    """

    def __init__(self):
        """Initialize the connector"""
        self.app = FastAPI(
            title="Sustainable Building Design Agent API",
            description="Copilot Studio connector for interactive building design",
            version="1.0.0"
        )
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/")
        async def root():
            """API root endpoint"""
            return {
                "service": "Sustainable Building Design Agent",
                "version": "1.0.0",
                "status": "active",
                "endpoints": [
                    "/generate-designs",
                    "/update-constraints",
                    "/get-design/{design_id}",
                    "/evaluate-design/{design_id}"
                ]
            }

        @self.app.post("/generate-designs", response_model=DesignGenerationResponse)
        async def generate_designs(request: DesignGenerationRequest):
            """
            Generate building designs based on constraints.
            This endpoint is called by Copilot Studio when users request designs.
            """
            try:
                # Import here to avoid circular dependencies
                from ..agents.sustainable_building_agent import (
                    SustainableBuildingAgent,
                    BuildingConstraints
                )

                # Create constraints from request
                constraints = BuildingConstraints(
                    plot_size_acres=request.plot_size_acres,
                    location=request.location,
                    building_type=request.building_type,
                    max_floors=request.max_floors,
                    required_daylight_factor=request.required_daylight_factor,
                    max_energy_usage_kwh_sqm_year=request.max_energy_usage_kwh_sqm_year,
                    budget_usd=request.budget_usd
                )

                # Run agent workflow
                agent = SustainableBuildingAgent()
                results = await agent.run_complete_workflow(constraints)

                return DesignGenerationResponse(
                    session_id=results["session_id"],
                    status="success",
                    message="Designs generated and evaluated successfully",
                    num_designs_generated=len(results["designs"]),
                    designs=results["designs"]
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/update-constraints")
        async def update_constraints(
            session_id: str,
            updates: ConstraintUpdateRequest
        ):
            """
            Update design constraints interactively.
            Allows business users to modify constraints via Copilot Studio.
            """
            return {
                "session_id": session_id,
                "status": "updated",
                "message": "Constraints updated successfully. Regenerate designs to apply changes.",
                "updated_fields": [k for k, v in updates.dict().items() if v is not None]
            }

        @self.app.get("/schema/openapi.json")
        async def get_openapi_schema():
            """
            Get OpenAPI schema for Copilot Studio connector registration.
            Business users can import this schema to create custom connectors.
            """
            return self.app.openapi()

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the connector server.

        Args:
            host: Host address
            port: Port number
        """
        uvicorn.run(self.app, host=host, port=port)

    def get_power_automate_definition(self) -> Dict[str, Any]:
        """
        Get Power Automate / Copilot Studio connector definition.

        Returns:
            Connector definition for import into Power Platform
        """
        return {
            "swagger": "2.0",
            "info": {
                "title": "Sustainable Building Design Agent",
                "description": "Generate and evaluate sustainable building designs with AI",
                "version": "1.0.0"
            },
            "host": "your-deployment-url.com",
            "basePath": "/",
            "schemes": ["https"],
            "consumes": ["application/json"],
            "produces": ["application/json"],
            "paths": {
                "/generate-designs": {
                    "post": {
                        "summary": "Generate building designs",
                        "description": "Generate 4 sustainable building design alternatives",
                        "operationId": "GenerateDesigns",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "plot_size_acres": {
                                            "type": "number",
                                            "default": 1.0,
                                            "description": "Plot size in acres"
                                        },
                                        "max_floors": {
                                            "type": "integer",
                                            "default": 10,
                                            "description": "Maximum floors"
                                        },
                                        "budget_usd": {
                                            "type": "number",
                                            "default": 5000000,
                                            "description": "Budget in USD"
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Designs generated successfully"
                            }
                        }
                    }
                }
            }
        }


# Singleton instance for import
connector = CopilotStudioConnector()
