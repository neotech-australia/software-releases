$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
py -3 -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[build]"
python -m PyInstaller --noconfirm --distpath release tiltmeter-installer.spec
Write-Host "Built: release\Tiltmeter Platform Installer.exe"
