$ErrorActionPreference = 'Stop'
$root = 'C:/projects/realestate_reco'
$editor = "$root/video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v8-jun"
Set-Location -LiteralPath $root
foreach ($stage in @('timeline','preflight','render','assembly','evidence')) {
  & "$root/tools/python311/python.exe" -X utf8 "$editor/jobs.py" $stage
  if ($LASTEXITCODE -ne 0) { throw "Job preparation failed: $stage" }
  & "$root/tools/python311/python.exe" -X utf8 "$root/analysis/video_task_runner.py" "$editor/${stage}_job.json"
  if ($LASTEXITCODE -ne 0) { throw "Job failed: $stage" }
}
& "$root/tools/python311/python.exe" -X utf8 "$editor/timing_audit.py"
if ($LASTEXITCODE -ne 0) { throw 'Timing audit failed' }
& "$root/tools/python311/python.exe" -X utf8 "$editor/handoff.py"
if ($LASTEXITCODE -ne 0) { throw 'Handoff verification failed' }
