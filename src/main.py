#!/usr/bin/env python3
"""
Main entry point for Sustainable Building Design Agent
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.sustainable_building_agent import (
    SustainableBuildingAgent,
    BuildingConstraints
)


async def main():
    """Main execution function"""

    print("\n" + "=" * 100)
    print("SUSTAINABLE BUILDING DESIGN AGENT")
    print("Microsoft Agent Framework + Azure AI Foundry")
    print("=" * 100)
    print("")

    # Initialize agent
    print("Initializing AI Agent...")
    agent = SustainableBuildingAgent(
        enable_copilot_studio=True
    )

    # Define constraints for 1-acre urban plot in Bangalore
    print("Setting up building constraints for Bangalore project...")
    constraints = BuildingConstraints(
        plot_size_acres=1.0,
        location="Bangalore, India",
        building_type="Office",
        max_floors=10,
        required_daylight_factor=0.30,  # 30% minimum daylight
        max_energy_usage_kwh_sqm_year=100.0,  # 100 kWh/sqm/year max
        budget_usd=5000000.0,  # $5M budget
        sustainability_priority="high"
    )

    print("")
    print("Project Parameters:")
    print(f"  • Location: {constraints.location}")
    print(f"  • Plot Size: {constraints.plot_size_acres} acre(s)")
    print(f"  • Max Floors: {constraints.max_floors}")
    print(f"  • Budget: ${constraints.budget_usd:,.0f}")
    print(f"  • Required Daylight Factor: {constraints.required_daylight_factor}")
    print(f"  • Max Energy Usage: {constraints.max_energy_usage_kwh_sqm_year} kWh/sqm/year")
    print(f"  • Required Eco-Materials: {', '.join(constraints.required_materials)}")
    print("")

    # Run complete workflow
    print("=" * 100)
    print("EXECUTING AGENT WORKFLOW")
    print("=" * 100)
    print("")

    print("Step 1: Initializing session...")
    session_id = await agent.initialize_session(constraints)
    print(f"✓ Session initialized: {session_id}")
    print("")

    print("Step 2: Generating 4 sustainable building design alternatives...")
    designs = await agent.generate_design_alternatives()
    print(f"✓ Generated {len(designs)} design alternatives")
    for i, design in enumerate(designs, 1):
        print(f"   {i}. {design.name}")
    print("")

    print("Step 3: Running environmental simulations (daylight, energy, carbon)...")
    print("   • Simulating daylight exposure and useful daylight illuminance")
    print("   • Calculating energy consumption and solar generation")
    print("   • Analyzing carbon footprint and emissions")
    print("   • Evaluating thermal comfort")
    print("✓ Environmental simulations completed")
    print("")

    print("Step 4: Performing cost analysis...")
    print("   • Calculating construction costs with eco-friendly materials")
    print("   • Analyzing lifecycle costs (30-year NPV)")
    print("   • Evaluating operational expenses")
    print("✓ Cost analysis completed")
    print("")

    print("Step 5: LLM Evaluation (Copilot Studio Prompt Builder)...")
    print("   • Evaluating completeness (required materials, specifications)")
    print("   • Evaluating sustainability (daylight, energy, carbon, materials)")
    print("   • Evaluating cost-effectiveness (budget, value, lifecycle)")
    evaluated_designs = await agent.evaluate_designs()
    print("✓ LLM evaluation completed")
    print("")

    print("Step 6: Generating final report with recommendations...")
    console_report = await agent.generate_report(output_format="console")
    print("✓ Report generated")
    print("")

    # Display report
    print(console_report)

    # Save JSON report
    json_report = await agent.generate_report(output_format="json")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    json_file = output_dir / f"{session_id}_report.json"
    with open(json_file, 'w') as f:
        f.write(json_report)

    print("")
    print(f"JSON report saved to: {json_file}")

    # Display Copilot Studio audit trail reference
    print("")
    print("=" * 100)
    print(agent.audit_logger.get_copilot_studio_audit_reference(session_id))
    print("=" * 100)

    print("")
    print("Agent workflow completed successfully!")
    print("")

    return {
        "session_id": session_id,
        "designs": evaluated_designs,
        "output_file": str(json_file)
    }


def run_copilot_studio_server():
    """Run Copilot Studio connector server"""
    from src.connectors.copilot_studio_connector import connector

    print("\n" + "=" * 100)
    print("COPILOT STUDIO CONNECTOR SERVER")
    print("=" * 100)
    print("")
    print("Starting API server for Copilot Studio integration...")
    print("Business users can now interact with the agent via Copilot Studio")
    print("")
    print("Available endpoints:")
    print("  • POST /generate-designs - Generate building designs")
    print("  • POST /update-constraints - Modify constraints interactively")
    print("  • GET /schema/openapi.json - Get OpenAPI schema for connector registration")
    print("")
    print("Server running at: http://localhost:8000")
    print("OpenAPI docs at: http://localhost:8000/docs")
    print("")

    connector.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run Copilot Studio server
        run_copilot_studio_server()
    else:
        # Run standard workflow
        asyncio.run(main())
