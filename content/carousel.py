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
HEADLINE_MIN = 72        # 넘침 재시도의 하한 (지시사항 9항)
FILL_STEP, FILL_MAX = 0.12, 2.4   # 빈 공간 채우기 반복 폭


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
    # 신고가는 **누적 거래가 두터운** 평형에서 고른다. 지표 JSON 은 편차가
    # 큰 순으로 정렬돼 있어 첫 행이 누적 6건짜리인 경우가 흔한데, 그런
    # "148% 경신"은 시세가 아니라 표본이 만든 숫자다.
    nh = [r for r in (data.get("daily", {}).get("new_high") or [])
          if r.get("history_count", 0) >= MIN_SAMPLE]
    new_high = max(nh, key=lambda r: r["history_count"]) if nh else None
    return {"busiest": busiest, "quiet": quiet, "top": top, "ranked": ranked,
            "new_high": new_high,
            "params": data.get("params") or {}, "asof": data["asof"]}


# ── 장 ───────────────────────────────────────────────────────────────────
def c1_cover(t: dict, n: int) -> dict:
    """표지 — 헤드라인이 궁금증을 만들고, 큰 숫자가 답의 크기를 보여준다.

    지시사항 5항: 지역명은 **회색 라벨이 아니라 헤드라인 안에** 넣는다.
    라벨로 빼두면 눈이 큰 글씨부터 읽어서 "어디 얘기인지"가 뒤늦게 들어온다.
    헤드라인은 질문형으로 두고, 왜 그런지는 2~3장이 받는다.
    """
    b = t["busiest"]
    mult = D.times(b["week_deals"], b["deals_avg_52w"])
    inner = (
        f'<div class="body">'
        f'<div class="kicker">{b.get("week_start", "")} 주 · 수도권 거래량</div>'
        f'<div class="h1">{b["sigungu_name"]} 거래가<br>갑자기 늘었어요.<br>'
        f'얼마나 늘었을까요?</div>'
        f'<div class="big-pre">평소의</div>'
        f'<div class="big up">{mult}</div>'
        f'<div class="lead">평소 {D.num(b["deals_avg_52w"])}건 → '
        f'이번 주 {b["week_deals"]}건</div>'
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
        # 아래 두 행이 up/down 을 쓴다. 여기에 형광펜 띠까지 더하면 한 장에
        # 의미색이 셋이 돼 증감 신호가 묻힌다 (지시사항 3항).
        f'<div class="quote">값이 올라도<br>사고판 사람은<br>늘지 않았어요</div>'
        f'<div class="rows">'
        f'<div class="row"><span class="k">{s["apt_name"]} 평단가</span>'
        f'<span class="v {D.delta_color(s["change_pct"])}">{D.delta(s["change_pct"])}</span></div>'
        f'<div class="row"><span class="k">같은 기간 거래 건수</span>'
        f'<span class="v {D.delta_color(drop)}">{D.delta(drop)}</span></div>'
        f'</div></div>')
    return {"name": "04_counter", "layout": "quote",
            "facts": {"top": s, "drop_pct": round(drop, 1)},
            "html": D.head(4, n) + inner + D.foot(t["asof"])}


