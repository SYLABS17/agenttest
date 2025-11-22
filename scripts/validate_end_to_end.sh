#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Running backend tests..."
python3 -m venv "${ROOT_DIR}/.venv-ci"
source "${ROOT_DIR}/.venv-ci/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r "${ROOT_DIR}/backend/requirements.txt" >/dev/null
pytest "${ROOT_DIR}/backend/tests"
deactivate

echo "Running frontend tests..."
pushd "${ROOT_DIR}/frontend" >/dev/null
npm install --no-fund --no-audit >/dev/null
npm run test >/dev/null
popd >/dev/null

echo "Collecting dummy observability logs..."
python - <<'PYCODE'
from pathlib import Path
log_file = Path("backend/logs/app.log")
if log_file.exists():
    print(log_file.read_text()[-1000:])
else:
    print("Log file not generated yet.")
PYCODE

echo "Validation complete."
