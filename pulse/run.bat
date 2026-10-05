@echo off
chcp 65001 >nul
REM 평소지도 - 자기 평소와 견주는 수도권 실거래 지도
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [!] .venv 를 찾을 수 없습니다. 프로젝트 루트에서 가상환경을 먼저 만드세요.
  pause
  exit /b 1
)
if not exist "pulse\cache\sgg_now.parquet" (
  echo 전처리가 없어 먼저 만듭니다 ^(약 2초^)...
  .venv\Scripts\python.exe -m pulse.build_pulse
)
echo 서버 기동 중... http://127.0.0.1:8001
start "" http://127.0.0.1:8001
.venv\Scripts\python.exe -m uvicorn pulse.main:app --host 127.0.0.1 --port 8001
pause
