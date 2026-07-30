#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

APP_NAME="NeoGT Device Configurator"
APP_BUNDLE="${APP_NAME}.app"
VERSION="1.4.0"
ARCH="$(uname -m)"
if [[ "${ARCH}" == "arm64" ]]; then
  RELEASE_ARCH="mac-arm64"
else
  RELEASE_ARCH="mac-${ARCH}"
fi

DMG_NAME="neogt-device-configurator-${RELEASE_ARCH}-${VERSION}.dmg"
BIN_DIR="$(cd .. && pwd)/bin"
DMG_ROOT="release/dmg-root"
export PYINSTALLER_CONFIG_DIR="${PWD}/build/pyinstaller-cache"

PYTHON_BIN="${PYTHON_BIN:-python3}"
INSTALL_EXTRAS="dev"
if [[ "${INCLUDE_3D:-0}" == "1" ]]; then
  INSTALL_EXTRAS="dev,3d"
fi
"${PYTHON_BIN}" - <<'PY'
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    raise SystemExit("Python 3.9 or newer is required.")

try:
    import tkinter
except Exception as exc:
    raise SystemExit(f"Python tkinter support is required for the macOS GUI build: {exc}")

executable = Path(sys.executable).resolve()
if "/Applications/Xcode.app/" in str(executable):
    raise SystemExit(
        "Do not build the macOS GUI with Xcode's bundled python3. "
        "It links against an old/system Tk that can crash on launch. "
        "Install python.org Python 3.11+ or Homebrew python-tk, then run: "
        "PYTHON_BIN=/path/to/python3 ./scripts/build-macos.sh"
    )

if tkinter.TkVersion < 8.6:
    raise SystemExit(
        f"Tk {tkinter.TkVersion} is too old for this macOS app build. "
        "Use a Python installation with Tk 8.6 or newer."
    )
PY

if [[ -x .venv/bin/python ]] && ! .venv/bin/python -c "import subprocess" >/dev/null 2>&1; then
  rm -rf .venv
fi

if [[ -x .venv/bin/python ]] && [[ "$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "$("${PYTHON_BIN}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" ]]; then
  rm -rf .venv
fi

"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
if [[ "${UPGRADE_BUILD_TOOLS:-0}" == "1" ]]; then
  python -m pip install --upgrade "pip" "setuptools<81" wheel
fi
python -m pip install --disable-pip-version-check "setuptools<81" wheel
python -m pip install --disable-pip-version-check --no-build-isolation -e ".[${INSTALL_EXTRAS}]"
rm -rf build "release/${APP_NAME}" "release/${APP_BUNDLE}" "release/${DMG_NAME}" "${DMG_ROOT}"
mkdir -p "${PYINSTALLER_CONFIG_DIR}"
python -m PyInstaller --noconfirm --distpath release config-tool.spec
mkdir -p "${BIN_DIR}"
mkdir -p "${DMG_ROOT}"
cp -R "release/${APP_BUNDLE}" "${DMG_ROOT}/${APP_BUNDLE}"
ln -s /Applications "${DMG_ROOT}/Applications"
hdiutil create \
  -volname "NeoGT Device Configurator" \
  -srcfolder "${DMG_ROOT}" \
  -ov \
  -format UDZO \
  "release/${DMG_NAME}"
cp "release/${DMG_NAME}" "${BIN_DIR}/${DMG_NAME}"
echo "Built: release/${APP_BUNDLE}"
echo "Built: release/${DMG_NAME}"
echo "Copied: ${BIN_DIR}/${DMG_NAME}"
