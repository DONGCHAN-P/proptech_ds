"""평소지도 — 전처리.

`web/cache/` 의 서빙용 파케이를 읽어 **"자기 평소와 견준"** 지표를 미리 만든다.
원본 거래 485만 건을 요청 때마다 스캔하면 지도가 느려서 못 쓴다.

이 앱이 호갱노노·리치고와 다른 지점이 전부 여기서 결정된다.

    호갱노노   비싼 곳이 빨갛다        (지역끼리 가격 비교)
    리치고     오를 곳이 빨갛다        (점수·예측)
    평소지도   평소와 달라진 곳이 빨갛다 (자기 과거와 비교)

강남과 가평은 거래량 규모가 애초에 달라서 횡단 비교가 무의미하다. 각 지역의
지난 52주 평균·표준편차로 지금을 재는 편이 "뭔가 벌어지고 있다"를 제대로
잡는다. `metrics/build_metrics.py` 의 `sgg_zscore` 와 같은 정의를 쓴다 —
사이트에 뜨는 "평소의 1.7배"와 인스타에 올라가는 "평소의 1.7배"가 **같은 수**
여야 한다. 따로 계산하면 언젠가 갈라지고, 갈라진 걸 아무도 못 알아챈다.

σ 는 계산에만 쓰고 화면에는 내보내지 않는다 (`content/design.py` 와 같은 규칙).
일반 독자는 표준편차를 해석하지 못하고, 해석하려 들면 틀린다.

실행:
  .venv\\Scripts\\python.exe -m pulse.build_pulse
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from metrics.filters import trades_cte  # noqa: E402

WEB_CACHE = ROOT / "web" / "cache"
OUT = Path(__file__).resolve().parent / "cache"

# 거래 원본은 **정본(master)** 을 직접 읽는다. web/cache 의 서빙용 사본이 아니다.
#
# 처음엔 web/cache/trades.parquet 을 썼는데 오산시 이번 주 거래가 91건으로 나왔다.
# 같은 주를 인스타 카드는 98건이라고 말하고 있었다. web/cache 는 지도용으로
# 좌표가 있는 단지만 남기고 가격 결측을 쳐낸 사본이라 7건이 빠진 것이다.
# 둘 다 "틀리지 않았"지만 같은 주에 대해 다른 수를 말하는 화면과 게시물이
# 동시에 존재하게 된다. 그걸 알아챌 사람은 아무도 없다.
#
# 그래서 지표는 정본에서, 좌표만 web/cache 에서 가져온다.
TRADES = (ROOT / "master" / "trade_events.parquet").as_posix()
APT = (WEB_CACHE / "apt_index.parquet").as_posix()
REGION = (WEB_CACHE / "region_index.parquet").as_posix()

# ── 기준값 ───────────────────────────────────────────────────────────────
#
# metrics/build_metrics.py 와 같은 값을 쓴다. 바꿀 일이 생기면 양쪽을 같이
# 고치고, 왜 갈라졌는지 설명할 수 없으면 갈라놓지 않는다.
LAG_DAYS = 28        # 신고 지연. 최근 주는 집계가 덜 차 있다
HIST_WEEKS = 52      # "평소" = 지난 52주
MIN_HIST_WEEKS = 26  # 과거 표본이 이보다 적으면 판단하지 않는다
# 이보다 적으면 색을 칠하지 않고 "표본 부족"으로 둔다.
#
# build_metrics 의 WEEK_MIN_DEALS 는 5 다. 거기선 z 를 **계산**할 수 있는
# 하한이고, 여기선 지도 전체를 **칠하는** 기준이라 더 높게 잡는다.
# 연천군은 이번 주 7건이 신고됐는데 평소가 2.8건이라 "평소의 2.5배"로 전국
# 1위가 됐다. 4건 차이다. 캐러셀이 헤드라인에 쓰는 기준(MIN_SAMPLE=10)과
# 맞춘다 — 지도도 헤드라인이다.
MIN_DEALS = 10
DONG_WINDOW = 28     # 읍면동은 주간 거래가 한 자릿수라 4주로 묶는다
KEEP_WEEKS = 157     # 화면에 쓸 시계열 길이 (3년)

# 가격은 **수준이 아니라 속도**로 잰다.
#
# 거래량은 평균회귀한다 — 많았던 주 다음엔 적은 주가 온다. 그래서 "이번 주
# 거래량 vs 지난 52주 평균"이 뜻을 갖는다.
#
# 평단가는 다르다. 추세가 있어서 오르는 시장에서는 이번 주 값이 지난 52주
# 평균보다 높은 게 당연하다. 수준으로 재면 **상승장에서 전 지역이 자동으로
# "평소보다 높음"** 이 된다 (실측: 82개 중 15개가 그렇게 분류됐다). 그건
# 지역에 대한 정보가 아니라 시장 전체에 대한 정보다.
#
# 그래서 "최근 PPY_LAG_WEEKS 주 동안 얼마나 올랐나"를 먼저 구하고, 그 **변화율**
# 을 그 지역의 평소 변화율과 견준다. 질문이 "비싼가"에서 "평소보다 빠른가"로
# 바뀐다 — 이게 이 지도가 답하려는 질문이다.
PPY_LAG_WEEKS = 13   # 평단가 변화율 측정 구간 (약 3개월)

# 사분면 경계. 자기 52주 표준편차의 몇 배부터 "평소와 다르다"로 볼 것인가.
DEV = 1.0

# 단지 비교 창 (weekly surge_apt 와 같은 정의)
APT_WINDOW = 90
# 최근·직전 어느 쪽이든 이보다 적으면 '표본 적음' 배지를 단다.
# 3 으로 뒀더니 '최근 3건 / 직전 3건' 으로 계산한 −11.5% 가 배지 없이
# 목록에 올라왔다. 한 건만 달라도 뒤집히는 수다.
APT_MIN_DEALS = 5

# 지도 마커에 올릴 마지막 거래의 유효기간.
# 5년 전 거래 한 건을 '현재 실거래가'라고 찍으면 그 자체가 틀린 정보다.
APT_MAP_MAX_AGE_DAYS = 730


def log(msg: str) -> None:
    print(f"  {msg}", flush=True)


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("PRAGMA threads=4")
    return con


# 평단가 변화율. 주 단위 계열 위에서 PPY_LAG_WEEKS 주 전과 견준다.
PPY_CHG = f"""
    CASE WHEN lag(ppy, {PPY_LAG_WEEKS}) OVER pw > 0
         THEN (ppy / lag(ppy, {PPY_LAG_WEEKS}) OVER pw - 1) * 100
    END AS ppy_chg
