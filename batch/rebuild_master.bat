@echo off
rem ============================================================
rem  Master Rebuild Script
rem  Patch v1.1 (2026-05-03)
rem  - apt_id ?뺤쓽媛 吏꾩쭨 ?됱젙肄붾뱶(umd_cd) 湲곕컲?쇰줈 諛붾뚯뼱
rem    紐⑤뱺 master ?뚯씠釉붿쓣 ??踰??щ퉴?쒗빐???⑸땲??
rem  - ??踰덈쭔 --force, ?댄썑??硫깅벑???뚮줈濡????곗씠?곕쭔 泥섎━.
rem ============================================================

setlocal
cd /d "%~dp0.."

echo.
echo === [1/5] venv activate ===
call .venv\Scripts\activate

echo.
echo === [2/5] Step 2: raw XML -^> staged parquet + apt_id_map (force rebuild) ===
python run_step2.py --force
if errorlevel 1 goto :error

echo.
echo === [3/5] Step 3: master/trade_events.parquet ===
python run_step3.py
if errorlevel 1 goto :error

echo.
echo === [4/5] Step 4: master/unified_apt_pyeong_daily.parquet ===
python run_step4_unified_daily.py
if errorlevel 1 goto :error

echo.
echo === [5/5] Step 6: regional_weights.json (backtest fixed) ===
python run_step6_model.py
if errorlevel 1 goto :error

echo.
echo === Step 7: undervalue Top 5 per sigungu (daily export) ===
python run_step7_undervalue.py
if errorlevel 1 goto :error

echo.
echo ============================================================
echo  REBUILD COMPLETE
echo  Verify:
echo    - master\trade_events.parquet  (rows must match backup +/-5%%)
echo    - master\apt_id_map.parquet    (apt_id is now 16-hex of real legal_dong_code)
echo    - config\regional_weights.json (backtest period updated)
echo    - exports\daily\undervalue_top5_*.csv
echo ============================================================
goto :end

:error
echo.
echo ============================================================
echo  ERROR: pipeline failed. master.backup_* ?대뜑濡?濡ㅻ갚 媛??
echo ============================================================
exit /b 1

:end
endlocal

