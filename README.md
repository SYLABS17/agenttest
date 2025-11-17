# Sustainable Building Design Agent

AI-powered agent for generating and evaluating sustainable office building designs using Microsoft Agent Framework and Azure AI Foundry.

## Overview

This project implements an intelligent agent that generates four sustainable office building design alternatives for a 1-acre urban plot in Bangalore, India. The agent uses Microsoft Agent Framework patterns with Azure AI Foundry to orchestrate design generation, environmental simulation, cost analysis, and LLM-based evaluation.

### Key Features

- **4 Design Alternatives**: Generates distinct sustainable building designs with different optimization strategies
- **Environmental Simulation**: Analyzes daylight exposure, energy usage, and carbon footprint
- **Cost Analysis**: Complete construction and lifecycle cost analysis
- **LLM Evaluation**: Uses Copilot Studio Prompt Builder patterns for scoring designs
- **Eco-Friendly Materials**: Integrates solar panels, green roofs, recycled steel, and bamboo
- **Copilot Studio Integration**: Interactive constraint modification for business users
- **Audit Trail**: Complete reproducibility and compliance logging

## Project Structure

```
agenttest/
├── src/
│   ├── agents/                      # AI agent orchestrators
│   │   └── sustainable_building_agent.py
│   ├── services/                    # Core services
│   │   ├── design_generator.py      # Design generation
│   │   ├── environmental_simulator.py # Daylight & energy simulation
│   │   ├── cost_analyzer.py         # Cost analysis
│   │   └── llm_evaluator.py         # LLM-based evaluation
│   ├── connectors/                  # Copilot Studio connectors
│   │   └── copilot_studio_connector.py
│   ├── utils/                       # Utilities
│   │   ├── audit_logger.py          # Audit trail logging
│   │   └── output_formatter.py      # Report formatting
│   └── main.py                      # Main entry point
├── config/                          # Configuration files
│   └── azure_config.yaml
├── outputs/                         # Generated reports
├── audit_trails/                    # Audit logs
├── requirements.txt                 # Python dependencies
├── package.json                     # Project metadata
├── .env.example                     # Environment variables template
├── CLAUDE.md                        # AI assistant guide
└── README.md                        # This file
```

## Installation

### Prerequisites

- Python 3.9 or higher
- Azure AI Foundry account (optional for LLM features)
- pip package manager

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/SYLABS17/agenttest.git
cd agenttest
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Azure AI (optional)**
```bash
cp .env.example .env
# Edit .env with your Azure AI credentials
```

## Usage

### Run Standard Workflow

Generate designs and evaluations with default settings:

```bash
python src/main.py
```

This will:
1. Initialize the agent
2. Generate 4 sustainable building designs
3. Run environmental simulations (daylight, energy, carbon)
4. Perform cost analysis
5. Evaluate designs using LLM
6. Generate comprehensive report with pass/fail recommendations

### Run Copilot Studio Server

Start the API server for Copilot Studio integration:

```bash
python src/main.py --server
```

The server will be available at:
- API: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- Schema: `http://localhost:8000/schema/openapi.json`

### Interactive Use

```python
import asyncio
from src.agents.sustainable_building_agent import (
    SustainableBuildingAgent,
    BuildingConstraints
)

async def custom_run():
    agent = SustainableBuildingAgent()

    # Custom constraints
    constraints = BuildingConstraints(
        plot_size_acres=1.0,
        location="Bangalore, India",
        max_floors=8,
        budget_usd=4000000.0
    )

    # Run workflow
    results = await agent.run_complete_workflow(constraints)

    # Access results
    for design in results['designs']:
        print(f"{design['name']}: {design['score']}/100")

asyncio.run(custom_run())
```

## Design Alternatives

The agent generates 4 distinct design strategies:

### 1. Solar Maximizer
- **Focus**: Maximum solar energy generation
- **Features**: 85% roof solar panel coverage, optimized orientation
- **Best for**: Energy independence priority

### 2. Green Oasis
- **Focus**: Biophilic design with maximum greenery
- **Features**: 60% green roof, vertical gardens, natural ventilation
- **Best for**: Sustainability and wellbeing priority

### 3. Daylight Optimizer
- **Focus**: Maximum natural daylight
- **Features**: High window-to-wall ratio, light wells, clerestory windows
- **Best for**: Daylight quality and energy savings

### 4. Balanced Eco-Design
- **Focus**: Optimal cost-effectiveness
- **Features**: Balanced integration of all sustainable features
- **Best for**: Best overall value

## Evaluation Criteria

Each design is evaluated on three criteria:

### 1. Completeness (25%)
- Required eco-materials coverage (solar panels, green roof, recycled steel, bamboo)
- Specification completeness
- Building systems integration

### 2. Sustainability (40%)
- Daylight factor (minimum 0.30 required)
- Energy use intensity (max 100 kWh/sqm/year)
- Renewable energy percentage
- Carbon footprint
- Eco-material diversity

### 3. Cost-Effectiveness (35%)
- Budget compliance
- Value for money
- Lifecycle cost efficiency
- Return on investment

