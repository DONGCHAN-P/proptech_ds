$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$units=Get-Content -Raw -Encoding UTF8 "$PSScriptRoot/units_prepared.json" | ConvertFrom-Json
$voice=New-Object -ComObject SAPI.SpVoice
$token=@($voice.GetVoices() | Where-Object {$_.GetDescription() -match 'Heami'})[0]
if (!$token) {throw 'Korean Heami voice not installed'}
$voice.Voice=$token
$voice.Rate=2
$voice.Volume=100
$dest=Join-Path $PSScriptRoot '../../outputs/production-v5/audio'
New-Item -ItemType Directory -Force $dest | Out-Null
foreach ($u in $units) {
  $target=Join-Path $dest $u.file
  if ((Test-Path $target) -and (Get-Item -LiteralPath $target).Length -gt 200) {continue}
  $stream=New-Object -ComObject SAPI.SpFileStream
  $stream.Format.Type=22
  $stream.Open($target,3,$false)
  $voice.AudioOutputStream=$stream
  [void]$voice.Speak($u.spoken_text,0)
  $stream.Close()
}
Write-Output "Generated $($units.Count) phrase WAV units; local Heami rate2; paid calls0"
