"""단지 소개 캐러셀 — 한 단지를 여섯 장으로.

    1 표지        그 단지가 신고가를 썼다 (도식 지도 + 이번 거래가)
    2 실거래 추이  월별 기록 위에 이번 거래를 붉은 점으로
    3 주변 비교    같은 동·같은 평형대 다른 단지들
    4 같이 볼 것   데이터로 확인되는 신호 3가지
    5 그 구는      단지보다 넓은 단위의 흐름
    6 팔로우

**4장은 "원인 분석"이 아니다.** 왜 올랐는지는 거래 데이터로 확인할 수 없다.
호갱노노·리치고를 긁어 오는 것도 하지 않는다 — 공개 API 가 없고, 그들의 분석을
재발행하는 건 이용약관·저작권 양쪽에 걸린다. 뉴스 해석을 옮기면 "공공데이터로
자동 생성한 자료"라고 밝혀온 것과도 어긋난다.

대신 **우리 데이터로 확인되는 것**만 적는다. 같은 단지 다른 평형도 올랐는지,
동네 다른 단지는 어떤지, 거래가 늘었는지. 그게 원인을 짚어 주지는 않지만
읽는 사람이 스스로 판단할 재료는 된다. 장 제목에도 "원인"이라고 쓰지 않는다.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from content import geo  # noqa: E402
from content import neighbor_map as NM  # noqa: E402

# 동네 데이터는 대체로 정사각이라 상자도 정사각에 가깝게 둔다.
MAP_W, MAP_H = 600, 392
TREND_W, TREND_H = 936, 420
MIN_SAMPLE = 10


def pf(prof: dict) -> dict:
    """검증기에 넘길 프로필. 좌표는 발행되는 숫자가 아니라 뺀다."""
    return {k: v for k, v in prof.items() if k not in ("lat", "lng")}


def short(name: str, limit: int = 10) -> str:
    return D.split_name(name, limit)[0]


# ── 1 표지 ───────────────────────────────────────────────────────────────
def cover(t: dict, prof: dict, n: int) -> dict:
    """그 단지가 어디 있고, 이번에 얼마에 팔렸나."""
    d = t["cover"].data
    name, paren = D.split_name(prof["apt_name"], 11)
    built = f'{prof["build_year"]}년 준공' if prof.get("build_year") else ""
    cond = D.cond(f'{prof["sigungu_name"]} {prof["legal_dong_name"]}', built,
                  D.pyeong(prof["pyeong_bucket"]))
    # 동네 지도가 먼저. 시군구 경계 지도는 "어디쯤"만 알려주는데, 단지를
    # 소개하는 글에서 궁금한 건 "주변에 뭐가 있나"다.
    svg = NM.render(prof, width=MAP_W, height=MAP_H, dark=True,
                    neighbors=prof.get("neighbors"))
    if not svg:
        svg = geo.svg({prof["sigungu_name"]: D.UP}, width=MAP_W, height=MAP_H,
                      line=D.LINE, fill=geo.mix(D.INK, "#FFFFFF", 0.18),
                      label_color=D.COVER_INK, label_halo=D.INK,
                      scope=geo.scope_of(prof.get("sigungu_code")),
                      pins=[{"lat": prof.get("lat"), "lng": prof.get("lng"),
                             "primary": True}])
    # 지도에 쓴 자료의 출처를 전부 밝힌다 (경계·도로).
    a = prof.get("around") or {}
    credit = " · ".join(x for x in (
        geo.CREDIT if svg and "mc-map" else None,
        a.get("road_credit") if a.get("roads") else None) if x)
    inner = (
        f'<div class="body">'
        f'{cond}'
        f'<div class="mc-h1">{name}{paren},<br>'
        f'<span style="color:{D.COVER_KEY}">종전 최고가를 썼어요</span></div>'
        f'<div class="mc-num" style="color:{D.COVER_INK}">'
        f'{D.won(d["deal_amount"])}</div>'
        f'<div class="mc-map">{svg}</div>'
        f'<div class="mc-foot">종전 최고 {D.won(d["prev_peak"])} → '
        f'이번 거래 {D.won(d["deal_amount"])} · {d["floor_band"]} · '
        f'최근 1년 이 단지 거래 {prof["deals_1y"]}건</div>'
        f'</div>')
    return {"name": "01_cover", "layout": "apt_cover", "dark": True,
            "scope": "apt", "facts": {"cover": d, "profile": pf(prof)},
            "html": D.head(1, n) + inner + D.foot(t["asof"], credit)}


# ── 2 실거래 추이 ────────────────────────────────────────────────────────
def trend(t: dict, prof: dict, n: int) -> dict:
    """월별 실거래 위에 **이번 거래**를 붉은 점으로.

    거래가 드문 단지를 선으로 이으면 없는 추세가 보인다. 점으로만 찍는다
    (지시사항 7항).
    """
    d = t["cover"].data
    pts = [p for p in prof["series"] if p.get("avg_price")]
    xs = [datetime.strptime(p["ym"], "%Y-%m") for p in pts]
    ys = [float(p["avg_price"]) for p in pts]
    t0, t1 = xs[0].timestamp(), xs[-1].timestamp()
    span = (t1 - t0) or 1
    lo, hi = min(ys), max(ys)
    pad = (hi - lo) * 0.18 or 1
    lo, hi = lo - pad, hi + pad
    pl, pr, ptop, pbot = 150, 36, 24, 60
    iw, ih = TREND_W - pl - pr, TREND_H - ptop - pbot

    def X(dt):
        return pl + (dt.timestamp() - t0) / span * iw

    def Y(v):
        return ptop + (1 - (v - lo) / (hi - lo)) * ih

    grid = "".join(
        f'<line x1="{pl}" x2="{TREND_W - pr}" y1="{Y(v):.1f}" '
        f'y2="{Y(v):.1f}" stroke="{D.LINE}" stroke-width="1"/>'
        f'<text x="{pl - 16}" y="{Y(v) + 10:.1f}" text-anchor="end" '
        f'font-size="26" fill="{D.SUB}">{D.won(v)}</text>'
        for v in (lo + (hi - lo) * (k + .5) / 3 for k in range(3)))

    years = [y for y in range(xs[0].year, xs[-1].year + 1)
             if xs[0] <= datetime(y, 1, 1) <= xs[-1]]
    step = max(1, len(years) // 6)
    ticks = "".join(
        f'<text x="{X(datetime(y, 1, 1)):.1f}" y="{TREND_H - 20}" '
        f'text-anchor="middle" font-size="26" fill="{D.SUB}">{y}</text>'
        for i, y in enumerate(years) if i % step == 0)

    dots = "".join(
        f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="7" fill="{D.NEUTRAL}" '
        f'stroke="{D.BG}" stroke-width="2"/>' for x, y in zip(xs[:-1], ys[:-1]))

    # 이번 거래 — 크고 붉게. 이 장의 주인공이다.
    lx, ly = X(xs[-1]), Y(ys[-1])
    mark = (f'<line x1="{lx:.1f}" x2="{lx:.1f}" y1="{ptop}" '
            f'y2="{TREND_H - pbot}" stroke="{D.UP}" stroke-width="2" '
            f'stroke-dasharray="5 5" opacity=".45"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="18" fill="{D.UP}" '
            f'opacity=".22"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="10" fill="{D.UP}" '
            f'stroke="#FFFFFF" stroke-width="3"/>')

    svg = (f'<svg width="{TREND_W}" height="{TREND_H}" '
           f'viewBox="0 0 {TREND_W} {TREND_H}" style="font-family:Pretendard">'
           f'{grid}{ticks}{dots}{mark}</svg>')
    cond = D.cond(f'{pts[0]["ym"]} ~ {pts[-1]["ym"]}', f'거래 {len(pts)}개월')
    inner = (
        f'<div class="body">'
        f'<div class="kicker">{short(prof["apt_name"], 14)} '
        f'{D.pyeong(prof["pyeong_bucket"])}</div>'
        f'{cond}'
        f'<div class="h1 sm">이번 거래는<br>여기예요</div>'
        f'<div>{svg}</div>'
        f'<div class="sub">붉은 점이 이번 거래 {D.won(d["deal_amount"])}, '
        f'회색 점은 지난 거래예요. 점은 그 달 평균이고요.</div>'
        f'</div>')
    return {"name": "02_trend", "layout": "apt_trend", "scope": "apt",
            # 파생값도 발행되는 숫자다. 출처를 대지 않으면 검증기가 막는다.
            "facts": {"cover": d, "profile": pf(prof), "months": len(pts)},
            "html": D.head(2, n) + inner + D.foot(t["asof"])}


# ── 3 주변 비교 ──────────────────────────────────────────────────────────
def nearby(t: dict, prof: dict, n: int) -> dict:
    """같은 동·같은 평형대의 다른 단지와 나란히.

    한 단지만 보면 "많이 올랐다"가 어느 정도인지 알 수 없다. 옆 단지가
    얼마에 팔렸는지가 있어야 눈금이 생긴다.
    """
    d = t["cover"].data
    me_row = {"apt_name": prof["apt_name"], "last_price": d["deal_amount"],
              "deals_1y": prof["deals_1y"], "me": True}
    # **자기 자신은 무조건 남긴다.** 가격순으로 자르다가 주인공이 잘려서
    # "빨간 막대가 ○○" 라고 써 놓고 빨간 막대가 없는 장이 나왔다.
    nb = sorted(prof["neighbors"], key=lambda r: r["last_price"], reverse=True)
    rows = [me_row] + [dict(r, me=False) for r in nb[:3]]
    rows.sort(key=lambda r: r["last_price"], reverse=True)
    mx = max(r["last_price"] for r in rows) or 1

    def one(r: dict) -> str:
        tag = "" if r["me"] else f'<span class="badge">1년 {r["deals_1y"]}건</span>'
        color = D.UP if r["me"] else D.NEUTRAL
        w = r["last_price"] / mx * 100
        return (f'<div class="bar-row"><div class="bar-top">'
                f'<span class="bar-name">{short(r["apt_name"])}{tag}</span>'
                f'<span class="bar-val">{D.won(r["last_price"])}</span></div>'
                f'<div class="bar-track"><div class="bar-fill" '
                f'style="width:{w:.0f}%;background:{color}"></div>'
                f'</div></div>')

    me = short(prof["apt_name"])
    inner = (
        f'<div class="body">'
        f'<div class="kicker">{prof["legal_dong_name"]} '
        f'{D.pyeong(prof["pyeong_bucket"])}</div>'
        f'{D.cond("같은 동 · 같은 평형대", "최근 1년 거래가 있는 단지")}'
        f'<div class="h1 sm">옆 단지는<br>얼마에 팔렸을까요?</div>'
        f'<div class="bars">{"".join(one(r) for r in rows)}</div>'
        f'<div class="sub">빨간 막대가 {me}, 나머지는 같은 동 다른 단지의 '
        f'마지막 거래예요.</div>'
        f'</div>')
    return {"name": "03_nearby", "layout": "compare_bars", "scope": "dong",
            "facts": {"cover": d, "profile": pf(prof)},
            "html": D.head(3, n) + inner + D.foot(t["asof"])}


# ── 4 같이 볼 것 ─────────────────────────────────────────────────────────
def signals(t: dict, prof: dict, n: int) -> dict:
    """**원인이 아니라 신호.**

    "왜 올랐나"는 거래 데이터로 답할 수 없다. 답할 수 있는 건 "이 거래가
    혼자 튄 것인지, 같이 움직인 것인지"다. 그 둘은 전혀 다른 질문이고,
    후자는 우리 데이터로 확인된다.
    """
    d = t["cover"].data
    out: list[tuple[str, str, str]] = []

    # ① 같은 단지의 다른 평형도 움직였나
    others = prof.get("other_pyeongs") or []
    if others:
        top = max(others, key=lambda r: r["deals_1y"])
        out.append((
            "같은 단지, 다른 평형",
            f'{D.pyeong(top["pyeong_bucket"])}는 {D.won(top["last_price"])}에 '
            f'거래됐어요 (최근 1년 {top["deals_1y"]}건)',
            "한 평형만 움직였는지, 단지 전체가 움직였는지를 가릅니다"))
    else:
        out.append((
            "같은 단지, 다른 평형",
            "최근 1년 다른 평형 거래가 없었어요",
            "이 평형 하나로만 판단해야 한다는 뜻이에요"))

    # ② 동네 다른 단지와 견주면
    nb = prof.get("neighbors") or []
    if nb:
        hi = max(nb, key=lambda r: r["last_price"])
        above = d["deal_amount"] >= hi["last_price"]
        out.append((
            "같은 동 다른 단지",
            f'가장 비싼 거래는 {short(hi["apt_name"])} '
            f'{D.won(hi["last_price"])}였어요',
            ("이번 거래가 동네에서 가장 높은 값이에요" if above
             else "이번 거래가 동네 최고가는 아니에요")))

    # ③ 거래가 늘었나 — 그 자체가 "관심"의 지표다
    pts = prof.get("series") or []
    recent = sum(p["deals"] for p in pts[-12:]) if pts else 0
    prior = sum(p["deals"] for p in pts[-24:-12]) if len(pts) > 12 else 0
    if prior:
        word = "늘었어요" if recent > prior else ("줄었어요" if recent < prior
                                              else "비슷했어요")
        out.append((
            "이 평형 거래 건수",
            f'직전 1년 {prior}건 → 최근 1년 {recent}건, {word}',
            "값이 오를 때 거래도 같이 늘었는지 봅니다"))
    else:
        out.append((
            "이 평형 거래 건수",
            f'최근 1년 {recent}건이에요',
            "비교할 직전 1년 기록이 없어요"))

    items = "".join(
        f'<div class="sig"><div class="sig-k">{k}</div>'
        f'<div class="sig-v">{v}</div><div class="sig-w">{w}</div></div>'
        for k, v, w in out[:3])
    inner = (
        f'<div class="body">'
        f'<div class="kicker">숫자를 믿기 전에</div>'
        f'{D.cond("왜 올랐는지는 거래 기록으로 알 수 없어요")}'
        f'<div class="h1 sm">같이 볼 만한 것<br>세 가지</div>'
        f'<div class="sigs">{items}</div>'
        f'</div>')
    return {"name": "04_signals", "layout": "signals", "scope": "dong",
            "facts": {"cover": d, "profile": pf(prof),
                      "deals_recent_1y": recent, "deals_prior_1y": prior},
            "html": D.head(4, n) + inner + D.foot(t["asof"])}


# ── 5 그 구는 ────────────────────────────────────────────────────────────
def region(t: dict, prof: dict, n: int) -> dict | None:
    """단지보다 넓은 단위 — 그 구의 최근 흐름.

    단지 한 곳을 다섯 장 보고 나면 "이 동네가 다 그런가"로 읽히기 쉽다.
    마지막에 한 번 넓혀서, 단지의 일과 구의 일을 갈라 둔다.
    """
    r = t.get("cover_region")
    if not r or not r.get("deals_avg_52w"):
        return None
    rd = r["week_deals"] / r["deals_avg_52w"]
    rp = (r["week_ppy"] / r["ppy_avg_52w"]) if r.get("ppy_avg_52w") else None
    word = ("평소보다 붐볐어요" if rd >= 1.1 else
            "평소보다 조용했어요" if rd <= 0.9 else "평소와 비슷했어요")
    rows = (
        f'<div class="row"><span class="k">주간 거래<small>평소 '
        f'{D.num(r["deals_avg_52w"])}건</small></span>'
        f'<span class="v {D.delta_color(rd - 1)}">{r["week_deals"]}건</span></div>')
    if rp:
        rows += (
            f'<div class="row"><span class="k">중위 평단가<small>평소 '
            f'{D.num(r["ppy_avg_52w"])}만</small></span>'
            f'<span class="v {D.delta_color(rp - 1)}">'
            f'{D.num(r["week_ppy"])}만</span></div>')
    cond = D.cond(f'{r["sigungu_name"]} · {r.get("week_start", "")} 주',
                  "평소 = 지난 52주 평균")
    inner = (
        f'<div class="body">'
        f'<div class="kicker">단지 말고, 구 전체는</div>'
        f'{cond}'
        f'<div class="h1 sm">{r["sigungu_name"]}는<br>{word}</div>'
        f'<div class="rows">{rows}</div>'
        f'<div class="sub">단지 한 곳이 신고가를 썼다고 그 구 전체가 같이 '
        f'움직이는 건 아니에요.</div>'
        f'</div>')
    return {"name": "05_region", "layout": "rows", "scope": "region",
            "facts": {"region": r, "ratio": round(rd, 2)},
            "html": D.head(5, n) + inner
                    + D.foot(t["asof"], "평소 = 지난 52주 평균")}
