param([Parameter(Mandatory=$true)][string]$FFmpegBin)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../../../../..')).Path
$out=Join-Path $PSScriptRoot '../../outputs/editor-preflight-v1'
$files=@(
 'video/public/namyangju-v13/brand_intro_no_caption.mp4',
 'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/caption-station-v13/brand_outro_v13_no_caption.mp4',
 'video/public/namyangju-map-led-v6/data_city_ambient_v1.wav',
 'video-agent-studio/episodes/goyang-changneung-20261015/outputs/editor-preflight-v1/brand_intro_generic_v1.mp4',
 'video-agent-studio/episodes/goyang-changneung-20261015/outputs/editor-preflight-v1/brand_outro_generic_v1.mp4'
)
$results=@()
foreach($relative in $files){
 $file=Join-Path $repo $relative
 $probe=(& (Join-Path $FFmpegBin 'ffprobe.exe') -v error -show_streams -show_format -of json $file | Out-String | ConvertFrom-Json)
 if($LASTEXITCODE -ne 0){throw "probe failed: $relative"}
 & (Join-Path $FFmpegBin 'ffmpeg.exe') -v error -i $file -f null - 2> (Join-Path $out ((Split-Path $file -Leaf)+'.decode.log'))
 if($LASTEXITCODE -ne 0){throw "decode failed: $relative"}
 $results+=@{path=$relative;sha256=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLower();bytes=(Get-Item -LiteralPath $file).Length;probe=$probe;whole_decode_passed=$true;actual_listening=$false;continuous_playback=$false}
}
$results | ConvertTo-Json -Depth 15 | Set-Content -Encoding UTF8 (Join-Path $out 'asset_technical.json')
foreach($name in @('brand_intro_generic_v1','brand_outro_generic_v1')){
 foreach($seconds in @(0.5,2,4.8)){
  & (Join-Path $FFmpegBin 'ffmpeg.exe') -v error -y -ss $seconds -i (Join-Path $out ($name+'.mp4')) -frames:v 1 (Join-Path $out ($name+'_'+$seconds+'.png'))
  if($LASTEXITCODE -ne 0){throw 'frame extraction failed'}
 }
}
& (Join-Path $FFmpegBin 'ffmpeg.exe') -v error -y -ss 9 -i (Join-Path $out 'brand_outro_generic_v1.mp4') -frames:v 1 (Join-Path $out 'brand_outro_generic_v1_9.png')
if($LASTEXITCODE -ne 0){throw 'outro hold extraction failed'}
Write-Output 'asset_technical.json and 7 representative frames written'
