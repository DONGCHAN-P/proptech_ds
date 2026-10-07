# 작업 스케줄러 등록 — 아침 후보 발송 + 봇 상주 (T23)
#
#   proptech_ds 아침브리핑   매일 08:00   후보 5곳을 텔레그램으로
#   proptech_ds 봇           로그온 시    번호 답장을 받는 상주 프로세스
#
# 봇은 상주해야 번호를 받는다. 로그온 시 한 번 띄우고, 죽으면 다시 띄운다
# (RestartCount). 아침 발송은 봇과 따로 둔다 — 봇이 죽어 있어도 후보는
# 와야 "봇이 죽었구나"를 알 수 있다.
#
# 실행:  powershell -ExecutionPolicy Bypass -File notify\install_tasks.ps1
# 해제:  powershell -ExecutionPolicy Bypass -File notify\install_tasks.ps1 -Remove

param(
  [switch]$Remove,
  [string]$At = "08:00"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py   = Join-Path $root ".venv\Scripts\python.exe"
$pyw  = Join-Path $root ".venv\Scripts\pythonw.exe"   # 창 없이
$TASK_BRIEF = "proptech_ds 아침브리핑"
$TASK_BOT   = "proptech_ds 봇"

function Drop($name) {
  if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Host "  해제: $name"
  } else {
    Write-Host "  없음: $name"
  }
}

if ($Remove) {
  Write-Host "`n작업 해제"
  Drop $TASK_BRIEF
  Drop $TASK_BOT
  Write-Host ""
  exit 0
}

if (-not (Test-Path $py)) { throw ".venv 를 찾을 수 없습니다: $py" }
$run = if (Test-Path $pyw) { $pyw } else { $py }

Write-Host "`n작업 등록"
Write-Host "  경로: $root"
Write-Host "  파이썬: $run"

# ── 아침 브리핑 ──────────────────────────────────────────────────────────
Drop $TASK_BRIEF
$a1 = New-ScheduledTaskAction -Execute $run `
        -Argument "-m notify.bot --morning" -WorkingDirectory $root
$t1 = New-ScheduledTaskTrigger -Daily -At $At
# 노트북이 배터리일 때도 돌아야 하고, 꺼져 있던 시간은 깨어나자마자 따라잡는다
$s1 = New-ScheduledTaskSettingsSet -StartWhenAvailable `
        -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName $TASK_BRIEF -Action $a1 -Trigger $t1 `
  -Settings $s1 -Description "단지 후보 5곳을 텔레그램으로 보낸다" | Out-Null
Write-Host "  등록: $TASK_BRIEF  (매일 $At)"

# ── 봇 상주 ──────────────────────────────────────────────────────────────
Drop $TASK_BOT
$a2 = New-ScheduledTaskAction -Execute $run `
        -Argument "-m notify.bot" -WorkingDirectory $root
# 사용자를 적지 않으면 "모든 사용자" 작업이 되어 관리자 권한을 요구한다.
$me = "$env:USERDOMAIN\$env:USERNAME"
$t2 = New-ScheduledTaskTrigger -AtLogOn -User $me
# 롱폴링은 끝나지 않는 일이다. 시간 제한을 걸면 스케줄러가 죽인다.
$s2 = New-ScheduledTaskSettingsSet -StartWhenAvailable `
        -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -RestartInterval (New-TimeSpan -Minutes 5) -RestartCount 999
Register-ScheduledTask -TaskName $TASK_BOT -Action $a2 -Trigger $t2 `
  -Settings $s2 -User $me `
  -Description "텔레그램 번호 답장을 받아 영상을 만든다" | Out-Null
Write-Host "  등록: $TASK_BOT  (로그온 시, 죽으면 5분 뒤 재시작)"

Write-Host "`n확인:  Get-ScheduledTask -TaskName 'proptech_ds*'"
Write-Host "지금 한 번 돌려보기:  Start-ScheduledTask -TaskName '$TASK_BRIEF'"
Write-Host ""
