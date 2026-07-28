# Tiltmeter Collector Installer App

Cross-platform GUI installer for the Tiltmeter Platform production Docker images.

The installer creates a local runtime directory, generates `.env`, creates a self-signed localhost TLS certificate, pulls production images from GHCR, and manages the Docker Compose stack.

## Runtime Defaults

- Collector image: `ghcr.io/neotech-australia/tiltmeter-platform/collector:latest`
- Dashboard image: `ghcr.io/neotech-australia/tiltmeter-platform/dashboard:latest`
- Default install folder:
  - macOS: `~/Library/Application Support/TiltmeterPlatform`
  - Windows: `%LOCALAPPDATA%\TiltmeterPlatform`
  - Linux: `~/.local/share/tiltmeter-platform`

## Generated Values

The installer generates these values locally:

- `JWT_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `ADMIN_PASSWORD`
- `certs/localhost.pem`
- `certs/localhost-key.pem`

The generated admin and database credentials are written to `credentials.txt` in the install folder.

## User Inputs

The GUI asks for one operational value:

- Dashboard Port, default `443`

After install, the app is available at `https://localhost:<Dashboard Port>`. The collector API and database are only reachable inside the Docker network through the dashboard proxy. If the dashboard port is already in use, the installer warns before continuing.

## Downloaded Installer Usage

Release binaries are published in `../bin/`.

macOS Apple Silicon:

```text
../bin/tiltmeter-collector-installer-mac-arm64-0.1.0.dmg
```

Windows 64-bit:

```text
../bin/tiltmeter-collector-installer-win64-0.1.0.exe
```

Linux 64-bit, when built:

```text
../bin/tiltmeter-collector-installer-linux-x64-0.1.0
```

Double-click the downloaded installer to use the GUI. The same installer can also run from a terminal for headless or SSH-only machines. When a command is run this way, Docker checks, image pulls, stack startup, status, and log output are printed to the terminal.

macOS GUI install:

1. Open `../bin/tiltmeter-collector-installer-mac-arm64-0.1.0.dmg`.
2. Drag `Tiltmeter Collector Installer App.app` to `Applications`.
3. Open it from `Applications`.

macOS terminal install:

```bash
"/Applications/Tiltmeter Collector Installer App.app/Contents/MacOS/Tiltmeter Collector Installer App" install --dashboard-port 443
```

macOS terminal status and logs:

```bash
"/Applications/Tiltmeter Collector Installer App.app/Contents/MacOS/Tiltmeter Collector Installer App" status
"/Applications/Tiltmeter Collector Installer App.app/Contents/MacOS/Tiltmeter Collector Installer App" logs --tail 300
```

Windows terminal install from the release `.exe`:

```powershell
cd ..\bin
.\tiltmeter-collector-installer-win64-0.1.0.exe install --dashboard-port 443
```

The Windows `.exe` is built with console output enabled so `--help`, `status`, `logs`, and install progress print in PowerShell or Command Prompt. Running the same `.exe` with no arguments opens the GUI.

Windows terminal status and logs:

```powershell
cd ..\bin
.\tiltmeter-collector-installer-win64-0.1.0.exe status
.\tiltmeter-collector-installer-win64-0.1.0.exe logs --tail 300
```

Linux terminal install from the release binary:

```bash
cd ../bin
chmod +x ./tiltmeter-collector-installer-linux-x64-0.1.0
./tiltmeter-collector-installer-linux-x64-0.1.0 install --dashboard-port 443
```

Linux terminal status and logs:

```bash
cd ../bin
./tiltmeter-collector-installer-linux-x64-0.1.0 status
./tiltmeter-collector-installer-linux-x64-0.1.0 logs --tail 300
```

Common CLI commands:

```bash
check-docker
install-docker
install --dashboard-port 443
start
stop
restart
status
logs --tail 300
```

Append the command after the release executable path. For example:

```bash
./tiltmeter-collector-installer-linux-x64-0.1.0 check-docker
```

If the selected dashboard port is already in use, `install` exits before changing the stack. Pass `--yes` to continue anyway:

```bash
./tiltmeter-collector-installer-linux-x64-0.1.0 install --dashboard-port 443 --yes
```

## Run From Source

Use these commands only when running from the source tree instead of a file from `../bin/`.

GUI from source:

macOS:

```bash
./scripts/run-macos.command
```

Linux:

```bash
./scripts/run-linux.sh
```

Windows PowerShell:

```powershell
.\scripts\run-windows.ps1
```

CLI from source:

```bash
PYTHONPATH=src python -m tiltmeter_installer --help
PYTHONPATH=src python -m tiltmeter_installer install --dashboard-port 443
PYTHONPATH=src python -m tiltmeter_installer status
PYTHONPATH=src python -m tiltmeter_installer logs --tail 300
```

## Build Platform Installers

Build on each target OS. PyInstaller cannot cross-compile reliably between macOS, Windows, and Linux.

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

Build outputs are written to `release/`. Build scripts also copy distributable files to `../bin/` with versioned names:

```text
../bin/tiltmeter-collector-installer-mac-arm64-0.1.0.dmg
../bin/tiltmeter-collector-installer-win64-0.1.0.exe
../bin/tiltmeter-collector-installer-linux-x64-0.1.0
```

The app streams Docker install and Docker image pull output into the status/log panel, so users see progress while requirements or production images are downloading.
