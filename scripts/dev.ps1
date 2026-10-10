$ErrorActionPreference = "Stop"
$root = (Resolve-Path "$PSScriptRoot\..").Path
$activate = Join-Path $root ".venv\Scripts\Activate.ps1"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; if (Test-Path '$activate') { & '$activate' }; `$env:PYTHONPATH='$root\src'; uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\web'; npm run dev"
