"""
Output Formatter
Formats design evaluation results into various output formats.
"""

import json
from typing import Dict, List, Any
from datetime import datetime


class OutputFormatter:
    """
    Formats agent output into various formats (console, JSON, HTML, Markdown).
    """

    def __init__(self):
        """Initialize the output formatter"""
        pass

    def format_report(
        self,
        session_id: str,
        constraints: Any,
        designs: List[Any],
        output_format: str = "console"
    ) -> str:
        """
        Format complete report.

        Args:
            session_id: Session identifier
            constraints: Building constraints
            designs: List of evaluated designs
            output_format: Output format (console, json, html, markdown)

        Returns:
            Formatted report
        """
        if output_format == "console":
            return self._format_console_report(session_id, constraints, designs)
        elif output_format == "json":
            return self._format_json_report(session_id, constraints, designs)
        elif output_format == "markdown":
            return self._format_markdown_report(session_id, constraints, designs)
        elif output_format == "html":
            return self._format_html_report(session_id, constraints, designs)
        else:
            return self._format_console_report(session_id, constraints, designs)

    def _format_console_report(
        self,
        session_id: str,
        constraints: Any,
        designs: List[Any]
    ) -> str:
        """
        Format report for console output with tables.

        Args:
            session_id: Session identifier
            constraints: Building constraints
            designs: List of designs

        Returns:
            Console-formatted report
        """
        lines = []

        # Header
        lines.append("=" * 100)
        lines.append("SUSTAINABLE BUILDING DESIGN AGENT - EVALUATION REPORT")
        lines.append("=" * 100)
        lines.append(f"Session ID: {session_id}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Location: {constraints.location}")
        lines.append(f"Plot Size: {constraints.plot_size_acres} acres")
        lines.append(f"Budget: ${constraints.budget_usd:,.0f}")
        lines.append("=" * 100)
        lines.append("")

        # Summary Table
        lines.append("DESIGN ALTERNATIVES SUMMARY")
        lines.append("-" * 100)
        lines.append(f"{'ID':<6} {'Design Name':<25} {'Score':<10} {'Status':<12} {'Cost':<15} {'Energy':<12}")
        lines.append("-" * 100)

        for design in designs:
            design_id = design.get('id', 'N/A')
            name = design.get('name', 'Unknown')[:24]
            score = design.get('score', 0)
            passed = design.get('passed', False)
            status = "✓ PASS" if passed else "✗ FAIL"

            cost_metrics = design.get('cost_metrics', {})
            total_cost = cost_metrics.get('total_construction_cost_usd', 0)

            env_metrics = design.get('environmental_metrics', {})
            eui = env_metrics.get('energy_use_intensity_kwh_sqm_year', 0)

            lines.append(
                f"{design_id:<6} {name:<25} {score:<10.1f} {status:<12} "
                f"${total_cost/1e6:<14.2f}M {eui:<12.1f}"
            )

        lines.append("-" * 100)
        lines.append("")

        # Detailed Results Table
        lines.append("DETAILED EVALUATION RESULTS")
        lines.append("=" * 100)

        for idx, design in enumerate(designs, 1):
            lines.append("")
            lines.append(f"DESIGN {idx}: {design.get('name', 'Unknown')}")
            lines.append("-" * 100)

            # Description
            lines.append(f"Description: {design.get('description', 'N/A')}")
            lines.append("")

            # Specifications
            specs = design.get('specifications', {})
            lines.append("Key Specifications:")
            lines.append(f"  • Total Floor Area: {specs.get('total_floor_area_sqm', 0):,.0f} sqm")
            lines.append(f"  • Number of Floors: {specs.get('num_floors', 0)}")
            lines.append(f"  • Solar Panels: {specs.get('solar_panel_area_sqm', 0):,.0f} sqm ({specs.get('solar_panel_capacity_kw', 0):.0f} kW)")
            lines.append(f"  • Green Roof: {specs.get('green_roof_area_sqm', 0):,.0f} sqm")
            lines.append(f"  • Window-to-Wall Ratio: {specs.get('window_to_wall_ratio', 0):.2f}")
            lines.append("")

            # Environmental Performance
            env = design.get('environmental_metrics', {})
            lines.append("Environmental Performance:")
            lines.append(f"  • Daylight Factor: {env.get('daylight_factor', 0):.3f} (Required: {constraints.required_daylight_factor})")
            lines.append(f"  • Energy Use Intensity: {env.get('energy_use_intensity_kwh_sqm_year', 0):.1f} kWh/sqm/year (Max: {constraints.max_energy_usage_kwh_sqm_year})")
            lines.append(f"  • Renewable Energy: {env.get('renewable_energy_percent', 0):.1f}%")
            lines.append(f"  • Annual Solar Generation: {env.get('annual_solar_generation_kwh', 0):,.0f} kWh")
            lines.append(f"  • Carbon Intensity: {env.get('carbon_intensity_kg_co2_sqm_year', 0):.2f} kg CO2/sqm/year")
            lines.append(f"  • Thermal Comfort Score: {env.get('thermal_comfort_score', 0):.1f}/100")
            lines.append("")

            # Cost Analysis
            cost = design.get('cost_metrics', {})
            lines.append("Cost Analysis:")
            lines.append(f"  • Total Construction Cost: ${cost.get('total_construction_cost_usd', 0):,.0f}")
            lines.append(f"  • Cost per sqm: ${cost.get('construction_cost_per_sqm_usd', 0):.2f}/sqm")
            lines.append(f"  • Budget Status: ${cost.get('total_construction_cost_usd', 0):,.0f} / ${constraints.budget_usd:,.0f} ({(cost.get('total_construction_cost_usd', 0)/constraints.budget_usd*100):.1f}%)")
            lines.append(f"  • Annual Operational Cost: ${cost.get('annual_operational_cost_usd', 0):,.0f}")
            lines.append(f"  • 30-Year Lifecycle Cost (NPV): ${cost.get('lifecycle_cost_30yr_npv_usd', 0):,.0f}")
            lines.append("")

            # Evaluation Scores
            lines.append("LLM Evaluation Scores:")
            lines.append(f"  • Completeness: {design.get('completeness_score', 0):.0f}/100")
            lines.append(f"  • Sustainability: {design.get('sustainability_score', 0):.0f}/100")
            lines.append(f"  • Cost-Effectiveness: {design.get('cost_effectiveness_score', 0):.0f}/100")
            lines.append(f"  • OVERALL SCORE: {design.get('score', 0):.1f}/100")
            lines.append("")

            # Pass/Fail
            passed = design.get('passed', False)
            status = "✓ PASS - RECOMMENDED" if passed else "✗ FAIL - NOT RECOMMENDED"
            lines.append(f"VERDICT: {status}")
            lines.append("")

            # Copilot Commentary
            commentary = design.get('copilot_commentary', 'No commentary available')
            lines.append("Copilot Studio Commentary:")
            lines.append(self._wrap_text(commentary, width=96, indent=2))
            lines.append("")
            lines.append("-" * 100)

        # Final Recommendation
        lines.append("")
        lines.append("FINAL RECOMMENDATION")
        lines.append("=" * 100)

        passing_designs = [d for d in designs if d.get('passed', False)]
        if passing_designs:
            # Sort by score
            best_design = max(passing_designs, key=lambda d: d.get('score', 0))
            lines.append(f"✓ {len(passing_designs)} design(s) meet all requirements.")
            lines.append(f"")
            lines.append(f"RECOMMENDED DESIGN: {best_design.get('name')}")
            lines.append(f"Overall Score: {best_design.get('score', 0):.1f}/100")
            lines.append(f"Cost: ${best_design.get('cost_metrics', {}).get('total_construction_cost_usd', 0):,.0f}")
        else:
            lines.append("✗ No designs meet all requirements. Review and adjust constraints.")

        lines.append("=" * 100)

        # Audit Trail Reference
        lines.append("")
        lines.append("AUDIT TRAIL REFERENCE")
        lines.append("-" * 100)
        lines.append(f"Session ID: {session_id}")
        lines.append(f"Audit Log: audit_trails/{session_id}_audit.jsonl")
        lines.append(f"All evaluations logged for Copilot Studio reproducibility and compliance")
        lines.append("=" * 100)

        return '\n'.join(lines)

    def _format_json_report(
        self,
        session_id: str,
        constraints: Any,
        designs: List[Any]
    ) -> str:
        """
        Format report as JSON.

        Args:
            session_id: Session identifier
            constraints: Building constraints
            designs: List of designs

        Returns:
            JSON formatted report
        """
        report = {
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "constraints": {
                "plot_size_acres": constraints.plot_size_acres,
                "location": constraints.location,
                "building_type": constraints.building_type,
                "max_floors": constraints.max_floors,
                "required_daylight_factor": constraints.required_daylight_factor,
                "max_energy_usage_kwh_sqm_year": constraints.max_energy_usage_kwh_sqm_year,
                "budget_usd": constraints.budget_usd
            },
            "designs": designs,
            "summary": {
                "total_designs": len(designs),
                "passing_designs": len([d for d in designs if d.get('passed', False)]),
                "failing_designs": len([d for d in designs if not d.get('passed', False)])
            }
        }

        return json.dumps(report, indent=2)

    def _format_markdown_report(
        self,
        session_id: str,
        constraints: Any,
        designs: List[Any]
    ) -> str:
        """
        Format report as Markdown.

        Args:
            session_id: Session identifier
            constraints: Building constraints
            designs: List of designs

        Returns:
            Markdown formatted report
        """
        lines = [
            "# Sustainable Building Design Evaluation Report",
            "",
            f"**Session ID:** {session_id}",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Location:** {constraints.location}",
            f"**Plot Size:** {constraints.plot_size_acres} acres",
            f"**Budget:** ${constraints.budget_usd:,.0f}",
            "",
            "## Design Alternatives Summary",
            "",
            "| Design | Score | Status | Cost (USD) | Energy (kWh/sqm/yr) |",
            "|--------|-------|--------|------------|---------------------|"
        ]

        for design in designs:
            name = design.get('name', 'Unknown')
            score = design.get('score', 0)
            status = "✓ PASS" if design.get('passed', False) else "✗ FAIL"
            cost = design.get('cost_metrics', {}).get('total_construction_cost_usd', 0)
            eui = design.get('environmental_metrics', {}).get('energy_use_intensity_kwh_sqm_year', 0)

            lines.append(f"| {name} | {score:.1f} | {status} | ${cost:,.0f} | {eui:.1f} |")

        lines.append("")
        lines.append("## Detailed Results")

        for design in designs:
            lines.append(f"")
            lines.append(f"### {design.get('name', 'Unknown')}")
            lines.append(f"")
            lines.append(f"**Description:** {design.get('description', 'N/A')}")
            lines.append(f"")
            lines.append(f"**Overall Score:** {design.get('score', 0):.1f}/100")
            lines.append(f"**Status:** {'✓ PASS' if design.get('passed', False) else '✗ FAIL'}")
            lines.append(f"")
            lines.append(f"**Copilot Commentary:**")
            lines.append(f"{design.get('copilot_commentary', 'N/A')}")
            lines.append(f"")

        return '\n'.join(lines)

    def _format_html_report(
        self,
        session_id: str,
        constraints: Any,
        designs: List[Any]
    ) -> str:
        """Format report as HTML (simplified version)"""
        return f"<html><body><h1>Report for session {session_id}</h1><p>See JSON or console format for full details</p></body></html>"

    def _wrap_text(self, text: str, width: int = 80, indent: int = 0) -> str:
        """
        Wrap text to specified width.

        Args:
            text: Text to wrap
            width: Maximum width
            indent: Indentation spaces

        Returns:
            Wrapped text
        """
        words = text.split()
        lines = []
        current_line = " " * indent

        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                current_line += word + " "
            else:
                lines.append(current_line.rstrip())
                current_line = " " * indent + word + " "

        if current_line.strip():
            lines.append(current_line.rstrip())

        return '\n'.join(lines)