"""
PPY_WINDOW = "WINDOW pw AS (PARTITION BY code ORDER BY week_start)"


def base_cte() -> str:
    """거래 공통 CTE.

    `metrics.filters.trades_cte` 를 그대로 쓴다 — 해제(취소) 건 제외와 가격
    이상치 경계가 SNS 지표와 한 글자도 다르면 안 된다. 여기서 WHERE 를 직접
    쓰면 언젠가 한쪽만 고쳐진다. 실제로 step8 이 해제 필터 없이 돌아서 취소된
    거래가 "신고가" Top 100 에 올라간 적이 있다.
    """
    return trades_cte(TRADES) + """,
    t AS (
        SELECT sigungu_code, legal_dong_code, deal_date,
               price_per_pyeong AS ppy
        FROM trades WHERE price_per_pyeong IS NOT NULL
    )
    """


# ── 시군구: 주간 ─────────────────────────────────────────────────────────
def build_sgg(con, cur_week: str) -> int:
    """시군구는 **7일 주간**으로 본다 — SNS 콘텐츠와 같은 창이다.

    주간 거래가 수백 건이라 7일로도 표본이 선다. 여기서 창을 바꾸면 사이트의
    "평소의 1.7배"와 인스타 카드의 "평소의 1.7배"가 달라진다.
    """
    sql = f"""
    {base_cte()},
    -- 거래가 없는 주도 0 으로 채운다. 빈 주를 건너뛰면 "지난 52주" 창이
    -- 밀려서 조용한 지역일수록 더 먼 과거와 비교하게 된다.
    spine AS (
        SELECT r.code, r.name, r.region, w.week_start
        FROM (SELECT code, name, region FROM read_parquet('{REGION}')
              WHERE level = 'sgg') r
        CROSS JOIN (
            SELECT unnest(generate_series(
                (SELECT date_trunc('week', min(deal_date)) FROM t),
                DATE '{cur_week}', INTERVAL 7 DAY))::DATE AS week_start
        ) w
    ),
    agg AS (
        SELECT sigungu_code AS code,
               date_trunc('week', deal_date)::DATE AS week_start,
               count(*) AS deals, median(ppy) AS ppy
        FROM t GROUP BY 1, 2
    ),
    joined AS (
        SELECT s.code, s.name, s.region, s.week_start,
               coalesce(a.deals, 0) AS deals, a.ppy
        FROM spine s LEFT JOIN agg a USING (code, week_start)
    ),
    chg AS (SELECT *, {PPY_CHG} FROM joined {PPY_WINDOW}),
    rolled AS (
        SELECT *,
               -- 자기 과거만 본다. 현재 주를 평균에 넣으면 자기 자신과 비교하게 된다.
               avg(deals) OVER w AS deals_avg,
               stddev_samp(deals) OVER w AS deals_sd,
               avg(ppy_chg) OVER w AS chg_avg,
               stddev_samp(ppy_chg) OVER w AS chg_sd,
               count(*) OVER w AS hist_weeks
        FROM chg
        WINDOW w AS (PARTITION BY code ORDER BY week_start
                     ROWS BETWEEN {HIST_WEEKS} PRECEDING AND 1 PRECEDING)
    )
    SELECT * FROM rolled
    WHERE week_start > DATE '{cur_week}' - INTERVAL {KEEP_WEEKS} WEEK
    ORDER BY code, week_start
    """
    con.execute(f"CREATE OR REPLACE TABLE sgg_weeks AS {sql}")
    return con.execute("SELECT count(*) FROM sgg_weeks").fetchone()[0]


# ── 읍면동: 4주 ──────────────────────────────────────────────────────────
def build_dong(con, cur_week: str) -> int:
    """읍면동은 **28일**로 묶는다.

    동 단위 주간 거래는 0~3건이다. 7일로 보면 한 건 차이로 "평소의 3배"가 돼
    지도가 매주 울긋불긋해진다. 보이는 건 시장이 아니라 잡음이다.

    창이 시군구와 다르므로 화면에도 "최근 4주"라고 따로 적는다. 같은 지도에
    다른 창이 섞여 있다는 걸 숨기지 않는다.
    """
    sql = f"""
    {base_cte()},
    spine AS (
        SELECT r.code, r.name, r.parent, r.region, w.week_start
        FROM (SELECT code, name, parent, region FROM read_parquet('{REGION}')
              WHERE level = 'dong') r
        CROSS JOIN (
            SELECT unnest(generate_series(
                DATE '{cur_week}' - INTERVAL {KEEP_WEEKS + HIST_WEEKS} WEEK,
                DATE '{cur_week}', INTERVAL 7 DAY))::DATE AS week_start
        ) w
    ),
    agg AS (
        SELECT s.code, s.name, s.parent, s.region, s.week_start,
               count(t.ppy) AS deals, median(t.ppy) AS ppy
        FROM spine s
        LEFT JOIN t ON t.legal_dong_code = s.code
                   AND t.deal_date > s.week_start - INTERVAL {DONG_WINDOW} DAY
                   AND t.deal_date <= s.week_start
        GROUP BY 1, 2, 3, 4, 5
    ),
    chg AS (SELECT *, {PPY_CHG} FROM agg {PPY_WINDOW}),
    rolled AS (
        SELECT *,
               avg(deals) OVER w AS deals_avg,
               stddev_samp(deals) OVER w AS deals_sd,
               avg(ppy_chg) OVER w AS chg_avg,
               stddev_samp(ppy_chg) OVER w AS chg_sd,
               count(*) OVER w AS hist_weeks
        FROM chg
        WINDOW w AS (PARTITION BY code ORDER BY week_start
                     ROWS BETWEEN {HIST_WEEKS} PRECEDING AND 1 PRECEDING)
    )
    SELECT * FROM rolled
    WHERE week_start > DATE '{cur_week}' - INTERVAL {KEEP_WEEKS} WEEK
    ORDER BY code, week_start
    """
    con.execute(f"CREATE OR REPLACE TABLE dong_weeks AS {sql}")
    return con.execute("SELECT count(*) FROM dong_weeks").fetchone()[0]


# ── 현재 상태 ────────────────────────────────────────────────────────────
STATE_SQL = """
    SELECT *,
           -- 거래량은 수준으로, 가격은 변화 속도로 잰다 (PPY_LAG_WEEKS 주석 참고)
           CASE WHEN deals_sd > 0 THEN (deals - deals_avg) / deals_sd END AS z_deals,
           CASE WHEN chg_sd   > 0 THEN (ppy_chg - chg_avg) / chg_sd   END AS z_ppy,
           -- 화면에 나가는 건 배수와 % 다. z 는 분류에만 쓰고 내보내지 않는다.
           CASE WHEN deals_avg > 0 THEN deals / deals_avg END AS r_deals
    FROM {src} WHERE week_start = DATE '{cur_week}'
