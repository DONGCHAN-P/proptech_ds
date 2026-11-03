$ErrorActionPreference = 'Continue'
$result = [ordered]@{
  checked_at_utc = [DateTime]::UtcNow.ToString('o')
  generation_invoked = $false
  network_requests = 0
  system_speech = $null
  sapi_com = $null
  registry_voices = @()
}
try {
  Add-Type -AssemblyName System.Speech -ErrorAction Stop
  $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $voices = @($synth.GetInstalledVoices() | ForEach-Object { [ordered]@{ name=$_.VoiceInfo.Name; culture=$_.VoiceInfo.Culture.Name; enabled=$_.Enabled } })
  $result.system_speech = [ordered]@{ status='enumerated'; voices=$voices }
  $synth.Dispose()
} catch { $result.system_speech = [ordered]@{ status='failed'; exception=$_.Exception.GetType().Name; reason='Installed voice enumeration failed; no synthesis attempted' } }
try {
  $sapi = New-Object -ComObject SAPI.SpVoice -ErrorAction Stop
  $items = $sapi.GetVoices()
  $voices = @()
  for ($i=0; $i -lt $items.Count; $i++) { $token=$items.Item($i); $voices += [ordered]@{ name=$token.GetDescription(); language_hex=$token.GetAttribute('Language') } }
  $result.sapi_com = [ordered]@{ status='enumerated'; voices=$voices }
} catch { $result.sapi_com = [ordered]@{ status='failed'; exception=$_.Exception.GetType().Name; reason='SAPI COM enumeration failed; no synthesis attempted' } }
foreach ($registryPath in @('HKLM:/SOFTWARE/Microsoft/Speech/Voices/Tokens','HKLM:/SOFTWARE/Microsoft/Speech_OneCore/Voices/Tokens')) {
  $result.registry_voices += @(Get-ChildItem -LiteralPath $registryPath -ErrorAction SilentlyContinue | ForEach-Object { [ordered]@{ key=$_.PSChildName; registry=$registryPath } })
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'local_windows_voices.json') -Encoding utf8
$result | ConvertTo-Json -Depth 8 -Compress
