$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Missing .venv. Run install.ps1 first."
    exit 1
}

& ".venv\Scripts\python.exe" -m unittest discover -s tests -v

