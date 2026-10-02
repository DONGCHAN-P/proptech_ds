# metrics/ — 지표 계산 (DuckDB 단독 SQL)

Python 메모리 연산 없이 DuckDB SQL로만 계산해 `output/metrics_YYYYMMDD.json` 으로 내보낸다.
공통 필터(해제 제외·소규모 단지 제외·층 구간화)는 `filters.sql` 공통 CTE로 강제한다. (T8/T9)
