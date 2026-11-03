param([ValidateSet('previews','check','body','visual-review','silent-review')][string]$Mode='previews',[string]$TimingLock='',[ValidatePattern('^v[0-9]+$')][string]$PreviewVersion='v1')
$ErrorActionPreference='Stop'
$repoRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../../../..')).Path
$episodeRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$projectRoot=Join-Path $episodeRoot 'outputs/production-v1-jun/project'
$checksRoot=Join-Path $episodeRoot 'outputs/production-v1-jun/checks'
$manifest=Get-Content -LiteralPath (Join-Path $episodeRoot 'outputs/production-v1-jun/reusable_assets/manifest.json') -Encoding UTF8 -Raw|ConvertFrom-Json
$env:PATH=(Split-Path -Parent $manifest.ffmpeg)+';'+$env:PATH
# Use installed binaries in place. Never copy executable files to evade permissions.
if($Mode -in @('visual-review','silent-review')){
  $reviewChecks=Join-Path $checksRoot 'visual-review'
  if((Test-Path (Join-Path $reviewChecks 'owner.json')) -and -not (Test-Path (Join-Path $reviewChecks 'render_exit.json'))){throw 'Owned visual-review render active; do not rebuild or duplicate'}
  if(Test-Path (Join-Path $episodeRoot 'outputs/production-v1-jun/previews/full_visual_review_body_v1.mp4')){throw 'Preserve rendered body; run assemble_visual_review.py separately'}
  $savedPreference=$ErrorActionPreference
  try{$ErrorActionPreference='Continue'; & (Join-Path $repoRoot 'tools/python311/python.exe') -X utf8 (Join-Path $PSScriptRoot 'prepare_visual_review.py'); $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
  if($nativeExit -ne 0){throw 'Provisional visual-review preparation failed'}
  Push-Location $projectRoot
  try{
    $savedPreference=$ErrorActionPreference
    try{$ErrorActionPreference='Continue'; & npx.cmd --offline --no-install hyperframes@0.8.181 render --composition visual-review.html --output ../previews/full_visual_review_body_v1.mp4 --fps 30 --quality looks --workers 2 --experimental-fast-capture=false --strict 2>&1 | Out-File -Encoding utf8 (Join-Path $reviewChecks 'render_body.log'); $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
    if($nativeExit -ne 0){throw 'Visual-review body render failed'}
  }finally{Pop-Location}
  $savedPreference=$ErrorActionPreference
  try{$ErrorActionPreference='Continue'; & (Join-Path $repoRoot 'tools/python311/python.exe') -X utf8 (Join-Path $PSScriptRoot 'assemble_visual_review.py'); $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
  if($nativeExit -ne 0){throw 'BGM-only review assembly failed'}
  exit 0
}
if($Mode -eq 'body'){
  if(-not $TimingLock){throw '실제 Jun timing_lock.json 경로가 필요합니다.'}
  $savedPreference=$ErrorActionPreference
  try{$ErrorActionPreference='Continue'; & (Join-Path $repoRoot 'tools/python311/python.exe') -X utf8 (Join-Path $PSScriptRoot 'build.py') --timing-lock $TimingLock; $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
  if($nativeExit -ne 0){throw '타임록 검증/재빌드 실패'}
  $savedPreference=$ErrorActionPreference
  try{$ErrorActionPreference='Continue'; & (Join-Path $repoRoot 'tools/python311/python.exe') -X utf8 (Join-Path $PSScriptRoot 'validate_audio_lock.py'); $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
  if($nativeExit -ne 0){throw '실제 음성 길이/스트림 검증 실패'}
}
Push-Location $projectRoot
try{
  if($Mode -eq 'check'){
    $savedPreference=$ErrorActionPreference
    try{$ErrorActionPreference='Continue'; & npx.cmd --no-install hyperframes check --samples 12 --snapshots --json | Out-File -LiteralPath (Join-Path $checksRoot 'hyperframes_check.json') -Encoding utf8; $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
    if($nativeExit -ne 0){throw 'HyperFrames check 실패: checks/hyperframes_check.json 확인'}
  }elseif($Mode -eq 'previews'){
    foreach($name in @('full2006paths','incheon2008-2016recovery','rawmedianvsindex')){
      if(Test-Path -LiteralPath "../previews/${name}_provisional_${PreviewVersion}.mp4"){throw '기존 원본 보존: 새 -PreviewVersion 값을 지정하세요.'}
      $savedPreference=$ErrorActionPreference
      try{$ErrorActionPreference='Continue'; & npx.cmd --no-install hyperframes render --composition "preview/$name.html" --output "../previews/${name}_provisional_${PreviewVersion}.mp4" --fps 30 --quality looks --workers 1 2>&1 | Tee-Object -FilePath (Join-Path $checksRoot "render_${name}_${PreviewVersion}.log"); $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
      if($nativeExit -ne 0){throw "프리뷰 렌더 실패: $name (권한 오류면 총괄에게 해당 명령 전달)"}
    }
  }else{
    $resolved=Get-Content -LiteralPath 'timing_resolved.json' -Encoding UTF8 -Raw|ConvertFrom-Json
    if(-not $resolved.timing_locked){throw '추정 타이밍 본편 렌더 금지'}
    $savedPreference=$ErrorActionPreference
    try{$ErrorActionPreference='Continue'; & npx.cmd --no-install hyperframes check --samples 39 --json | Out-File -LiteralPath (Join-Path $checksRoot 'actual_timing_check.json') -Encoding utf8; $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
    if($nativeExit -ne 0){throw '실제 타이밍 검사 실패'}
    $savedPreference=$ErrorActionPreference
    try{$ErrorActionPreference='Continue'; & npx.cmd --no-install hyperframes render --output ../previews/body_actual_jun_v1.mp4 --fps 30 --quality delivery --workers 1; $nativeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$savedPreference}
    if($nativeExit -ne 0){throw '본문 렌더 실패'}
  }
}finally{Pop-Location}
