# 맞춤 찾기 웹 배포 — 묶음을 새로 만들고 Fly.io 에 올린다.
#   powershell -ExecutionPolicy Bypass -File deploy\deploy.ps1
# 일일 갱신(run_daily_update.py) 뒤에 돌리면 최신 실거래가 반영된다.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

& "$root\.venv\Scripts\python.exe" "$root\web\build_index.py"
& "$root\.venv\Scripts\python.exe" "$root\deploy\bundle.py"

Push-Location "$root\deploy\build"
try {
    fly deploy --remote-only
} finally {
    Pop-Location
}
