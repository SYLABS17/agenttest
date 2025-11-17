"""
Environmental Simulator Service
Simulates daylight exposure, energy usage, and environmental performance.
"""

import asyncio
import math
from typing import Dict, Any


class EnvironmentalSimulator:
    """
    Simulates environmental performance of building designs.
    Integrates daylight analysis, energy consumption, and sustainability metrics.
    """

    def __init__(self):
        """Initialize the environmental simulator"""
        # Bangalore climate data (approximate)
        self.location_data = {
            "latitude": 12.9716,
            "longitude": 77.5946,
            "avg_solar_radiation_kwh_sqm_day": 5.2,
            "avg_temperature_celsius": 24.0,
            "humidity_percent": 60.0,
            "cooling_degree_days": 2500,
            "heating_degree_days": 0
        }

    async def simulate(
        self,
        design: Dict[str, Any],
        constraints: Any
    ) -> Dict[str, float]:
        """
        Run complete environmental simulation for a design.

        Args:
            design: Building design specifications
            constraints: Building constraints

        Returns:
            Environmental performance metrics
        """
        specs = design["specifications"]

        # Run simulations in parallel
        daylight_metrics = await self._simulate_daylight(specs)
        energy_metrics = await self._simulate_energy_usage(specs, design["configuration"])
        carbon_metrics = await self._simulate_carbon_footprint(specs, energy_metrics)
        comfort_metrics = await self._simulate_thermal_comfort(specs)

        # Combine all metrics
        return {
            **daylight_metrics,
            **energy_metrics,
            **carbon_metrics,
            **comfort_metrics
        }

    async def _simulate_daylight(self, specs: Dict[str, Any]) -> Dict[str, float]:
        """
        Simulate daylight exposure and availability.

        Args:
            specs: Building specifications

        Returns:
            Daylight performance metrics
        """
        # Simulate daylight calculation
        await asyncio.sleep(0.1)  # Simulate processing time

        # Calculate daylight factor based on window-to-wall ratio and design features
        base_daylight_factor = specs["window_to_wall_ratio"] * 0.6

        # Adjust for special features
        if specs.get("light_wells_count"):
            base_daylight_factor += 0.05 * specs["light_wells_count"]

        if specs.get("clerestory_window_area_sqm"):
            base_daylight_factor += 0.08

        if specs.get("facade_type") == "double_skin_facade":
            base_daylight_factor += 0.05

        # Adjust for building orientation
        orientation_factors = {
            "south_facing": 1.15,
            "north_south": 1.10,
            "east_west": 1.05,
            "optimized": 1.12,
            "default": 1.0
        }
        orientation = specs.get("building_orientation", "default")
        daylight_factor = base_daylight_factor * orientation_factors.get(orientation, 1.0)

        # Calculate useful daylight illuminance (UDI)
        udi_percentage = min(95, daylight_factor * 150)

        # Calculate daylight autonomy
        daylight_autonomy = min(85, daylight_factor * 140)

        return {
            "daylight_factor": round(daylight_factor, 3),
            "useful_daylight_illuminance_percent": round(udi_percentage, 1),
            "daylight_autonomy_percent": round(daylight_autonomy, 1),
            "annual_sunlight_exposure_hours": round(
                self.location_data["avg_solar_radiation_kwh_sqm_day"] * 365 / 5.0 * daylight_factor,
                1
            )
        }

    async def _simulate_energy_usage(
        self,
        specs: Dict[str, Any],
        configuration: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Simulate annual energy consumption and generation.

        Args:
            specs: Building specifications
            configuration: Design configuration

        Returns:
            Energy performance metrics
        """
        await asyncio.sleep(0.1)  # Simulate processing time

        total_floor_area = specs["total_floor_area_sqm"]

        # Base energy consumption (kWh/sqm/year)
        base_consumption = 120.0  # Typical office building in Bangalore

        # Adjustments for sustainable features

        # 1. Solar panel generation
        solar_capacity_kw = specs.get("solar_panel_capacity_kw", 0)
        annual_solar_generation_kwh = (
            solar_capacity_kw *
            self.location_data["avg_solar_radiation_kwh_sqm_day"] *
            365 *
            0.75  # Performance ratio
        )

        # 2. Green roof cooling benefit (reduces cooling load)
        green_roof_area = specs.get("green_roof_area_sqm", 0)
        green_roof_savings_percent = min(15, (green_roof_area / specs["building_footprint_sqm"]) * 20)

        # 3. Glazing efficiency
        glazing_savings_percent = 12  # Low-E triple glazing

        # 4. LED and daylight sensors
        lighting_savings_percent = 30

        # 5. Efficient HVAC
        hvac_savings_percent = 25

        # 6. Building orientation
        orientation_savings = {
            "south_facing": 8,
            "north_south": 10,
            "east_west": 6,
            "optimized": 12,
            "default": 0
        }
        orientation = specs.get("building_orientation", "default")
        orientation_savings_percent = orientation_savings.get(orientation, 0)

        # Calculate total savings
        total_savings_percent = (
            green_roof_savings_percent * 0.3 +  # Cooling is 30% of total
            glazing_savings_percent * 0.3 +     # Envelope efficiency
            lighting_savings_percent * 0.2 +     # Lighting
            hvac_savings_percent * 0.4 +         # HVAC
            orientation_savings_percent * 0.1    # Orientation
        )

        # Net energy consumption
        net_consumption_kwh_sqm_year = base_consumption * (1 - total_savings_percent / 100)
        total_consumption_kwh_year = net_consumption_kwh_sqm_year * total_floor_area

        # Net energy after solar generation
        net_energy_consumption_kwh_year = max(0, total_consumption_kwh_year - annual_solar_generation_kwh)
        net_energy_consumption_kwh_sqm_year = net_energy_consumption_kwh_year / total_floor_area

        # Energy Use Intensity (EUI)
        eui = net_energy_consumption_kwh_sqm_year

        # Renewable energy percentage
        renewable_energy_percent = min(100, (annual_solar_generation_kwh / total_consumption_kwh_year) * 100)

        return {
            "annual_energy_consumption_kwh": round(total_consumption_kwh_year, 0),
            "annual_solar_generation_kwh": round(annual_solar_generation_kwh, 0),
            "net_energy_consumption_kwh": round(net_energy_consumption_kwh_year, 0),
            "energy_use_intensity_kwh_sqm_year": round(eui, 2),
            "renewable_energy_percent": round(renewable_energy_percent, 1),
            "energy_savings_percent": round(total_savings_percent, 1),
            "estimated_annual_energy_cost_usd": round(net_energy_consumption_kwh_year * 0.12, 0)  # $0.12/kWh
        }

    async def _simulate_carbon_footprint(
        self,
        specs: Dict[str, Any],
        energy_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate carbon footprint and emissions.

        Args:
            specs: Building specifications
            energy_metrics: Energy usage metrics

        Returns:
            Carbon footprint metrics
        """
        await asyncio.sleep(0.05)  # Simulate processing time

        # India grid carbon intensity (kg CO2/kWh)
        grid_carbon_intensity = 0.82

        # Operational carbon (annual)
        net_energy_kwh = energy_metrics["net_energy_consumption_kwh"]
        operational_carbon_kg_year = net_energy_kwh * grid_carbon_intensity

        # Embodied carbon (one-time, amortized over 50 years)
        total_floor_area = specs["total_floor_area_sqm"]

        # Base embodied carbon for recycled steel structure
        base_embodied_carbon_kg_sqm = 180  # Lower than conventional (250-300)

        # Adjustments for sustainable materials
        bamboo_area = specs.get("bamboo_flooring_sqm", 0) + specs.get("bamboo_facade_elements_sqm", 0)
        bamboo_savings_kg = bamboo_area * 15  # Bamboo saves ~15 kg CO2/sqm vs conventional

        green_roof_carbon_kg = specs.get("green_roof_area_sqm", 0) * 5  # Green roofs sequester carbon

        # Total embodied carbon
        embodied_carbon_total_kg = total_floor_area * base_embodied_carbon_kg_sqm - bamboo_savings_kg
        embodied_carbon_annual_kg = embodied_carbon_total_kg / 50  # Amortized over 50 years

        # Carbon sequestration from green features
        annual_carbon_sequestration_kg = green_roof_carbon_kg * 2  # Annual sequestration

        # Total carbon impact
        total_carbon_impact_kg_year = (
            operational_carbon_kg_year +
            embodied_carbon_annual_kg -
            annual_carbon_sequestration_kg
        )

        return {
            "operational_carbon_kg_co2_year": round(operational_carbon_kg_year, 0),
            "embodied_carbon_kg_co2_year": round(embodied_carbon_annual_kg, 0),
            "carbon_sequestration_kg_co2_year": round(annual_carbon_sequestration_kg, 0),
            "total_carbon_impact_kg_co2_year": round(total_carbon_impact_kg_year, 0),
            "carbon_intensity_kg_co2_sqm_year": round(total_carbon_impact_kg_year / total_floor_area, 2)
        }

    async def _simulate_thermal_comfort(self, specs: Dict[str, Any]) -> Dict[str, float]:
        """
        Simulate thermal comfort performance.

        Args:
            specs: Building specifications

        Returns:
            Thermal comfort metrics
        """
        await asyncio.sleep(0.05)  # Simulate processing time

        # Base comfort score
        base_comfort = 70

        # Adjustments
        green_roof_bonus = (specs.get("green_roof_area_sqm", 0) / specs["building_footprint_sqm"]) * 5
        glazing_bonus = 8  # Triple glazing
        hvac_bonus = 10  # VRF with heat recovery

        if specs.get("vertical_garden_area_sqm"):
            biophilic_bonus = 5
        else:
            biophilic_bonus = 0

        thermal_comfort_score = min(95, base_comfort + green_roof_bonus + glazing_bonus + hvac_bonus + biophilic_bonus)

        # PMV/PPD calculations (simplified)
        predicted_mean_vote = 0.2  # Near neutral (0)
        predicted_percentage_dissatisfied = 8  # Good comfort

        return {
            "thermal_comfort_score": round(thermal_comfort_score, 1),
            "predicted_mean_vote": round(predicted_mean_vote, 2),
            "predicted_percentage_dissatisfied": round(predicted_percentage_dissatisfied, 1),
            "adaptive_comfort_compliance_percent": round(min(95, thermal_comfort_score), 1)
        }
