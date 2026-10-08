"""예산 지도 — "N억이면 어디 살 수 있나".

왜 이 아젠다인가
    단지 소개는 **그 단지를 아는 사람**에게만 뜻이 통한다. "부천 보람마을"은
    나를 모르는 사람에게 아무 의미가 없는데, 릴스는 모르는 사람에게 노출되는
    매체다. 실측으로 평균 시청 2초 / 21초였다.

    예산은 반대다. 설명이 필요 없고, 보는 사람 모두가 자기 숫자를 갖고 있다.
    그리고 "강남 0.0% (724건 중 0건)" 같은 값은 통념을 숫자로 못박는다.

재는 것
    최근 1년, 고른 평형대의 실거래 중 **예산 이하가 몇 %인가**를 시군구별로.
    평균가가 아니라 비율로 재는 이유는, 평균은 "그 동네에 내가 살 집이
    있는가"에 답하지 못하기 때문이다. 평균 9억인 동네에도 6억짜리가 30%
    있으면 선택지가 있는 것이고, 0% 면 없는 것이다.

주의
    ① 평형을 고정한다. 안 그러면 "6억으로 강남"이 소형 한 건으로 참이 된다.
    ② 표본이 얇은 시군구는 비운다. 12건 중 1건을 8.3% 로 쓰면 숫자가 거짓말을
       한다.
    ③ 실거래가 **있었다**는 뜻이지 지금 그 값에 살 수 있다는 뜻이 아니다.
       문구에 적는다.

실행:
  .venv\\Scripts\\python.exe -m content.budget --cap 6
  .venv\\Scripts\\python.exe -m content.budget --cap 6 --no-render
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from content import geo as G  # noqa: E402
from content import reels as R  # noqa: E402

TRADE = ROOT / "master" / "trade_events.parquet"
MONTHS = 12
PYEONGS = ("25P", "30P")        # 25~35평 — "국민평형" 언저리
PYEONG_LABEL = "25~35평"
MIN_DEALS = 30                  # 이보다 얇으면 비율을 쓰지 않는다
LIST_N = 5                      # 장마다 보여줄 지역 수
MID_LO, MID_HI = 0.2, 0.8       # "반반"으로 볼 구간

# 살 수 있는 비율 구간. 평소 지도와 **다른 잣대**라 구간도 색의 뜻도 다르다.
#   파랑이 진할수록 선택지가 많다 / 빨강은 한 건도 없다
BINS = [(0.001, "up", 1.0),     # 0% — 한 건도 없음
        (0.25, "down", 0.25),
        (0.5, "down", 0.5),
        (0.9, "down", 0.75),
        (9e9, "down", 1.0)]
LEGEND = ("한 건도 없음", "4곳 중 1곳 미만", "절반쯤", "대부분", "거의 전부")


def won_eok(man: int) -> str:
    """6억 처럼 억 단위로. 입력은 만원."""
    v = man / 10000
    return f"{v:.0f}억" if abs(v - round(v)) < 0.05 else f"{v:.1f}억"


def compute(cap_man: int, *, pyeongs=PYEONGS, months: int = MONTHS,
            min_deals: int = MIN_DEALS) -> dict:
    """시군구별로 '예산 이하 비율'을 잰다."""
    import duckdb
    from metrics.filters import trades_cte

    if not TRADE.exists():
        raise RuntimeError(f"거래 원장이 없다: {TRADE}")
    buckets = ",".join(f"'{p}'" for p in pyeongs)
    con = duckdb.connect()
    try:
        rows = con.execute(f"""
            {trades_cte(TRADE.as_posix())}
            SELECT sigungu_name,
                   any_value(sigungu_code) AS sigungu_code,
                   count(*) AS deals,
                   sum(CASE WHEN deal_amount <= {cap_man} THEN 1 ELSE 0 END)
                     AS under,
                   round(median(deal_amount)) AS mid
            FROM trades
            WHERE deal_date > (SELECT max(deal_date) FROM trades)
                               - INTERVAL {months} MONTH
              AND pyeong_bucket IN ({buckets})
            GROUP BY 1
            ORDER BY 1
        """).fetchall()
        asof = con.execute(
            f"{trades_cte(TRADE.as_posix())} "
            f"SELECT max(deal_date) FROM trades").fetchone()[0]
    finally:
        con.close()

    out = []
    for name, code, deals, under, mid in rows:
        if deals < min_deals:
            continue          # 얇은 표본으로 비율을 말하지 않는다
        out.append({"sigungu_name": name, "sigungu_code": code,
                    "deals": int(deals), "under": int(under),
                    "ratio": round(under / deals, 4),
                    "median": int(mid)})
    out.sort(key=lambda r: (-r["ratio"], -r["deals"]))
    return {
        "cap": cap_man, "cap_label": won_eok(cap_man),
        "asof": asof.date().isoformat(),
        "pyeong_label": PYEONG_LABEL, "months": months,
        "min_deals": min_deals,
        "rows": out,
        "none": [r for r in out if r["under"] == 0],
        "all_": [r for r in out if r["ratio"] >= 0.9],
        "mid": [r for r in out if MID_LO <= r["ratio"] <= MID_HI],
    }


def facts(b: dict) -> dict:
    """검증기에 넘길 재료. 화면에 나오는 숫자는 전부 여기 있어야 한다.

    비율을 0.77 로만 담으면 화면의 "77%" 가 출처 없는 숫자가 된다. 반올림한
    값도 **발행되는 값**이라 같이 댄다. 평형 라벨의 25·35, 표본 문턱 30 도
    마찬가지다 — 라벨은 숫자를 새로 만든다.
    """
    lo, hi = (int(x) for x in
              b["pyeong_label"].replace("평", "").split("~"))
    return {
        "cap": b["cap"], "months": b["months"],
        "regions": len(b["rows"]),
        "none_n": len(b["none"]), "all_n": len(b["all_"]),
        "mid_n": len(b["mid"]),
        "min_deals": b["min_deals"],
        "pyeong_lo": lo, "pyeong_hi": hi,
        "rows": [dict(r, pct=int(round(r["ratio"] * 100))) for r in b["rows"]],
    }


def pct(r: dict) -> str:
    """0% 는 **한 건도 없을 때만** 쓴다.

    1,000건 중 2건(0.2%)을 반올림해 0% 로 적으면 "한 건도 없다"와 구분되지
    않는다. 지도에서는 둘이 다른 색인데 목록에서만 같아지면, 보는 사람은
    둘 중 하나가 틀렸다고 생각한다.
    """
    v = r["ratio"] * 100
    if r["under"] == 0:
        return "0%"
    if v < 0.5:
        return "1% 미만"
    if v >= 99.5:
        return "100%" if r["under"] == r["deals"] else "99% 이상"
    return f"{v:.0f}%"


def rows_html(items: list[dict], *, show_pct: bool = True) -> str:
    out = []
    for r in items:
        right = pct(r) if show_pct else f'{r["deals"]:,}건 중 {r["under"]:,}건'
        out.append(
            f'<div class="rv-bar"><div class="t">'
            f'<span>{r["sigungu_name"]}</span><span>{right}</span>'
            f'</div></div>')
    return f'<div class="rv-bars">{"".join(out)}</div>'


def legend_html() -> str:
    cells = []
    for (edge, side, t), lab in zip(BINS, LEGEND):
        c = G.mix(D.BG, D.UP if side == "up" else D.DOWN, t)
        cells.append(f'<span style="display:inline-flex;align-items:center;'
                     f'gap:10px"><i style="width:30px;height:30px;'
                     f'border-radius:7px;background:{c};display:inline-block">'
                     f'</i>{lab}</span>')
    return (f'<div style="display:flex;flex-wrap:wrap;gap:18px 26px;'
            f'font-size:28px;color:{D.SUB}">{"".join(cells)}</div>')


def heat_svg(b: dict, *, width: int, height: int) -> str:
    vals = {r["sigungu_name"]: r["ratio"] for r in b["rows"]}
    return G.heat(vals, width=width, height=height, bg=D.BG,
                  up=D.UP, down=D.DOWN, dim=D.NEUTRAL, bins=BINS) or ""


def scenes(b: dict) -> list[dict]:
    """릴스 6장. 단지 덱과 같은 규격·같은 검증을 쓴다."""
    cap = b["cap_label"]
    src = f'국토교통부 실거래가 · {b["asof"]} 기준'
    cond = f'{b["pyeong_label"]} · 최근 {b["months"]}개월'
    f = facts(b)
    out: list[dict] = []
    svg_small = heat_svg(b, width=848, height=330)
    svg_big = heat_svg(b, width=848, height=640)

    # 1 훅 — 멈춰 세운다. 첫 프레임이 전부다.
    out.append({
        "dark": True, "static": True, "foot": f'{src} · {cond}',
        "facts": f,
        "body": lambda p, _s=svg_small: (
            f'<div class="rv-kick" {R.anim(0, 1.0)}>{cond}</div>'
            f'<div class="rv-h1" {R.anim(1, 1.0)}>{cap}이면<br>'
            f'어디 살 수 있을까요?</div>'
            f'<div class="rv-map" {R.anim(3, 1.0)}>{_s}</div>'),
    })

    # 2 지도 — 색이 곧 답이다
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _s=svg_big: (
            f'<div class="rv-kick" {R.anim(0, p)}>수도권 '
            f'{f["regions"]}개 시군구</div>'
            f'<div {R.anim(1, p)}>{_s}</div>'
            f'<div {R.anim(2, p)}>{legend_html()}</div>'),
    })

    # 3 거의 전부 살 수 있는 곳
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=b["all_"][:LIST_N]: (
            f'<div class="rv-kick" {R.anim(0, p)}>거래 10건 중 9건 이상이 '
            f'{cap} 이하</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>여기는<br>고를 수 있어요</div>'
            f'<div {R.anim(2, p)}>{rows_html(_r)}</div>'),
    })

    # 4 한 건도 없는 곳 — 이 장이 가장 세다
    out.append({
        "dark": True, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=b["none"][:LIST_N]: (
            f'<div class="rv-kick" {R.anim(0, p)}>최근 '
            f'{b["months"]}개월 거래 전부를 봐도</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>{cap}짜리가<br>'
            f'한 건도 없어요</div>'
            f'<div {R.anim(2, p)}>{rows_html(_r, show_pct=False)}</div>'),
    })

    # 5 반반 — 현실적인 선택지
    out.append({
        "dark": False, "foot": f'{src} · {cond}', "facts": f,
        "body": lambda p, _r=b["mid"][:LIST_N]: (
            f'<div class="rv-kick" {R.anim(0, p)}>절반쯤 되는 곳</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>여기가<br>갈림길이에요</div>'
            f'<div {R.anim(2, p)}>{rows_html(_r)}</div>'),
    })

    # 6 팔로우
    out.append({
        "dark": False, "last": True, "foot": src, "facts": f,
        "body": lambda p: (
            f'<div class="rv-kick" {R.anim(0, p)}>다음 주에도</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>금액을 바꿔<br>'
            f'또 그려드릴게요</div>'
            f'<div {R.anim(2, p)}><span class="rv-handle">'
            f'{D.HANDLE}</span></div>'
            f'<div class="rv-sub" {R.anim(3, p)}>· 실제로 거래된 값이에요. '
            f'지금 그 값에 살 수 있다는 뜻은 아니에요<br>'
            f'· 표본이 {b["min_deals"]}건보다 적은 곳은 비웠어요</div>'
            f'<div class="rv-disc" {R.anim(4, p)}>'
            f'{R.DISCLAIMER_SOCIAL}</div>'),
    })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="예산 지도 릴스")
    ap.add_argument("--cap", type=float, default=6, help="예산 (억)")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()

    cap_man = int(round(a.cap * 10000))
    b = compute(cap_man)
    bar = "=" * 62
    print(f"\n{bar}\n  예산 지도  {b['cap_label']}  "
          f"({b['pyeong_label']} · 최근 {b['months']}개월)\n{bar}")
    print(f"  시군구 {len(b['rows'])}곳 "
          f"(표본 {b['min_deals']}건 미만 제외)")
    print(f"  거의 전부 {len(b['all_'])}곳 · 반반 {len(b['mid'])}곳 · "
          f"한 건도 없음 {len(b['none'])}곳")
    for r in b["all_"][:3]:
        print(f"    + {r['sigungu_name']:12} {pct(r):>5}  "
              f"({r['under']:,}/{r['deals']:,}건)")
    for r in b["none"][:3]:
        print(f"    - {r['sigungu_name']:12} {pct(r):>5}  "
              f"(0/{r['deals']:,}건)")

    scs = scenes(b)
    fails = []
    for i, sc in enumerate(scs, 1):
        text = R.strip_html(sc["body"](1.0))
        D.assert_no_jargon(text, f"budget{i}")
        r = R.validate(text, {"card": sc["facts"]}, require_disclaimer=False)
        if not r.ok:
            fails += [f"{i}장: {w}" for w in r.reasons]
    if fails:
        print(f"\n  검증 실패 {len(fails)}건 — 렌더하지 않는다")
        for x in fails:
            print(f"    ! {x}")
        return 1
    print("  검증 통과")

    if a.no_render:
        print(f"{bar}\n")
        return 0
    outdir = ROOT / "output" / b["asof"]
    outdir.mkdir(parents=True, exist_ok=True)
    final = R.render(scs, outdir, name=f"budget_{b['cap_label']}.mp4")
    print(f"\n  저장: {final}  ({final.stat().st_size / 1e6:.1f}MB)\n{bar}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
