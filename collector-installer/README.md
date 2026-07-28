# Tiltmeter Platform Installer

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

## Run From Source

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

Build outputs are written to `release/`.

The app streams Docker install and Docker image pull output into the status/log panel, so users see progress while requirements or production images are downloading.
