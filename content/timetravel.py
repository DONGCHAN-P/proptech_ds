"""시간여행 — "20년 전 그 아파트는 얼마였을까".

왜 이 아젠다인가
    2006년부터 쌓인 실거래가 이 프로젝트의 가장 큰 자산이다. 연 15~36만 건이
    있어 20년 전과 지금을 같은 잣대로 견줄 수 있다. 포털 시세로는 못 하는
    일이다.

    그리고 숫자가 세다. 서울 30평대 중위가가 2006년 3.1억에서 지금 10.5억이다.

가장 센 장면은 **같은 값에서 갈라진 곳**이다
    성남수정구와 고양일산서구는 20년 전 둘 다 2.7~2.8억이었다. 지금은
    12.3억과 4.1억이다. "그때 어디를 샀느냐"가 8억을 갈랐다는 이야기는
    설명이 필요 없다.

조심할 것
    ① 중위가는 **그 해 거래된 집들의 가운데 값**이다. 같은 집을 추적한 게
       아니다. 재건축·신축이 섞이면 같은 동네라도 구성이 바뀐다.
    ② 물가와 소득도 올랐다. 배수만 보면 과장된다. 마지막 장에 적는다.

실행:
  .venv\\Scripts\\python.exe -m content.timetravel
  .venv\\Scripts\\python.exe -m content.timetravel --from 2006 --no-render
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import agenda as A  # noqa: E402
from content import design as D  # noqa: E402
from content import reels as R  # noqa: E402

TRADE = ROOT / "master" / "trade_events.parquet"
FROM_YEAR = 2006
PYEONG = "30P"
PYEONG_LABEL = "30평대"
MIN_DEALS = 30          # 해당 연도 시군구 표본 문턱
LIST_N = 4
SAME_TOL = 0.08         # "그때 같은 값" 으로 볼 범위 (±8%)


def compute(*, from_year: int = FROM_YEAR, pyeong: str = PYEONG,
            min_deals: int = MIN_DEALS) -> dict:
    import duckdb
    from metrics.filters import trades_cte

    con = duckdb.connect()
    try:
        T = trades_cte(TRADE.as_posix())
        to_year = con.execute(
            f"{T} SELECT max(year(deal_date)) FROM trades").fetchone()[0]
        asof = con.execute(
            f"{T} SELECT max(deal_date) FROM trades").fetchone()[0]
        mid_year = (from_year + to_year) // 2

        rows = con.execute(f"""
            {T}
            SELECT sigungu_name, any_value(sigungu_code) AS code,
              sum(CASE WHEN year(deal_date)={from_year} THEN 1 ELSE 0 END)
                AS n_old,
              median(CASE WHEN year(deal_date)={from_year}
                          THEN deal_amount END) AS p_old,
              sum(CASE WHEN year(deal_date)={to_year} THEN 1 ELSE 0 END)
                AS n_new,
              median(CASE WHEN year(deal_date)={to_year}
                          THEN deal_amount END) AS p_new
            FROM trades WHERE pyeong_bucket='{pyeong}'
            GROUP BY 1
            HAVING n_old >= {min_deals} AND n_new >= {min_deals}
        """).fetchall()

        seoul = {}
        for y in (from_year, mid_year, to_year):
            v = con.execute(f"""
                {T} SELECT median(deal_amount) FROM trades
                WHERE pyeong_bucket='{pyeong}' AND year(deal_date)={y}
                  AND sigungu_code LIKE '11%'
            """).fetchone()[0]
            if v:
                seoul[y] = int(round(v))
    finally:
        con.close()

    out = []
    for name, code, n_old, p_old, n_new, p_new in rows:
        if not (p_old and p_new) or p_old <= 0:
            continue
        out.append({"sigungu_name": name, "sigungu_code": code,
                    "old": int(round(p_old)), "new": int(round(p_new)),
                    "n_old": int(n_old), "n_new": int(n_new),
                    "times": round(p_new / p_old, 1)})
    if not out:
        raise RuntimeError("20년 비교가 가능한 시군구가 없다")
    out.sort(key=lambda r: -r["times"])

    return {
        "asof": asof.date().isoformat(),
        "from_year": from_year, "mid_year": mid_year, "to_year": to_year,
        "span": to_year - from_year,
        "pyeong_label": PYEONG_LABEL, "min_deals": min_deals,
        "rows": out, "regions": len(out),
        "seoul": seoul,
        "seoul_times": (round(seoul[to_year] / seoul[from_year], 1)
                        if len(seoul) >= 2 else None),
        "pair": same_start(out),
    }


def same_start(rows: list[dict]) -> tuple[dict, dict] | None:
    """20년 전 값이 가장 비슷했는데 지금 가장 벌어진 두 곳.

    "그때 같은 값이었다"가 성립해야 이야기가 선다. 비슷한 값끼리만 짝을
    짓고, 그 중 지금 차이가 가장 큰 쌍을 고른다.
    """
    best = None
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            lo, hi = sorted((a["old"], b["old"]))
            if hi > lo * (1 + SAME_TOL):
                continue
            gap = abs(a["new"] - b["new"])
            if best is None or gap > best[0]:
                hi_r, lo_r = (a, b) if a["new"] >= b["new"] else (b, a)
                best = (gap, hi_r, lo_r)
    return (best[1], best[2]) if best else None


def facts(t: dict) -> dict:
    f = {
        "from_year": t["from_year"], "mid_year": t["mid_year"],
        "to_year": t["to_year"], "span": t["span"],
        "min_deals": t["min_deals"], "regions": t["regions"],
        "rows": t["rows"],
        "seoul": [{"year": y, "price": v} for y, v in t["seoul"].items()],
        "seoul_times": t["seoul_times"],
        "pyeong_lo": 30,
    }
    # 화면에 억 단위로 쓰므로 반올림한 값도 근거를 댄다
    f["seoul_eok"] = [round(v / 10000, 1) for v in t["seoul"].values()]
    f["rows_eok"] = [{"old": round(r["old"] / 10000, 1),
                      "new": round(r["new"] / 10000, 1)} for r in t["rows"]]
    if t["pair"]:
        hi, lo = t["pair"]
        f["pair_gap_eok"] = round((hi["new"] - lo["new"]) / 10000, 1)
        f["pair_old_eok"] = [round(hi["old"] / 10000, 1),
                             round(lo["old"] / 10000, 1)]
    return f


def scenes(t: dict) -> list[dict]:
    src = f'국토교통부 실거래가 · {t["asof"]} 기준'
    cond = f'{t["pyeong_label"]} · {t["from_year"]} vs {t["to_year"]}'
    f = facts(t)
    y0, y1 = t["from_year"], t["to_year"]
    out: list[dict] = []

    # 1 훅 — 20년 전 값
    first = A.eok(t["seoul"][y0]) if t["seoul"] else ""
    out.append({
        "dark": True, "static": True, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p: (
            f'<div class="rv-kick" {R.anim(0, 1.0)}>{y0}년 서울 '
            f'{t["pyeong_label"]}</div>'
            f'<div class="rv-h1" {R.anim(1, 1.0)}>그때는<br>얼마였을까요?</div>'
            f'<div class="rv-num" {R.anim(2, 1.0)}>{first}</div>'
            f'<div class="rv-sub" {R.anim(3, 1.0)}>'
            f'그해 거래된 집들의 가운데 값</div>'),
    })

    # 2 서울 흐름
    rows = [(f'{y}년', v, D.UP if y == y1 else D.NEUTRAL)
            for y, v in t["seoul"].items()]
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=rows: (
            f'<div class="rv-kick" {R.anim(0, p)}>서울 '
            f'{t["pyeong_label"]} 중위 실거래가</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>{t["span"]}년 만에<br>'
            f'{t["seoul_times"]}배</div>'
            f'<div {R.anim(2, p)}>{A.bar_rows(_r, fmt=A.eok)}</div>'),
    })

    # 3 가장 많이 오른 곳
    top = [(r["sigungu_name"], f'{r["times"]}배') for r in t["rows"][:LIST_N]]
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=top: (
            f'<div class="rv-kick" {R.anim(0, p)}>{t["regions"]}개 시군구 중</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>가장 많이<br>오른 곳</div>'
            f'<div {R.anim(2, p)}>{A.rows_html(_r)}</div>'),
    })

    # 4 덜 오른 곳
    bot = [(r["sigungu_name"], f'{r["times"]}배') for r in t["rows"][-LIST_N:]]
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=bot: (
            f'<div class="rv-kick" {R.anim(0, p)}>같은 {t["span"]}년인데</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>여기는<br>이만큼이었어요</div>'
            f'<div {R.anim(2, p)}>{A.rows_html(_r)}</div>'),
    })

    # 5 같은 값에서 갈라진 두 곳 — 가장 센 장
    if t["pair"]:
        hi, lo = t["pair"]
        pair_rows = [
            (f'{hi["sigungu_name"]}', f'{A.eok(hi["old"])} → {A.eok(hi["new"])}'),
            (f'{lo["sigungu_name"]}', f'{A.eok(lo["old"])} → {A.eok(lo["new"])}'),
        ]
        out.append({
            "dark": True, "foot": f'{src} · {cond}', "facts": f,
            "body": lambda p, _r=pair_rows: (
                f'<div class="rv-kick" {R.anim(0, p)}>{y0}년에는 '
                f'거의 같은 값이었어요</div>'
                f'<div class="rv-h1" {R.anim(1, p)}>지금은<br>'
                f'{f["pair_gap_eok"]}억 차이</div>'
                f'<div {R.anim(2, p)}>{A.rows_html(_r)}</div>'),
        })

    out.append(A.follow(f, lead="다른 평형도<br>되감아 드릴게요", notes=[
        "같은 집을 따라간 게 아니라, 그해 거래된 집들의 가운데 값이에요",
        "물가와 소득도 함께 올랐어요. 배수만 보면 과장됩니다",
        f'그해 거래가 {t["min_deals"]}건보다 적은 곳은 비웠어요',
    ]))
    for sc in out:
        sc.setdefault("foot", src)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="시간여행 릴스")
    ap.add_argument("--from", dest="from_year", type=int, default=FROM_YEAR)
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()

    t = compute(from_year=a.from_year)
    bar = "=" * 62
    print(f"\n{bar}\n  시간여행  {t['from_year']} → {t['to_year']}  "
          f"({t['pyeong_label']})\n{bar}")
    for y, v in t["seoul"].items():
        print(f"  서울 {y}  {A.eok(v)}")
    print(f"  -> {t['span']}년 만에 {t['seoul_times']}배")
    print(f"  비교 가능 {t['regions']}곳")
    for r in t["rows"][:3]:
        print(f"    + {r['sigungu_name']:12} {A.eok(r['old'])} → "
              f"{A.eok(r['new'])}  ({r['times']}배)")
    for r in t["rows"][-2:]:
        print(f"    - {r['sigungu_name']:12} {A.eok(r['old'])} → "
              f"{A.eok(r['new'])}  ({r['times']}배)")
    if t["pair"]:
        hi, lo = t["pair"]
        print(f"  같은 값에서 갈라짐: {hi['sigungu_name']} vs "
              f"{lo['sigungu_name']}")

    out = A.publish(scenes(t), "timetravel", ROOT / "output" / t["asof"],
                    f"timetravel_{t['from_year']}.mp4", dry=a.no_render)
    print(f"{bar}\n")
    return 0 if (out or a.no_render) else 1


if __name__ == "__main__":
    sys.exit(main())
