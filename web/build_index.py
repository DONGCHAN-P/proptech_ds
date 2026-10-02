"""호갱노노 스타일 웹 서비스용 인덱스 빌더.

master/, legacy/realestate.db 원본을 읽어 web/cache/ 아래에
서빙 전용 파케이 4종을 만든다. 원본은 건드리지 않는다.

  trades.parquet       실거래 (apt_id 정렬) — 상세 차트/목록
  apt_pyeong.parquet   단지×평형 — 평형 필터 / 상세 평형별 시세
  apt_index.parquet    단지 1행  — 지도 마커 + 필터
  region_index.parquet 시군구·읍면동 집계 — 축소 줌 말풍선

실행:  .venv\\Scripts\\python.exe web\\build_index.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE = Path(__file__).resolve().parent.parent
MASTER = BASE / "master"
DB_PATH = BASE / "legacy" / "realestate.db"
CACHE = Path(__file__).resolve().parent / "cache"

TRADE = (MASTER / "trade_events.parquet").as_posix()
APTMAP = (MASTER / "apt_id_map.parquet").as_posix()


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute(f"ATTACH '{DB_PATH.as_posix()}' AS ext (TYPE sqlite, READ_ONLY);")
    return con


def build_trades(con: duckdb.DuckDBPyConnection) -> None:
    """취소분 제외 + apt_id 정렬. 정렬해두면 row-group 통계로 단지 조회가 빨라진다."""
    out = (CACHE / "trades.parquet").as_posix()
    con.execute(f"""
        COPY (
            SELECT apt_id, area_m2_key, pyeong_bucket, deal_date, deal_amount,
                   area_m2, floor, build_year, price_per_pyeong, price_per_m2
            FROM '{TRADE}'
            WHERE NOT is_canceled AND deal_amount > 0
            ORDER BY apt_id, deal_date
        ) TO '{out}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 60000)
    """)
    n = con.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0]
    log(f"trades.parquet  {n:,}행")


def build_apt_pyeong(con: duckdb.DuckDBPyConnection) -> None:
    """단지×평형 요약. 최근 1년 거래가 없으면 마지막 거래로 폴백."""
    trades = (CACHE / "trades.parquet").as_posix()
    out = (CACHE / "apt_pyeong.parquet").as_posix()
    con.execute(f"""
        COPY (
            WITH t AS (SELECT * FROM '{trades}'),
            maxd AS (SELECT max(deal_date) AS d FROM t),
            last_deal AS (
                SELECT apt_id, pyeong_bucket, deal_date, deal_amount, price_per_pyeong,
                       area_m2, floor,
                       row_number() OVER (PARTITION BY apt_id, pyeong_bucket
                                          ORDER BY deal_date DESC, deal_amount DESC) AS rn
                FROM t
            ),
            agg AS (
                SELECT t.apt_id, t.pyeong_bucket,
                       count(*)                                                   AS trade_total,
                       count(*) FILTER (t.deal_date >= maxd.d - INTERVAL 365 DAY)  AS trade_1y,
                       count(*) FILTER (t.deal_date >= maxd.d - INTERVAL 90 DAY)   AS trade_3m,
                       avg(t.area_m2)                                             AS area_m2,
                       max(t.deal_amount)                                         AS peak_price,
                       arg_max(t.deal_date, t.deal_amount)                        AS peak_date,
                       avg(t.price_per_pyeong) FILTER (t.deal_date >= maxd.d - INTERVAL 365 DAY) AS ppy_1y,
                       avg(t.price_per_pyeong) FILTER (t.deal_date BETWEEN maxd.d - INTERVAL 730 DAY
                                                                       AND maxd.d - INTERVAL 365 DAY) AS ppy_prev1y,
                       avg(t.price_per_pyeong) FILTER (t.deal_date BETWEEN maxd.d - INTERVAL 1460 DAY
                                                                       AND maxd.d - INTERVAL 1095 DAY) AS ppy_3y
                FROM t, maxd
                GROUP BY 1, 2
            )
            SELECT a.apt_id,
                   a.pyeong_bucket,
                   round(a.area_m2, 2)                       AS area_m2,
                   l.deal_date                               AS last_date,
                   l.deal_amount                             AS last_price,
                   round(l.price_per_pyeong)                 AS last_ppy,
                   l.floor                                   AS last_floor,
                   round(l.area_m2, 2)                       AS last_area_m2,
                   a.trade_total, a.trade_1y, a.trade_3m,
                   a.peak_price, a.peak_date,
                   round(a.ppy_1y)                           AS ppy_1y,
                   CASE WHEN a.ppy_prev1y > 0
                        THEN round((a.ppy_1y / a.ppy_prev1y - 1) * 100, 1) END AS chg_1y,
                   CASE WHEN a.ppy_3y > 0
                        THEN round((a.ppy_1y / a.ppy_3y - 1) * 100, 1) END     AS chg_3y,
                   CASE WHEN a.peak_price > 0
                        THEN round((l.deal_amount / a.peak_price - 1) * 100, 1) END AS vs_peak
            FROM agg a
            JOIN last_deal l
              ON l.apt_id = a.apt_id AND l.pyeong_bucket = a.pyeong_bucket AND l.rn = 1
        ) TO '{out}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0]
    log(f"apt_pyeong.parquet  {n:,}행")


