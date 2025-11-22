# Azure AI Research System

This repository provisions and deploys an Azure-hosted, multi-agent research assistant. A Manager Agent coordinates two worker agents (Bing Search + Azure AI Search) to answer research questions, aggregate findings in a group-chat format, and produce a final report. The project ships with end-to-end infrastructure as code, a FastAPI backend, a Tailwind-powered React frontend, observability plumbing, and deployment scripts suitable for Azure DevOps/GitHub Actions.

## Repository Layout

```
infra/                # ARM templates for App Service, Cognitive Search/OpenAI, Azure Monitor
backend/              # FastAPI service, agent orchestration, observability + tests
frontend/             # React + Tailwind single-page app with testing setup
scripts/              # Deployment & validation scripts
test/data|reports/    # Dummy fixtures + generated sample research reports
.env.template         # Environment variables to copy into .env
```

Legacy LangGraph samples remain under `src/` for reference but are not used by the new system.

## Infrastructure as Code (ARM)

All templates are parameterized, tagged, and private-network ready:

| Template | Purpose |
| --- | --- |
| `infra/monitor.json` | Creates Log Analytics workspace, Application Insights, Data Collection Endpoint/Rule, and resource locks. |
| `infra/app_service.json` | Provisions Storage Account, Azure App Service Plan, Linux Web App, VNet + NSG, private endpoint, and diagnostics. |
| `infra/cognitive_search.json` | Deploys Azure Cognitive Search, Azure OpenAI, Azure Language Service, diagnostic settings, and private endpoints. |
| `infra/outputs.json` | Aggregates outputs from the module deployments for downstream automation. |

Deployment helper: `scripts/deploy_resources.sh <rg> <location> <name-prefix> <owner-email> [env] [cost-center]`

## Backend (FastAPI)

Located in `backend/`:

- `main.py`: FastAPI app exposing `/healthz`, `/api/research`, and `/api/logs`.
- Agents (`backend/agents/*`):
  - `ManagerAgent`: coordinates worker agents, builds chat transcript, merges final report, and triggers evaluations.
  - `BingSearchAgent` & `AISearchAgent`: simulate grounded searches using fixtures in `test/data`.
- Services:
  - `observability.py`: OpenCensus tracer + JSON logging to Azure Application Insights and rotating files.
  - `evaluator.py`: Dummy scoring engine that logs metrics to Azure Monitor.
- Config via `backend/config.py` (Pydantic). Copy `.env.template` → `.env` for local development.
- Tests live in `backend/tests/` (pytest + pytest-asyncio).

Run locally:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

## Frontend (React + Tailwind)

Under `frontend/`:

- Vite + TypeScript setup with Tailwind and React Testing Library.
- `src/App.tsx` renders chat UI, report viewer, observability panel, and dark-mode toggle.
- Components in `src/components/` with ARIA labels + responsive design.
- Tests in `frontend/__tests__/App.test.tsx` (Vitest).

Dev loop:

```bash
cd frontend
npm install
npm run dev
```

Point `VITE_API_BASE_URL` to the backend URL (local or Azure) via `.env` or environment variable.

## Testing & Validation

- Backend: `pytest backend/tests`
- Frontend: `cd frontend && npm run test`
- Combined workflow: `scripts/validate_end_to_end.sh` (creates temporary venv, runs pytest + vitest, and prints observability log tail).

## Deployment Scripts

| Script | Description |
| --- | --- |
| `deploy_resources.sh` | Validates & deploys all ARM templates with `az deployment group what-if/create`. |
| `deploy_backend.sh <web-app> <rg>` | Zips the FastAPI backend and pushes via `az webapp deploy`. |
| `deploy_frontend.sh <storage-account> <container>` | Builds the React app and uploads static assets to Azure Storage. |
| `validate_end_to_end.sh` | Runs backend/frontend tests and outputs recent logs. |

All scripts use `--only-show-errors` and assume the executing identity has contributor access to the target resource group/storage account.

## Observability

- OpenCensus traces/logs flow to Application Insights (connection string via `.env`).
- Diagnostic settings for App Service, Storage, Cognitive Search, and Azure OpenAI send telemetry to Log Analytics.
- Frontend displays current evaluation metrics plus the latest log entries fetched from `/api/logs`.

## Dummy Data & Reports

Sample agent responses live in:

- `test/data/bing_results.json`
- `test/data/ai_search_results.json`

Generated Markdown reports are saved automatically to `test/reports/` for auditing.

## CI/CD (Ready for GitHub Actions)

- Backend + frontend rely on standard toolchains (pip/pytest + npm/vitest).
- ARM templates include descriptive outputs for pipeline chaining (see `infra/outputs.json`).
- Add workflow jobs to run `scripts/deploy_resources.sh`, `deploy_backend.sh`, and `deploy_frontend.sh` as needed.

## Next Steps

- Wire Azure Key Vault + managed identity for secret retrieval.
- Expand worker agents with real Bing/Azure AI Search clients once keys are provided.
- Add GitHub Actions workflow (see `.github/workflows/deploy.yml` placeholder mention).

For additional details on coding standards and contribution workflow, review `CLAUDE.md`.
