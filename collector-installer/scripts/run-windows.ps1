$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
py -3 -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m tiltmeter_installer