def build_geo_bridge(con: duckdb.DuckDBPyConnection) -> None:
    """좌표 부착.

    T10a 에서 apt_id_map 을 신규 apt_id 기준으로 재생성하면서 이 함수의 존재
    이유였던 세대 불일치가 사라졌다. 예전엔 apt_id_map 이 구버전 해시라
    (시군구, 정규화명, 도로명주소) 로 이름 조인을 해야 했고, 그 과정에서
    매칭률이 2~7%p 씩 샜다. 지금은 apt_id 로 바로 붙는다.

    old_apt_id 컬럼은 하위 호환으로 남긴다 (값은 apt_id 와 같다).
    """
    out = CACHE / "apt_geo.parquet"
    m = pd.read_parquet(APTMAP, columns=["apt_id", "lat", "lng"])
    m = m[m["lat"].notna() & m["lng"].notna()]

    new = con.execute(f"SELECT DISTINCT apt_id FROM '{TRADE}'").df()
    bridge = new.merge(m, on="apt_id", how="inner")
    bridge["old_apt_id"] = bridge["apt_id"]
    bridge = bridge[["apt_id", "old_apt_id", "lat", "lng"]]
    bridge.to_parquet(out, index=False)

    rate = len(bridge) / max(len(new), 1) * 100
    log(f"apt_geo.parquet  {len(bridge):,}행  "
        f"(좌표 매칭 {rate:.1f}%, 미매칭 {len(new) - len(bridge):,})")


