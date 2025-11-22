#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
DIST_DIR="${ROOT_DIR}/dist"
BACKEND_APP_NAME="${BACKEND_APP_NAME:?Set BACKEND_APP_NAME to the Azure Web App name}"
RESOURCE_GROUP="${RESOURCE_GROUP:?Set RESOURCE_GROUP for the target App Service}"

python3 -m venv "${BACKEND_DIR}/.venv"
source "${BACKEND_DIR}/.venv/bin/activate"
pip install --upgrade pip
pip install -r "${BACKEND_DIR}/requirements.txt"

pushd "$BACKEND_DIR" >/dev/null
pytest
popd >/dev/null

mkdir -p "$DIST_DIR"
PACKAGE_PATH="${DIST_DIR}/backend.zip"
pushd "$BACKEND_DIR" >/dev/null
zip -r "$PACKAGE_PATH" . -x "__pycache__/*" ".venv/*" >/dev/null
popd >/dev/null

az webapp deployment source config-zip \
  --only-show-errors \
  --resource-group "$RESOURCE_GROUP" \
  --name "$BACKEND_APP_NAME" \
  --src "$PACKAGE_PATH"
