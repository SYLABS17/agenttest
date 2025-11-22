# Azure AI Multi-Agent Research System

This project is a full-stack AI research system hosted on Azure, demonstrating multi-agent orchestration using Python (FastAPI) and a React frontend.

## Architecture

- **Frontend**: React + Tailwind CSS (Local chat interface & report viewer)
- **Backend**: FastAPI (Python)
- **Agents**:
  - **Manager Agent**: Orchestrates the research process.
  - **Bing Search Agent**: Searches the web (simulated).
  - **AI Search Agent**: Searches internal knowledge base (simulated).
- **Infrastructure**: Azure App Service, Cognitive Search, OpenAI, Monitor, Application Insights (defined in ARM templates).

## Directory Structure

- `/infra`: ARM templates for Azure resources.
- `/backend`: Python FastAPI application and agent logic.
- `/frontend`: React application.
- `/scripts`: Deployment and validation scripts.
- `/test`: Dummy data and test reports.

## Getting Started

### Prerequisites

- Azure CLI
- Python 3.10+
- Node.js 16+
- `jq` and `zip` utilities

### Local Development

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.template .env
   # Fill in .env variables (or leave defaults for simulation)
   python main.py
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. **Testing**:
   ```bash
   ./scripts/validate_end_to_end.sh
   ```

### Deployment

1. **Login to Azure**:
   ```bash
   az login
   ```

2. **Deploy Infrastructure**:
   ```bash
   ./scripts/deploy_resources.sh
   ```
   This will generate `infra/outputs.json` with the resource names.

3. **Deploy Application**:
   ```bash
   # Build frontend and deploy backend
   ./scripts/deploy_frontend.sh
   ./scripts/deploy_backend.sh <resource_group> <webapp_name>
   ```

## Observability

The system is integrated with Azure Application Insights. Logs and traces are sent automatically.
- Check the `/logs` endpoint (simulated in frontend) for real-time feedback.
- View "Application Map" in Azure Portal to see agent interactions.

## Agents & Simulation

By default, `SIMULATE_AGENTS=True` in `.env`. This uses dummy data in `test/data/` to simulate search results without incurring API costs. Set to `False` and provide API keys to use real services.
