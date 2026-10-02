# collector/ — 수집 레이어

국토부 RTMS·kapt 등 외부 API에서 원본을 받아 `raw/` 에 적재한다.
현재 매매 수집은 `run_daily_update.py` 의 `fetch_rtms()` 가 담당하며,
T7(90일 롤링 upsert) 작업에서 이쪽으로 분리한다.
