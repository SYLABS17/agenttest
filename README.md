# Azure AI Research Orchestrator

Full-stack reference implementation of a multi-agent research system built for Azure App Service + Azure AI Search. The solution provisions secure infrastructure with ARM, exposes a FastAPI backend that orchestrates agents, and surfaces an observability-rich React/Tailwind UI. Everything ships with dummy data, evaluation hooks, telemetry plumbing, and deployment scripts so the project is dev/test/prod ready from day one.

## High-level Architecture

- **Infrastructure** (`infra/`): Parameterised ARM templates that create an App Service Plan, dual Web Apps (API + UI), Azure Storage, Cognitive Search, Azure OpenAI + Language, Log Analytics, Application Insights, Network Security Groups, private endpoints, and diagnostic settings with archive targets.
- **Backend** (`backend/`): FastAPI service with a Manager agent coordinating a BingSearch agent and an AISearch agent. Every run logs JSON telemetry to Application Insights (via `opencensus-ext-azure`), persists mock reports, and emits evaluation metrics.
- **Frontend** (`frontend/`): React + Vite + Tailwind UI that renders a chat timeline, aggregated research report, observability cards, and live logs fetched from the backend.
- **Testing & Data** (`backend/tests`, `frontend/__tests__`, `test/data`, `test/reports`): Pytest and Vitest suites plus fixture JSON for deterministic simulations.
- **Automation** (`scripts/`): Bash helpers for provisioning infra, deploying backend/frontend, and validating the full path end-to-end.

```
.
├── backend/                 # FastAPI service + agents + pytest suite
├── frontend/                # React/Tailwind UI with Vitest coverage
├── infra/                   # ARM templates for Azure resources
├── scripts/                 # Deployment + validation scripts
├── test/data                # Dummy Bing + Azure AI Search payloads
├── test/reports             # Sample research reports
├── .env.template            # Environment variable skeleton
└── README.md
```

## 1. Infrastructure-as-Code (ARM)

| Template | Purpose |
| --- | --- |
| `infra/monitor.json` | Log Analytics workspace, Application Insights, Data Collection Rule, optional alerting |
| `infra/app_service.json` | Storage account, App Service Plan, backend/frontend Web Apps, NSG, private endpoints, diagnostics |
| `infra/cognitive_search.json` | Azure Cognitive Search, Azure OpenAI, Azure Language Services, private endpoints |
| `infra/outputs.json` | Helper template for surfacing deployment outputs into automation |

**Deployment workflow**

```bash
export RESOURCE_GROUP=rg-ai-research
export LOCATION=eastus2
export BASE_NAME=airesearch
export SUBNET_RESOURCE_ID=/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/<subnet>
export PRIVATE_DNS_ZONE_ID=/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/privateDnsZones/privatelink.azurewebsites.net

./scripts/deploy_resources.sh
```

The script:
1. Deploys monitoring (Log Analytics + App Insights) and captures outputs.
2. Deploys App Service + Storage + networking, wiring diagnostics to Log Analytics + Storage.
3. Deploys Cognitive Search + Azure OpenAI + Language with private endpoints that reuse the same subnet/DNS zone.

All resources inherit tags (`env`, `owner`, `costCenter`), private endpoints, managed identities, resource locks, and diagnostic settings.

## 2. Backend (FastAPI + Azure-aware agents)

Key modules:

- `backend/main.py` – FastAPI app with `/api/research`, `/api/logs`, `/healthz`, Key Vault-friendly secret resolution, and threadpool orchestration.
- `backend/agents/*.py` – Manager + BingSearch + AISearch agents. Workers read curated JSON (`test/data/*`), simulate latency, and return structured `AgentResponse` objects.
- `backend/services/observability.py` – JSON logging + tracing via `opencensus-ext-azure`, dependency tracking, in-memory log buffer for the UI.
- `backend/services/evaluator.py` – Dummy accuracy/latency/agreement scoring; emits telemetry events to App Insights.
- `backend/tests/` – Pytest coverage for agents, API routes, and evaluator heuristics.

