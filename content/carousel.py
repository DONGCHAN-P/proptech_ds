"""T16 — 인스타 캐러셀 + 스레드 이미지.

`docs/02_CLI_디자인지시사항.md` 를 따른다. 토큰과 헬퍼는 `content/design.py`.

구성 7장 — 같은 레이아웃이 연속으로 오지 않게 섞는다.
  1 표지        hero_number   큰 숫자 1개 + 헤드라인
  2 지역 순위    ranked_bars   평소 대비 배수. "평소=1.0" 기준선을 긋는다
  3 양 끝        rows          붐빈 곳 ↔ 조용한 곳 (빨강/파랑이 제 일을 한다)
  4 반전/맥락    quote         반대로 읽히는 신호 (앞 장 안 봐도 이해되게)
  5 단지 비교    compare_bars
  6 표본 경고    hero_number   표본이 적다는 사실 자체를 장으로
  7 정리 + CTA   summary_cta   새 숫자 금지

차트 모듈(T11)의 단독 4:5 PNG 는 스레드에 붙이는 1~2장으로 쓴다. 캐러셀
안에 또 넣으면 2장과 같은 그래프가 두 번 나온다.

지키는 것
  · 빨강/파랑은 증감 전용. 일반 강조는 형광펜 띠
  · σ·표준편차 금지 — "평소의 1.7배" 로 번역
  · 표본 n<10 은 큰 숫자 장에 쓰지 않고 배지를 붙인다
  · 렌더 후 안전영역 이탈·연속 레이아웃을 검사해 실패시 폰트를 줄여 재시도

실행:
  .venv\\Scripts\\python.exe -m content.carousel
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from content.validator import validate  # noqa: E402
from templates.disclaimers import DISCLAIMER_SOCIAL  # noqa: E402

MIN_SAMPLE = 10          # 이보다 적으면 큰 숫자 장에 쓰지 않는다
HEADLINE_MIN = 72        # 넘침 재시도의 하한 (지시사항)


def _img(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


# ── 소재 ─────────────────────────────────────────────────────────────────
def pick(data: dict) -> dict | None:
    z = [r for r in (data.get("weekly", {}).get("sgg_zscore") or [])
         if r.get("deals_z") is not None]
    surge = data.get("weekly", {}).get("surge_apt") or []
    if not z or not surge:
        return None
    for r in z:
        r["ratio"] = (r["week_deals"] / r["deals_avg_52w"]
                      if r.get("deals_avg_52w") else 0)
    solid = [r for r in z if r["week_deals"] >= MIN_SAMPLE
             and r.get("deals_avg_52w")]
    pool = solid or [r for r in z if r.get("deals_avg_52w")]
    busiest = max(pool, key=lambda r: r["week_deals"] / r["deals_avg_52w"])
    # 조용한 쪽도 같은 표본 기준을 태운다. 3건짜리 동네를 "평소의 0.2배"로
    # 내보내면 붐빈 쪽에만 기준을 적용한 셈이 된다.
    quiet = min(pool, key=lambda r: r["week_deals"] / r["deals_avg_52w"])
    top = surge[0]
    # 평소 대비 배수로 줄 세운다 (절대량이면 늘 큰 도시가 1위)
    ranked = sorted([r for r in (solid or z) if r["ratio"]],
                    key=lambda r: r["ratio"], reverse=True)[:6]
    return {"busiest": busiest, "quiet": quiet, "top": top, "ranked": ranked,
            "params": data.get("params") or {}, "asof": data["asof"]}


# ── 장 ───────────────────────────────────────────────────────────────────
def c1_cover(t: dict, n: int) -> dict:
    b = t["busiest"]
    mult = D.times(b["week_deals"], b["deals_avg_52w"])
    inner = (
        f'<div class="body">'
        f'<div class="kicker">{b.get("week_start", "")} 주 · 거래량</div>'
        f'<div class="label">{b["sigungu_name"]}</div>'
        f'<div class="big-pre">평소의</div>'
        f'<div class="big up">{mult}</div>'
        f'<div class="lead">평소 {D.num(b["deals_avg_52w"])}건 → '
        f'이번 주 <span class="mark">{b["week_deals"]}건</span></div>'
        f'</div>')
    return {"name": "01_cover", "layout": "hero_number",
            "facts": {"busiest": b},
            "html": D.head(1, n) + inner + D.foot(t["asof"])}


def c4_counter(t: dict, n: int) -> dict:
    """반전. 1~3장은 앞 장을 안 봐도 이해되게 쓴다."""
    s = t["top"]
    drop = (s["deals_recent"] / s["deals_prior"] - 1) * 100
    inner = (
        f'<div class="body">'
        f'<div class="kicker">같이 봐야 할 것</div>'
        f'<div class="quote">값이 올라도<br>'
        f'<span class="mark">사고판 사람은</span><br>늘지 않았어요</div>'
        f'<div class="rows" style="margin-top:8px">'
        f'<div class="row"><span class="k">{s["apt_name"]} 평단가</span>'
        f'<span class="v {D.delta_color(s["change_pct"])}">{D.delta(s["change_pct"])}</span></div>'
        f'<div class="row"><span class="k">같은 기간 거래 건수</span>'
        f'<span class="v {D.delta_color(drop)}">{D.delta(drop)}</span></div>'
        f'</div></div>')
    return {"name": "04_counter", "layout": "quote",
            "facts": {"top": s, "drop_pct": round(drop, 1)},
            "html": D.head(4, n) + inner + D.foot(t["asof"])}


def c2_ranked(t: dict, n: int) -> dict:
    rows = t["ranked"]
    top = rows[0]
    mx = max(r["ratio"] for r in rows) or 1
    base_pos = 1.0 / mx * 100      # "평소" 위치
    bars = []
    for r in rows:
        color = D.UP if r is top else D.NEUTRAL
        w = r["ratio"] / mx * 100
        bars.append(
            f'<div class="rank-row">'
            f'<div class="rank-name">{r["sigungu_name"]}</div>'
            f'<div class="rank-track">'
            f'<div class="rank-fill" style="width:{w:.0f}%;background:{color}"></div>'
            f'<div class="rank-base" style="left:{base_pos:.1f}%"></div></div>'
            f'<div class="rank-val">{r["ratio"]:.1f}배</div></div>')
    inner = (
        f'<div class="body">'
        f'<div class="h1 xs">평소보다<br>붐빈 지역</div>'
        f'<div class="rank" style="margin-top:4px">{"".join(bars)}</div>'
        f'<div class="rank-baselabel">세로선이 평소 수준이에요</div>'
        f'<div class="sub" style="margin-top:20px">'
        f'{top["sigungu_name"]}만 평소보다 {D.diff_count(top["week_deals"], top["deals_avg_52w"])} '
        f'거래됐어요.</div>'
        f'</div>')
    # 파생값도 발행되는 숫자라 facts 에 남긴다 (검증기가 대조할 수 있게)
    return {"name": "02_ranked", "layout": "ranked_bars",
            "facts": {"ranked": rows,
                      "top_diff": round(top["week_deals"] - top["deals_avg_52w"])},
            "html": D.head(2, n) + inner + D.foot(t["asof"], "평소 = 지난 52주 평균")}


def c3_extremes(t: dict, n: int) -> dict:
    """같은 주의 양 끝.

    순위 장(2)은 붐빈 쪽만 보여준다. 거기서 끊으면 "수도권 거래가 늘었다"로
    읽히는데, 같은 주에 평소의 절반만 거래된 곳도 있다. 빨강/파랑이 증감
    전용이라는 규칙이 처음으로 제 일을 하는 장이기도 하다.
    """
    b, q = t["busiest"], t["quiet"]
    hi = b["week_deals"] / b["deals_avg_52w"]
    lo = q["week_deals"] / q["deals_avg_52w"]
    inner = (
        f'<div class="body">'
        f'<div class="kicker">같은 주, 정반대</div>'
        f'<div class="h1 xs">한 주에도<br>동네마다 달라요</div>'
        f'<div class="rows" style="margin-top:8px">'
        f'<div class="row"><span class="k">{b["sigungu_name"]} '
        f'{b["week_deals"]}건</span>'
        f'<span class="v up">평소의 {hi:.1f}배</span></div>'
        f'<div class="row"><span class="k">{q["sigungu_name"]} '
        f'{q["week_deals"]}건</span>'
        f'<span class="v down">평소의 {lo:.1f}배</span></div>'
        f'</div>'
        f'<div class="sub">수도권을 한 덩어리로 보면 '
        f'<span class="mark">둘 다 안 보여요.</span></div>'
        f'</div>')
    return {"name": "03_extremes", "layout": "rows",
            "facts": {"busiest": b, "quiet": q,
                      "hi_ratio": round(hi, 1), "lo_ratio": round(lo, 1)},
            "html": D.head(3, n) + inner + D.foot(t["asof"], "평소 = 지난 52주 평균")}


def c5_compare(t: dict, n: int) -> dict:
    s = t["top"]
    prior, recent = s["ppy_prior_90d"], s["ppy_recent_90d"]
    mx = max(prior, recent) or 1
    name, paren = D.split_name(s["apt_name"])
    paren_html = (f'<div class="sub" style="font-size:30px">{paren}</div>'
                  if paren else "")
    thin = (f'<div><span class="badge">거래 {s["deals_recent"]}건</span></div>'
            if s["deals_recent"] < MIN_SAMPLE else "")

    def bar(label, val, color):
        return (f'<div class="bar-row"><div class="bar-top">'
                f'<span class="bar-name">{label}</span>'
                f'<span class="bar-val">{D.num(val)}만</span></div>'
                f'<div class="bar-track"><div class="bar-fill" '
                f'style="width:{val / mx * 100:.0f}%;background:{color}"></div>'
                f'</div></div>')

    inner = (
        f'<div class="body">'
        f'<div class="kicker">{s["sigungu_name"]} {s["legal_dong_name"]} · {s["pyeong_bucket"]}</div>'
        f'<div class="h1 xs">{name}</div>{paren_html}'
        f'<div class="sub">평당가, 3개월 전과 비교</div>'
        f'<div class="bars">'
        f'{bar("직전 3개월", prior, D.NEUTRAL)}{bar("최근 3개월", recent, D.UP)}'
        f'</div>{thin}</div>')
    return {"name": "05_compare", "layout": "compare_bars",
            "facts": {"top": s},
            "html": D.head(5, n) + inner + D.foot(t["asof"])}


def c6_sample(t: dict, n: int) -> dict:
    """표본이 적다는 사실 자체를 한 장으로. 숨기면 오해를 부른다."""
    s = t["top"]
    inner = (
        f'<div class="body">'
        f'<div class="kicker">숫자를 믿기 전에</div>'
        f'<div class="big xs">{s["deals_recent"]}건</div>'
        f'<div class="lead">최근 3개월 동안 이 평형에서<br>신고된 거래 수예요.</div>'
        f'<div class="sub"><span class="mark">몇 건으로 평균이 크게 흔들려요.</span><br>'
        f'어떤 층과 어떤 향이 팔렸는지에 따라 달라져요.</div>'
        f'</div>')
    return {"name": "06_sample", "layout": "hero_number",
            "facts": {"top": s},
            "html": D.head(6, n) + inner + D.foot(t["asof"])}


def c7_outro(t: dict, n: int) -> dict:
    """정리. 새 숫자를 쓰지 않는다 — 앞에 나온 값만 되짚는다."""
    b, s = t["busiest"], t["top"]
    inner = (
        f'<div class="body">'
        f'<div class="kicker">정리</div>'
        f'<div class="h1 xs">세 줄 요약</div>'
        f'<div class="lead">'
        f'· {b["sigungu_name"]} 거래가 평소보다 많았어요<br>'
        f'· {s["apt_name"]} 평단가는 올랐어요<br>'
        f'· 다만 거래 건수는 줄었어요</div>'
        f'<div class="cta">저장해두고 <span class="mark">다음 주와 비교</span>해보세요.<br>'
        f'여러분 동네는 이번 주 어땠나요?</div>'
        f'<div class="disc">{DISCLAIMER_SOCIAL}</div>'
        f'</div>')
    return {"name": "07_outro", "layout": "summary_cta",
            "facts": {}, "html": D.head(7, n) + inner}


def build_cards(data: dict, chart_dir: Path | None = None) -> list[dict]:
    """chart_dir 은 더 이상 읽지 않는다 — 차트 조각을 카드에 넣지 않는다.
    호출부(테스트 포함)가 넘기고 있어 인자만 남긴다."""
    t = pick(data)
    if t is None:
        return []
    n = 7
    cards = [c1_cover(t, n), c2_ranked(t, n), c3_extremes(t, n),
             c4_counter(t, n), c5_compare(t, n), c6_sample(t, n),
             c7_outro(t, n)]
    # 글에 나오는 방법론 상수(52주, 3개월 등)도 출처가 있어야 한다.
    # 지표 JSON 의 params 를 함께 넘겨 숫자 검증기가 대조하게 한다.
    for c in cards:
        c["facts"] = {"card": c["facts"], "params": t["params"]}
    return cards


# ── 검사 ─────────────────────────────────────────────────────────────────
def strip_html(h: str) -> str:
    t = re.sub(r"<br\s*/?>", " ", h)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def check_layout_variety(cards: list[dict]) -> list[str]:
    return [f"{a['name']}·{b['name']} 레이아웃 연속 ({a['layout']})"
            for a, b in zip(cards, cards[1:]) if a["layout"] == b["layout"]]


def check_copy(cards: list[dict]) -> list[str]:
    bad = []
    for c in cards:
        text = strip_html(c["html"])
        try:
            D.assert_no_jargon(text, c["name"])
        except ValueError as e:
            bad.append(str(e))
        for w in ("폭등", "역대급", "지금 사야", "놓치면", "떡상"):
            if w in text:
                bad.append(f"{c['name']}: 자극 표현 '{w}'")
    return bad


# ── 렌더 ─────────────────────────────────────────────────────────────────
OVERFLOW_JS = """() => {
  const PX = %d, W = %d, H = %d, bad = [];
  document.querySelectorAll('.card .body *, .card .hd, .card .ft').forEach(el => {
    if (!el.textContent.trim() && el.tagName !== 'IMG') return;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    if (r.left < PX - 1 || r.right > W - PX + 1 || r.top < 8 || r.bottom > H - 8)
      bad.push((el.className || el.tagName) + '@' + Math.round(r.top) + ':' + Math.round(r.bottom));
  });
  return bad;
}"""


def render(cards: list[dict], outdir: Path) -> tuple[list[Path], list[str]]:
    """렌더 후 안전영역 이탈을 검사하고, 넘치면 폰트를 줄여 재시도한다."""
    from playwright.sync_api import sync_playwright

    made, problems = [], []
    js = OVERFLOW_JS % (D.PAD_X, D.W, D.H)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for c in cards:
            page = br.new_page(viewport={"width": D.W, "height": D.H},
                               device_scale_factor=1)
            shrink = 0
            while True:
                extra = ""
                if shrink:
                    extra = (f".h1{{font-size:{max(HEADLINE_MIN, 96 - shrink)}px}}"
                             f".big{{font-size:{max(140, 280 - shrink * 3)}px}}"
                             f".quote{{font-size:{max(48, 64 - shrink)}px}}")
                page.set_content(
                    f"<style>{D.base_css()}{extra}</style>"
                    f'<div class="card">{c["html"]}</div>', wait_until="load")
                page.wait_for_timeout(150)
                over = page.evaluate(js)
                if not over or shrink >= 24:
                    if over:
                        problems.append(f"{c['name']}: 넘침 {over[:2]}")
                    break
                shrink += 4
            out = outdir / f"{c['name']}.png"
            page.screenshot(path=str(out))
            page.close()
            made.append(out)
        br.close()
    return made, problems


def main() -> int:
    ap = argparse.ArgumentParser(description="T16 캐러셀")
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

    print(f"\n{'=' * 62}\n  캐러셀  {data['asof']}  ({D.W}×{D.H})\n{'=' * 62}")
    if not D.has_font():
        print("  ⚠️ Pretendard 없음 — 폰트 품질이 떨어진다")

    cards = build_cards(data, outdir)
    if not cards:
        print("  재료 부족 — 이번 주는 만들지 않는다 (폴백)")
        return 0

    fails = check_layout_variety(cards) + check_copy(cards)
    for c in cards:
        r = validate(strip_html(c["html"]), c["facts"], require_disclaimer=False)
        if not r.ok:
            fails += [f"{c['name']}: {w}" for w in r.reasons]
    if fails:
        print(f"\n  검증 실패 {len(fails)}건 — 렌더하지 않는다")
        for f in fails:
            print(f"    ! {f}")
        return 1

    made, problems = render(cards, outdir)
    for c, p in zip(cards, made):
        print(f"  {c['name']:14s} {c['layout']:14s} {p.stat().st_size / 1024:>5.0f}KB")
    if problems:
        print("\n  넘침 경고:")
        for p in problems:
            print(f"    ! {p}")
    print(f"\n  저장: {outdir}\n{'=' * 62}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
