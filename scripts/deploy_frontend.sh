#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <storage-account-name> <container-name>" >&2
  exit 1
fi

STORAGE_ACCOUNT="$1"
CONTAINER="$2"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pushd "${ROOT_DIR}/frontend" >/dev/null
npm install --no-fund --no-audit
npm run build
popd >/dev/null

az storage container create \
  --only-show-errors \
  --name "$CONTAINER" \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login >/dev/null || true

az storage blob upload-batch \
  --only-show-errors \
  --destination "$CONTAINER" \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login \
  --source "${ROOT_DIR}/frontend/dist" >/dev/null

echo "Frontend artifacts uploaded to container ${CONTAINER} in ${STORAGE_ACCOUNT}."
