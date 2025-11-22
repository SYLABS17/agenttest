#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
DIST_DIR="${ROOT_DIR}/dist"
FRONTEND_APP_NAME="${FRONTEND_APP_NAME:?Set FRONTEND_APP_NAME to the Azure Web App hosting the React UI}"
RESOURCE_GROUP="${RESOURCE_GROUP:?Set RESOURCE_GROUP for the target App Service}"

pushd "$FRONTEND_DIR" >/dev/null
npm install
npm run test
npm run build
popd >/dev/null

mkdir -p "$DIST_DIR"
PACKAGE_PATH="${DIST_DIR}/frontend.zip"
pushd "${FRONTEND_DIR}/dist" >/dev/null
zip -r "$PACKAGE_PATH" . >/dev/null
popd >/dev/null

az webapp deployment source config-zip \
  --only-show-errors \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FRONTEND_APP_NAME" \
  --src "$PACKAGE_PATH"
