$ErrorActionPreference = 'Stop'
$episodePath = 'C:\projects\realestate_reco\video-agent-studio\episodes\housing-choice-networth-20261020'
$qaPath = Join-Path $episodePath 'qa\jun-production-v1'
$packetDirectory = Join-Path $episodePath 'outputs\jun-production-v1'
$packetPath = Join-Path $packetDirectory 'encoded_frame_plan.json'
$watcher = [System.IO.FileSystemWatcher]::new($packetDirectory, 'encoded_frame_plan.json')
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::FileName
$watcher.EnableRaisingEvents = $true
try {
    while ($true) {
        $packet = $null
        if (Test-Path -LiteralPath $packetPath) {
            try { $packet = Get-Content -LiteralPath $packetPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $packet = $null }
        }
        if ($packet -and $packet.status -eq 'encoded_frames_extracted_review_pending' -and $packet.final_sha256) { break }
        $null = $watcher.WaitForChanged([System.IO.WatcherChangeTypes]::All)
    }
} finally {
    $watcher.Dispose()
}
Write-Output 'Actual encoded packet ready; independent final AV checks starting.'
& 'C:\projects\realestate_reco\tools\python311\python.exe' -B -X utf8 (Join-Path $qaPath 'verify_final_media.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
