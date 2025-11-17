"""
LLM Evaluator Service
Uses Azure OpenAI / Copilot Studio to evaluate building designs.
Implements Copilot Studio Prompt Builder patterns for structured evaluation.
"""

import asyncio
import json
from typing import Dict, Any, Optional


class LLMEvaluator:
    """
    LLM-based evaluator for building designs.
    Uses Copilot Studio Prompt Builder patterns with Azure AI Foundry.
    """

    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None
    ):
        """
        Initialize the LLM evaluator.

        Args:
            azure_endpoint: Azure AI endpoint
            azure_api_key: Azure AI API key
        """
        self.azure_endpoint = azure_endpoint
        self.azure_api_key = azure_api_key

        # Evaluation criteria weights
        self.evaluation_criteria = {
            "completeness": 0.25,
            "sustainability": 0.40,
            "cost_effectiveness": 0.35
        }

        # Thresholds for pass/fail
        self.pass_threshold = 70.0  # Minimum score of 70/100

    async def evaluate_design(
        self,
        design: Any,
        constraints: Any
    ) -> Dict[str, Any]:
        """
        Evaluate a building design using LLM.

        Args:
            design: Design alternative to evaluate
            constraints: Building constraints

        Returns:
            Evaluation results with scores and commentary
        """
        # Prepare evaluation prompt using Copilot Studio Prompt Builder pattern
        prompt = self._build_evaluation_prompt(design, constraints)

        # Execute LLM evaluation (simulated with rule-based logic for this implementation)
        # In production, this would call Azure OpenAI via the AI Foundry SDK
        evaluation_result = await self._execute_llm_evaluation(prompt, design, constraints)

        return evaluation_result

    def _build_evaluation_prompt(
        self,
        design: Any,
        constraints: Any
    ) -> str:
        """
        Build evaluation prompt using Copilot Studio Prompt Builder pattern.

        Args:
            design: Design alternative
            constraints: Building constraints

        Returns:
            Structured evaluation prompt
        """
        prompt = f"""
# Building Design Evaluation Task

You are an expert sustainable building design evaluator. Evaluate the following office building design for a 1-acre urban plot in Bangalore, India.

## Design to Evaluate:
**Name:** {design.name}
**Description:** {design.description}

### Specifications:
- Total Floor Area: {design.specifications.get('total_floor_area_sqm', 0):.0f} sqm
- Number of Floors: {design.specifications.get('num_floors', 0)}
- Solar Panel Area: {design.specifications.get('solar_panel_area_sqm', 0):.0f} sqm
- Green Roof Area: {design.specifications.get('green_roof_area_sqm', 0):.0f} sqm
- Window-to-Wall Ratio: {design.specifications.get('window_to_wall_ratio', 0):.2f}

### Environmental Performance:
- Daylight Factor: {design.environmental_metrics.get('daylight_factor', 0):.3f}
- Energy Use Intensity: {design.environmental_metrics.get('energy_use_intensity_kwh_sqm_year', 0):.1f} kWh/sqm/year
- Renewable Energy: {design.environmental_metrics.get('renewable_energy_percent', 0):.1f}%
- Carbon Intensity: {design.environmental_metrics.get('carbon_intensity_kg_co2_sqm_year', 0):.2f} kg CO2/sqm/year

### Cost Metrics:
- Total Construction Cost: ${design.cost_metrics.get('total_construction_cost_usd', 0):,.0f}
- Cost per sqm: ${design.cost_metrics.get('construction_cost_per_sqm_usd', 0):.2f}/sqm
- Budget: ${constraints.budget_usd:,.0f}

### Materials Used:
{', '.join(design.materials_used)}

## Evaluation Criteria:

### 1. Completeness (25 points)
- Are all required eco-friendly materials included? (solar panels, green roof, recycled steel, bamboo)
- Is the design specification complete and detailed?
- Are all building systems properly specified?

### 2. Sustainability (40 points)
- Daylight exposure: Does it meet the minimum daylight factor of {constraints.required_daylight_factor}?
- Energy efficiency: Does it meet the max energy usage of {constraints.max_energy_usage_kwh_sqm_year} kWh/sqm/year?
- Use of eco-friendly materials: Quality and quantity
- Carbon footprint: How low is the carbon intensity?
- Renewable energy generation: Percentage of energy from renewables

### 3. Cost Effectiveness (35 points)
- Budget compliance: Does it stay within ${constraints.budget_usd:,.0f}?
- Value for money: Balance between features and cost
- Lifecycle cost efficiency
- Return on investment for sustainable features

## Required Output Format:
Provide scores (0-100) for each criterion and an overall score. Include pass/fail recommendation and detailed commentary.
"""
        return prompt

    async def _execute_llm_evaluation(
        self,
        prompt: str,
        design: Any,
        constraints: Any
    ) -> Dict[str, Any]:
        """
        Execute LLM evaluation (simulated with intelligent rule-based scoring).

        In production, this would call Azure OpenAI via AI Foundry SDK:
        ```python
        from azure.ai.projects import AIProjectsClient
        from azure.identity import DefaultAzureCredential

        client = AIProjectsClient(
            credential=DefaultAzureCredential(),
            endpoint=self.azure_endpoint
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        ```

        Args:
            prompt: Evaluation prompt
            design: Design alternative
            constraints: Building constraints

        Returns:
            Evaluation results
        """
        await asyncio.sleep(0.2)  # Simulate LLM processing time

        # Simulate LLM evaluation with rule-based scoring
        scores = await self._calculate_scores(design, constraints)

        # Generate Copilot commentary
        commentary = self._generate_copilot_commentary(design, scores, constraints)

        # Calculate overall score
        overall_score = (
            scores["completeness"] * self.evaluation_criteria["completeness"] +
            scores["sustainability"] * self.evaluation_criteria["sustainability"] +
            scores["cost_effectiveness"] * self.evaluation_criteria["cost_effectiveness"]
        )

        # Pass/fail determination
        passed = overall_score >= self.pass_threshold

        return {
            "completeness_score": scores["completeness"],
            "sustainability_score": scores["sustainability"],
            "cost_effectiveness_score": scores["cost_effectiveness"],
            "overall_score": round(overall_score, 1),
            "passed": passed,
            "copilot_commentary": commentary,
            "evaluation_details": scores.get("details", {})
        }

    async def _calculate_scores(
        self,
        design: Any,
        constraints: Any
    ) -> Dict[str, float]:
        """
        Calculate evaluation scores based on metrics.

        Args:
            design: Design alternative
            constraints: Building constraints

        Returns:
            Score breakdown
        """
        scores = {}
        details = {}

        # 1. COMPLETENESS SCORE (0-100)
        completeness_score = 0
        required_materials = set(constraints.required_materials)
        design_materials = set(design.materials_used)

        # Check required materials (15 points)
        materials_present = required_materials.intersection(design_materials)
        material_score = (len(materials_present) / len(required_materials)) * 15
        completeness_score += material_score

        # Specification completeness (10 points)
        spec_count = len([v for v in design.specifications.values() if v])
        spec_score = min(10, spec_count / 2)
        completeness_score += spec_score

        scores["completeness"] = min(100, completeness_score * 4)  # Scale to 100
        details["materials_coverage"] = f"{len(materials_present)}/{len(required_materials)}"

        # 2. SUSTAINABILITY SCORE (0-100)
        sustainability_score = 0

        # Daylight factor (20 points)
        daylight_factor = design.environmental_metrics.get("daylight_factor", 0)
        if daylight_factor >= constraints.required_daylight_factor:
            daylight_score = 20
            if daylight_factor >= constraints.required_daylight_factor * 1.5:
                daylight_score = 25  # Bonus for exceeding
        else:
            # Partial credit
            daylight_score = (daylight_factor / constraints.required_daylight_factor) * 15

        sustainability_score += daylight_score
        details["daylight_compliance"] = daylight_factor >= constraints.required_daylight_factor

        # Energy efficiency (25 points)
        eui = design.environmental_metrics.get("energy_use_intensity_kwh_sqm_year", 999)
        if eui <= constraints.max_energy_usage_kwh_sqm_year:
            energy_score = 25
            # Bonus for being much better
            if eui <= constraints.max_energy_usage_kwh_sqm_year * 0.7:
                energy_score = 30
        else:
            # Penalty for exceeding
            energy_score = max(0, 25 - (eui - constraints.max_energy_usage_kwh_sqm_year) / 10)

        sustainability_score += energy_score
        details["energy_compliance"] = eui <= constraints.max_energy_usage_kwh_sqm_year

        # Renewable energy (20 points)
        renewable_pct = design.environmental_metrics.get("renewable_energy_percent", 0)
        renewable_score = min(20, renewable_pct / 5)
        sustainability_score += renewable_score

        # Carbon footprint (20 points)
        carbon_intensity = design.environmental_metrics.get("carbon_intensity_kg_co2_sqm_year", 100)
        # Lower is better, score based on range 0-50 kg/sqm/year
        carbon_score = max(0, 20 - (carbon_intensity / 2.5))
        sustainability_score += carbon_score

        # Eco-materials diversity (15 points)
        eco_material_count = len(design.materials_used)
        material_diversity_score = min(15, eco_material_count)
        sustainability_score += material_diversity_score

        scores["sustainability"] = min(100, sustainability_score)
        details["renewable_energy_percent"] = renewable_pct
        details["carbon_intensity"] = carbon_intensity

        # 3. COST EFFECTIVENESS SCORE (0-100)
        cost_effectiveness_score = 0

        # Budget compliance (40 points)
        total_cost = design.cost_metrics.get("total_construction_cost_usd", 0)
        if total_cost <= constraints.budget_usd:
            # Full points if within budget
            budget_score = 40
            # Bonus for being well under budget
            if total_cost <= constraints.budget_usd * 0.85:
                budget_score = 45
        else:
            # Penalty for over budget
            overage_pct = ((total_cost - constraints.budget_usd) / constraints.budget_usd) * 100
            budget_score = max(0, 40 - overage_pct)

        cost_effectiveness_score += budget_score
        details["budget_compliance"] = total_cost <= constraints.budget_usd
        details["budget_utilization_pct"] = round((total_cost / constraints.budget_usd) * 100, 1)

        # Value for money (30 points)
        # Consider cost per sqm vs sustainability score
        cost_per_sqm = design.cost_metrics.get("construction_cost_per_sqm_usd", 9999)
        # Good value: $1200-1800/sqm for sustainable building in India
        if 1200 <= cost_per_sqm <= 1800:
            value_score = 30
        elif cost_per_sqm < 1200:
            value_score = 25  # Too cheap might compromise quality
        else:
            # Penalty for expensive
            value_score = max(0, 30 - (cost_per_sqm - 1800) / 50)

        cost_effectiveness_score += value_score

        # Lifecycle efficiency (30 points)
        lifecycle_cost_per_year = design.cost_metrics.get("lifecycle_cost_per_year_usd", 999999)
        # Good lifecycle cost: < $200k/year for this size building
        if lifecycle_cost_per_year < 200000:
            lifecycle_score = 30
        else:
            lifecycle_score = max(0, 30 - (lifecycle_cost_per_year - 200000) / 10000)

        cost_effectiveness_score += lifecycle_score

        scores["cost_effectiveness"] = min(100, cost_effectiveness_score)
        details["cost_per_sqm"] = cost_per_sqm

        scores["details"] = details
        return scores

    def _generate_copilot_commentary(
        self,
        design: Any,
        scores: Dict[str, float],
        constraints: Any
    ) -> str:
        """
        Generate Copilot-style commentary for the design evaluation.

        Args:
            design: Design alternative
            scores: Calculated scores
            constraints: Building constraints

        Returns:
            Human-readable commentary
        """
        details = scores.get("details", {})

        commentary_parts = []

        # Overall assessment
        overall_score = (
            scores["completeness"] * self.evaluation_criteria["completeness"] +
            scores["sustainability"] * self.evaluation_criteria["sustainability"] +
            scores["cost_effectiveness"] * self.evaluation_criteria["cost_effectiveness"]
        )

        if overall_score >= 85:
            commentary_parts.append("EXCELLENT design with outstanding performance across all criteria.")
        elif overall_score >= 70:
            commentary_parts.append("GOOD design that meets requirements with solid performance.")
        elif overall_score >= 60:
            commentary_parts.append("ACCEPTABLE design but with room for improvement.")
        else:
            commentary_parts.append("NEEDS IMPROVEMENT to meet project requirements.")

        # Completeness commentary
        materials_coverage = details.get("materials_coverage", "N/A")
        commentary_parts.append(
            f"Completeness: {scores['completeness']:.0f}/100. "
            f"Required eco-materials coverage: {materials_coverage}."
        )

        # Sustainability commentary
        if scores["sustainability"] >= 80:
            sustainability_comment = "Strong sustainability performance"
        elif scores["sustainability"] >= 60:
            sustainability_comment = "Moderate sustainability performance"
        else:
            sustainability_comment = "Sustainability needs enhancement"

        daylight_status = "meets" if details.get("daylight_compliance") else "does not meet"
        energy_status = "meets" if details.get("energy_compliance") else "exceeds"

        commentary_parts.append(
            f"Sustainability: {scores['sustainability']:.0f}/100. {sustainability_comment}. "
            f"Design {daylight_status} daylight requirements and {energy_status} energy limits. "
            f"Renewable energy contribution: {details.get('renewable_energy_percent', 0):.1f}%."
        )

        # Cost effectiveness commentary
        budget_status = "within budget" if details.get("budget_compliance") else "over budget"
        budget_util = details.get("budget_utilization_pct", 0)

        commentary_parts.append(
            f"Cost-Effectiveness: {scores['cost_effectiveness']:.0f}/100. "
            f"Design is {budget_status} ({budget_util:.1f}% of allocated budget). "
            f"Construction cost: ${details.get('cost_per_sqm', 0):.0f}/sqm."
        )

        # Recommendations
        if overall_score < 70:
            commentary_parts.append(
                "RECOMMENDATION: Consider optimizing the design to improve weak areas before proceeding."
            )
        elif overall_score < 85:
            commentary_parts.append(
                "RECOMMENDATION: Design is viable with minor improvements in identified areas."
            )
        else:
            commentary_parts.append(
                "RECOMMENDATION: Proceed with this excellent design."
            )

        return " ".join(commentary_parts)
