param(
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskPrefix = $taskRoot.TrimEnd('\') + '\'
$manifestPath = Join-Path $PSScriptRoot 'delete_manifest.json'
$protectedPath = Join-Path $PSScriptRoot 'protected_hashes.json'
$masterGuidePath = Join-Path $taskRoot 'video-agent-studio\guides\영상제작_마스터가이드.md'
$reviewPath = Join-Path $PSScriptRoot 'retention_review.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$protected = Get-Content -LiteralPath $protectedPath -Raw -Encoding UTF8 | ConvertFrom-Json
$allowedPrefixes = @(
    (Join-Path $taskRoot 'video-agent-studio\episodes\'),
    (Join-Path $taskRoot '.cache\webpack\'),
    (Join-Path $taskRoot 'video\node_modules\.cache\')
)
$protectedSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($row in $protected.files) { [void]$protectedSet.Add($row.path.Replace('/', '\')) }
$safeParents = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

function Get-CheckedTarget([string]$relativePath) {
    $pathParts = $relativePath -split '[/\\]'
    if ([IO.Path]::IsPathRooted($relativePath) -or ($pathParts -contains '..')) {
        throw "Unexpected absolute or parent-traversal manifest path: $relativePath"
    }
    $resolvedTarget = [IO.Path]::GetFullPath((Join-Path $taskRoot $relativePath.Replace('/', '\')))
    if (-not $resolvedTarget.StartsWith($taskPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Target escaped workspace: $relativePath" }
    $insideAllowed = $false
    foreach ($prefix in $allowedPrefixes) {
        if ($resolvedTarget.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { $insideAllowed = $true; break }
    }
    if (-not $insideAllowed) { throw "Target outside explicit video cleanup roots: $relativePath" }
    if ($protectedSet.Contains($relativePath.Replace('/', '\'))) { throw "Protected target appeared in deletion manifest: $relativePath" }
    $parent = [IO.Path]::GetDirectoryName($resolvedTarget)
    while ($parent -ne $taskRoot) {
        if ($safeParents.Contains($parent)) { break }
        $item = Get-Item -LiteralPath $parent -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Parent is a reparse point: $relativePath" }
        [void]$safeParents.Add($parent)
        $parent = [IO.Path]::GetDirectoryName($parent)
    }
    return $resolvedTarget
}

# Preflight all absolute targets before performing any deletion. Input text is
# data, never a command. No recursive removal or cross-shell deletion is used.
$targets = [Collections.Generic.List[object]]::new()
$duplicateHashes = @{}
foreach ($row in $manifest.files) {
    $target = Get-CheckedTarget $row.path
    $item = Get-Item -LiteralPath $target -Force
    if ($item.PSIsContainer -or (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw "Not a regular file: $($row.path)" }
    if ($item.Length -ne [long]$row.bytes) { throw "Size changed before execution: $($row.path)" }
    if ($row.retained_duplicate) {
        $retainedPath = [IO.Path]::GetFullPath((Join-Path $taskRoot $row.retained_duplicate.Replace('/', '\')))
        if (-not $retainedPath.StartsWith($taskPrefix, [StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $retainedPath -PathType Leaf)) { throw "Missing retained duplicate: $($row.path)" }
        if (-not $duplicateHashes.ContainsKey($retainedPath)) { $duplicateHashes[$retainedPath] = (Get-FileHash -LiteralPath $retainedPath -Algorithm SHA256).Hash.ToLowerInvariant() }
        if ($duplicateHashes[$retainedPath] -ne $row.sha256) { throw "Retained duplicate content differs: $($row.path)" }
    }
    $targets.Add([pscustomobject]@{ Row = $row; AbsolutePath = $target })
}
if (-not $Execute) {
    [pscustomobject]@{ status = 'dry_run_paths_validated'; files = $targets.Count; logical_bytes = $manifest.delete_logical_bytes; master_guide_exists = (Test-Path -LiteralPath $masterGuidePath); recursive_delete = $false } | ConvertTo-Json -Compress
    exit 0
}

if (-not (Test-Path -LiteralPath $masterGuidePath -PathType Leaf)) { throw 'Complete the master feedback guide before deletion.' }
if (-not (Test-Path -LiteralPath $reviewPath -PathType Leaf)) { throw 'Missing independent retention review.' }
$review = Get-Content -LiteralPath $reviewPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($review.approved -ne $true -or $review.required_open -ne 0) { throw 'Retention review still has required issues.' }
$actualManifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($review.delete_manifest_sha256 -ne $actualManifestHash) { throw 'The reviewed deletion manifest has changed.' }
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'deletion_result.json')) { throw 'This deletion run already has a result; create a new run instead.' }

$drive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($taskRoot))
$freeBefore = $drive.AvailableFreeSpace
$removed = [Collections.Generic.List[object]]::new()
$failed = [Collections.Generic.List[object]]::new()
$logPath = Join-Path $PSScriptRoot 'deletion_events.jsonl'
$encoding = [Text.UTF8Encoding]::new($false)
$log = [IO.StreamWriter]::new($logPath, $false, $encoding)
$log.AutoFlush = $true
try {
    foreach ($entry in $targets) {
        $row, $target = $entry.Row, $entry.AbsolutePath
        try {
            $item = Get-Item -LiteralPath $target -Force
            if ($item.PSIsContainer -or (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw 'File became a directory or reparse point.' }
            if ($item.Length -ne [long]$row.bytes) { throw 'File length changed.' }
            $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($hash -ne $row.sha256) { throw 'File contents changed after planning.' }
            Remove-Item -LiteralPath $target -Force
            if (Test-Path -LiteralPath $target) { throw 'The file still exists.' }
            $event = [pscustomobject]@{ path = $row.path; bytes = [long]$row.bytes; sha256 = $hash; status = 'deleted'; reason = $row.reason }
            $removed.Add($event)
        }
        catch {
            $event = [pscustomobject]@{ path = $row.path; bytes = [long]$row.bytes; status = 'skipped_or_failed'; error = $_.Exception.Message }
            $failed.Add($event)
        }
        $log.WriteLine(($event | ConvertTo-Json -Compress))
    }
}
finally { $log.Dispose() }

$result = [ordered]@{
    status = 'files_deleted_pending_protection_verification'
    completed_at_utc = [DateTime]::UtcNow.ToString('o')
    manifest_sha256 = $actualManifestHash
    deleted_files = $removed.Count
    deleted_logical_bytes = [long](($removed | Measure-Object -Property bytes -Sum).Sum)
    failed_or_skipped_files = $failed.Count
    failures = @($failed.ToArray())
    volume_free_before_bytes = $freeBefore
    volume_free_after_bytes = ([IO.DriveInfo]::new([IO.Path]::GetPathRoot($taskRoot))).AvailableFreeSpace
    physical_space_note = 'Volume free-space delta is observed, may include concurrent system writes, and does not double-count hardlink aliases.'
    recursive_delete_used = $false
    original_data_auth_conversations_targeted = $false
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'deletion_result.json'), ($result | ConvertTo-Json -Depth 8), $encoding)
[pscustomobject]@{ status = $result.status; deleted_files = $removed.Count; logical_GiB = [Math]::Round($result.deleted_logical_bytes / 1GB, 3); failed_or_skipped_files = $failed.Count; volume_free_delta_GiB = [Math]::Round(($result.volume_free_after_bytes - $freeBefore) / 1GB, 3) } | ConvertTo-Json -Compress
