$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

$Version = "1.4.0"
$AppName = "NeoGT Device Configurator"
$ReleaseName = "neogt-device-configurator-win64-$Version.exe"
$BinDir = Join-Path (Resolve-Path "..") "bin"
$env:PYINSTALLER_CONFIG_DIR = Join-Path (Get-Location) "build\pyinstaller-cache"

py -3 -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev,3d]"
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "release\$AppName.exe" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $env:PYINSTALLER_CONFIG_DIR | Out-Null
python -m PyInstaller --noconfirm --distpath release config-tool.spec
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
Copy-Item -Force "release\$AppName.exe" (Join-Path $BinDir $ReleaseName)
Write-Host "Built: release\$AppName.exe"
Write-Host "Copied: $(Join-Path $BinDir $ReleaseName)"
