-- prices 폴더를 작업 디렉터리로 실행합니다. SELECT만 사용합니다.
-- snapshot은 해제/결측을 포함하며 집계 시 아래 조건을 직접 적용합니다.
SELECT s.region_id, s.scene_id, s.rank::INTEGER AS rank,
       s.province, s.region,
       count(*) AS n, count(DISTINCT t.apt_id) AS complex_count,
       median(t.deal_amount) AS median_manwon,
       quantile_cont(t.deal_amount, 0.25) AS p25_manwon,
       quantile_cont(t.deal_amount, 0.75) AS p75_manwon,
       min(t.deal_date)::DATE AS first_contract,
       max(t.deal_date)::DATE AS last_contract,
       min(t.area_m2) AS actual_area_min_m2, max(t.area_m2) AS actual_area_max_m2
FROM read_parquet('snapshots/trade_events_20regions.parquet') t
JOIN read_csv('scope_codes.csv', all_varchar=true) s ON t.sigungu_code = s.current_code
WHERE t.deal_date >= DATE '2026-04-01' AND t.deal_date < DATE '2026-10-01'
  AND t.area_m2 BETWEEN 83 AND 85
  AND t.deal_amount > 0
  AND t.is_canceled IS FALSE AND t.cancel_date IS NULL
GROUP BY 1,2,3,4,5 ORDER BY rank;
