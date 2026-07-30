# LoRaWAN Configuration Tool

Desktop utility for provisioning LoRaWAN IoT sensors over a COM port using AT/ATC commands.

## Requirements

- Python 3.9+
- Windows (primary); Linux/macOS supported for development
- Tkinter (bundled with the official python.org installer on Windows/macOS; on Homebrew Python install `python-tk`, on Debian/Ubuntu install `python3-tk`)
- Runtime dependencies (installed automatically): `customtkinter`, `pyserial`
- `vpython` — required only for the 3D board orientation viewer (the "3D" button in the Measurements tab). Install with the `3d` extra below; without it the rest of the app works, but opening the 3D viewer will fail.

## Install

```bash
py -m pip install -i https://mirror-pypi.runflare.com/simple -e ".[dev,3d]"
```

Omit `,3d` if you don't need the 3D orientation viewer. The `-i` mirror flag is optional; use the default PyPI index if you have direct access.

## Usage

### CLI

```bash
# Profile management
config-tool-cli profiles list
config-tool-cli profiles add --name "MyProfile" --appeui 0000000000000001 --appkey 2B7E151628AED2A6ABF7158809CF4F3C --band 4 --mask 0000 --uplinkperiod 600 --gpsdecimationfactor 4
config-tool-cli profiles set-active --name "MyProfile"
config-tool-cli profiles export --name "MyProfile" --file profile.json
config-tool-cli profiles import --file profile.json

# Serial port operations
config-tool-cli ports
config-tool-cli connect --port COM3 read
config-tool-cli connect --port COM3 apply --profile "MyProfile"
config-tool-cli connect --port COM3 disconnect

# Offline testing with mock device
config-tool-cli --mock connect --port MOCK read
config-tool-cli --mock connect --port MOCK apply --profile "MyProfile"
```

### GUI

```bash
config-tool-gui
```

## Profile storage

Profiles are saved to `profiles.json` in the same directory as the executable (or project root during development).

## Serial protocol

- Baud rate: 115200, 8N1
- Line ending: `\r\n` on every command
- Flow: `ATC+STARTCONFIG` → device dump → write parameters → `ATC+CONFIGDONE`

See `Prompts and documents/Serial Protocol.md` for full command reference.

## Building Windows executable

```bash
build.bat
```

Or manually:

```bash
py -m pip install -i https://mirror-pypi.runflare.com/simple pyinstaller
py -m PyInstaller --name config-tool --windowed --onefile --paths src --collect-all customtkinter --icon assets\icon.ico --add-data "assets;assets" src/config_tool/gui/app.py
```

Copy the resulting executable; `profiles.json` will be created beside it on first run.

## Release Builds

Build release binaries on each target OS. PyInstaller cannot cross-compile
reliably between macOS, Windows, and Linux.

macOS:

```bash
./scripts/build-macos.sh
```

Linux:

```bash
./scripts/build-linux.sh
```

Windows PowerShell:

```powershell
.\scripts\build-windows.ps1
```

Build outputs are written to `release/`. Build scripts also copy
distributable files to `../bin/` with versioned names:

```text
../bin/neogt-device-configurator-mac-arm64-1.4.0.dmg
../bin/neogt-device-configurator-win64-1.4.0.exe
../bin/neogt-device-configurator-linux-x64-1.4.0
```

Run from source:

```bash
./scripts/run-macos.command
./scripts/run-linux.sh
```

Windows PowerShell:

```powershell
.\scripts\run-windows.ps1
```

## Running and building on macOS

### Setup

```bash
# If using Homebrew Python, Tkinter must be installed separately:
brew install python-tk

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev,3d]"
```

Note: the `py` launcher used elsewhere in this README is Windows-only; use `python3` on macOS.

### Run

```bash
config-tool-gui        # GUI
config-tool-cli ports  # CLI
```

Serial ports on macOS appear as `/dev/cu.usbserial-*` or `/dev/cu.usbmodem*` instead of `COMx`:

```bash
config-tool-cli connect --port /dev/cu.usbserial-0001 read
```

USB-serial adapters (CP210x, CH340, FTDI) may require a vendor driver on older macOS versions; recent macOS includes drivers for most common chips.

### Build a macOS app

```bash
python3 -m PyInstaller --name config-tool --windowed --onefile \
    --paths src \
    --collect-all customtkinter \
    --icon assets/icon.icns \
    --add-data "assets:assets" \
    src/config_tool/gui/app.py
```

Add `--collect-all vpython` if the 3D viewer must work in the packaged app.

The `--icon` flag sets the app icon (`assets/icon.icns` on macOS, `assets/icon.ico` on Windows), and `--add-data` bundles the `assets/` folder (window icon, logo, device image) into the executable. Note the separator differs: `assets:assets` on macOS/Linux, `assets;assets` on Windows.

If you get `No module named PyInstaller`, you are probably not in the virtual environment (or skipped the `dev` extra). Activate the venv — creating it first if it doesn't exist — and install the project with dev extras:

```bash
python3 -m venv .venv          # only if .venv doesn't exist yet
source .venv/bin/activate
python3 -m pip install -i https://mirror-pypi.runflare.com/simple -e ".[dev,3d]"
```

Or, without a venv, install PyInstaller directly into your current Python:

```bash
python3 -m pip install -i https://mirror-pypi.runflare.com/simple pyinstaller
```

**pyenv users:** pyenv builds Python from source, so Tk support and framework mode depend on what was available at build time. If you get `ModuleNotFoundError: No module named '_tkinter'`, or the packaged GUI app fails to launch, install Tcl/Tk via Homebrew and rebuild Python:

```bash
brew install tcl-tk@8   # Python <= 3.12 needs Tcl/Tk 8.x, not 9
env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install --force 3.11.11
```

Then recreate the venv (it is linked to the old interpreter):

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -i https://mirror-pypi.runflare.com/simple -e ".[dev,3d]"
```

Verify Tk works with `python3 -m tkinter` (a small test window should open). Alternatively, use the python.org installer, which ships with Tk and is a framework build by default.

This produces both `dist/config-tool` (a plain executable) and `dist/config-tool.app` (an app bundle). The binary is architecture-specific (Apple Silicon vs Intel) — build on the architecture you target.

Since the app is unsigned, Gatekeeper will block it on other Macs. Either right-click → Open on first launch, or clear the quarantine flag:

```bash
xattr -cr dist/config-tool.app
```

For distribution, sign and notarize with an Apple Developer ID (`codesign` / `notarytool`).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port in use | Close other serial terminal apps |
| Connection timeout | Check cable, correct COM port, device powered |
| AT_PARAM_ERROR | Verify hex lengths (APPEUI 16, APPKEY 32, MASK 4 digits) |
| AT_BUSY_ERROR | Wait for LoRa module to finish, retry |
