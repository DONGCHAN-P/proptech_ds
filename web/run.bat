@echo off
chcp 65001 >nul
REM 집값지도 - 호갱노노 스타일 실거래 지도 웹서버
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [!] .venv 를 찾을 수 없습니다. 프로젝트 루트에서 가상환경을 먼저 만드세요.
  pause
  exit /b 1
)
echo 서버 기동 중... http://127.0.0.1:8000
start "" http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn web.main:app --host 127.0.0.1 --port 8000
pause
