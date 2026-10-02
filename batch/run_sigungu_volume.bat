@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
cd /d "%~dp0.."

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value 2^>nul') do set DT=%%a
set YYYYMMDD=%DT:~0,8%

set LOG_DIR=exports\daily
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG=%LOG_DIR%\sigungu_volume_log_%YYYYMMDD%.txt

set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
    echo [ERROR] %PY% not found
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8
"%PY%" run_sigungu_volume.py > "%LOG%" 2>&1
set RC=%ERRORLEVEL%

type "%LOG%"
echo.
echo --------------------------------------------------
echo  Exit code : %RC%
echo  CSV       : %LOG_DIR%\sigungu_volume_%YYYYMMDD%.csv
echo  Parquet   : %LOG_DIR%\sigungu_volume_%YYYYMMDD%.parquet
echo  PNG       : %LOG_DIR%\sigungu_volume_%YYYYMMDD%.png
echo  Viewer    : %LOG_DIR%\sigungu_volume_viewer.html
echo --------------------------------------------------

if "%1"=="" pause
exit /b %RC%

