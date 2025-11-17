"""
Cost Analyzer Service
Analyzes construction and operational costs for building designs.
"""

import asyncio
from typing import Dict, Any, List


class CostAnalyzer:
    """
    Analyzes costs for sustainable building designs.
    Includes material costs, construction costs, and lifecycle costs.
    """

    def __init__(self):
        """Initialize the cost analyzer with price database"""
        self.material_costs_usd = self._initialize_material_costs()
        self.labor_rate_usd_hour = 25.0  # Bangalore construction labor rate
        self.markup_percent = 25.0  # Contractor markup

    def _initialize_material_costs(self) -> Dict[str, float]:
        """
        Initialize material cost database (USD per unit).

        Returns:
            Dictionary of material costs
        """
        return {
            # Structural materials (per sqm)
            "recycled_steel": 85.0,
            "concrete": 120.0,
            "cross_laminated_timber": 180.0,
            "recycled_aluminum": 95.0,

            # Roofing (per sqm)
            "solar_panels": 250.0,
            "green_roof": 120.0,
            "reflective_roof_coating": 15.0,

            # Facade and glazing (per sqm)
            "low_e_glass": 180.0,
            "double_skin_facade": 350.0,
            "standard_facade": 120.0,
            "bamboo_facade_elements": 95.0,

            # Flooring (per sqm)
            "bamboo_flooring": 55.0,
            "recycled_content_tiles": 45.0,

            # Insulation (per sqm)
            "bio_based_insulation": 35.0,

            # MEP Systems (per sqm of floor area)
            "vrf_hvac_system": 85.0,
            "led_lighting_system": 40.0,
            "rainwater_harvesting": 25.0,

            # Special features (per sqm or per unit)
            "vertical_garden_system": 200.0,
            "light_shelf_system": 75.0,
            "electrochromic_glazing": 450.0,
            "living_wall_system": 220.0,

            # Site work (per sqm of plot)
            "permeable_paving": 55.0,
            "landscaping": 30.0
        }

    async def analyze(
        self,
        design: Dict[str, Any],
        constraints: Any
    ) -> Dict[str, float]:
        """
        Perform complete cost analysis for a design.

        Args:
            design: Building design specifications
            constraints: Building constraints

        Returns:
            Cost analysis metrics
        """
        specs = design["specifications"]
        materials = design.get("materials", [])

        # Run cost analyses
        construction_costs = await self._calculate_construction_costs(specs, materials)
        operational_costs = await self._calculate_operational_costs(specs)
        lifecycle_costs = await self._calculate_lifecycle_costs(
            construction_costs,
            operational_costs
        )

        return {
            **construction_costs,
            **operational_costs,
            **lifecycle_costs
        }

    async def _calculate_construction_costs(
        self,
        specs: Dict[str, Any],
        materials: List[str]
    ) -> Dict[str, float]:
        """
        Calculate construction costs.

        Args:
            specs: Building specifications
            materials: List of materials used

        Returns:
            Construction cost breakdown
        """
        await asyncio.sleep(0.1)  # Simulate processing time

        costs = {}
        total_floor_area = specs["total_floor_area_sqm"]
        building_footprint = specs["building_footprint_sqm"]

        # 1. Structural costs
        structural_cost = total_floor_area * self.material_costs_usd["recycled_steel"] * 0.8
        costs["structural_cost_usd"] = structural_cost

        # 2. Facade costs
        facade_type = specs.get("facade_type", "standard_facade")
        facade_area = total_floor_area * 0.4  # Approximate facade area
        facade_cost_per_sqm = self.material_costs_usd.get(facade_type, 120.0)
        facade_cost = facade_area * facade_cost_per_sqm
        costs["facade_cost_usd"] = facade_cost

        # 3. Glazing costs
        window_area = facade_area * specs["window_to_wall_ratio"]
        glazing_cost = window_area * self.material_costs_usd["low_e_glass"]
        costs["glazing_cost_usd"] = glazing_cost

        # 4. Roofing costs
        solar_panel_area = specs.get("solar_panel_area_sqm", 0)
        green_roof_area = specs.get("green_roof_area_sqm", 0)

        solar_panel_cost = solar_panel_area * self.material_costs_usd["solar_panels"]
        green_roof_cost = green_roof_area * self.material_costs_usd["green_roof"]

        # Remaining roof area (standard roofing)
        remaining_roof = building_footprint - solar_panel_area - green_roof_area
        standard_roof_cost = max(0, remaining_roof * 45.0)

        roofing_cost = solar_panel_cost + green_roof_cost + standard_roof_cost
        costs["roofing_cost_usd"] = roofing_cost
        costs["solar_panel_cost_usd"] = solar_panel_cost
        costs["green_roof_cost_usd"] = green_roof_cost

        # 5. Bamboo costs
        bamboo_flooring_area = specs.get("bamboo_flooring_sqm", 0)
        bamboo_facade_area = specs.get("bamboo_facade_elements_sqm", 0)
        bamboo_cost = (
            bamboo_flooring_area * self.material_costs_usd["bamboo_flooring"] +
            bamboo_facade_area * self.material_costs_usd["bamboo_facade_elements"]
        )
        costs["bamboo_cost_usd"] = bamboo_cost

        # 6. MEP systems
        hvac_cost = total_floor_area * self.material_costs_usd["vrf_hvac_system"]
        lighting_cost = total_floor_area * self.material_costs_usd["led_lighting_system"]
        mep_cost = hvac_cost + lighting_cost

        # Water systems
        if specs.get("water_system") == "rainwater_harvesting":
            water_system_cost = total_floor_area * self.material_costs_usd["rainwater_harvesting"]
            mep_cost += water_system_cost

        costs["mep_systems_cost_usd"] = mep_cost

        # 7. Special features
        special_features_cost = 0

        if specs.get("vertical_garden_area_sqm"):
            special_features_cost += (
                specs["vertical_garden_area_sqm"] *
                self.material_costs_usd["vertical_garden_system"]
            )

        if specs.get("light_wells_count"):
            special_features_cost += specs["light_wells_count"] * 25000  # Per light well

        if specs.get("clerestory_window_area_sqm"):
            special_features_cost += (
                specs["clerestory_window_area_sqm"] *
                self.material_costs_usd["low_e_glass"] * 1.3  # Premium for clerestory
            )

        costs["special_features_cost_usd"] = special_features_cost

        # 8. Site work
        plot_area = specs["plot_area_sqm"]
        site_work_cost = plot_area * 40.0  # Basic site preparation
        costs["site_work_cost_usd"] = site_work_cost

        # 9. Labor costs (typically 40% of material costs in India)
        material_subtotal = sum([
            costs.get("structural_cost_usd", 0),
            costs.get("facade_cost_usd", 0),
            costs.get("glazing_cost_usd", 0),
            costs.get("roofing_cost_usd", 0),
            costs.get("bamboo_cost_usd", 0),
            costs.get("mep_systems_cost_usd", 0),
            costs.get("special_features_cost_usd", 0),
            costs.get("site_work_cost_usd", 0)
        ])

        labor_cost = material_subtotal * 0.40
        costs["labor_cost_usd"] = labor_cost

        # 10. Contractor markup
        subtotal = material_subtotal + labor_cost
        markup = subtotal * (self.markup_percent / 100)
        costs["contractor_markup_usd"] = markup

        # 11. Contingency (10%)
        contingency = subtotal * 0.10
        costs["contingency_usd"] = contingency

        # Total construction cost
        total_construction_cost = subtotal + markup + contingency
        costs["total_construction_cost_usd"] = round(total_construction_cost, 0)

        # Cost per square meter
        costs["construction_cost_per_sqm_usd"] = round(
            total_construction_cost / total_floor_area,
            2
        )

        # Round all costs
        for key in costs:
            if key != "construction_cost_per_sqm_usd":
                costs[key] = round(costs[key], 0)

        return costs

    async def _calculate_operational_costs(
        self,
        specs: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate annual operational costs.

        Args:
            specs: Building specifications

        Returns:
            Operational cost metrics
        """
        await asyncio.sleep(0.05)  # Simulate processing time

        total_floor_area = specs["total_floor_area_sqm"]

        # Annual costs per sqm (USD)
        maintenance_cost_sqm = 8.0
        cleaning_cost_sqm = 6.0
        insurance_cost_sqm = 4.0
        management_cost_sqm = 5.0

        annual_maintenance_cost = total_floor_area * maintenance_cost_sqm
        annual_cleaning_cost = total_floor_area * cleaning_cost_sqm
        annual_insurance_cost = total_floor_area * insurance_cost_sqm
        annual_management_cost = total_floor_area * management_cost_sqm

        # Green roof and solar panel maintenance
        green_roof_maintenance = specs.get("green_roof_area_sqm", 0) * 5.0
        solar_panel_maintenance = specs.get("solar_panel_area_sqm", 0) * 8.0

        total_annual_operational_cost = (
            annual_maintenance_cost +
            annual_cleaning_cost +
            annual_insurance_cost +
            annual_management_cost +
            green_roof_maintenance +
            solar_panel_maintenance
        )

        return {
            "annual_maintenance_cost_usd": round(annual_maintenance_cost, 0),
            "annual_operational_cost_usd": round(total_annual_operational_cost, 0),
            "operational_cost_per_sqm_usd": round(total_annual_operational_cost / total_floor_area, 2)
        }

    async def _calculate_lifecycle_costs(
        self,
        construction_costs: Dict[str, float],
        operational_costs: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate lifecycle costs (30-year analysis).

        Args:
            construction_costs: Construction cost breakdown
            operational_costs: Operational cost breakdown

        Returns:
            Lifecycle cost metrics
        """
        await asyncio.sleep(0.05)  # Simulate processing time

        analysis_period_years = 30
        discount_rate = 0.05

        # Initial construction cost
        initial_cost = construction_costs["total_construction_cost_usd"]

        # Annual operational costs
        annual_operational = operational_costs["annual_operational_cost_usd"]

        # Calculate NPV of operational costs
        npv_operational = 0
        for year in range(1, analysis_period_years + 1):
            npv_operational += annual_operational / ((1 + discount_rate) ** year)

        # Major replacements (simplified)
        # Solar panels replacement at year 25
        solar_panel_replacement_cost = construction_costs.get("solar_panel_cost_usd", 0) * 0.8
        npv_replacement = solar_panel_replacement_cost / ((1 + discount_rate) ** 25)

        # Total lifecycle cost
        total_lifecycle_cost = initial_cost + npv_operational + npv_replacement

        return {
            "lifecycle_cost_30yr_npv_usd": round(total_lifecycle_cost, 0),
            "lifecycle_cost_per_year_usd": round(total_lifecycle_cost / analysis_period_years, 0),
            "payback_period_years": round(
                initial_cost / max(1, annual_operational * 0.2),  # Simplified payback
                1
            )
        }