def build_apt_index(con: duckdb.DuckDBPyConnection) -> None:
    """단지 1행. 대표 평형 = 최근 1년 거래가 가장 많은 평형(없으면 전체 최다)."""
    trades = (CACHE / "trades.parquet").as_posix()
    pyeong = (CACHE / "apt_pyeong.parquet").as_posix()
    geo = (CACHE / "apt_geo.parquet").as_posix()
    out = (CACHE / "apt_index.parquet").as_posix()
    con.execute(f"""
        COPY (
            WITH rep AS (
                SELECT apt_id, pyeong_bucket,
                       row_number() OVER (PARTITION BY apt_id
                                          ORDER BY trade_1y DESC, trade_total DESC,
                                                   last_date DESC) AS rn
                FROM '{pyeong}'
            ),
            tot AS (
                SELECT apt_id,
                       max(build_year)               AS build_year,
                       count(*)                      AS trade_total,
                       max(deal_date)                AS last_date,
                       count(DISTINCT pyeong_bucket) AS pyeong_cnt
                FROM '{trades}' GROUP BY 1
            ),
            m AS (
                SELECT apt_id,
                       mode(apt_name_raw)      AS apt_name,
                       any_value(sigungu_code) AS sigungu_code,
                       any_value(sigungu_name) AS sigungu_name,
                       mode(legal_dong_code)   AS legal_dong_code,
                       mode(legal_dong_name)   AS legal_dong_name,
                       mode(road_address)      AS road_address
                FROM '{TRADE}' GROUP BY 1
            )
            SELECT m.apt_id,
                   m.apt_name,
                   m.sigungu_code, m.sigungu_name,
                   m.legal_dong_code, m.legal_dong_name,
                   m.road_address,
                   g.lat, g.lng,
                   CASE substr(m.sigungu_code, 1, 2)
                        WHEN '11' THEN '서울' WHEN '28' THEN '인천'
                        WHEN '41' THEN '경기' END AS region,
                   tot.build_year, tot.trade_total, tot.pyeong_cnt, tot.last_date,
                   p.pyeong_bucket AS rep_pyeong,
                   p.area_m2       AS rep_area,
                   p.last_price    AS rep_price,
                   p.last_ppy      AS rep_ppy,
                   p.ppy_1y        AS rep_ppy_1y,
                   p.chg_1y, p.chg_3y, p.vs_peak,
                   p.trade_1y, p.trade_3m,
                   p.peak_price, p.peak_date,
                   e.nearest_station, e.nearest_station_dist, e.nearest_line,
                   e.line_grade, e.walk_min,
                   e.elem_school_cnt_1km, e.nearest_school_dist,
                   e.park_dist, e.river_dist, e.green_score,
                   e.redv_nearby, e.redv_status_best,
                   e.gtx_dist, e.gtx_line,
                   e.commerce_score, e.hospital_cnt, e.infra_score
            FROM m
            JOIN '{geo}' g ON g.apt_id = m.apt_id
            JOIN tot ON tot.apt_id = m.apt_id
            JOIN rep ON rep.apt_id = m.apt_id AND rep.rn = 1
            JOIN '{pyeong}' p
              ON p.apt_id = rep.apt_id AND p.pyeong_bucket = rep.pyeong_bucket
            LEFT JOIN ext.apt_external e ON e.apt_seq = g.old_apt_id
            WHERE g.lat IS NOT NULL AND g.lng IS NOT NULL
        ) TO '{out}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0]
    log(f"apt_index.parquet  {n:,}행")


def build_region_index(con: duckdb.DuckDBPyConnection) -> None:
    """시군구/읍면동 집계 — 줌 아웃 상태의 말풍선."""
    apt = (CACHE / "apt_index.parquet").as_posix()
    out = (CACHE / "region_index.parquet").as_posix()
    con.execute(f"""
        COPY (
            SELECT 'sgg' AS level, sigungu_code AS code, sigungu_name AS name,
                   any_value(region) AS region, CAST(NULL AS VARCHAR) AS parent,
                   count(*) AS apt_cnt, sum(trade_1y) AS trade_1y,
                   round(median(rep_ppy_1y)) AS ppy,
                   round(median(chg_1y), 1) AS chg_1y,
                   avg(lat) AS lat, avg(lng) AS lng
            FROM '{apt}' WHERE rep_ppy_1y IS NOT NULL GROUP BY 1, 2, 3
            UNION ALL
            SELECT 'dong', legal_dong_code, legal_dong_name,
                   any_value(region), any_value(sigungu_name),
                   count(*), sum(trade_1y),
                   round(median(rep_ppy_1y)), round(median(chg_1y), 1),
                   avg(lat), avg(lng)
            FROM '{apt}' WHERE rep_ppy_1y IS NOT NULL GROUP BY 1, 2, 3
        ) TO '{out}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0]
    log(f"region_index.parquet  {n:,}행")


def main() -> int:
    if not (MASTER / "trade_events.parquet").exists():
        log("master/trade_events.parquet 없음 — 중단")
        return 1
    CACHE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    con = connect()
    build_trades(con)
    build_apt_pyeong(con)
    build_geo_bridge(con)
    build_apt_index(con)
    build_region_index(con)
    con.close()
    total = sum(p.stat().st_size for p in CACHE.glob("*.parquet"))
    log(f"완료 — {time.time() - t0:.1f}초, 캐시 {total / 1024 / 1024:.0f}MB → {CACHE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
