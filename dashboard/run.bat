@echo off
REM ─────────────────────────────────────────────────────────────
REM 대시보드 실행 (Windows)
REM 사용법: dashboard\run.bat
REM ─────────────────────────────────────────────────────────────

cd /d "%~dp0\.."
call .venv\Scripts\activate
streamlit run dashboard\app.py