def c2_ranked(t: dict, n: int) -> dict:
    """평소 대비 배수 순위.

    지시사항 5항: **1.0(평소)을 기준선으로 굵게 긋고, 기준선을 넘는 부분만**
    의미색으로 칠한다. 막대 전체를 칠하면 1.0 까지의 길이까지 "성과"처럼
    보인다 — 평소만큼 거래된 것도 빨갛게 나오는 셈이다. 초과분만 칠해야
    "평소보다 얼마나 더"가 길이로 읽힌다.
    """
    rows = t["ranked"]
    top = rows[0]
    mx = max(r["ratio"] for r in rows) or 1
    base_pos = 1.0 / mx * 100      # "평소" 위치
    bars = []
    for r in rows:
        w = r["ratio"] / mx * 100
        over = max(0.0, w - base_pos)
        color = D.UP if r is top else D.NEUTRAL
        bars.append(
            f'<div class="rank-row">'
            f'<div class="rank-name">{r["sigungu_name"]}</div>'
            f'<div class="rank-track">'
            f'<div class="rank-fill" style="width:{min(w, base_pos):.1f}%"></div>'
            + (f'<div class="rank-over" style="left:{base_pos:.1f}%;'
               f'width:{over:.1f}%;background:{color}"></div>' if over > 0 else '')
            + f'<div class="rank-base" style="left:{base_pos:.1f}%"></div></div>'
            f'<div class="rank-val">{r["ratio"]:.1f}배</div></div>')
    inner = (
        f'<div class="body">'
        f'<div class="h1 sm">평소보다<br>붐빈 지역</div>'
        f'<div class="rank">{"".join(bars)}</div>'
        f'<div class="rank-baselabel">굵은 세로선이 평소 수준이에요. '
        f'색칠된 부분이 그걸 넘은 만큼이고요.</div>'
        f'<div class="sub">'
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

    의미색은 up/down 둘뿐이다 — 지시사항 3항이 한 장에 두 개까지만 허용한다.
    여기에 형광펜 띠까지 쓰면 셋이 되고, 그러면 빨강/파랑이 "증감"이라는
    신호가 묻힌다.
    """
    b, q = t["busiest"], t["quiet"]
    hi = b["week_deals"] / b["deals_avg_52w"]
    lo = q["week_deals"] / q["deals_avg_52w"]
    inner = (
        f'<div class="body">'
        f'<div class="kicker">같은 주, 정반대</div>'
        f'<div class="h1 sm">한 주에도<br>동네마다 달라요</div>'
        f'<div class="rows">'
        f'<div class="row"><span class="k">{b["sigungu_name"]} '
        f'{b["week_deals"]}건</span>'
        f'<span class="v up">평소의 {hi:.1f}배</span></div>'
        f'<div class="row"><span class="k">{q["sigungu_name"]} '
        f'{q["week_deals"]}건</span>'
        f'<span class="v down">평소의 {lo:.1f}배</span></div>'
        f'</div>'
        f'<div class="sub">수도권을 한 덩어리로 보면 둘 다 안 보여요.</div>'
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
    # 표본은 **항상** 적는다. 얇을 때만 붙이면 "배지가 없으면 안심"이라는
    # 신호가 되는데, 15건으로 뽑은 평균도 흔들린다. 지시사항 9항대로 양쪽
    # 값을 모두 쓴다 — "거래 14건 → 9건".
    warn = " · 몇 건으로 평균이 크게 흔들려요" \
        if min(s["deals_recent"], s["deals_prior"]) < MIN_SAMPLE else ""
    sample = (f'<div><span class="badge">거래 {s["deals_prior"]}건 → '
              f'{s["deals_recent"]}건{warn}</span></div>')

    def bar(label, val, color):
        return (f'<div class="bar-row"><div class="bar-top">'
                f'<span class="bar-name">{label}</span>'
                f'<span class="bar-val">{D.num(val)}만</span></div>'
                f'<div class="bar-track"><div class="bar-fill" '
                f'style="width:{val / mx * 100:.0f}%;background:{color}"></div>'
                f'</div></div>')

    inner = (
        f'<div class="body">'
        f'<div class="kicker">{s["sigungu_name"]} {s["legal_dong_name"]} · {D.pyeong(s["pyeong_bucket"])}</div>'
        f'<div class="h1 sm">{name}</div>{paren_html}'
        f'<div class="sub">평당가, 3개월 전과 비교</div>'
        f'<div class="bars">'
        f'{bar("직전 3개월", prior, D.NEUTRAL)}{bar("최근 3개월", recent, D.UP)}'
        f'</div>{sample}</div>')
    return {"name": "05_compare", "layout": "compare_bars",
            "facts": {"top": s},
            "html": D.head(5, n) + inner + D.foot(t["asof"])}


def c6_newhigh(t: dict, n: int) -> dict | None:
    """이번 주 신고가 — **다른 단지**를 쓴다.

    4·5장이 모두 같은 단지(급등 단지)라, 6장까지 같은 대상이면 한 캐러셀에
    같은 단지가 3장 연속으로 나온다. 지시사항 5항은 한 대상당 최대 2장이다.
    보는 사람 입장에서도 세 장째면 "아직도 이 단지야?"가 된다.

    표본이 얇은 신고가는 쓰지 않는다. 누적 6건짜리 평형에서 "종전 최고가
    148% 경신"이 나오는데, 그건 시세가 아니라 표본이 만든 숫자다
    (지시사항 6항: n<10 은 hero_number 금지).
    """
    h = t.get("new_high")
    if not h:
        return None
    # 긴 단지명은 괄호를 떼어 작은 글씨로 내린다 (9항). 떼지 않으면
    # "청솔마을(주공9단지) 15P가 종전 최고를..."가 헤드라인에서 네 줄을 먹는다.
    name, paren = D.split_name(h["apt_name"])
    tail = (f'<div class="sub">{paren} · {D.pyeong(h["pyeong_bucket"])}</div>'
            if paren else
            f'<div class="sub">{D.pyeong(h["pyeong_bucket"])}</div>')
    inner = (
        f'<div class="body">'
        f'<div class="kicker">이번 주 신고가 · {h["sigungu_name"]}</div>'
        f'<div class="h1 sm">{name}가<br>종전 최고를 넘었어요</div>'
        f'{tail}'
        f'<div class="big sm up">{D.delta(h["over_peak_pct"], arrow=False)}</div>'
        f'<div class="lead">종전 최고 {D.won(h["prev_peak"])} → '
        f'이번 거래 {D.won(h["deal_amount"])}</div>'
        f'<div><span class="badge">이 평형 누적 거래 '
        f'{D.num(h["history_count"])}건</span></div>'
        f'</div>')
    return {"name": "06_newhigh", "layout": "hero_number",
            "facts": {"new_high": h},
            "html": D.head(6, n) + inner + D.foot(t["asof"])}


def c7_outro(t: dict, page: int, n: int) -> dict:
    """정리. 새 숫자를 쓰지 않는다 — 앞에 나온 값만 되짚는다."""
    b, s = t["busiest"], t["top"]
    inner = (
        f'<div class="body">'
        f'<div class="kicker">정리</div>'
        f'<div class="h1 sm">세 줄 요약</div>'
        f'<div class="lead">'
        f'· {b["sigungu_name"]} 거래가 평소보다 많았어요<br>'
        f'· {s["apt_name"]} 평단가는 올랐어요<br>'
        f'· 다만 거래 건수는 줄었어요</div>'
        f'<div class="cta">저장해두고 <span class="mark">다음 주와 비교</span>해보세요.<br>'
        f'여러분 동네는 이번 주 어땠나요?</div>'
        f'<div class="disc">{DISCLAIMER_SOCIAL}</div>'
        f'</div>')
    return {"name": "07_outro", "layout": "summary_cta",
            "facts": {}, "html": D.head(page, n) + inner}


def build_cards(data: dict, chart_dir: Path | None = None) -> list[dict]:
    """chart_dir 은 더 이상 읽지 않는다 — 차트 조각을 카드에 넣지 않는다.
    호출부(테스트 포함)가 넘기고 있어 인자만 남긴다."""
    t = pick(data)
    if t is None:
        return []
    # 신고가 재료가 없으면 6장으로 낸다. 억지로 7장을 채우려고 같은 단지를
    # 세 번 쓰지 않는다 (지시사항 5항: 5~8장, 한 대상 최대 2장).
    n = 7 if t.get("new_high") else 6
    cards = [c1_cover(t, n), c2_ranked(t, n), c3_extremes(t, n),
             c4_counter(t, n), c5_compare(t, n)]
    six = c6_newhigh(t, n)
    if six:
        cards.append(six)
    cards.append(c7_outro(t, len(cards) + 1, n))
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


GEOM_JS = """() => {
  const b = document.querySelector('.card .body');
  const kids = [...b.querySelectorAll(':scope > *')]
      .filter(e => e.getBoundingClientRect().height);
  if (!kids.length) return null;
  const ft = document.querySelector('.card .ft');
  const bot = Math.max(...kids.map(e => e.getBoundingClientRect().bottom));
  const stop = ft ? ft.getBoundingClientRect().top : %d;
  const big = document.querySelector('.card .big');
  return {gap: stop - bot, bigW: big ? big.getBoundingClientRect().width : null};
}"""


def fill_css(f: float) -> str:
    """남는 공간을 **키워서** 채운다 (지시사항 5항).

    세로 중앙 정렬로 때우면 위아래가 똑같이 비어서 "덜 채운 장"이 된다.
    본문 글자는 34~36px 상한이 따로 있으므로(2항) 늘릴 수 있는 건 구조 쪽이다 —
    행 높이, 막대 두께, 장 사이 여백, 그리고 상한이 없는 인용문.
    8px 그리드를 깨지 않도록 8의 배수로 맞춘다.
    """
    def g(base: int, cap: int) -> int:
        return min(cap, round(base * f / 8) * 8)
    return (f".body{{gap:{g(32, 72)}px}}"
            f".row{{padding:{g(24, 56)}px 0}}"
            f".rank{{gap:{g(16, 40)}px}}"
            f".rank-track{{height:{g(24, 48)}px}}"
            f".bars{{gap:{g(32, 64)}px}}"
            f".bar-track{{height:{g(32, 56)}px}}"
            f".quote{{font-size:{g(64, 88)}px}}")


def render(cards: list[dict], outdir: Path) -> tuple[list[Path], list[str]]:
    """넘치면 줄이고, 비면 키운다.

    두 방향을 다 본다. 넘침만 보면 안전영역은 지키지만 아래가 300px 넘게
    비는 장이 나오고, 그건 지시사항 5항이 실패로 규정한 상태다.
    """
    from playwright.sync_api import sync_playwright

    made, problems = [], []
    js = OVERFLOW_JS % (D.PAD_X, D.W, D.H)
    gjs = GEOM_JS % (D.H - D.PAD_BOTTOM + 48)

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for c in cards:
            page = br.new_page(viewport={"width": D.W, "height": D.H},
                               device_scale_factor=1)

            def draw(shrink: int, fill: float):
                extra = fill_css(fill)
                if shrink:
                    extra += (f".h1{{font-size:{max(HEADLINE_MIN, 104 - shrink)}px}}"
                              f".big{{font-size:{max(140, 280 - shrink * 3)}px}}"
                              f".quote{{font-size:{max(48, 64 - shrink)}px}}")
                page.set_content(
                    f"<style>{D.base_css()}{extra}</style>"
                    f'<div class="card">{c["html"]}</div>', wait_until="load")
                page.wait_for_timeout(120)
                return page.evaluate(js), page.evaluate(gjs)

            # ① 빈 공간을 채운다 — 넘치기 직전까지만 키운다
            fill, best = 1.0, 1.0
            while fill <= FILL_MAX:
                over, geo = draw(0, fill)
                if over:
                    break
                best = fill
                if geo and geo["gap"] <= D.MAX_BOTTOM_GAP:
                    break
                fill += FILL_STEP
            fill = best

            # ② 그래도 넘치면 폰트를 줄인다 (9항: 헤드라인 하한 72px)
            shrink = 0
            while True:
                over, geo = draw(shrink, fill)
                if not over or shrink >= 24:
                    break
                shrink += 4

            if over:
                problems.append(f"{c['name']}: 안전영역 넘침 {over[:2]}")
            if geo and geo["gap"] > D.MAX_BOTTOM_GAP:
                problems.append(
                    f"{c['name']}: 하단 빈 공간 {geo['gap']:.0f}px "
                    f"(한도 {D.MAX_BOTTOM_GAP})")
            # 표지 대형 숫자는 가로 폭의 70% 이상이어야 한다 (5항)
            if c["name"].endswith("cover") and geo and geo["bigW"]:
                r = geo["bigW"] / D.W
                if r < D.COVER_NUM_RATIO:
                    problems.append(
                        f"{c['name']}: 대형 숫자가 폭의 {r:.0%} "
                        f"(최소 {D.COVER_NUM_RATIO:.0%})")

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
