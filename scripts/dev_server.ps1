# dev_server.ps1 - Run uvicorn with --reload, leaving the terminal open.
# Just double-click or run from PowerShell; do not press Ctrl+C while editing code.

Set-Location -Path (Split-Path -Parent $PSScriptRoot)
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --log-level warning
