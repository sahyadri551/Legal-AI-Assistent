# Starts backend and frontend, each in its own window, both auto-reloading.
# Usage (from repo root, venv active):  .\scripts\dev.ps1
# Set-ExecutionPolicy -Scope Process Bypass
# Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
$root = (Resolve-Path "$PSScriptRoot\..").Path
$activate = Join-Path $root ".venv\Scripts\Activate.ps1"
$setup = "Set-Location '$root'; if (Test-Path '$activate') { & '$activate' }; `$env:PYTHONPATH='$root\src';"

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "$setup uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload --reload-dir src"

# Theme env vars guarantee the light base + blue accent even if .streamlit/config.toml is missed.
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "$setup `$env:STREAMLIT_THEME_BASE='light'; `$env:STREAMLIT_THEME_PRIMARY_COLOR='#2563eb'; streamlit run src/frontend/app.py --server.port 8501 --server.runOnSave true"
