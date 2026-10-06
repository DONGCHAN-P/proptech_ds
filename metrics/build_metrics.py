"""T9 — 지표 계산 (DuckDB 단독 SQL).

콘텐츠가 인용할 숫자는 전부 여기서 나온다. Python 으로 집계하지 않는다.
4,900만 행을 pandas 로 올리면 RAM 이 터지고, 무엇보다 "어떤 필터가 걸렸나"가
코드 여기저기로 흩어진다. 모든 쿼리는 metrics.filters.trades_cte() 가 만든
`trades` CTE 에서 시작하므로 해제·이상치 필터를 빠뜨릴 수 없다.

일간
  new_high      신고가 경신 — 2006~ 전체 이력 기준, 같은 단지·같은 평형
  vs_peak       전고점 이격 — 전고점 대비 현재가
  outlier       특이 거래 — 같은 단지·평형의 직전 90일 평균 대비 +-N%

주간
  sgg_zscore    시군구 Z-score — 자기 과거(52주) 평균·표준편차 대비
                거래량·중위 평단가 변동
  surge_apt     상위 지역 안에서 많이 오른 단지

산출물: output/metrics_YYYYMMDD.json  (일간·주간 한 파일)

실행:
  .venv\\Scripts\\python.exe -m metrics.build_metrics
  .venv\\Scripts\\python.exe -m metrics.build_metrics --asof 2026-09-30
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import DIRS  # noqa: E402
from metrics.filters import trades_cte  # noqa: E402

TRADE = (DIRS["master"] / "trade_events.parquet").as_posix()
OUT_DIR = ROOT / "output"

# ── 임계값 ───────────────────────────────────────────────────────────────
DAILY_WINDOW = 7        # "최근" 거래로 볼 일수

# 주간 지표는 기준일에서 이만큼 **뒤로 물린 주**를 본다.
#
# 계약 후 30일 내 신고라 최근 주는 신고가 덜 들어와 있다. 실측(2026-10-01 기준):
#   기준일 직전 주 697건 (평소 3,900건의 18%)
#   1주 전   1,180건 (30%)
#   2주 전   3,151건 (81%)
#   3주 전   3,667건 (94%)
#   4주 전   3,889건 (거의 완전)
# 물리지 않으면 "이번 주 거래량이 평소보다 적다"는 결론이 매주 나온다. 시장이
# 아니라 신고 지연을 보고 있는 것이다. 4주를 물려 신고가 대체로 끝난 주를 쓴다.
#
# 참고: 이렇게 해도 거래량 z 의 **중앙값은 -0.4 근처**다. 지연 탓이 아니라
# 주간 거래량 분포가 우편향이라 그렇다 (몇몇 폭증 주가 평균을 끌어올려 중앙값이
# 평균보다 낮다). 지연을 35·42·49일로 늘려도 -0.33 ~ -0.57 사이에서 맴돌 뿐
# 0 으로 수렴하지 않는다. 정상이니 "보정"하지 말 것.
WEEKLY_LAG_DAYS = 28
WEEKLY_WINDOW = 7       # 주간 집계 창
WEEK_MIN_DEALS = 5      # 이보다 적으면 중위가가 요동쳐 Z-score 를 내지 않는다
OUTLIER_PCT = 15.0      # 직전 평균 대비 이 % 이상 벌어지면 특이
OUTLIER_MIN_REF = 3     # 비교 기준 거래가 이보다 적으면 판단 보류
RARE_AREA_MIN = 5       # 같은 단지·평형 누적 거래가 이보다 적으면 희귀 면적
ZSCORE_HIST_WEEKS = 52  # "평소" 로 삼는 과거 구간 (주). 카드 문구와 같은 값
ZSCORE_MIN_WEEKS = 26   # 과거 표본이 이보다 적은 시군구는 Z-score 생략
TOP_N = 50
CHART_SERIES_N = 5    # 차트용 시계열을 뽑을 단지 수

# 세대수 필터는 T6b(K-apt 기본정보) 수집 후 켠다. 지금은 세대수 자체가 없어
# 켜면 전 건이 "세대수 미상"으로 통과하거나 전부 사라진다. None = 비활성.
MIN_HOUSEHOLDS: int | None = None


def peak_ram_mb() -> float | None:
    """이 프로세스의 피크 작업 집합(MB).

    완료 기준이 "피크 RAM 2GB 이내"라 자기 자신을 재야 한다. 밖에서 재면
    DuckDB 가 쓰는 메모리를 놓치기 쉽다.
    """
    try:
        import ctypes
        import ctypes.wintypes as w

        class PMC(ctypes.Structure):
            _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        m = PMC()
        m.cb = ctypes.sizeof(m)
        # restype 을 지정하지 않으면 핸들이 int 로 잘려 호출이 조용히 실패한다
        get_proc = ctypes.windll.kernel32.GetCurrentProcess
        get_proc.restype = ctypes.c_void_p
        h = get_proc()
        fn = ctypes.windll.psapi.GetProcessMemoryInfo
        fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(PMC), w.DWORD]
        if fn(h, ctypes.byref(m), m.cb):
            return round(m.PeakWorkingSetSize / 1024 / 1024, 1)
    except Exception:
        pass
    try:
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    except Exception:
        return None


def q(con, sql: str) -> list[dict]:
    df = con.execute(sql).df()
    out = []
    for r in df.to_dict(orient="records"):
        d = {}
        for k, v in r.items():
            if v is None or v != v:
                d[k] = None
            elif hasattr(v, "isoformat"):
                d[k] = v.isoformat()[:10]
            elif hasattr(v, "item"):
                d[k] = v.item()
            else:
                d[k] = v
        out.append(d)
    return out


def cte() -> str:
    return trades_cte(TRADE, min_households=MIN_HOUSEHOLDS)


# ── 일간 ─────────────────────────────────────────────────────────────────
def new_high(con, asof: date) -> list[dict]:
    """신고가 경신 — 2006~ 전체 이력 기준.

    같은 단지·같은 평형에서 그 거래 **이전까지의** 최고가를 넘었는지 본다.
    이력이 1건뿐이면 비교 대상이 없으므로 신고가로 치지 않는다.
    """
    since = asof - timedelta(days=DAILY_WINDOW)
    return q(con, f"""
        {cte()},
        ranked AS (
            SELECT apt_id, apt_name_raw, sigungu_code, sigungu_name, legal_dong_name,
                   pyeong_bucket, floor_band, deal_date, deal_amount, area_m2,
                   price_per_pyeong,
                   max(deal_amount) OVER (
                       PARTITION BY apt_id, pyeong_bucket ORDER BY deal_date
                       ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                   ) AS prev_peak,
                   count(*) OVER (PARTITION BY apt_id, pyeong_bucket) AS hist_n
            FROM trades
        )
        SELECT apt_name_raw AS apt_name, sigungu_name, legal_dong_name,
               pyeong_bucket, floor_band, deal_date, deal_amount,
               round(area_m2, 1) AS area_m2,
               round(price_per_pyeong) AS price_per_pyeong,
               prev_peak,
               round((deal_amount / prev_peak - 1) * 100, 1) AS over_peak_pct,
               hist_n AS history_count
        FROM ranked
        WHERE deal_date > DATE '{since}' AND deal_date <= DATE '{asof}'
          AND prev_peak IS NOT NULL
          AND deal_amount > prev_peak
          AND hist_n >= {RARE_AREA_MIN}
        ORDER BY over_peak_pct DESC
        LIMIT {TOP_N}
    """)


def vs_peak(con, asof: date) -> list[dict]:
    """전고점 이격 — 최근 거래가 역대 최고가에서 얼마나 내려와 있나."""
    since = asof - timedelta(days=DAILY_WINDOW)
    return q(con, f"""
        {cte()},
        peaks AS (
            SELECT apt_id, pyeong_bucket,
                   max(deal_amount) AS peak_price,
                   arg_max(deal_date, deal_amount) AS peak_date,
                   count(*) AS hist_n
            FROM trades GROUP BY 1, 2
        ),
        recent AS (
            SELECT apt_id, pyeong_bucket,
                   arg_max(deal_amount, deal_date) AS last_price,
                   max(deal_date) AS last_date,
                   any_value(apt_name_raw) AS apt_name,
                   any_value(sigungu_name) AS sigungu_name,
                   any_value(legal_dong_name) AS legal_dong_name
            FROM trades
            WHERE deal_date > DATE '{since}' AND deal_date <= DATE '{asof}'
            GROUP BY 1, 2
        )
        SELECT r.apt_name, r.sigungu_name, r.legal_dong_name, r.pyeong_bucket,
               r.last_date, r.last_price, p.peak_price, p.peak_date,
               round((r.last_price / p.peak_price - 1) * 100, 1) AS vs_peak_pct,
               p.hist_n AS history_count
        FROM recent r JOIN peaks p USING (apt_id, pyeong_bucket)
        WHERE p.hist_n >= {RARE_AREA_MIN} AND p.peak_price > 0
        ORDER BY vs_peak_pct ASC
        LIMIT {TOP_N}
    """)


def outliers(con, asof: date) -> list[dict]:
    """특이 거래 — 같은 단지·평형의 직전 90일 평균 대비 +-N%.

    비교 기준이 {OUTLIER_MIN_REF}건 미만이면 평균이 흔들려 판단을 보류한다.
    """
    since = asof - timedelta(days=DAILY_WINDOW)
    return q(con, f"""
        {cte()},
        base AS (
            SELECT t.apt_id, t.pyeong_bucket, t.deal_date, t.deal_amount,
                   t.apt_name_raw, t.sigungu_name, t.legal_dong_name,
                   t.floor_band, t.area_m2,
                   avg(p.deal_amount) AS ref_avg,
                   count(p.deal_amount) AS ref_n
            FROM trades t
            LEFT JOIN trades p
              ON p.apt_id = t.apt_id AND p.pyeong_bucket = t.pyeong_bucket
             AND p.deal_date < t.deal_date
             AND p.deal_date >= t.deal_date - INTERVAL 90 DAY
            WHERE t.deal_date > DATE '{since}' AND t.deal_date <= DATE '{asof}'
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
        )
        SELECT apt_name_raw AS apt_name, sigungu_name, legal_dong_name,
               pyeong_bucket, floor_band, deal_date, deal_amount,
               round(area_m2, 1) AS area_m2,
               round(ref_avg) AS ref_avg, ref_n AS ref_count,
               round((deal_amount / ref_avg - 1) * 100, 1) AS deviation_pct
        FROM base
        WHERE ref_n >= {OUTLIER_MIN_REF} AND ref_avg > 0
          AND abs(deal_amount / ref_avg - 1) * 100 >= {OUTLIER_PCT}
        ORDER BY abs(deal_amount / ref_avg - 1) DESC
        LIMIT {TOP_N}
    """)


# ── 주간 ─────────────────────────────────────────────────────────────────
def sgg_zscore(con, asof: date) -> list[dict]:
    """시군구 Z-score — 자기 과거 대비 이번 주가 얼마나 벗어났나.

    지역끼리 비교하지 않는다. 강남과 가평은 애초에 거래량 규모가 달라서
    횡단 비교가 무의미하다. 각 시군구의 지난 52주 평균·표준편차를 기준으로
    이번 주를 재는 편이 "평소와 다르다"를 제대로 잡는다.
    """
    target = asof - timedelta(days=WEEKLY_LAG_DAYS)
    # 주 경계에 맞춰 자른다. 날짜로 자르면 가장 이른 주가 반쪽만 들어와
    # 그 주 거래량이 모자란 채로 평균에 섞인다 ("평소"가 실제보다 낮아진다).
    # 평소지도(pulse/build_pulse.py)와 같은 창이어야 사이트와 게시물이
    # 같은 수를 말한다.
    hist_start = target - timedelta(days=target.weekday()) - timedelta(weeks=ZSCORE_HIST_WEEKS)
    return q(con, f"""
        {cte()},
        obs AS (
            SELECT sigungu_code, any_value(sigungu_name) AS sigungu_name,
                   date_trunc('week', deal_date) AS wk,
                   count(*) AS deals,
                   median(price_per_pyeong) AS med_ppy
            FROM trades
            -- 기준 주를 중간에서 자르면 그 주만 4일치가 돼 거래량이 늘
            -- 모자라 보인다. 주 끝(월요일+6일)까지 포함한다.
            WHERE deal_date >= DATE '{hist_start}'
              AND deal_date <= date_trunc('week', DATE '{target}') + INTERVAL 6 DAY
            GROUP BY 1, 3
        ),
        names AS (
            SELECT sigungu_code, any_value(sigungu_name) AS sigungu_name
            FROM obs GROUP BY 1
        ),
        -- 거래가 0인 주도 0 으로 채운다.
        --
        -- GROUP BY 는 거래가 없는 주를 아예 만들지 않는다. 그 상태로 평균을
        -- 내면 **조용한 주가 빠진 평균**이 나와 "평소"가 부풀려진다. 조용한
        -- 지역일수록 심하다 — 연천군은 52주 중 49주만 세서 평소가 2.81건
        -- 대신 3.0건이 됐다. 그만큼 "평소보다 많다"가 덜 잡힌다.
        -- 80개 시군구 중 24곳이 영향을 받고 있었다.
        spine AS (
            SELECT n.sigungu_code, w.wk
            FROM names n
            CROSS JOIN (
                SELECT unnest(generate_series(
                    DATE '{hist_start}',
                    date_trunc('week', DATE '{target}'),
                    INTERVAL 7 DAY))::DATE AS wk
            ) w
        ),
        weekly AS (
            SELECT sp.sigungu_code, n.sigungu_name, sp.wk,
                   coalesce(o.deals, 0) AS deals,
                   -- 중위가는 채우지 않는다. 거래가 없는 주에 "가격"은 없다.
                   o.med_ppy
            FROM spine sp
            JOIN names n USING (sigungu_code)
            LEFT JOIN obs o USING (sigungu_code, wk)
        ),
        hist AS (
            SELECT sigungu_code,
                   avg(deals) AS deals_mu, stddev_samp(deals) AS deals_sd,
                   avg(med_ppy) AS ppy_mu, stddev_samp(med_ppy) AS ppy_sd,
                   count(*) AS weeks
            FROM weekly
            WHERE wk < date_trunc('week', DATE '{target}')
            GROUP BY 1
        ),
        cur AS (
            SELECT sigungu_code, sigungu_name, wk, deals, med_ppy
            FROM weekly
            WHERE wk = date_trunc('week', DATE '{target}')
        )
        SELECT c.sigungu_code, c.sigungu_name,
               CAST(c.wk AS DATE) AS week_start,
               c.deals AS week_deals, round(h.deals_mu, 1) AS deals_avg_52w,
               round((c.deals - h.deals_mu) / nullif(h.deals_sd, 0), 2) AS deals_z,
               round(c.med_ppy) AS week_ppy, round(h.ppy_mu) AS ppy_avg_52w,
               round((c.med_ppy - h.ppy_mu) / nullif(h.ppy_sd, 0), 2) AS ppy_z,
               h.weeks AS hist_weeks
        FROM cur c JOIN hist h USING (sigungu_code)
        WHERE h.weeks >= {ZSCORE_MIN_WEEKS}
          AND h.deals_sd > 0 AND h.ppy_sd > 0
          AND c.deals >= {WEEK_MIN_DEALS}
        ORDER BY abs(coalesce(deals_z, 0)) + abs(coalesce(ppy_z, 0)) DESC
    """)


def surge_apt(con, asof: date) -> list[dict]:
    """최근 90일 평단가가 그 직전 90일 대비 많이 오른 단지."""
    return q(con, f"""
        {cte()},
        w AS (
            SELECT apt_id, any_value(apt_name_raw) AS apt_name,
                   any_value(sigungu_code) AS sigungu_code,
                   any_value(sigungu_name) AS sigungu_name,
                   any_value(legal_dong_name) AS legal_dong_name,
                   pyeong_bucket,
                   avg(price_per_pyeong) FILTER (
                       deal_date > DATE '{asof}' - INTERVAL 90 DAY) AS ppy_now,
                   avg(price_per_pyeong) FILTER (
                       deal_date <= DATE '{asof}' - INTERVAL 90 DAY
                   AND deal_date > DATE '{asof}' - INTERVAL 180 DAY) AS ppy_prev,
                   count(*) FILTER (
                       deal_date > DATE '{asof}' - INTERVAL 90 DAY) AS n_now,
                   count(*) FILTER (
                       deal_date <= DATE '{asof}' - INTERVAL 90 DAY
                   AND deal_date > DATE '{asof}' - INTERVAL 180 DAY) AS n_prev
            FROM trades
            WHERE deal_date > DATE '{asof}' - INTERVAL 180 DAY
              AND deal_date <= DATE '{asof}'
            GROUP BY apt_id, pyeong_bucket
        )
        SELECT apt_name, sigungu_name, legal_dong_name, pyeong_bucket,
               round(ppy_now) AS ppy_recent_90d,
               round(ppy_prev) AS ppy_prior_90d,
               round((ppy_now / ppy_prev - 1) * 100, 1) AS change_pct,
               n_now AS deals_recent, n_prev AS deals_prior
        FROM w
        WHERE n_now >= {OUTLIER_MIN_REF} AND n_prev >= {OUTLIER_MIN_REF}
          AND ppy_prev > 0
        ORDER BY change_pct DESC
        LIMIT {TOP_N}
    """)


def series_for_charts(con, asof: date, picks: list[dict]) -> list[dict]:
    """차트가 그릴 월별 시계열.

    차트는 **이 JSON 안의 숫자만** 그린다. 따로 DB 를 뒤지면 발행된 그림과
    T12 숫자 검증기가 대조하는 값이 어긋날 수 있다. 같은 파일에서 나와야 한다.
    """
    if not picks:
        return []
    out = []
    for p in picks[:CHART_SERIES_N]:
        rows = q(con, f"""
            {cte()}
            SELECT strftime(date_trunc('month', deal_date), '%Y-%m') AS ym,
                   round(avg(deal_amount)) AS avg_price,
                   count(*) AS deals
            FROM trades
            WHERE apt_name_raw = '{p["apt_name"].replace("'", "''")}'
              AND sigungu_name = '{p["sigungu_name"]}'
              AND pyeong_bucket = '{p["pyeong_bucket"]}'
              AND deal_date >= DATE '{asof}' - INTERVAL 5 YEAR
              AND deal_date <= DATE '{asof}'
            GROUP BY 1 ORDER BY 1
        """)
        if len(rows) >= 6:
            out.append({
                "apt_name": p["apt_name"],
                "sigungu_name": p["sigungu_name"],
                "legal_dong_name": p.get("legal_dong_name"),
                "pyeong_bucket": p["pyeong_bucket"],
                "points": rows,
            })
    return out


# ── 메인 ─────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="T9 지표 계산")
    ap.add_argument("--asof", help="기준일 (기본: trade_events 최신 거래일)")
    ap.add_argument("--out", help="출력 경로")
    args = ap.parse_args()

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order = false")
    con.execute("SET memory_limit = '2GB'")   # 완료 기준: 피크 RAM 2GB 이내

    if args.asof:
        asof = datetime.strptime(args.asof, "%Y-%m-%d").date()
    else:
        asof = con.execute(f"SELECT max(deal_date) FROM '{TRADE}'").fetchone()[0].date()

    t0 = datetime.now()
    print(f"\n{'=' * 60}\n  지표 계산  기준일 {asof}\n{'=' * 60}")

    sections = [
        ("new_high", "신고가 경신", new_high),
        ("vs_peak", "전고점 이격", vs_peak),
        ("outlier", "특이 거래", outliers),
        ("sgg_zscore", "시군구 Z-score", sgg_zscore),
        ("surge_apt", "급등 단지", surge_apt),
    ]
    result: dict = {
        "generated_at": t0.isoformat(),
        "asof": asof.isoformat(),
        "params": {
            "daily_window_days": DAILY_WINDOW,
            "outlier_pct": OUTLIER_PCT,
            "outlier_min_ref": OUTLIER_MIN_REF,
            "rare_area_min": RARE_AREA_MIN,
            "zscore_min_weeks": ZSCORE_MIN_WEEKS,
            "weekly_lag_days": WEEKLY_LAG_DAYS,
            # 아래는 SQL 에 박혀 있던 상수를 끌어올린 것이다. 발행 문구가
            # "직전 90일 평균" 처럼 인용하므로 숫자 검증기가 대조할 수 있어야
            # 한다. 글의 모든 숫자는 이 파일에서 유래해야 한다는 원칙.
            "outlier_ref_window_days": 90,
            "surge_window_days": 90,
            "zscore_hist_weeks": ZSCORE_HIST_WEEKS,
            "data_start_year": 2006,
            "report_deadline_days": 30,   # 계약 후 신고 기한 (법정)
            "week_min_deals": WEEK_MIN_DEALS,
            "weekly_note": ("주간 지표는 신고 지연 때문에 기준일에서 "
                            f"{WEEKLY_LAG_DAYS}일 물린 주를 쓴다"),
            "min_households": MIN_HOUSEHOLDS,
            "note": "min_households=None — 세대수 미수집(T6b). 300세대 필터 비활성.",
        },
        "daily": {}, "weekly": {},
    }

    for key, label, fn in sections:
        s = datetime.now()
        rows = fn(con, asof)
        bucket = "weekly" if key in ("sgg_zscore", "surge_apt") else "daily"
        result[bucket][key] = rows
        print(f"  {label:14s} {len(rows):>4}건  ({(datetime.now() - s).total_seconds():.1f}s)")

    result["series"] = series_for_charts(con, asof, result["daily"]["new_high"])
    print(f"  {'차트 시계열':14s} {len(result['series']):>4}건")
    con.close()
    result["peak_ram_mb"] = peak_ram_mb()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else OUT_DIR / f"metrics_{asof:%Y%m%d}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    ram = result["peak_ram_mb"]
    print(f"\n  저장: {out} ({out.stat().st_size / 1024:.0f}KB)")
    print(f"  소요: {(datetime.now() - t0).total_seconds():.1f}s"
          f"  |  피크 RAM: {ram}MB (기준 2048MB)")
    print(f"{'=' * 60}\n")
    if ram and ram > 2048:
        print("  ⚠️ 피크 RAM 이 완료 기준을 넘었다")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
