$root = Split-Path $PSScriptRoot -Parent; Set-Location -Path $root

$ymd = Get-Date -Format 'yyyyMMdd'
$logDir = Join-Path $root 'exports\daily'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "anomaly_log_$ymd.txt"

$py = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
    Write-Error "Python not found at $py"
    exit 1
}

"=== run_anomaly_detection.py | $ymd ===`n" | Out-File -Encoding utf8 $log
& $py 'run_anomaly_detection.py' *>&1 | Tee-Object -FilePath $log -Append

$rc = $LASTEXITCODE
Write-Host ""
Write-Host "--------------------------------------------------"
Write-Host "  Exit code : $rc"
Write-Host "  Log file  : $log"
Write-Host "  Parquet   : $logDir\anomaly_$ymd.parquet"
Write-Host "--------------------------------------------------"

exit $rc

