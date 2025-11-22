#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <web-app-name> <resource-group>" >&2
  exit 1
fi

WEB_APP="$1"
RESOURCE_GROUP="$2"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT="${ROOT_DIR}/backend.zip"

pushd "$ROOT_DIR" >/dev/null
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
deactivate

echo "Creating deployment package..."
zip -r "$ARTIFACT" backend -x "backend/__pycache__/*" >/dev/null

echo "Deploying FastAPI backend to ${WEB_APP}..."
az webapp deploy \
  --only-show-errors \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEB_APP" \
  --src-path "$ARTIFACT" \
  --type zip

rm -f "$ARTIFACT"
popd >/dev/null
