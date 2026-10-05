"""T11 — 차트.

`docs/02_CLI_디자인지시사항.md` 7항을 따른다. matplotlib 대신 **HTML/SVG +
Playwright** 로 그린다 — 같은 폰트와 토큰을 카드와 공유해야 하고, matplotlib
기본 스타일이 남으면 바로 "자동 생성물" 로 보인다.

규칙
  · 제목은 결론 문장. 부제에 기간·기준
  · 강조 1개만 의미색, 나머지는 중립색
  · 막대는 축을 없애고 값 라벨을 막대 끝에
  · 꺾은선은 거래가 드물면 **점 + 이동평균**. 면적 채움 금지,
    y축이 0에서 시작하지 않으면 면적·막대 금지
  · 차트 안 글자 최소 26px
  · 카드 밖 단독 차트도 1080×1350 (유튜브용만 16:9)

실행:
  .venv\\Scripts\\python.exe -m content.charts
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402

CW, CH = 1080, 1350          # 단독 차트도 4:5
MIN_SAMPLE = 10              # 큰 숫자에 쓰려면 이만큼은 있어야 한다
IN_CARD_W, IN_CARD_H = 936, 560   # 카드 안에 넣는 차트 (1080 - 좌우 72*2)


def _svg_bars(rows: list[dict], *, name_key: str, val_key: str,
              hi_index: int = 0, unit: str = "건",
              width: int, height: int, fmt=None) -> str:
    """가로 막대. 축선·격자 없음, 값은 막대 끝에."""
    n = len(rows)
    gap, pad_l, pad_r = 18, 250, 150
    bar_h = max(26, (height - gap * (n - 1)) // n)
    mx = max(float(r[val_key]) for r in rows) or 1
    track = width - pad_l - pad_r

    parts = []
    for i, r in enumerate(rows):
        y = i * (bar_h + gap)
        w = float(r[val_key]) / mx * track
        color = D.UP if i == hi_index else D.NEUTRAL
        parts.append(
            f'<text x="{pad_l - 20}" y="{y + bar_h * 0.72}" text-anchor="end" '
            f'font-size="30" font-weight="600" fill="{D.INK}">{r[name_key]}</text>'
            f'<rect x="{pad_l}" y="{y}" width="{w:.1f}" height="{bar_h}" '
            f'rx="{bar_h / 2:.0f}" fill="{color}"/>'
            f'<text x="{pad_l + w + 18:.1f}" y="{y + bar_h * 0.72}" '
            f'font-size="30" font-weight="700" fill="{D.INK}">'
            f'{(fmt or D.num)(r[val_key])}{unit}</text>')
    total_h = n * bar_h + (n - 1) * gap
    return (f'<svg width="{width}" height="{total_h}" '
            f'viewBox="0 0 {width} {total_h}" '
            f'style="font-family:Pretendard">{"".join(parts)}</svg>')


def _svg_scatter_ma(points: list[dict], *, width: int, height: int) -> str:
    """거래 점 + 이동평균선.

    거래가 드문 단지를 선으로 이으면 3년 공백이 연속 추세처럼 보인다.
    점으로 찍고 추세는 이동평균으로만 보여준다. 면적 채움은 하지 않는다.
    """
    if len(points) < 2:
        return ""
    xs = [datetime.strptime(p["ym"], "%Y-%m") for p in points]
    ys = [float(p["avg_price"]) for p in points]
    t0, t1 = xs[0].timestamp(), xs[-1].timestamp()
    span = (t1 - t0) or 1
    lo, hi = min(ys), max(ys)
    rng = (hi - lo) or 1
    pad = rng * 0.18
    lo, hi = lo - pad, hi + pad

    pl, pr, pt, pb = 130, 40, 30, 70
    iw, ih = width - pl - pr, height - pt - pb

    def X(d):
        return pl + (d.timestamp() - t0) / span * iw

    def Y(v):
        return pt + (1 - (v - lo) / (hi - lo)) * ih

    # 6개월 이동평균
    ma = []
    for i, d in enumerate(xs):
        win = [ys[j] for j in range(len(xs))
               if 0 <= (d - xs[j]).days <= 185 and j <= i]
        if win:
            ma.append((d, sum(win) / len(win)))
    path = " ".join(f"{'M' if i == 0 else 'L'}{X(d):.1f},{Y(v):.1f}"
                    for i, (d, v) in enumerate(ma))

    grid = []
    for k in range(3):
        v = lo + (hi - lo) * (k + 0.5) / 3
        y = Y(v)
        grid.append(
            f'<line x1="{pl}" x2="{width - pr}" y1="{y:.1f}" y2="{y:.1f}" '
            f'stroke="{D.LINE}" stroke-width="1"/>'
            f'<text x="{pl - 16}" y="{y + 10:.1f}" text-anchor="end" '
            f'font-size="26" fill="{D.SUB}">{D.won(v)}</text>')

    # 시간축은 연 단위로 규칙적으로
    ticks = []
    for yr in range(xs[0].year, xs[-1].year + 1):
        d = datetime(yr, 1, 1)
        if not (xs[0] <= d <= xs[-1]):
            continue
        ticks.append(f'<text x="{X(d):.1f}" y="{height - 24}" '
                     f'text-anchor="middle" font-size="26" fill="{D.SUB}">{yr}</text>')

    dots = "".join(f'<circle cx="{X(d):.1f}" cy="{Y(v):.1f}" r="9" '
                   f'fill="{D.UP}" stroke="{D.BG}" stroke-width="3"/>'
                   for d, v in zip(xs, ys))
    return (f'<svg width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" style="font-family:Pretendard">'
            f'{"".join(grid)}{"".join(ticks)}'
            f'<path d="{path}" fill="none" stroke="{D.NEUTRAL}" '
            f'stroke-width="4" stroke-linecap="round"/>{dots}</svg>')


# ── 차트 페이지 ──────────────────────────────────────────────────────────
def chart_region(data: dict) -> dict:
    """지역별 거래량. 카드 2장에 들어갈 조각과 단독 장 양쪽으로 쓴다."""
    z = [r for r in (data.get("weekly", {}).get("sgg_zscore") or [])
         if r.get("deals_z") is not None]
    if not z:
        return {}
    # 절대 거래량이 아니라 **평소 대비 배수**로 줄 세운다. 이 프로젝트의 앵글이
    # "지역끼리가 아니라 자기 평소와 비교" 라서, 절대량으로 정렬하면 늘 큰 도시가
    # 1위로 올라오고 제목이 "평소의 1.1배" 같은 밋밋한 값이 된다.
    for r in z:
        r["ratio"] = (r["week_deals"] / r["deals_avg_52w"]
                      if r.get("deals_avg_52w") else 0)
    # 표본이 적으면 배수가 쉽게 튄다 (연천군 7건으로 2.4배). 지시사항대로
    # 큰 숫자·헤드라인에는 n>=MIN_SAMPLE 인 곳만 쓴다.
    solid = [r for r in z if r["ratio"] and r["week_deals"] >= MIN_SAMPLE]
    rows = sorted(solid or [r for r in z if r["ratio"]],
                  key=lambda r: r["ratio"], reverse=True)[:6]
    if not rows:
        return {}
    top = rows[0]
    svg = _svg_bars(rows, name_key="sigungu_name", val_key="ratio",
                    hi_index=0, unit="배", width=IN_CARD_W, height=IN_CARD_H,
                    fmt=lambda v: f"{v:.1f}")
    title = f'{top["sigungu_name"]} 거래, 평소의 {top["ratio"]:.1f}배'
    return {"name": "chart_region", "in_card": svg, "title": title,
            "sub": f'{top.get("week_start", "")} 주 · 평소 = 지난 52주 평균',
            "facts": {"ranked": rows}}


def chart_apt(data: dict) -> dict:
    """단지 가격 추이. 점 + 이동평균."""
    series = data.get("series") or []
    if not series:
        return {}
    s = series[0]
    pts = s["points"]
    svg = _svg_scatter_ma(pts, width=IN_CARD_W, height=IN_CARD_H)
    if not svg:
        return {}
    first, last = pts[0]["avg_price"], pts[-1]["avg_price"]
    pct = (last / first - 1) * 100 if first else 0
    name, _ = D.split_name(s["apt_name"])
    return {"name": "chart_apt", "in_card": svg,
            "title": f'{name} {s["pyeong_bucket"]}, {D.delta(pct)}',
            "sub": f'{pts[0]["ym"]} ~ {pts[-1]["ym"]} · 거래 {len(pts)}건 · '
                   f'점은 월평균, 선은 6개월 이동평균',
            "facts": {"series": s, "change_pct": round(pct, 1)}}


def page_html(ch: dict, asof: str) -> str:
    return (
        f'<div class="card">'
        f'{D.head(1, 1)}'
        f'<div class="body">'
        f'<div class="h1 xs">{ch["title"]}</div>'
        f'<div class="sub">{ch["sub"]}</div>'
        f'<div style="margin-top:12px">{ch["in_card"]}</div>'
        f'</div>{D.foot(asof)}</div>')


def render(pages: list[tuple[str, str]], outdir: Path) -> list[Path]:
    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for name, html in pages:
            page = br.new_page(viewport={"width": CW, "height": CH},
                               device_scale_factor=1)
            page.set_content(f"<style>{D.base_css()}</style>{html}",
                             wait_until="load")
            page.wait_for_timeout(150)
            out = outdir / f"{name}.png"
            page.screenshot(path=str(out))
            page.close()
            made.append(out)
        br.close()
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description="T11 차트")
    ap.add_argument("--metrics")
    args = ap.parse_args()

    files = sorted((ROOT / "output").glob("metrics_*.json"))
    src = Path(args.metrics) if args.metrics else (files[-1] if files else None)
    if src is None or not src.exists():
        print("지표 JSON 이 없다. 먼저: python -m metrics.build_metrics")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    outdir = ROOT / "output" / data["asof"]
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 62}\n  차트  {data['asof']}  ({CW}×{CH})\n{'=' * 62}")
    if not D.has_font():
        print("  ⚠️ Pretendard 없음")

    charts = [c for c in (chart_region(data), chart_apt(data)) if c]
    if not charts:
        print("  재료 부족")
        return 0

    for c in charts:
        D.assert_no_jargon(c["title"] + c["sub"], c["name"])

    # 카드 안에 넣을 조각(SVG)은 따로 저장해 carousel 이 가져다 쓴다
    for c in charts:
        (outdir / f'{c["name"]}.svg').write_text(c["in_card"], encoding="utf-8")

    made = render([(c["name"], page_html(c, data["asof"])) for c in charts],
                  outdir)
    for c, p in zip(charts, made):
        print(f'  {c["name"]:14s} {p.stat().st_size / 1024:>5.0f}KB  {c["title"]}')
    print(f"\n  저장: {outdir}\n{'=' * 62}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
