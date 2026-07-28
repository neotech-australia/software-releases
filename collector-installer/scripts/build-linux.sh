#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
VERSION="0.1.0"
ARCH="$(uname -m)"
if [[ "${ARCH}" == "x86_64" || "${ARCH}" == "amd64" ]]; then
  RELEASE_ARCH="linux-x64"
elif [[ "${ARCH}" == "aarch64" || "${ARCH}" == "arm64" ]]; then
  RELEASE_ARCH="linux-arm64"
else
  RELEASE_ARCH="linux-${ARCH}"
fi
RELEASE_NAME="tiltmeter-collector-installer-${RELEASE_ARCH}-${VERSION}"
BIN_DIR="$(cd .. && pwd)/bin"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[build]"
python -m PyInstaller --noconfirm --distpath release tiltmeter-installer.spec
mkdir -p "${BIN_DIR}"
cp "release/Tiltmeter Collector Installer App" "${BIN_DIR}/${RELEASE_NAME}"
chmod +x "${BIN_DIR}/${RELEASE_NAME}"
echo "Built: release/Tiltmeter Collector Installer App"
echo "Copied: ${BIN_DIR}/${RELEASE_NAME}"
