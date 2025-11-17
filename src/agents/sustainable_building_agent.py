"""
Sustainable Building Design Agent
Orchestrates the generation and evaluation of sustainable building designs
using Microsoft Agent Framework patterns and Azure AI Foundry.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from ..services.design_generator import DesignGenerator
from ..services.environmental_simulator import EnvironmentalSimulator
from ..services.cost_analyzer import CostAnalyzer
from ..services.llm_evaluator import LLMEvaluator
from ..utils.audit_logger import AuditLogger
from ..utils.output_formatter import OutputFormatter


@dataclass
class BuildingConstraints:
    """Constraints for building design"""
    plot_size_acres: float = 1.0
    location: str = "Bangalore, India"
    building_type: str = "Office"
    max_floors: int = 10
    required_daylight_factor: float = 0.3  # 30% minimum
    max_energy_usage_kwh_sqm_year: float = 100.0
    budget_usd: float = 5000000.0
    sustainability_priority: str = "high"

    # Eco-friendly material requirements
    required_materials: List[str] = None

    def __post_init__(self):
        if self.required_materials is None:
            self.required_materials = [
                "solar_panels",
                "green_roof",
                "recycled_steel",
                "bamboo"
            ]


@dataclass
class DesignAlternative:
    """Represents a single building design alternative"""
    id: str
    name: str
    description: str
    specifications: Dict[str, Any]
    environmental_metrics: Dict[str, float]
    cost_metrics: Dict[str, float]
    materials_used: List[str]
    score: Optional[float] = None
    passed: Optional[bool] = None
    copilot_commentary: Optional[str] = None


class SustainableBuildingAgent:
    """
    Main AI Agent for sustainable building design.
    Follows Microsoft Agent Framework patterns with Azure AI Foundry integration.
    """

    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        enable_copilot_studio: bool = True
    ):
        """
        Initialize the Sustainable Building Agent.

        Args:
            azure_endpoint: Azure AI Foundry endpoint
            azure_api_key: Azure AI API key
            enable_copilot_studio: Enable Copilot Studio connectors
        """
        self.azure_endpoint = azure_endpoint
        self.azure_api_key = azure_api_key
        self.enable_copilot_studio = enable_copilot_studio

        # Initialize services
        self.design_generator = DesignGenerator()
        self.environmental_simulator = EnvironmentalSimulator()
        self.cost_analyzer = CostAnalyzer()
        self.llm_evaluator = LLMEvaluator(
            azure_endpoint=azure_endpoint,
            azure_api_key=azure_api_key
        )

        # Initialize utilities
        self.audit_logger = AuditLogger()
        self.output_formatter = OutputFormatter()

        # Session state
        self.session_id = None
        self.constraints = None
        self.design_alternatives = []

    async def initialize_session(self, constraints: BuildingConstraints) -> str:
        """
        Initialize a new design session.

        Args:
            constraints: Building design constraints

        Returns:
            Session ID for tracking
        """
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.constraints = constraints
        self.design_alternatives = []

        # Log session initialization
        await self.audit_logger.log_event(
            session_id=self.session_id,
            event_type="session_initialized",
            data=asdict(constraints)
        )

        return self.session_id

    async def generate_design_alternatives(self) -> List[DesignAlternative]:
        """
        Generate 4 sustainable building design alternatives.

        Returns:
            List of design alternatives
        """
        await self.audit_logger.log_event(
            session_id=self.session_id,
            event_type="generation_started",
            data={"num_alternatives": 4}
        )

        # Generate 4 design alternatives
        raw_designs = await self.design_generator.generate_designs(
            constraints=self.constraints,
            num_alternatives=4
        )

        # Process each design through environmental simulation and cost analysis
        for idx, design in enumerate(raw_designs):
            # Environmental simulation
            env_metrics = await self.environmental_simulator.simulate(
                design=design,
                constraints=self.constraints
            )

            # Cost analysis
            cost_metrics = await self.cost_analyzer.analyze(
                design=design,
                constraints=self.constraints
            )

            # Create design alternative
            alternative = DesignAlternative(
                id=f"design_{idx + 1}",
                name=design["name"],
                description=design["description"],
                specifications=design["specifications"],
                environmental_metrics=env_metrics,
                cost_metrics=cost_metrics,
                materials_used=design["materials"]
            )

            self.design_alternatives.append(alternative)

            # Log design generation
            await self.audit_logger.log_event(
                session_id=self.session_id,
                event_type="design_generated",
                data={
                    "design_id": alternative.id,
                    "name": alternative.name
                }
            )

        return self.design_alternatives

    async def evaluate_designs(self) -> List[DesignAlternative]:
        """
        Evaluate all design alternatives using LLM.

        Returns:
            Evaluated design alternatives with scores and pass/fail status
        """
        await self.audit_logger.log_event(
            session_id=self.session_id,
            event_type="evaluation_started",
            data={"num_designs": len(self.design_alternatives)}
        )

        # Evaluate each design
        for alternative in self.design_alternatives:
            evaluation = await self.llm_evaluator.evaluate_design(
                design=alternative,
                constraints=self.constraints
            )

            # Update design with evaluation results
            alternative.score = evaluation["overall_score"]
            alternative.passed = evaluation["passed"]
            alternative.copilot_commentary = evaluation["copilot_commentary"]

            # Log evaluation
            await self.audit_logger.log_event(
                session_id=self.session_id,
                event_type="design_evaluated",
                data={
                    "design_id": alternative.id,
                    "score": alternative.score,
                    "passed": alternative.passed
                }
            )

        return self.design_alternatives

    async def generate_report(self, output_format: str = "console") -> str:
        """
        Generate final report with all designs and evaluations.

        Args:
            output_format: Output format (console, json, html, markdown)

        Returns:
            Formatted report
        """
        await self.audit_logger.log_event(
            session_id=self.session_id,
            event_type="report_generation_started",
            data={"format": output_format}
        )

        report = self.output_formatter.format_report(
            session_id=self.session_id,
            constraints=self.constraints,
            designs=self.design_alternatives,
            output_format=output_format
        )

        # Log report generation
        await self.audit_logger.log_event(
            session_id=self.session_id,
            event_type="report_generated",
            data={"format": output_format}
        )

        return report

    async def run_complete_workflow(
        self,
        constraints: Optional[BuildingConstraints] = None
    ) -> Dict[str, Any]:
        """
        Run the complete workflow: initialize, generate, evaluate, report.

        Args:
            constraints: Building constraints (uses defaults if not provided)

        Returns:
            Complete workflow results
        """
        # Use default constraints if not provided
        if constraints is None:
            constraints = BuildingConstraints()

        # Initialize session
        session_id = await self.initialize_session(constraints)

        # Generate design alternatives
        designs = await self.generate_design_alternatives()

        # Evaluate designs
        evaluated_designs = await self.evaluate_designs()

        # Generate reports in multiple formats
        console_report = await self.generate_report(output_format="console")
        json_report = await self.generate_report(output_format="json")

        # Get audit trail
        audit_trail = await self.audit_logger.get_session_trail(session_id)

        return {
            "session_id": session_id,
            "constraints": asdict(constraints),
            "designs": [asdict(d) for d in evaluated_designs],
            "console_report": console_report,
            "json_report": json_report,
            "audit_trail": audit_trail
        }

    def get_copilot_studio_schema(self) -> Dict[str, Any]:
        """
        Get schema for Copilot Studio connector integration.
        This enables business users to modify constraints interactively.

        Returns:
            OpenAPI-compatible schema for Copilot Studio
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Sustainable Building Design Agent API",
                "version": "1.0.0",
                "description": "Interactive API for generating sustainable building designs"
            },
            "paths": {
                "/design/generate": {
                    "post": {
                        "summary": "Generate building designs",
                        "operationId": "generateDesigns",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BuildingConstraints"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Design alternatives generated successfully"
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "BuildingConstraints": {
                        "type": "object",
                        "properties": {
                            "plot_size_acres": {"type": "number", "default": 1.0},
                            "location": {"type": "string", "default": "Bangalore, India"},
                            "building_type": {"type": "string", "default": "Office"},
                            "max_floors": {"type": "integer", "default": 10},
                            "required_daylight_factor": {"type": "number", "default": 0.3},
                            "max_energy_usage_kwh_sqm_year": {"type": "number", "default": 100.0},
                            "budget_usd": {"type": "number", "default": 5000000.0}
                        }
                    }
                }
            }
        }