"""

# 사분면. "판단 보류"를 먼저 거른다 — 표본이 얇으면 나머지 분류는 의미가 없다.
#
# 라벨은 상태 서술이지 권유가 아니다. "매수 적기" 같은 말은 쓰지 않는다
# (content/validator.py 의 금지 표현과 같은 기준, tests/test_pulse.py 가 막는다).
QUAD_SQL = f"""
    CASE
      WHEN hist_weeks < {MIN_HIST_WEEKS} OR deals_sd IS NULL THEN 'unknown'
      WHEN deals < {MIN_DEALS} THEN 'thin'
      WHEN z_deals >= {DEV} AND z_ppy >= {DEV} THEN 'hot'
      WHEN z_deals >= {DEV} THEN 'churn'
      WHEN z_ppy >= {DEV} THEN 'thin_rise'
      WHEN z_deals <= -{DEV} AND coalesce(z_ppy, 0) <= 0 THEN 'quiet'
      ELSE 'normal'
    END AS state
"""


def build_now(con, cur_week: str) -> tuple[int, int]:
    for level, src, geo_level in (("sgg", "sgg_weeks", "sgg"),
                                  ("dong", "dong_weeks", "dong")):
        con.execute(f"""
        CREATE OR REPLACE TABLE {level}_now AS
        SELECT s.*, {QUAD_SQL}, g.lat, g.lng
        FROM ({STATE_SQL.format(src=src, cur_week=cur_week)}) s
        JOIN (SELECT code, lat, lng FROM read_parquet('{REGION}')
              WHERE level = '{geo_level}') g USING (code)
        WHERE g.lat IS NOT NULL
        """)
    return (con.execute("SELECT count(*) FROM sgg_now").fetchone()[0],
            con.execute("SELECT count(*) FROM dong_now").fetchone()[0])


# ── 단지 ─────────────────────────────────────────────────────────────────
def build_apt(con, asof: str) -> tuple[int, int]:
    """단지 — 평형별로 만든다.

    "현재 실거래가"는 **평형을 빼면 거짓말이 된다.** 같은 단지에서 15평과
    40평이 두 배 넘게 차이 나서, 평형 없이 한 숫자만 찍으면 어느 쪽을 봐도
    틀린 값이 된다. 그래서 (단지 × 평형)이 기본 단위이고, 지도 마커에는
    **대표 평형**(최근 1년 거래가 가장 많은 평형)을 쓰고 그 평형을 같이 적는다.

    변화율은 90일 vs 직전 90일 (weekly surge_apt 와 같은 정의). 단지 하나의
    주간 거래는 0건인 주가 대부분이라 주간 비교가 성립하지 않는다.

    마지막 거래가는 **사실**이라 표본 경고가 필요 없다. 경고가 붙는 건
    변화율 쪽이다 — 3건으로 뽑은 −11% 는 한 건만 달라도 뒤집힌다.
    """
    W, Y = APT_WINDOW, 365
    sql = trades_cte(TRADES) + f""",
    t AS (
        SELECT apt_id, pyeong_bucket, area_m2, deal_date, deal_amount,
               price_per_pyeong AS ppy, floor_band
        FROM trades
        WHERE price_per_pyeong IS NOT NULL AND pyeong_bucket IS NOT NULL
          AND deal_date <= DATE '{asof}'
    ),
    agg AS (
        SELECT apt_id, pyeong_bucket,
               count(*) AS n_total,
               count(*) FILTER (WHERE deal_date > DATE '{asof}' - INTERVAL {Y} DAY)
                   AS n_1y,
               count(*) FILTER (WHERE deal_date > DATE '{asof}' - INTERVAL {W} DAY)
                   AS n_recent,
               count(*) FILTER (
                   WHERE deal_date <= DATE '{asof}' - INTERVAL {W} DAY
                     AND deal_date >  DATE '{asof}' - INTERVAL {W * 2} DAY
               ) AS n_prior,
               median(ppy) FILTER (WHERE deal_date > DATE '{asof}' - INTERVAL {W} DAY)
                   AS ppy_recent,
               median(ppy) FILTER (
                   WHERE deal_date <= DATE '{asof}' - INTERVAL {W} DAY
                     AND deal_date >  DATE '{asof}' - INTERVAL {W * 2} DAY
               ) AS ppy_prior,
               -- 전고점은 같은 평형 안에서만 뜻이 있다
               max(deal_amount) AS peak_price,
               arg_max(deal_date, deal_amount)::DATE AS peak_date,
               arg_max(deal_date, deal_date)::DATE AS last_date,
               arg_max(deal_amount, deal_date) AS last_price,
               arg_max(ppy, deal_date) AS last_ppy,
               arg_max(floor_band, deal_date) AS last_floor,
               arg_max(area_m2, deal_date) AS last_area
        FROM t GROUP BY 1, 2
    )
    SELECT a.apt_id, x.apt_name, x.sigungu_code, x.sigungu_name,
           x.legal_dong_code, x.legal_dong_name, x.lat, x.lng, x.build_year,
           a.pyeong_bucket, a.n_total, a.n_1y, a.n_recent, a.n_prior,
           a.ppy_recent, a.ppy_prior,
           (a.ppy_recent / a.ppy_prior - 1) * 100 AS chg_pct,
           a.last_date, a.last_price, a.last_ppy, a.last_floor, a.last_area,
           a.peak_price, a.peak_date,
           (a.last_price / a.peak_price - 1) * 100 AS vs_peak_pct,
           (a.ppy_recent IS NULL OR a.ppy_prior IS NULL
            OR a.n_recent < {APT_MIN_DEALS} OR a.n_prior < {APT_MIN_DEALS}) AS thin
    FROM agg a
    JOIN read_parquet('{APT}') x USING (apt_id)
    WHERE x.lat IS NOT NULL
    """
    con.execute(f"CREATE OR REPLACE TABLE apt_pyeong_now AS {sql}")

    # 지도 마커용 1행/1단지. 대표 평형은 최근 1년 거래가 가장 많은 평형이고,
    # 1년 거래가 아예 없으면 누적 최다 평형으로 떨어진다.
    con.execute(f"""
    CREATE OR REPLACE TABLE apt_now AS
    SELECT * EXCLUDE (rn) FROM (
        SELECT *, row_number() OVER (
            PARTITION BY apt_id
            ORDER BY n_1y DESC, n_total DESC, last_date DESC
        ) AS rn
        FROM apt_pyeong_now
    ) WHERE rn = 1
      -- 지도에 올릴 값은 '최근'이어야 한다. 5년 전 거래 한 건을 '현재
      -- 실거래가'로 찍으면 그 자체가 틀린 정보다.
      AND last_date > DATE '{asof}' - INTERVAL {APT_MAP_MAX_AGE_DAYS} DAY
    """)
    return (con.execute("SELECT count(*) FROM apt_pyeong_now").fetchone()[0],
            con.execute("SELECT count(*) FROM apt_now").fetchone()[0])


# ── 메인 ─────────────────────────────────────────────────────────────────
TABLES = ["sgg_weeks", "dong_weeks", "sgg_now", "dong_now",
          "apt_now", "apt_pyeong_now"]


def main() -> int:
    if not Path(TRADES).exists():
        print("web/cache 가 없다. 먼저: .venv\\Scripts\\python.exe web\\build_index.py")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    con = connect()
    t0 = time.time()

    asof, cur_week = con.execute(f"""
        SELECT max(deal_date)::DATE,
               date_trunc('week', max(deal_date) - INTERVAL {LAG_DAYS} DAY)::DATE
        FROM read_parquet('{TRADES}')
    """).fetchone()
    print(f"\n{'=' * 62}\n  평소지도 전처리\n{'=' * 62}")
    log(f"마지막 거래 {asof} · 기준 주 {cur_week} (신고 지연 {LAG_DAYS}일 반영)")

    log(f"시군구 주간 … {build_sgg(con, str(cur_week)):,}행")
    log(f"읍면동 {DONG_WINDOW}일 … {build_dong(con, str(cur_week)):,}행")
    n_sgg, n_dong = build_now(con, str(cur_week))
    log(f"현재 상태 … 시군구 {n_sgg} · 읍면동 {n_dong}")
    n_ap, n_a = build_apt(con, str(asof))
    log(f"단지×평형 … {n_ap:,}행 · 지도 마커 {n_a:,}개 "
        f"(최근 {APT_MAP_MAX_AGE_DAYS}일 안에 거래가 있는 단지)")

    for t in TABLES:
        con.execute(f"COPY {t} TO '{(OUT / f'{t}.parquet').as_posix()}' (FORMAT PARQUET)")
    con.execute(f"""
        COPY (SELECT '{asof}' AS asof, '{cur_week}' AS cur_week,
                     {LAG_DAYS} AS lag_days, {HIST_WEEKS} AS hist_weeks,
                     {MIN_DEALS} AS min_deals, {DONG_WINDOW} AS dong_window,
                     {APT_WINDOW} AS apt_window)
        TO '{(OUT / 'meta.parquet').as_posix()}' (FORMAT PARQUET)
    """)

    size = sum(p.stat().st_size for p in OUT.glob("*.parquet")) / 1e6
    print(f"\n  저장: {OUT}  ({size:.1f}MB, {time.time() - t0:.1f}초)")

    dist = con.execute(
        "SELECT state, count(*) n FROM sgg_now GROUP BY 1 ORDER BY 2 DESC").fetchall()
    log("시군구 상태 분포: " + " · ".join(f"{s} {n}" for s, n in dist))
    print(f"{'=' * 62}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
