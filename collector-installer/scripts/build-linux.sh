#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[build]"
python -m PyInstaller --noconfirm --distpath release tiltmeter-installer.spec
echo "Built: release/Tiltmeter Collector Installer App"
