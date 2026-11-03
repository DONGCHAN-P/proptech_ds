$ErrorActionPreference = 'Stop'
$workspace = [System.IO.Path]::GetFullPath('C:\projects\realestate_reco').TrimEnd('\')
$auditRoot = Join-Path $workspace 'output\cleanup-20261015'
$allowed = @((Join-Path $workspace 'video-agent-studio\episodes\namyangju-wangsuk-20261014'),(Join-Path $workspace 'video\out'),(Join-Path $workspace 'video\node_modules\.cache'))
$dirs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($name in @('deletion_result_video.json','deletion_result_bundle.json','deletion_result_cache.json')) {
  $r = Get-Content -LiteralPath (Join-Path $auditRoot $name) -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($row in $r.results) {
    if ($row.status -ne 'deleted') { continue }
    $p = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($row.path))
    while ($p) {
      $inside = $false
      foreach ($a in $allowed) { if ($p.StartsWith($a + '\',[System.StringComparison]::OrdinalIgnoreCase)) {$inside=$true} }
      if (-not $inside) { break }
      [void]$dirs.Add($p)
      $p = [System.IO.Path]::GetDirectoryName($p)
    }
  }
}
$removed = [System.Collections.Generic.List[string]]::new()
foreach ($p in ($dirs | Sort-Object Length -Descending)) {
  if (-not (Test-Path -LiteralPath $p -PathType Container)) { continue }
  $item = Get-Item -LiteralPath $p -Force
  if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
  if (@(Get-ChildItem -LiteralPath $p -Force).Count -eq 0) {
    Remove-Item -LiteralPath $p -Force
    $removed.Add($p)
  }
}
$result = @{removed_empty_directories=$removed.Count;paths=$removed;recursive_delete_used=$false}
[System.IO.File]::WriteAllText((Join-Path $auditRoot 'empty_directories_removed.json'),($result | ConvertTo-Json -Depth 5),[System.Text.UTF8Encoding]::new($false))
Write-Output "Removed empty directories: $($removed.Count)"
