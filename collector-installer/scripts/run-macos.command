#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
"${PYTHON_BIN}" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")

try:
    import tkinter
except Exception as exc:
    raise SystemExit(f"Python tkinter support is required for the macOS GUI: {exc}")
PY

if [[ -x .venv/bin/python ]] && ! .venv/bin/python -c "import tkinter" >/dev/null 2>&1; then
  rm -rf .venv
fi

"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
PYTHONPATH=src python -m tiltmeter_installer
