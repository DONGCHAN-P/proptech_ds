param([Parameter(Mandatory=$true)][string]$Manifest)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$resolvedManifest = [System.IO.Path]::GetFullPath($Manifest)
$parentPath = [System.IO.Path]::GetDirectoryName($resolvedManifest)
$leafName = [System.IO.Path]::GetFileName($resolvedManifest)
$watcher = [System.IO.FileSystemWatcher]::new($parentPath, $leafName)
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::Size
$watcher.EnableRaisingEvents = $true
$subscription = Register-ObjectEvent -InputObject $watcher -EventName Changed -SourceIdentifier 'assembly-manifest-changed'
try {
    Write-Output '{"status":"waiting_filesystem_completion_event","polling":false}'
    while ($true) {
        $data = $null
        try { $data = Get-Content -LiteralPath $resolvedManifest -Encoding UTF8 -Raw | ConvertFrom-Json } catch [System.ArgumentException] { }
        if ($null -ne $data) {
            $count = @($data.scenes | Where-Object { $_.status -eq 'encoded' }).Count
            if ($count -eq 34) {
                Write-Output ('{"status":"all34_encoded_completion_event","manifest":' + ($resolvedManifest | ConvertTo-Json -Compress) + '}')
                exit 0
            }
        }
        $event = Wait-Event -SourceIdentifier 'assembly-manifest-changed'
        Remove-Event -EventIdentifier $event.EventIdentifier
    }
} finally {
    Unregister-Event -SourceIdentifier 'assembly-manifest-changed'
    Remove-Job -Id $subscription.Id -Force
    $watcher.Dispose()
}
