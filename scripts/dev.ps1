$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\backend'; python -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; npm run dev -- --host 127.0.0.1"

Write-Host "StockTek backend:  http://127.0.0.1:8000"
Write-Host "StockTek frontend: http://127.0.0.1:5173"

