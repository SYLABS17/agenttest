#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

log() {
  printf "\n[%s] %s\n" "$(date '+%H:%M:%S')" "$*"
}

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required for validation" >&2
  exit 1
fi

log "Running backend unit tests..."
pushd "$BACKEND_DIR" >/dev/null
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pytest
deactivate
popd >/dev/null

log "Running frontend unit tests..."
pushd "$FRONTEND_DIR" >/dev/null
npm install
npm run test
popd >/dev/null

log "Invoking backend health check at ${BACKEND_URL}/healthz"
curl --fail --silent --show-error "${BACKEND_URL}/healthz" | jq

for query in "Future of renewable energy in Africa" "Impact of generative AI on journalism"; do
  log "Triggering research workflow for '${query}'"
  curl --fail --silent --show-error -X POST \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"${query}\"}" \
    "${BACKEND_URL}/api/research" | jq '.final_report.title, .evaluation'
done

log "Validation completed successfully."
