-- final-api-20261103-v2 폴더를 작업 디렉터리로 사용합니다.
-- 공개 API의 정상 복수 행을 중복 제거하지 않습니다. 고유 계약ID 기반 추가 삭제는 없습니다.
SELECT region_id, count(*) AS n, count(DISTINCT api_complex_id) AS complex_count,
       median(deal_amount_manwon) AS median_manwon,
       min(deal_date) AS first_observed_contract, max(deal_date) AS last_observed_contract
FROM read_parquet('api_rows_all.parquet')
WHERE deal_date >= '2026-05-01' AND deal_date <= '2026-10-31'
  AND area_m2 BETWEEN 83 AND 85 AND deal_amount_manwon > 0
  AND coalesce(cdealType, '') = '' AND coalesce(cdealDay, '') = ''
GROUP BY region_id ORDER BY region_id;