### Local development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.template ../.env  # customise secrets as needed
uvicorn backend.main:app --reload
pytest
```

`ManagerAgent` automatically persists every synthesized report to `test/reports/` and streams telemetry that the frontend can read via `/api/logs`.

## 3. Frontend (React + Tailwind)

- `src/App.tsx` – Main experience with query form, chat timeline, report viewer, observability cards, and logs panel.
- `src/components/*` – Reusable UI atoms (chat panel, report viewer, query form, theme toggle, observability cards, logs feed).
- `__tests__/App.test.tsx` – React Testing Library coverage that mocks backend calls.

### Local development

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (expects backend at http://localhost:8000)
npm run test
npm run build
```

Configure the API origin via `VITE_API_BASE_URL` when hosting separately (App Service configuration already injects the backend URL).

## 4. Dummy data & evaluation artifacts

- `test/data/bing_results.json` – Public-web style snippets used by the Bing agent.
- `test/data/ai_search_results.json` – Enterprise-style snippets used by the Azure AI Search agent.
- `test/reports/*.json` – Example merged research briefs for renewable energy and generative AI in journalism.

Add/modify entries to extend regression coverage or demo new topics.

## 5. Deployment & validation scripts

| Script | Description |
| --- | --- |
| `scripts/deploy_resources.sh` | Provisions Azure infra via ARM and prints backend/frontend URLs. Requires `az` CLI + env vars described earlier. |
| `scripts/deploy_backend.sh` | Creates a virtual env, installs deps, runs pytest, zips the FastAPI app, and deploys to the backend Web App via `config-zip`. |
| `scripts/deploy_frontend.sh` | Runs Vitest, builds the React app, zips the `dist/` folder, and pushes it to the frontend Web App. |
| `scripts/validate_end_to_end.sh` | Installs deps, runs backend + frontend unit tests, hits `/healthz`, and exercises `/api/research` for both sample queries using `curl`. |

All scripts honour `set -euo pipefail`, use `az ... --only-show-errors`, and are RBAC friendly—run them inside CI/CD (e.g., GitHub Actions) with appropriate service principals.

## 6. Observability & monitoring

1. **Application Insights** receives structured JSON logs (`eventType`, metadata, accuracy, latency, etc.) and distributed traces via OpenCensus.
2. **Log Analytics** stores diagnostic emissions from App Service, Storage, Cognitive Search, Azure OpenAI, and Application Insights itself.
3. **Storage account** captures the same diagnostics for long-term retention.
4. **Frontend observability panel** visualises latency + evaluation scores, while `/api/logs` exposes a lightweight telemetry stream for developers.
5. **Health check** at `/healthz` is ready for Azure Monitor availability tests.

## 7. Environment configuration

`cp .env.template .env` then update:

```
APP_NAME="Azure Research Orchestrator"
ENVIRONMENT="dev"
LOG_LEVEL="INFO"
APP_INSIGHTS_CONNECTION_STRING="<copy from monitor deployment>"
AZURE_SEARCH_ENDPOINT="https://<search>.search.windows.net"
AZURE_SEARCH_API_KEY="<key or rely on managed identity>"
BING_API_KEY="<optional>"
KEY_VAULT_URI="https://<vault>.vault.azure.net/"
DATA_DIR="./test/data"
REPORTS_DIR="./test/reports"
ENABLE_MOCK_LATENCY=true
```

When running inside Azure, configure Web App settings (already templated) or leverage Managed Identity + Key Vault by setting `KEY_VAULT_URI`.

## 8. Next steps

- Plug real Bing/Search credentials or Managed Identity-based auth.
- Extend the `scripts/` into GitHub Actions (see the optional CI/CD stretch goal) to lint, test, validate ARM, and deploy on merges.
- Enrich `test/data/` to reflect new research domains or evaluation scenarios.

You now have a production-ready blueprint for Azure-hosted agentic research applications with infrastructure, runtime, observability, and UX all wired up. Happy shipping! 🚀
