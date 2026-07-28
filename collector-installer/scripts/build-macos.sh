#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

APP_NAME="Tiltmeter Collector Installer App"
APP_BUNDLE="${APP_NAME}.app"
VERSION="0.1.0"
ARCH="$(uname -m)"
if [[ "${ARCH}" == "arm64" ]]; then
  RELEASE_ARCH="mac-arm64"
else
  RELEASE_ARCH="mac-${ARCH}"
fi

DMG_NAME="tiltmeter-collector-installer-${RELEASE_ARCH}-${VERSION}.dmg"
BIN_DIR="$(cd .. && pwd)/bin"
DMG_ROOT="release/dmg-root"

PYTHON_BIN="${PYTHON_BIN:-python3}"
"${PYTHON_BIN}" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")

try:
    import tkinter
except Exception as exc:
    raise SystemExit(f"Python tkinter support is required for the macOS GUI build: {exc}")
PY

if [[ -x .venv/bin/python ]] && ! .venv/bin/python -c "import subprocess" >/dev/null 2>&1; then
  rm -rf .venv
fi

"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
python -m pip install --disable-pip-version-check -r requirements.txt "pyinstaller>=6.10.0" "wheel"
python -m pip install --disable-pip-version-check --no-build-isolation --no-deps -e .
rm -rf build "release/${APP_NAME}" "release/${APP_BUNDLE}" "release/${DMG_NAME}" "${DMG_ROOT}"
python -m PyInstaller --noconfirm --distpath release tiltmeter-installer.spec
mkdir -p "${BIN_DIR}"
mkdir -p "${DMG_ROOT}"
cp -R "release/${APP_BUNDLE}" "${DMG_ROOT}/${APP_BUNDLE}"
ln -s /Applications "${DMG_ROOT}/Applications"
hdiutil create \
  -volname "Tiltmeter Collector Installer" \
  -srcfolder "${DMG_ROOT}" \
  -ov \
  -format UDZO \
  "release/${DMG_NAME}"
cp "release/${DMG_NAME}" "${BIN_DIR}/${DMG_NAME}"
echo "Built: release/${APP_BUNDLE}"
echo "Built: release/${DMG_NAME}"
echo "Copied: ${BIN_DIR}/${DMG_NAME}"
