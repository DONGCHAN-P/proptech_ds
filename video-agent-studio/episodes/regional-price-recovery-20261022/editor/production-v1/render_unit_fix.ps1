# Reproduce only the Incheon REQ-01 correction using installed CLI0.8.181.
$ErrorActionPreference='Stop'
$episodeRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$projectRoot=Join-Path $episodeRoot 'outputs/production-v1-jun/project'
$outputRoot=Join-Path $episodeRoot 'outputs/production-v1-jun'
$manifest=Get-Content -LiteralPath (Join-Path $outputRoot 'reusable_assets/manifest.json') -Encoding UTF8 -Raw|ConvertFrom-Json
$env:PATH=(Split-Path -Parent $manifest.ffmpeg)+';'+$env:PATH
Push-Location $projectRoot
try{
  if(Test-Path -LiteralPath '../previews/incheon2008-2016recovery_provisional_v3.mp4'){throw 'v3 already exists; preserve it'}
  $saved=$ErrorActionPreference
  try{
    $ErrorActionPreference='Continue'
    & npx.cmd --offline --no-install hyperframes@0.8.181 render --composition preview/incheon2008-2016recovery.html --output ../previews/incheon2008-2016recovery_provisional_v3.mp4 --fps 30 --quality looks --workers 1 --experimental-fast-capture=false 2>&1 | Out-File -Encoding utf8 ../checks/fix_req01/render_incheon_v3.log
    $nativeExit=$LASTEXITCODE
  }finally{$ErrorActionPreference=$saved}
  if($nativeExit -ne 0){throw "Incheon v3 render failed: $nativeExit"}
}finally{Pop-Location}
