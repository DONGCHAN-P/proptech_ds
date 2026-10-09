"""역세권 프리미엄 — "역세권, 진짜 비쌀까".

왜 이 아젠다인가
    지하철은 수도권 거의 모두의 일상이라 설명이 필요 없다. 그리고 "역세권은
    비싸다"는 모두가 믿지만 **얼마나**인지는 아무도 숫자로 모른다.

핵심은 **착시를 걷어내는 것**이다
    수도권 전체를 한 줄로 세우면 역 500m 이내가 1.5km 밖보다 1.7배 비싸다.
    그런데 이건 역세권 효과가 아니라 **도심 대 외곽**을 잰 것이다. 역은
    사람이 많은 곳에 놓이니, 역 근처가 비싼 게 당연하다.

    같은 시군구 안에서만 견주면 중앙값 1.2배로 내려앉는다. 그리고 55곳 중
    17곳은 **역에서 먼 쪽이 오히려 비싸다**. 통념이 3곳 중 1곳에서 틀린다.

    이 차이를 보여주는 게 이 글의 값이다. 1.7배만 내보내면 틀린 말은
    아니지만 틀린 인상을 준다.

재는 법
    단지 좌표에서 가장 가까운 역까지 **직선거리**. 실제 도보는 더 멀고,
    환승·급행 여부는 보지 않는다. 마지막 장에 적는다.

실행:
  .venv\\Scripts\\python.exe -m content.subway
  .venv\\Scripts\\python.exe -m content.subway --no-render
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import DB_PATH  # noqa: E402
from content import agenda as A  # noqa: E402
from content import design as D  # noqa: E402
from content import reels as R  # noqa: E402

TRADE = ROOT / "master" / "trade_events.parquet"
APT_MAP = ROOT / "master" / "apt_id_map.parquet"
MONTHS = 12
PYEONGS = ("25P", "30P")
PYEONG_LABEL = "25~35평"
NEAR_M, FAR_M = 500, 1000     # 가까움 / 멂의 경계
SGG_MIN = 50                  # 시군구별 구간 표본 문턱
BAND_MIN = 300                # 전체 구간 표본 문턱
LIST_N = 4

BANDS = ((500, "역 500m 이내"), (1000, "500m~1km"),
         (1500, "1~1.5km"), (10 ** 9, "1.5km 밖"))


def _stations():
    import sqlite3
    import pandas as pd
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=8)
    try:
        return pd.read_sql(
            "SELECT line, lat, lng FROM subway_stations "
            "WHERE lat IS NOT NULL AND lng IS NOT NULL", con)
    finally:
        con.close()


def _band_case(col: str = "m") -> str:
    parts = " ".join(f"WHEN {col}<={e} THEN '{lab}'" for e, lab in BANDS[:-1])
    return f"CASE {parts} ELSE '{BANDS[-1][1]}' END"


def compute(*, months: int = MONTHS, pyeongs=PYEONGS) -> dict:
    import duckdb
    from metrics.filters import trades_cte

    st = _stations()
    if st.empty:
        raise RuntimeError("지하철역 좌표가 없다")
    buckets = ",".join(f"'{p}'" for p in pyeongs)
    con = duckdb.connect()
    con.register("st", st)
    try:
        hav = ("6371000*2*asin(sqrt(pow(sin(radians(s.lat-t.lat)/2),2)"
               "+cos(radians(t.lat))*cos(radians(s.lat))"
               "*pow(sin(radians(s.lng-t.lng)/2),2)))")
        base = f"""
            {trades_cte(TRADE.as_posix())},
            apt AS (SELECT apt_id, lat, lng
                    FROM read_parquet('{APT_MAP.as_posix()}')
                    WHERE lat IS NOT NULL),
            t AS (SELECT tr.sigungu_name, tr.sigungu_code,
                         tr.price_per_pyeong, a.lat, a.lng
                  FROM trades tr JOIN apt a USING (apt_id)
                  WHERE tr.deal_date > (SELECT max(deal_date) FROM trades)
                                        - INTERVAL {months} MONTH
                    AND tr.pyeong_bucket IN ({buckets})
                    AND tr.price_per_pyeong > 0),
            near AS (SELECT t.sigungu_name, t.sigungu_code,
                            t.price_per_pyeong, min({hav}) AS m
                     FROM t CROSS JOIN st s GROUP BY 1,2,3)
        """
        bands = con.execute(f"""
            {base}
            SELECT {_band_case()} AS band, count(*) AS deals,
                   round(median(price_per_pyeong)) AS ppy
            FROM near GROUP BY 1 ORDER BY min(m)
        """).fetchall()
        sgg = con.execute(f"""
            {base}
            SELECT sigungu_name, any_value(sigungu_code) AS code,
              round(median(CASE WHEN m<={NEAR_M} THEN price_per_pyeong END))
                AS inner_ppy,
              round(median(CASE WHEN m>{FAR_M} THEN price_per_pyeong END))
                AS outer_ppy,
              sum(CASE WHEN m<={NEAR_M} THEN 1 ELSE 0 END) AS ni,
              sum(CASE WHEN m>{FAR_M} THEN 1 ELSE 0 END) AS no_
            FROM near GROUP BY 1
            HAVING ni >= {SGG_MIN} AND no_ >= {SGG_MIN}
        """).fetchall()
        asof = con.execute(
            f"{trades_cte(TRADE.as_posix())} "
            f"SELECT max(deal_date) FROM trades").fetchone()[0]
    finally:
        con.close()

    bl = [{"band": b, "deals": int(n), "ppy": int(p)}
          for b, n, p in bands if n >= BAND_MIN and p]
    if len(bl) < 2:
        raise RuntimeError("거리 구간 표본이 모자라다")

    rows = []
    for name, code, ip, op, ni, no_ in sgg:
        if not (ip and op) or op <= 0:
            continue
        rows.append({"sigungu_name": name, "sigungu_code": code,
                     "inner": int(ip), "outer": int(op),
                     "gap": round(ip / op, 3),
                     "gap_pct": int(round((ip / op - 1) * 100)),
                     "near_n": int(ni), "far_n": int(no_)})
    if not rows:
        raise RuntimeError("시군구별 비교 표본이 모자라다")
    rows.sort(key=lambda r: -r["gap"])
    gaps = sorted(r["gap"] for r in rows)
    mid = gaps[len(gaps) // 2] if len(gaps) % 2 else \
        (gaps[len(gaps) // 2 - 1] + gaps[len(gaps) // 2]) / 2
    cheaper = [r for r in rows if r["gap"] < 1]

    return {
        "asof": asof.date().isoformat(), "months": months,
        "pyeong_label": PYEONG_LABEL, "sgg_min": SGG_MIN,
        "bands": bl,
        "naive": round(bl[0]["ppy"] / bl[-1]["ppy"], 2),
        "rows": rows, "regions": len(rows),
        "median_gap": round(mid, 2),
        "median_pct": int(round((mid - 1) * 100)),
        "cheaper": cheaper, "cheaper_n": len(cheaper),
    }


def facts(s: dict) -> dict:
    lo, hi = (int(x) for x in s["pyeong_label"].replace("평", "").split("~"))
    return {
        "months": s["months"], "pyeong_lo": lo, "pyeong_hi": hi,
        "near_m": NEAR_M, "far_m": FAR_M, "sgg_min": s["sgg_min"],
        "naive": s["naive"], "median_gap": s["median_gap"],
        "median_pct": s["median_pct"],
        "regions": s["regions"], "cheaper_n": s["cheaper_n"],
        "bands": s["bands"], "rows": s["rows"],
        # 화면에 쓰는 파생값도 근거를 댄다
        "near_km": 0.5, "far_km": 1.5,
        "band_near": s["bands"][0]["ppy"], "band_far": s["bands"][-1]["ppy"],
    }


def scenes(s: dict) -> list[dict]:
    src = f'국토교통부 실거래가 · {s["asof"]} 기준'
    cond = f'{s["pyeong_label"]} · 최근 {s["months"]}개월'
    f = facts(s)
    out: list[dict] = []

    # 1 훅 — 질문으로 연다
    out.append({
        "dark": True, "static": True, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p: (
            f'<div class="rv-kick" {R.anim(0, 1.0)}>{cond}</div>'
            f'<div class="rv-h1" {R.anim(1, 1.0)}>역세권,<br>'
            f'진짜 비쌀까요?</div>'
            f'<div class="rv-num" {R.anim(2, 1.0)}>{s["naive"]}배</div>'
            f'<div class="rv-sub" {R.anim(3, 1.0)}>'
            f'수도권 전체 · 역 500m 이내 vs 1.5km 밖</div>'),
    })

    # 2 거리별 기울기
    rows = [(b["band"], b["ppy"], D.UP if i == 0 else D.NEUTRAL)
            for i, b in enumerate(s["bands"])]
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=rows: (
            f'<div class="rv-kick" {R.anim(0, p)}>평당가</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>멀어질수록<br>싸 보입니다</div>'
            f'<div {R.anim(2, p)}>'
            f'{A.bar_rows(_r, fmt=A.man)}</div>'),
    })

    # 3 착시 — 이 장이 글의 값이다
    out.append({
        "dark": True, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p: (
            f'<div class="rv-kick" {R.anim(0, p)}>그런데 역은 사람 많은 곳에 '
            f'놓입니다</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>같은 구 안에서<br>'
            f'다시 재면</div>'
            f'<div class="rv-num" {R.anim(2, p)}>{s["median_gap"]}배</div>'
            f'<div class="rv-sub" {R.anim(3, p)}>'
            f'{s["regions"]}개 시군구 중앙값. 앞의 {s["naive"]}배에는 '
            f'도심과 외곽의 차이가 섞여 있었어요.</div>'),
    })

    # 4 반전 — 통념이 틀리는 곳
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=s["cheaper"][:LIST_N]: (
            f'<div class="rv-kick" {R.anim(0, p)}>'
            f'{s["regions"]}곳 중 {s["cheaper_n"]}곳은</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>역에서 먼 쪽이<br>'
            f'더 비쌉니다</div>'
            f'<div {R.anim(2, p)}>{A.rows_html([(r["sigungu_name"], f"{r[chr(103)+chr(97)+chr(112)]}배") for r in _r])}</div>'),
    })

    # 5 효과가 큰 곳
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=s["rows"][:LIST_N]: (
            f'<div class="rv-kick" {R.anim(0, p)}>반대로</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>역 하나에<br>'
            f'가장 크게 갈리는 곳</div>'
            f'<div {R.anim(2, p)}>{A.rows_html([(r["sigungu_name"], f"{r[chr(103)+chr(97)+chr(112)]}배") for r in _r])}</div>'),
    })

    out.append(A.follow(f, lead="이런 착시를<br>또 걷어내 드릴게요", notes=[
        "직선거리예요. 실제 걷는 거리는 더 멉니다",
        "환승역인지 급행이 서는지는 보지 않았어요",
        f"구간별 거래가 {s['sgg_min']}건보다 적은 시군구는 비웠어요",
    ]))
    for sc in out:
        sc.setdefault("foot", src)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="역세권 프리미엄 릴스")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()

    s = compute()
    bar = "=" * 62
    print(f"\n{bar}\n  역세권 프리미엄  ({s['pyeong_label']} · "
          f"최근 {s['months']}개월)\n{bar}")
    for b in s["bands"]:
        print(f"  {b['band']:14} 평당 {b['ppy']:>6,}만원  ({b['deals']:,}건)")
    print(f"  전체로 보면 {s['naive']}배")
    print(f"  같은 구 안에서 보면 {s['median_gap']}배 "
          f"({s['regions']}곳 중앙값)")
    print(f"  역에서 먼 쪽이 비싼 곳 {s['cheaper_n']}곳")
    for r in s["rows"][:3]:
        print(f"    + {r['sigungu_name']:12} {r['gap']}배")
    for r in s["cheaper"][-3:]:
        print(f"    - {r['sigungu_name']:12} {r['gap']}배")

    out = A.publish(scenes(s), "subway", ROOT / "output" / s["asof"],
                    "subway.mp4", dry=a.no_render)
    print(f"{bar}\n")
    return 0 if (out or a.no_render) else 1


if __name__ == "__main__":
    sys.exit(main())