**Pass Threshold**: 70/100 overall score

## Output Format

### Console Report

The agent generates a comprehensive console report with:
- Design alternatives summary table
- Detailed specifications for each design
- Environmental performance metrics
- Cost analysis breakdown
- LLM evaluation scores
- Pass/fail recommendations
- Copilot Studio commentary
- Audit trail reference

### JSON Report

Complete machine-readable results saved to `outputs/{session_id}_report.json`

## Copilot Studio Integration

### For Business Users

The agent provides a REST API compatible with Copilot Studio connectors, allowing non-technical users to:

1. **Generate designs** with custom parameters
2. **Modify constraints** interactively
3. **View evaluations** in natural language
4. **Access audit trails** for compliance

### Setting Up the Connector

1. Start the server: `python src/main.py --server`
2. Download OpenAPI schema: `http://localhost:8000/schema/openapi.json`
3. Import schema into Copilot Studio / Power Platform
4. Configure authentication and endpoints
5. Build conversational flows in Copilot Studio

### Example Copilot Studio Flow

```
User: "Generate building designs with a budget of $4.5 million"
Copilot: [Calls /generate-designs endpoint]
Copilot: "I've generated 4 designs. The Solar Maximizer scores 85/100
          and passes all requirements. Would you like details?"
User: "Show me the cost breakdown"
Copilot: [Returns formatted cost analysis]
```

## Environmental Simulation

### Daylight Analysis
- Daylight factor calculation
- Useful daylight illuminance (UDI)
- Daylight autonomy
- Annual sunlight exposure

### Energy Analysis
- Base energy consumption modeling
- Solar generation prediction
- HVAC, lighting, and envelope efficiency
- Energy Use Intensity (EUI)
- Renewable energy percentage

### Carbon Footprint
- Operational carbon emissions
- Embodied carbon (amortized)
- Carbon sequestration from green features
- Total carbon intensity

## Cost Analysis

### Construction Costs
- Structural systems (recycled steel)
- Facade and glazing
- Solar panels and green roofs
- Bamboo flooring and elements
- MEP systems
- Special features
- Labor and contractor markup
- Contingency

### Lifecycle Costs (30 years)
- Operational costs
- Maintenance
- Replacements
- Net present value (NPV) analysis

## Audit Trail

All agent operations are logged for reproducibility:

- Session initialization
- Design generation
- Simulation execution
- Evaluation decisions
- Report generation

Audit logs are saved to `audit_trails/{session_id}_audit.jsonl`

Access via Copilot Studio audit trail reference for compliance and reproducibility.

## Configuration

### Azure AI Configuration

Edit `config/azure_config.yaml` or set environment variables:

```yaml
azure:
  endpoint: ${AZURE_AI_ENDPOINT}
  api_key: ${AZURE_AI_API_KEY}

agent:
  enable_copilot_studio: true
  evaluation_model: "gpt-4"
  pass_threshold: 70.0
```

### Building Constraints

Default constraints (customizable):

```python
BuildingConstraints(
    plot_size_acres=1.0,
    location="Bangalore, India",
    building_type="Office",
    max_floors=10,
    required_daylight_factor=0.30,
    max_energy_usage_kwh_sqm_year=100.0,
    budget_usd=5000000.0,
    required_materials=["solar_panels", "green_roof",
                        "recycled_steel", "bamboo"]
)
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Style

This project follows PEP 8 conventions. Format code with:

```bash
pip install black pylint
black src/
pylint src/
```

## Microsoft Agent Framework Patterns

This implementation follows Microsoft Agent Framework best practices:

1. **Agent Orchestration**: Central agent coordinates all services
2. **Service Modularity**: Separate services for generation, simulation, analysis
3. **Plugin Architecture**: Environmental and cost plugins
4. **LLM Integration**: Structured prompts via Copilot Studio Prompt Builder
5. **Audit Trail**: Complete logging for reproducibility
6. **API Exposure**: REST API for Copilot Studio connectors

## Azure AI Foundry Integration

The agent integrates with Azure AI Foundry:

- **Azure OpenAI**: LLM evaluation (GPT-4)
- **Azure AI Projects**: Agent orchestration
- **Copilot Studio**: Business user interface
- **Prompt Builder**: Structured evaluation prompts

## Contributing

See [CLAUDE.md](CLAUDE.md) for AI assistant development guidelines.

### Contribution Workflow

1. Create feature branch from `main`
2. Follow code conventions in CLAUDE.md
3. Write tests for new features
4. Update documentation
5. Submit pull request with clear description

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: https://github.com/SYLABS17/agenttest/issues
- Documentation: See CLAUDE.md for detailed guidelines

## Acknowledgments

- Microsoft Agent Framework
- Azure AI Foundry
- Copilot Studio
- Sustainable building design best practices

## Version History

- **1.0.0** (2025-11-17): Initial release
  - 4 design alternatives
  - Complete evaluation pipeline
  - Copilot Studio integration
  - Audit trail system

---

**Built with Microsoft Agent Framework and Azure AI Foundry**
