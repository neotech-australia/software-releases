$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
$Version = "0.1.0"
$ReleaseName = "tiltmeter-collector-installer-win64-$Version.exe"
$BinDir = Join-Path (Resolve-Path "..") "bin"

py -3 -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[build]"
python -m PyInstaller --noconfirm --distpath release tiltmeter-installer.spec
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
Copy-Item -Force "release\Tiltmeter Collector Installer App.exe" (Join-Path $BinDir $ReleaseName)
Write-Host "Built: release\Tiltmeter Collector Installer App.exe"
Write-Host "Copied: $(Join-Path $BinDir $ReleaseName)"
