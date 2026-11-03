param([Parameter(Mandatory=$true)][string]$PlanPath, [Parameter(Mandatory=$true)][string]$ReceiptPath)
$ErrorActionPreference = 'Stop'
$workspace = [System.IO.Path]::GetFullPath('C:\projects\realestate_reco').TrimEnd('\')
$approvedRoots = @(
  (Join-Path $workspace 'video-agent-studio\episodes\namyangju-wangsuk-20261014'),
  (Join-Path $workspace 'video\out'),
  (Join-Path $workspace 'video\public'),
  (Join-Path $workspace 'video\build'),
  (Join-Path $workspace 'video\.remotion'),
  (Join-Path $workspace 'video\node_modules\.cache'),
  (Join-Path $workspace '.remotion')
)
$guideReceipt = Join-Path $workspace 'output\cleanup-20261015\guide_complete.json'
if (-not (Test-Path -LiteralPath $guideReceipt -PathType Leaf)) { throw 'Guide completion receipt missing' }
$guide = Get-Content -LiteralPath $guideReceipt -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($entry in $guide.files) {
  $gp = [System.IO.Path]::GetFullPath($entry.path)
  if (-not $gp.StartsWith($workspace + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Guide path outside workspace' }
  if ((Get-FileHash -LiteralPath $gp -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Guide changed after completion check' }
}
$planFull = [System.IO.Path]::GetFullPath($PlanPath)
$receiptFull = [System.IO.Path]::GetFullPath($ReceiptPath)
if (-not $planFull.StartsWith((Join-Path $workspace 'output\cleanup-20261015\'), [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Unapproved plan location' }
if (-not $receiptFull.StartsWith((Join-Path $workspace 'output\cleanup-20261015\'), [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Unapproved receipt location' }
if (Test-Path -LiteralPath $receiptFull) { throw 'Receipt exists; do not silently repeat cleanup' }
$plan = Get-Content -LiteralPath $planFull -Raw -Encoding UTF8 | ConvertFrom-Json
$protected = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$protectedFile = Join-Path $workspace 'output\cleanup-20261015\protected.json'
if (Test-Path -LiteralPath $protectedFile) {
  $protectData = Get-Content -LiteralPath $protectedFile -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($protectData.files) { foreach ($p in $protectData.files) { [void]$protected.Add($p.absolutePath) } }
}
$targets = [System.Collections.Generic.List[object]]::new()
foreach ($row in $plan.files) {
  if ($row.status -ne 'delete') { throw 'Plan contains non-delete row' }
  $full = [System.IO.Path]::GetFullPath($row.absolutePath)
  $allowed = $false
  foreach ($prefix in $approvedRoots) { if ($full.StartsWith($prefix.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) { $allowed = $true } }
  if (-not $allowed -or -not $full.StartsWith($workspace + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw "Target outside approved video roots: $full" }
  if ($protected.Contains($full)) { throw "Protected file selected: $full" }
  if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Expected file missing: $full" }
  $item = Get-Item -LiteralPath $full -Force
  if ($item.Length -ne [long]$row.bytes) { throw "File size changed since audit: $full" }
  $ancestor = $item
  while ($ancestor -and $ancestor.FullName -ne $workspace) {
    if (($ancestor.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse point rejected: $full" }
    if ($ancestor -is [System.IO.FileInfo]) { $ancestor = $ancestor.Directory } else { $ancestor = $ancestor.Parent }
  }
  $targets.Add([PSCustomObject]@{path=$full;bytes=$item.Length;reason=$row.reason})
}
$results = [System.Collections.Generic.List[object]]::new()
foreach ($target in $targets) {
  try {
    Remove-Item -LiteralPath $target.path -Force -ErrorAction Stop
    if (Test-Path -LiteralPath $target.path) { throw 'File remains after removal' }
    $results.Add([PSCustomObject]@{path=$target.path;bytes=$target.bytes;status='deleted';reason=$target.reason})
  } catch {
    $results.Add([PSCustomObject]@{path=$target.path;bytes=$target.bytes;status='failed';reason=$_.Exception.Message})
  }
}
$deleted = @($results | Where-Object status -eq 'deleted')
$failed = @($results | Where-Object status -eq 'failed')
$report = [PSCustomObject]@{finished_at=[DateTimeOffset]::Now.ToString('o');plan=$planFull;delete_method='PowerShell Remove-Item -LiteralPath file-by-file; no recursive deletion';deleted_count=$deleted.Count;deleted_bytes=($deleted | Measure-Object -Property bytes -Sum).Sum;failed_count=$failed.Count;results=$results}
$json = $report | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($receiptFull,$json,[System.Text.UTF8Encoding]::new($false))
$report | Select-Object deleted_count,deleted_bytes,failed_count | ConvertTo-Json
