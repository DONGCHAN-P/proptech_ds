$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$units=Get-Content -Raw -Encoding UTF8 "$PSScriptRoot/units.json" | ConvertFrom-Json
$voice=New-Object -ComObject SAPI.SpVoice
$token=@($voice.GetVoices() | Where-Object {$_.GetDescription() -match 'Heami'})[0]
if (!$token) {throw 'Korean Heami voice not installed'}
$voice.Voice=$token
$voice.Rate=-1
$voice.Volume=100
$dest=Join-Path $PSScriptRoot '../../outputs/production-v6-preview/audio'
foreach ($u in $units) {
  $stream=New-Object -ComObject SAPI.SpFileStream
  $stream.Format.Type=22
  $stream.Open((Join-Path $dest $u.file),3,$false)
  $voice.AudioOutputStream=$stream
  [void]$voice.Speak($u.spoken_text,0)
  $stream.Close()
}
Write-Output "Generated $($units.Count) semantic WAV units with $($token.GetDescription()), rate -1"
