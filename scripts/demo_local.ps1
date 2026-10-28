# Local demo fallback: the whole demo from this laptop, no internet needed.
# API on :8000 in DEMO_MODE (data from artifacts/, AI text only from cache/llm/, template on a miss),
# web on :3000 built against it. Run from the repo root:  powershell -File scripts\demo_local.ps1
# Then: python scripts\warmup.py --local, and present from http://localhost:3000.
# Sign-in (Supabase) and live voice need the internet; everything on Audit, Check, Ask, Trust works offline.

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Start-Process powershell -ArgumentList '-NoExit', '-Command', `
  "`$env:PYTHONUTF8='1'; `$env:DEMO_MODE='1'; .venv\Scripts\python.exe -m uvicorn api.main:app --port 8000"

# NEXT_PUBLIC_API_BASE is baked in at build time, so build against localhost explicitly.
$env:NEXT_PUBLIC_API_BASE = 'http://127.0.0.1:8000'  # not localhost: IPv6-first lookup adds ~2 s a call
pnpm --dir web build
if ($LASTEXITCODE -ne 0) { Write-Host 'Web build failed; the live site is still the main path.'; exit 1 }
Start-Process powershell -ArgumentList '-NoExit', '-Command', "pnpm --dir web start --port 3000"

Write-Host 'API http://localhost:8000  ·  web http://localhost:3000  ·  next: python scripts\warmup.py --local'
