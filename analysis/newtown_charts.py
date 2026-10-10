"""신도시 1편 차트 — 롱폼 영상에 올릴 그림.

16:9 (1920x1080) 로 뽑는다. 릴스(9:16)와 달리 유튜브 롱폼이라 가로다.

여기 그리는 것은 **대본의 주장을 떠받치는 근거**다. 그래서 숫자를 고르는
기준을 그림 안에 적는다 — "같은 단지만 추적", "30평대", "표본 n곳" 처럼.
보는 사람이 "저 숫자 어디서 났지"를 묻지 않게 해야 한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis.newtown import TOWNS, con, town_where  # noqa: E402
from content import design as D  # noqa: E402
from metrics.filters import trades_cte  # noqa: E402

TRADE = (ROOT / "master" / "trade_events.parquet").as_posix()
from content import frame as FR  # noqa: E402
# 테두리 안쪽 판에 꼭 맞게 그린다. 1920 으로 그려 줄이면
# 글자가 한 번 더 뭉개진다.
W, H = FR.CONTENT_W, FR.CONTENT_H
OUT = ROOT / "output" / "longform" / "newtown1"

WIN = "#2F6FED"    # 성공조
LOSE = "#E5484D"   # 부진조
GREY = "#9AA0A6"
GOLD = "#E8A33D"

WINNERS = ("광교", "동탄1", "동탄2")


def css() -> str:
    return f"""
{D.base_css()}
.pg{{width:{W}px;height:{H}px;background:{D.BG};position:relative;
    /* 종이 결. 참고한 포맷은 인쇄물을 책상에 놓고 찍는데, 우리는 실사
       촬영 대신 결만 깐다. 2% 농도라 보이진 않고 느껴지기만 한다. */
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='3'/><feColorMatrix type='saturate' values='0'/></filter><rect width='220' height='220' filter='url(%23n)' opacity='0.055'/></svg>");
    padding:42px 64px;box-sizing:border-box;
    border-radius:{FR.RADIUS}px;overflow:hidden;
    font-family:Pretendard,system-ui,sans-serif;color:{D.INK};}}
.kick{{font-size:27px;font-weight:600;color:{D.SUB};letter-spacing:-.01em;}}
.ttl{{font-size:47px;font-weight:800;letter-spacing:-.03em;margin-top:8px;
     line-height:1.14;}}
.ttl em{{font-style:normal;color:{LOSE};}}
.ttl b{{color:{WIN};}}
/* 아래에 두면 자막 띠에 가린다. 띠 높이는 줄 수에 따라 변해서 여백을
   얼마로 잡든 언젠가 또 겹친다. 그래서 제목 밑으로 올렸다 — 방법론
   단서는 차트를 보기 전에 읽는 편이 낫기도 하다. */
.note{{margin-top:10px;font-size:21px;color:{D.SUB};line-height:1.45;
      max-width:1180px;}}
.wrap{{margin-top:20px;}}
table{{width:100%;border-collapse:collapse;font-size:30px;}}
th{{font-size:23px;color:{D.SUB};font-weight:600;text-align:right;
   padding:0 0 10px;}}
th:first-child{{text-align:left;}}
td{{padding:7px 0;border-top:1px solid {D.LINE};text-align:right;
   font-weight:700;font-variant-numeric:tabular-nums;}}
td:first-child{{text-align:left;font-weight:600;}}
tr.win td{{color:{WIN};}}
tr.lose td{{color:{LOSE};}}
tr.base td{{color:{D.SUB};}}
tr.base td:first-child{{color:{D.SUB};}}
.bars{{display:flex;flex-direction:column;gap:8px;margin-top:2px;}}
.bar .t{{display:flex;justify-content:space-between;align-items:baseline;
        font-size:26px;font-weight:700;}}
.bar .t small{{font-size:21px;font-weight:500;color:{D.SUB};}}
.bar .track{{height:19px;border-radius:999px;background:#E9E6DE;
            margin-top:6px;position:relative;overflow:hidden;}}
.bar .fill{{height:100%;border-radius:999px;position:absolute;top:0;}}
.lg{{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:19px;
    color:{D.SUB};margin-top:4px;}}
.lg i{{width:26px;height:26px;border-radius:7px;display:inline-block;
      margin-right:9px;vertical-align:-4px;}}
.two{{display:flex;gap:56px;}}
.two>div{{flex:1;}}
.badge{{position:absolute;right:64px;top:42px;
       background:{D.INK};color:#FFFFFF;font-size:22px;font-weight:800;
       letter-spacing:.04em;padding:8px 18px;border-radius:8px;}}
