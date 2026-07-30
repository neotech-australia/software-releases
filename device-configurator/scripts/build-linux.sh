#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION="1.4.0"
ARCH="$(uname -m)"
if [[ "${ARCH}" == "x86_64" || "${ARCH}" == "amd64" ]]; then
  RELEASE_ARCH="linux-x64"
elif [[ "${ARCH}" == "aarch64" || "${ARCH}" == "arm64" ]]; then
  RELEASE_ARCH="linux-arm64"
else
  RELEASE_ARCH="linux-${ARCH}"
fi

APP_NAME="NeoGT Device Configurator"
RELEASE_NAME="neogt-device-configurator-${RELEASE_ARCH}-${VERSION}"
BIN_DIR="$(cd .. && pwd)/bin"
export PYINSTALLER_CONFIG_DIR="${PWD}/build/pyinstaller-cache"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev,3d]"
rm -rf build "release/${APP_NAME}"
mkdir -p "${PYINSTALLER_CONFIG_DIR}"
python -m PyInstaller --noconfirm --distpath release config-tool.spec
mkdir -p "${BIN_DIR}"
cp "release/${APP_NAME}" "${BIN_DIR}/${RELEASE_NAME}"
chmod +x "${BIN_DIR}/${RELEASE_NAME}"
echo "Built: release/${APP_NAME}"
echo "Copied: ${BIN_DIR}/${RELEASE_NAME}"