/* 본문 아래 빈 자리에 둔다. 위쪽에 두면 막대를 덮는다. */
.callout{{position:absolute;right:72px;bottom:208px;
         background:{D.INK};color:#FFFFFF;border-radius:12px;
         padding:16px 26px;text-align:right;
         box-shadow:0 12px 30px rgba(0,0,0,.28);
         font-size:62px;font-weight:800;letter-spacing:-.03em;
         line-height:1;}}
.callout small{{display:block;font-size:21px;font-weight:600;
               color:rgba(255,255,255,.72);margin-top:9px;
               letter-spacing:0;}}
.cap{{font-size:25px;font-weight:700;color:{D.SUB};margin-bottom:14px;}}
.big{{font-size:104px;font-weight:800;letter-spacing:-.04em;line-height:1;}}
.big.w{{color:{WIN};}} .big.l{{color:{LOSE};}}
"""


def page(kick: str, ttl: str, body: str, note: str) -> str:
    return (f'<div class="pg"><div class="kick">{kick}</div>'
            f'<div class="ttl">{ttl}</div>'
            f'<div class="note">{note}</div>'
            f'<div class="wrap">{body}</div></div>')


def deco(html: str, *, badge: str = "", callout: str = "",
         sub: str = "") -> str:
    """번호 배지와 핵심 수치 박스를 얹는다.

    page() 에 인자로 넣지 않고 밖에서 덧붙이는 이유: 호출부마다 note 가
    위치 인자라, 키워드를 끼워 넣으면 순서가 깨진다. 밖에서 감싸면 어느
    호출에도 똑같이 붙일 수 있다.

    수치 박스를 따로 두는 까닭은 참고한 포맷과 같다 — 막대가 여덟 줄이면
    어디를 보라는 건지 모른다. 한 숫자만 띄워 두면 눈이 거기서 멈춘다.
    """
    add = ""
    if badge:
        add += f'<div class="badge">{badge}</div>'
    if callout:
        s2 = f'<small>{sub}</small>' if sub else ""
        add += f'<div class="callout">{callout}{s2}</div>'
    return html.replace('<div class="pg">', f'<div class="pg">{add}', 1)


def bars(rows, *, mx=None, zero=False) -> str:
    """rows: (라벨, 값, 색, 표시문자열). zero=True 면 0 을 가운데 둔다."""
    vals = [v for _, v, _, _ in rows]
    lim = mx or max(abs(v) for v in vals) or 1
    out = []
    for lab, v, c, txt in rows:
        if zero:
            w = abs(v) / lim * 50
            left = 50 if v >= 0 else 50 - w
            style = f"left:{left:.1f}%;width:{w:.1f}%;background:{c}"
        else:
            style = f"left:0;width:{max(1.5, v / lim * 100):.1f}%;background:{c}"
        out.append(f'<div class="bar"><div class="t"><span>{lab}</span>'
                   f'<span>{txt}</span></div>'
                   f'<div class="track"><div class="fill" style="{style}">'
                   f'</div></div></div>')
    return f'<div class="bars">{"".join(out)}</div>'


# ── 데이터 ───────────────────────────────────────────────────────────────
def same_apt(c, where: str, a: int, b: int) -> tuple[int, float] | None:
    r = c.execute(f"""
        {trades_cte(TRADE)},
        g AS (SELECT apt_id,
                median(CASE WHEN year(deal_date)={a}
                       THEN price_per_pyeong END) AS p0,
                median(CASE WHEN year(deal_date)={b}
                       THEN price_per_pyeong END) AS p1
              FROM trades WHERE pyeong_bucket='30P' AND price_per_pyeong>0
                AND ({where}) GROUP BY 1)
        SELECT count(*), median(p1/p0)*100-100 FROM g WHERE p0>0 AND p1>0
    """).fetchone()
    return (int(r[0]), float(r[1])) if r and r[0] else None


def naive(c, where: str, a: int, b: int) -> float | None:
    r = c.execute(f"""
        {trades_cte(TRADE)}
        SELECT median(CASE WHEN year(deal_date)={a} THEN price_per_pyeong END),
               median(CASE WHEN year(deal_date)={b} THEN price_per_pyeong END)
        FROM trades WHERE pyeong_bucket='30P' AND price_per_pyeong>0
          AND ({where})
    """).fetchone()
    return (r[1] / r[0] - 1) * 100 if r and r[0] and r[1] else None


def level(c, where: str, year: int = 2026) -> tuple[int, int] | None:
    r = c.execute(f"""
        {trades_cte(TRADE)}
        SELECT count(*), round(median(price_per_pyeong))
        FROM trades WHERE pyeong_bucket='30P' AND price_per_pyeong>0
          AND year(deal_date)>={year} AND ({where})
    """).fetchone()
    return (int(r[0]), int(r[1])) if r and r[1] else None


def series(c, where: str) -> list[tuple[int, int]]:
    rows = c.execute(f"""
        {trades_cte(TRADE)}
        SELECT year(deal_date) AS y, round(median(deal_amount))
        FROM trades WHERE pyeong_bucket='30P' AND ({where})
        GROUP BY 1 HAVING count(*)>=8 ORDER BY 1
    """).fetchall()
    return [(int(y), int(v)) for y, v in rows if v]


def line_svg(sets: list[tuple[str, list[tuple[int, int]], str]],
             *, width=1500, height=500) -> str:
    """연도별 꺾은선. 억 단위."""
    pl, pr, pt, pb = 130, 330, 30, 70
    xs = sorted({y for _, s, _ in sets for y, _ in s})
    ys = [v for _, s, _ in sets for _, v in s]
    if not xs or not ys:
        return ""
    x0, x1 = min(xs), max(xs)
    lo, hi = 0, max(ys) * 1.12
    iw, ih = width - pl - pr, height - pt - pb
    X = lambda y: pl + (y - x0) / max(1, x1 - x0) * iw        # noqa: E731
    Y = lambda v: pt + (1 - (v - lo) / (hi - lo)) * ih        # noqa: E731

    parts = []
    for gv in range(0, int(hi), 50000):
        parts.append(f'<line x1="{pl}" y1="{Y(gv):.0f}" x2="{pl + iw}" '
                     f'y2="{Y(gv):.0f}" stroke="{D.LINE}" stroke-width="1.5"/>')
        parts.append(f'<text x="{pl - 18}" y="{Y(gv) + 10:.0f}" '
                     f'text-anchor="end" font-size="26" fill="{D.SUB}">'
                     f'{gv // 10000}억</text>')
    for y in xs:
        if y % 3 == 0 or y == x1:
            parts.append(f'<text x="{X(y):.0f}" y="{pt + ih + 46}" '
                         f'text-anchor="middle" font-size="26" '
                         f'fill="{D.SUB}">{y}</text>')
    # 라벨이 겹치면 읽히지 않는다. 끝값이 가까운 선들을 아래로 밀어 둔다.
    ends = sorted(((s[-1][1], name, s, color) for name, s, color in sets
                   if s), key=lambda r: -r[0])
    used: list[float] = []
    for lv, name, s, color in ends:
        d = " ".join(f'{"M" if i == 0 else "L"}{X(y):.1f},{Y(v):.1f}'
                     for i, (y, v) in enumerate(s))
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" '
                     f'stroke-width="5" stroke-linejoin="round"/>')
        ly = s[-1][0]
        cy = Y(lv)
        ty = cy + 10
        while any(abs(ty - u) < 40 for u in used):
            ty += 40
        used.append(ty)
        parts.append(f'<circle cx="{X(ly):.1f}" cy="{cy:.1f}" r="9" '
                     f'fill="{color}"/>')
        if abs(ty - (cy + 10)) > 2:
            parts.append(f'<line x1="{X(ly) + 11:.0f}" y1="{cy:.0f}" '
                         f'x2="{X(ly) + 22:.0f}" y2="{ty - 10:.0f}" '
                         f'stroke="{color}" stroke-width="2"/>')
        parts.append(f'<text x="{X(ly) + 26:.0f}" y="{ty:.0f}" '
                     f'font-size="27" font-weight="700" fill="{color}">'
                     f'{name} {lv / 10000:.1f}억</text>')
    return (f'<svg width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>')


# ── 각 장 ────────────────────────────────────────────────────────────────
def chart_level(c) -> tuple[str, str]:
    """① 지금 얼마나 벌어져 있나 — 평당가 수준."""
    rows = []
    base = level(c, "1=1")
    for t in TOWNS:
        lv = level(c, town_where(t))
        if lv:
            rows.append((t, lv[1], WIN if t in WINNERS else LOSE,
                         f"{lv[1]:,}만원"))
    rows.sort(key=lambda r: -r[1])
    rows.append(("수도권 전체", base[1], GREY, f"{base[1]:,}만원"))
    body = bars(rows) + (
        f'<div class="lg"><span><i style="background:{WIN}"></i>'
        f'광교·동탄</span><span><i style="background:{LOSE}"></i>'
        f'검단·김포·운정·옥정</span>'
        f'<span><i style="background:{GREY}"></i>수도권 전체</span></div>')
    return "01_level", deco(page(
        "2026년 · 30평대 중위 평당가",
        '지금은 <b>세 배</b> 가까이 벌어져 있습니다',
        body,
        "국토교통부 실거래가 · 2026년 거래 · 해제 건 제외 · "
        "신도시는 법정동 기준"), badge="그래프 ①")


def chart_naive(c) -> tuple[str, str]:
    """② 흔한 착시 — 연도별 중위값으로 보면 정반대."""
    rows = []
    for t in TOWNS:
        v = naive(c, town_where(t), 2015, 2026)
        if v is not None:
            rows.append((t, v, WIN if t in WINNERS else LOSE, f"+{v:.0f}%"))
    rows.sort(key=lambda r: -r[1])
    bv = naive(c, "1=1", 2015, 2026)
    rows.append(("수도권 전체", bv, GREY, f"+{bv:.0f}%"))
    return "02_naive", deco(page(
        "2015 → 2026 · 동네별 중위 평당가 상승률",
        '이대로 보면 <em>옥정·검단이 광교보다 위</em>입니다',
        bars(rows),
        "그런데 이 그림은 틀렸습니다. 2026년에 거래된 집이 2015년과 "
        "같은 집이 아니기 때문입니다."), badge="그래프 ②")


def chart_mix(c) -> tuple[str, str]:
    """③ 왜 틀렸나 — 신축이 섞였다."""
    rows = []
    for t in ("인천 검단", "양주 옥정", "파주 운정", "동탄2", "광교"):
        r = c.execute(f"""
            {trades_cte(TRADE)}
            SELECT count(*) AS n,
              sum(CASE WHEN build_year>=2020 THEN 1 ELSE 0 END) AS new_,
              round(median(CASE WHEN build_year>=2020
                           THEN price_per_pyeong END)) AS pn,
              round(median(CASE WHEN build_year<2020
                           THEN price_per_pyeong END)) AS po
            FROM trades WHERE year(deal_date)=2026 AND pyeong_bucket='30P'
              AND price_per_pyeong>0 AND ({town_where(t)})
        """).fetchone()
        if not r or not r[0]:
            continue
        share = r[1] / r[0] * 100
        extra = (f'<small>신축 {r[2]:,} · 기존 {r[3]:,}만원</small>'
                 if r[2] and r[3] else "")
        rows.append((f"{t} {extra}", share,
                     GOLD if share >= 30 else GREY, f"{share:.0f}%"))
    return "03_mix", deco(page(
        "2026년 거래 중 '2020년 이후 지은 집'의 비율",
        '검단은 <em>절반 이상이 새 집</em>이었습니다',
        bars(rows, mx=100),
        "새 아파트가 대거 입주하면 동네 중위값이 올라갑니다. "
        "기존 집값이 오른 게 아닙니다."), badge="그래프 ③", callout="58%", sub="인천 검단 · 2020년 이후 준공")


def chart_same(c) -> tuple[str, str]:
    """④ 같은 단지만 추적 — 진짜 답."""
    rows = []
    for t in TOWNS:
        r = same_apt(c, town_where(t), 2019, 2026)
        if r and r[0] >= 4:
            rows.append((f"{t} <small>{r[0]}곳</small>", r[1],
                         WIN if t in WINNERS else LOSE, f"+{r[1]:.0f}%"))
    rows.sort(key=lambda r: -r[1])
    b = same_apt(c, "1=1", 2019, 2026)
    rows.append((f"수도권 전체 <small>{b[0]:,}곳</small>", b[1], GREY,
                 f"+{b[1]:.0f}%"))
    return "04_same", deco(page(
        "2019 → 2026 · 두 해 모두 거래된 '같은 단지'만",
        '다시 재면 <b>순서가 뒤집힙니다</b>',
        bars(rows),
        "같은 단지의 30평대 상승률 중앙값. 새로 지은 집이 섞이는 문제를 "
        "없앴습니다."), badge="그래프 ④")


def chart_split(c) -> tuple[str, str]:
    """⑤ 언제 갈렸나 — 상승기 vs 조정기."""
    cells = []
    hdr = ('<tr><th>동네</th><th>상승기 2015→2021</th>'
           '<th>조정기 2021→2026</th></tr>')
    order = list(WINNERS) + [t for t in TOWNS if t not in WINNERS]
    for t in order:
        up = same_apt(c, town_where(t), 2015, 2021)
        dn = same_apt(c, town_where(t), 2021, 2026)
        if not (up and dn):
            continue
        cls = "win" if t in WINNERS else "lose"
        thin = " <small>표본 적음</small>" if min(up[0], dn[0]) < 5 else ""
        cells.append(f'<tr class="{cls}"><td>{t}{thin}</td>'
                     f'<td>+{up[1]:.0f}%</td><td>{dn[1]:+.0f}%</td></tr>')
    bu = same_apt(c, "1=1", 2015, 2021)
    bd = same_apt(c, "1=1", 2021, 2026)
    cells.append(f'<tr class="base"><td>수도권 전체</td>'
                 f'<td>+{bu[1]:.0f}%</td><td>{bd[1]:+.0f}%</td></tr>')
    return "05_split", deco(page(
        "같은 단지 기준 · 30평대",
        '상승기엔 <b>덜 올랐고</b>, 조정기엔 <em>더 빠졌습니다</em>',
        f'<table>{hdr}{"".join(cells)}</table>',
        "두 번 벌어졌습니다. 오를 때 덜 오르고, 내릴 때 더 내렸습니다."), badge="그래프 ⑤")


def chart_apt(c) -> tuple[str, str]:
    """⑥ 대표 단지 추이."""
    picks = [("자연앤힐스테이트", "광교 자연앤힐스테이트", WIN),
             ("시범한빛마을삼부르네상스", "동탄1 시범한빛마을", WIN),
             ("한빛마을2단지휴먼빌", "운정 한빛마을2단지", LOSE),
             ("수정마을(쌍용예가)", "김포 수정마을", LOSE)]
    sets = []
    for raw, label, color in picks:
        q = raw.replace("'", "''")
        sets.append((label, series(c, f"apt_name_raw='{q}'"), color))
    return "06_apt", deco(page(
        "대표 단지 30평대 · 연도별 중위 실거래가",
        '같은 기간, 네 단지가 이렇게 갈렸습니다',
        line_svg(sets),
        "단지별 거래가 가장 많은 곳을 하나씩 골랐습니다. "
        "그 동네 전체를 대표하지는 않습니다."), badge="그래프 ⑥")


def chart_peak(c) -> tuple[str, str]:
    """⑦ 2021 고점 대비 지금."""
    rows = []
    for t in TOWNS:
        r = same_apt(c, town_where(t), 2021, 2026)
        if r and r[0] >= 4:
            rows.append((f"{t} <small>{r[0]}곳</small>", r[1],
                         WIN if r[1] >= -5 else LOSE, f"{r[1]:+.0f}%"))
    rows.sort(key=lambda r: -r[1])
    b = same_apt(c, "1=1", 2021, 2026)
    rows.append((f"수도권 전체 <small>{b[0]:,}곳</small>", b[1], GREY,
                 f"{b[1]:+.0f}%"))
    return "07_peak", deco(page(
        "2021년 고점 대비 2026년 · 같은 단지",
        '지키느냐 빠지느냐가 <em>여기서</em> 갈립니다',
        bars(rows, zero=True),
        "가운데가 0%. 오른쪽이 고점보다 오른 곳, 왼쪽이 내린 곳입니다."), badge="그래프 ⑦")


# 신도시 중심 좌표 (지도에 점 찍는 용도). 강남은 기준점.
PINS = [
    {"label": "강남", "lat": 37.4979, "lng": 127.0276, "primary": True},
    {"label": "광교", "lat": 37.2860, "lng": 127.0530},
    {"label": "동탄", "lat": 37.2010, "lng": 127.1050},
    {"label": "검단", "lat": 37.6060, "lng": 126.6650},
    {"label": "김포한강", "lat": 37.6430, "lng": 126.6680},
    {"label": "운정", "lat": 37.7250, "lng": 126.7500},
    {"label": "옥정", "lat": 37.8220, "lng": 127.0620},
]


def chart_map(c) -> tuple[str, str]:
    """⑧ 어디에 있나 — 강남 기준 위치."""
    from content import geo as G
    hl = {}
    for t in WINNERS:
        hl[TOWNS[t][0]] = G.mix(D.BG, WIN, 0.55)
    for t in TOWNS:
        if t not in WINNERS:
            hl[TOWNS[t][0]] = G.mix(D.BG, LOSE, 0.55)
    hl["강남구"] = "#111111"
    svg = G.svg(hl, width=1150, height=500, line=D.SUB, fill=D.NEUTRAL,
                label_color=D.INK, label_halo="#FFFFFF", pins=PINS,
                show_labels=False) or ""
    side = (
        f'<div class="cap">성공한 쪽</div>'
        f'<div style="font-size:34px;font-weight:700;color:{WIN};'
        f'line-height:1.7">광교 · 동탄1 · 동탄2</div>'
        f'<div class="cap" style="margin-top:30px">부진한 쪽</div>'
        f'<div style="font-size:34px;font-weight:700;color:{LOSE};'
        f'line-height:1.7">검단 · 김포한강<br>운정 · 옥정</div>'
        f'<div style="font-size:26px;color:{D.SUB};margin-top:34px;'
        f'line-height:1.6">검은 점이 강남입니다.<br>'
        f'성공한 쪽은 모두 <b style="color:{WIN}">남쪽</b>에 있습니다.</div>')
    body = (f'<div class="two"><div style="flex:3">{svg}</div>'
            f'<div style="flex:1">{side}</div></div>')
    return "08_map", deco(page(
        "2기 신도시 일곱 곳",
        '성패가 갈린 선은 <b>강남과의 거리</b>가 아니라 <em>방향</em>이었습니다',
        body,
        "경계: 통계청 SGIS · 점은 각 신도시 중심의 대략적 위치입니다"), badge="그래프 ⑧")


OVERFLOW_JS = """() => {
  const el = document.querySelector('.pg');
  const note = document.querySelector('.note');
  const wrap = document.querySelector('.wrap');
  const bad = [];
  if (el && el.scrollHeight > el.clientHeight + 2)
    bad.push(`${el.scrollHeight - el.clientHeight}px 넘침`);
  // 자막 띠가 카드 아래쪽을 쓴다. 세 줄까지 늘어날 수 있으므로 넉넉히
  // 비워 둔다 — 여기 침범하면 자막에 가려진다.
  const SUB_ZONE = 196;
  if (wrap) {
    const w = wrap.getBoundingClientRect();
    const limit = (el ? el.clientHeight : 0) - SUB_ZONE;
    if (w.bottom > limit + 2)
      bad.push(`본문이 자막 자리를 ${(w.bottom - limit).toFixed(0)}px 침범`);
  }
  // 수치 박스가 본문을 덮으면 막대가 가려진다. 처음에 그렇게 나갔다.
  const co = document.querySelector('.callout');
  if (co && wrap) {
    const c = co.getBoundingClientRect(), w = wrap.getBoundingClientRect();
    if (c.top < w.bottom - 2 && c.bottom > w.top + 2)
      bad.push(`수치 박스가 본문과 ${(w.bottom - c.top).toFixed(0)}px 겹침`);
  }

  return bad;
}"""


def render(pages, outdir: Path) -> list[Path]:
    """판 크기를 바꾸면 조용히 넘친다. 찍기 전에 재고 세운다 — 마지막
    행이 잘린 채로 영상에 들어간 적이 있다."""
    from playwright.sync_api import sync_playwright
    outdir.mkdir(parents=True, exist_ok=True)
    made, bad = [], []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for name, html in pages:
            pg = br.new_page(viewport={"width": W, "height": H},
                             device_scale_factor=2)
            pg.set_content(f"<style>{css()}</style>{html}", wait_until="load")
            pg.wait_for_timeout(200)
            for w in pg.evaluate(OVERFLOW_JS):
                bad.append(f"{name}: {w}")
            out = outdir / f"{name}.png"
            pg.screenshot(path=str(out))
            pg.close()
            made.append(out)
        br.close()
    if bad:
        raise RuntimeError("판을 넘쳤다 — " + " / ".join(bad))
    return made


def main() -> int:
    c = con()
    builders = [chart_level, chart_naive, chart_mix, chart_same,
                chart_split, chart_apt, chart_peak, chart_map]
    pages = []
    for b in builders:
        print(f"  계산: {b.__name__}")
        pages.append(b(c))
    made = render(pages, OUT)
    print(f"\n  저장: {OUT}")
    for p in made:
        print(f"    {p.name}  {p.stat().st_size / 1024:.0f}KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
