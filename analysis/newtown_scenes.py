"""움직이는 장면 — 자라나는 차트, 점이 찍히는 지도, 쌓이는 단지.

왜 따로 두나
    본편(`newtown1_video.py`)과 앞 1분(`newtown1_part1.py`)이 같은 장면을
    쓴다. 한쪽에만 고치면 두 영상이 서로 달라진다.

장 수는 여기서 정하지 않는다. `LV.fit_anim` 이 장면 길이에서 거꾸로
계산한다 — 손으로 박아 두면 한 장이 1.9프레임처럼 어중간하게 걸려
재생이 끊기는 것처럼 보인다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis.newtown import con, town_where  # noqa: E402
from content import design as D  # noqa: E402
from content import emoji as EM  # noqa: E402
from content import frame as FR  # noqa: E402
from content import geo as G  # noqa: E402
from content import longvideo as LV  # noqa: E402
from metrics.filters import trades_cte  # noqa: E402

TRADE = (ROOT / "master" / "trade_events.parquet").as_posix()
W, H = FR.CONTENT_W, FR.CONTENT_H
WIN, LOSE, GREY, GOLD = "#2F6FED", "#E5484D", "#9AA0A6", "#E8A33D"

# 대장 단지 — 30평대 거래 20건 이상인 곳 중 최고 실거래가가 가장 높았던 곳.
FLAGS = [
    ("광교", "자연앤힐스테이트", WIN),
    ("동탄2", "더샵센트럴시티", LOSE),
]


def flagship(c, apt: str) -> dict:
    """한 단지의 연도별 중위가 + 첫해 · 최고가."""
    q = apt.replace("'", "''")
    rows = c.execute(f"""
        {trades_cte(TRADE)}
        SELECT year(deal_date) y, count(*) n,
               median(deal_amount) md, max(deal_amount) hi
        FROM trades
        WHERE pyeong_bucket='30P' AND deal_amount>0 AND apt_name_raw='{q}'
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    peak = max(r[3] for r in rows)
    return {"name": apt,
            "series": [(r[0], r[2] / 10000) for r in rows],
            "first_y": rows[0][0], "first": rows[0][2] / 10000,
            "peak": peak / 10000,
            "peak_y": max(rows, key=lambda r: r[3])[0]}


def load_flags() -> list[dict]:
    c = con()
    out = []
    for town, apt, color in FLAGS:
        d = flagship(c, apt)
        d["town"], d["color"] = town, color
        out.append(d)
    return out


# ── 공통 ─────────────────────────────────────────────────────────────────
def css() -> str:
    """공용 디자인(`design.py`)이 `.hd` `.rule` 같은 흔한 이름을 이미 쓰고
    있다. 그대로 쓰면 제목이 오른쪽으로 밀리고 선이 120px 로 잘린다 —
    실제로 한 번 당했다. 그래서 여기 것은 전부 `p1` 을 붙인다."""
    return LV.card_css() + f"""
.pg.p1{{padding:0;}}
.p1h{{position:absolute;left:92px;top:68px;right:92px;}}
.p1h .k{{font-size:28px;font-weight:700;color:{D.SUB};}}
.p1h .t{{font-size:52px;font-weight:800;letter-spacing:-.03em;
        margin-top:6px;line-height:1.15;}}
.p1h .t b{{color:{WIN};}}
.p1h .t em{{font-style:normal;color:{LOSE};}}
.p1f{{position:absolute;left:92px;top:214px;right:92px;
     display:flex;gap:52px;}}
.p1f .c{{flex:1;border-radius:22px;padding:32px 38px;
        border:3px solid {D.LINE};background:rgba(0,0,0,.022);}}
.p1f .tw{{display:inline-block;font-size:25px;font-weight:800;
         color:#FFFFFF;padding:7px 16px;border-radius:9px;}}
.p1f .ap{{font-size:42px;font-weight:800;letter-spacing:-.03em;
         margin-top:16px;}}
.p1f .bg{{font-size:100px;font-weight:800;letter-spacing:-.05em;
         line-height:1.04;margin-top:8px;}}
.p1f .wh{{font-size:24px;color:{D.SUB};margin-top:0;}}
.p1f .rl{{width:100%;height:3px;background:{D.LINE};margin:22px 0 16px;}}
.p1f .th{{font-size:29px;color:{D.SUB};line-height:1.45;}}
.p1f .th b{{color:{D.INK};font-weight:800;}}
.p1s{{position:absolute;right:96px;top:252px;width:430px;}}
"""


def ease(t: float) -> float:
    return LV.ease(t)


def page(body: str, kick: str = "", title: str = "", p: float = 1.0,
         dark: bool = False) -> str:
    hd = ""
    if kick or title:
        hd = (f'<div class="p1h" style="{LV._in(p, 0)}">'
              f'<div class="k">{kick}</div>'
              f'<div class="t">{title}</div></div>')
    return f'<div class="pg p1{" dark" if dark else ""}">{hd}{body}</div>'


# ── ① 두 대장 단지 ───────────────────────────────────────────────────────
def flags_card(flags: list[dict]):
    def html(p: float) -> str:
        cols = []
        for i, f in enumerate(flags):
            e = ease((p - 0.12 * i) / 0.6)
            cols.append(
                f'<div class="c" style="opacity:{e:.3f};'
                f'transform:translateY({(1 - e) * 26:.1f}px)">'
                f'<div class="tw" style="background:{f["color"]}">'
                f'{f["town"]}</div>'
                f'<div class="ap">{f["name"]}</div>'
                f'<div class="bg" style="color:{f["color"]}">'
                f'{f["peak"]:.1f}억</div>'
                f'<div class="wh">{f["peak_y"]}년 최고 실거래가 · '
                f'30평대</div>'
                f'<div class="rl"></div>'
                f'<div class="th">{f["first_y"]}년 입주 첫해 '
                f'<b>{f["first"]:.1f}억</b></div></div>')
        return page(f'<div class="p1f">{"".join(cols)}</div>',
                    "국토교통부 실거래가 · 30평대",
                    '그 동네 <b>대장 단지</b>는 지금 이렇습니다', p)
    return html


# ── ② 자라나는 꺾은선 ────────────────────────────────────────────────────
# 완성된 그림을 툭 띄우면 "그래서 뭐"가 된다. 2010년부터 선이 자라면
# **시간이 흐르는 게 보이고**, 어디서 벌어지기 시작했는지 눈이 따라간다.
PX0, PX1 = 182, 1180          # 그림판 가로 (오른쪽은 이름표 자리)
PY0, PY1 = 206, 604           # 세로 (아래가 0원)
Y0, Y1 = 2010, 2026
VMAX = 24.0                   # 억


def _x(y: float) -> float:
    return PX0 + (y - Y0) / (Y1 - Y0) * (PX1 - PX0)


def _y(v: float) -> float:
    return PY1 - min(v, VMAX) / VMAX * (PY1 - PY0)


def _upto(series: list[tuple[int, float]], yc: float):
    """커서 연도까지의 점들. 마지막 한 칸은 사이값으로 끊는다.

    그림판은 2010년부터다. 2006년부터 거래가 있는 단지를 같이 그리면
    선이 판 왼쪽 밖으로 나간다 — 축을 늘리는 대신 잘라 쓴다.
    """
    series = [(y, v) for y, v in series if y >= Y0]
    pts = [(y, v) for y, v in series if y <= yc]
    nxt = next(((y, v) for y, v in series if y > yc), None)
    if pts and nxt:
        (ly, lv), (ny, nv) = pts[-1], nxt
        t = (yc - ly) / (ny - ly)
        pts.append((yc, lv + (nv - lv) * t))
    return pts


def line_anim(flags: list[dict]):
    def html(p: float) -> str:
        e = ease(min(1.0, p / 0.88))
        yc = Y0 + (Y1 - Y0) * e
        g = []
        # 가로 눈금. 아주 옅게 — 선이 주인공이다.
        for v in range(0, int(VMAX) + 1, 5):
            g.append(f'<line x1="{PX0}" y1="{_y(v):.1f}" x2="{PX1}" '
                     f'y2="{_y(v):.1f}" stroke="{D.LINE}" stroke-width="1.5"/>')
            g.append(f'<text x="{PX0 - 22}" y="{_y(v) + 10:.1f}" '
                     f'text-anchor="end" font-size="26" fill="{D.SUB}">'
                     f'{v}억</text>')
        for y in range(Y0, Y1 + 1, 4):
            g.append(f'<text x="{_x(y):.1f}" y="{PY1 + 48}" '
                     f'text-anchor="middle" font-size="26" fill="{D.SUB}">'
                     f'{y}</text>')
        # 흐르는 연도. 장 표지의 큰 숫자와 같은 수법이라 한 영상처럼 보인다.
        # 선은 왼쪽 아래에서 시작해 오른쪽 위로 간다. 그래서 왼쪽 위가
        # 끝까지 비어 있다 — 흐르는 연도를 거기 둔다.
        g.append(f'<text x="{PX0 + 10}" y="{PY0 + 132}" '
                 f'font-size="176" font-weight="800" fill="rgba(17,17,17,.07)" '
                 f'letter-spacing="-8">{int(yc)}</text>')
        g.append(f'<line x1="{_x(yc):.1f}" y1="{PY0 - 14}" '
                 f'x2="{_x(yc):.1f}" y2="{PY1}" stroke="{D.SUB}" '
                 f'stroke-width="2" opacity=".22"/>')

        tips, lines = [], []
        for f in flags:
            pts = _upto(f["series"], yc)
            if len(pts) < 2:
                continue
            d = " ".join(f'{"M" if i == 0 else "L"}{_x(y):.1f},{_y(v):.1f}'
                         for i, (y, v) in enumerate(pts))
            col = f["color"]
            # 면은 전부 먼저 깔고 선을 뒤에 긋는다. 한 쌍씩 그리면 뒤
            # 계열의 면이 앞 계열의 선을 덮어 흐려진다.
            area = (f'{d} L{_x(pts[-1][0]):.1f},{PY1} '
                    f'L{_x(pts[0][0]):.1f},{PY1} Z')
            g.append(f'<path d="{area}" fill="{col}" opacity=".085"/>')
            lines.append(f'<path d="{d}" fill="none" stroke="{col}" '
                         f'stroke-width="6" stroke-linecap="round" '
                         f'stroke-linejoin="round"/>')
            ly, lv = pts[-1]
            tips.append((f, _x(ly), _y(lv), lv))
        g.extend(lines)
        # 끝점과 이름표. 두 선이 붙어 있어 위아래로 갈라 놓는다.
        # 여섯 줄이 되면 끝값이 바닥에 뭉친다. 아래로 차례로 밀어
        # 최소 간격을 지킨다 — 겹치면 둘 다 못 읽는다.
        tips.sort(key=lambda t: t[2])
        # 아래로만 밀면 끝에서 자막 자리를 밟는다. 들어갈 자리가
        # 모자라면 위로 돌려 쌓는다.
        GAP, used = 44.0, -1e9
        FLOOR = H - 196 - 14
        need = len(tips) * GAP
        used = max(-1e9, min(tips[0][2] + 10, FLOOR - need) - GAP)             if tips else -1e9
        for k, (f, tx, ty, lv) in enumerate(tips):
            col = f["color"]
            g.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="9" '
                     f'fill="{col}" stroke="#FFFFFF" stroke-width="3"/>')
            ly = max(ty + 10, used + GAP)
            used = ly
            if abs(ly - ty) > 14:
                g.append(f'<line x1="{tx + 10:.1f}" y1="{ty:.1f}" '
                         f'x2="{tx + 22:.1f}" y2="{ly - 10:.1f}" '
                         f'stroke="{col}" stroke-width="2" opacity=".5"/>')
            g.append(f'<text x="{tx + 26:.1f}" y="{ly:.1f}" '
                     f'font-size="25" font-weight="800" fill="{col}">'
                     f'{f["town"]} {lv:.1f}억</text>')
        svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
               f'style="position:absolute;inset:0">{"".join(g)}</svg>')
        return page(svg, "대장 단지 30평대 · 연도별 중위 실거래가",
                    '같은 출발선에서 <b>이렇게</b> 벌어졌습니다', 1.0)
    return html


# ── ③ 지도 ───────────────────────────────────────────────────────────────
MAP_W, MAP_H = 1080, 548
GANGNAM = {"label": "강남", "lat": 37.4979, "lng": 127.0276, "primary": True}

# 1기 신도시 다섯 곳. 점이 하나씩 찍히면 "다섯 곳"이 숫자가 아니라
# 자리로 남는다.
GEN1 = [
    ("분당", "성남분당구", 37.3800, 127.1200),
    ("일산", "고양일산동구", 37.6580, 126.7700),
    ("평촌", "안양동안구", 37.3900, 126.9500),
    ("산본", "군포시", 37.3580, 126.9300),
    ("중동", "부천시", 37.5030, 126.7630),
]


def _map(hl: dict, pins: list[dict]) -> str:
    return G.svg(hl, width=MAP_W, height=MAP_H, line=D.SUB,
                 fill=D.NEUTRAL, label_color=D.INK, label_halo="#FFFFFF",
                 pins=pins, show_labels=False) or ""


def _side(rows: list[tuple[str, str, float]]) -> str:
    out = []
    for nm, col, op in rows:
        out.append(f'<div style="opacity:{op:.3f};font-size:36px;'
                   f'font-weight:800;color:{col};line-height:1.9;'
                   f'transform:translateX({(1 - op) * 18:.1f}px)">{nm}</div>')
    return "".join(out)


def yeongtong_map():
    """영통이 어디인지 한 번은 보여 줘야 한다. 이름만 부르면 수원 어디쯤인지
    모르는 사람이 대부분이다."""
    def html(p: float) -> str:
        e = ease(p / 0.7)
        hl = {"수원영통구": G.mix(D.BG, WIN, 0.25 + 0.35 * e)}
        pins = [{"label": "영통", "lat": 37.2520, "lng": 127.0710},
                dict(GANGNAM, label="강남")]
        body = (f'<div data-bleed style="position:absolute;left:62px;top:212px;'
                f'opacity:{e:.3f}">{_map(hl, pins)}</div>'
                f'<div class="p1s">'
                f'<div style="font-size:30px;font-weight:700;color:{D.SUB}">'
                f'수원시 영통구</div>'
                f'<div style="font-size:56px;font-weight:800;color:{WIN};'
                f'letter-spacing:-.03em;margin-top:10px">90년대 후반<br>'
                f'택지지구</div>'
                f'<div style="font-size:28px;color:{D.SUB};line-height:1.6;'
                f'margin-top:24px">강남에서 남쪽으로 약 30km.<br>'
                f'광교와 동탄 사이에 있습니다.</div></div>')
        return page(body, "01 · 제가 살던 동네",
                    '여기가 <b>영통</b>입니다', p)
    return html


def gen1_map():
    """1기 신도시 다섯 곳이 순서대로 찍힌다."""
    def html(p: float) -> str:
        # 다섯 점이 고르게 찍히고 마지막에 잠깐 머문다.
        pos = ease(min(1.0, p / 0.86)) * len(GEN1)
        hl, pins, rows = {}, [], []
        for k, (nm, sgg, lat, lng) in enumerate(GEN1):
            on = min(1.0, max(0.0, pos - k))
            if on <= 0:
                rows.append((nm, D.NEUTRAL, 0.22))
                continue
            hl[sgg] = G.mix(D.BG, WIN, 0.26 + 0.52 * on)
            if on > 0.35:
                pins.append({"label": nm, "lat": lat, "lng": lng})
            rows.append((nm, WIN, 0.25 + 0.75 * on))
        body = (f'<div data-bleed style="position:absolute;left:62px;top:212px">'
                f'{_map(hl, pins)}</div>'
                f'<div class="p1s">'
                f'<div style="font-size:30px;font-weight:700;color:{D.SUB};'
                f'margin-bottom:14px">1기 신도시 다섯 곳</div>'
                f'{_side(rows)}'
                f'<div style="font-size:26px;color:{D.SUB};line-height:1.6;'
                f'margin-top:16px">영통은 여기 들어가지 않습니다.</div>'
                f'</div>')
        return page(body, "1989년 발표 · 1991~1996년 입주",
                    '1기는 <b>이 다섯 곳</b>입니다', 1.0)
    return html


# ── ④ 급변하는 배경 ──────────────────────────────────────────────────────
def surge_card():
    """「큰 변화 두 번」 — 글자만 두면 변화가 안 느껴진다. 뒤에서 도시가
    솟아오르게 한다. 눈에 띄면 글자를 잡아먹으므로 아주 옅게 깐다."""
    N = 34

    def html(p: float) -> str:
        e = ease(p)
        bars = []
        for k in range(N):
            # 결정값. 매 프레임 흔들리면 노이즈가 된다.
            seed = ((k * 97 + 31) % 61) / 61
            # 두 번의 파도 — 왼쪽 무리가 먼저, 오른쪽이 뒤따라 솟는다.
            wave = 0 if k < N * 0.52 else 0.42
            t = ease(min(1.0, max(0.0, (e - wave) / 0.58)))
            h = (90 + seed * 420) * t
            col = WIN if k < N * 0.52 else LOSE
            bars.append(
                f'<div style="width:{W / N - 9:.1f}px;height:{h:.0f}px;'
                f'background:{col};opacity:.085;border-radius:7px 7px 0 0">'
                f'</div>')
        back = (f'<div style="position:absolute;left:0;right:0;bottom:0;'
                f'height:620px;display:flex;align-items:flex-end;gap:9px;'
                f'padding:0 4px">{"".join(bars)}</div>')
        ico = EM.img("눈", 300)
        t1 = ease(p / 0.5)
        t2 = ease((p - 0.18) / 0.5)
        fore = (f'<div class="pg" style="position:absolute;inset:0;'
                f'background:transparent;padding:0 150px">'
                f'<div class="row">'
                f'<div class="icon" style="opacity:{t1:.3f};'
                f'transform:scale({0.72 + 0.28 * t1:.3f})">{ico}</div>'
                f'<div class="txt"><div class="big" '
                f'style="{LV._in(p, 1)}">큰 변화 <b>두 번</b></div>'
                f'<div class="cap" style="{LV._in(p, 2)}">'
                f'광교 · 동탄</div></div></div></div>')
        return (f'<div class="pg" style="overflow:hidden">{back}{fore}</div>')
    return html




# ── 새 집이 섞이면 (본편 5:20) ───────────────────────────────────────────
# 이 영상에서 제일 중요한 설명인데 글자 카드 한 장으로 지나가고 있었다.
# "동네 중위값이 올랐다"와 "내 집값이 올랐다"는 다른 말이라는 걸,
# **기존 집들이 한 채도 안 움직이는 걸 보여 주며** 말해야 한다.
MIX_LO, MIX_HI = 700, 2900          # 평당가 축 (만원)
MIX_X0, MIX_X1 = 210, 1430
MIX_Y = 500                          # 점 구름의 중심
MIX_ROWS = 7


def load_mix(town: str = "인천 검단", year: int = 2026) -> dict:
    """그 해 그 동네 30평대 거래를 신축/기존으로 갈라 분포째 가져온다.

    요약값(중위 몇 만원)만 쓰면 "그래서 뭐"가 된다. 점을 실제 분포대로
    찍어야 두 무리가 **따로 떨어져 있다**는 게 보인다.
    """
    c = con()
    w = town_where(town)
    rows = c.execute(f"""
        {trades_cte(TRADE)}
        SELECT price_per_pyeong ppy, build_year >= 2020 AS is_new
        FROM trades WHERE year(deal_date)={year} AND pyeong_bucket='30P'
          AND price_per_pyeong > 0 AND ({w})
        ORDER BY ppy
    """).fetchall()
    old = [r[0] for r in rows if not r[1]]
    new = [r[0] for r in rows if r[1]]
    allv = sorted(old + new)

    def med(xs):
        n = len(xs)
        return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2

    def thin(xs, k):
        """분포 모양을 지키며 k 개로 솎는다 (등간격 분위수)."""
        if len(xs) <= k:
            return list(xs)
        return [xs[round(i * (len(xs) - 1) / (k - 1))] for i in range(k)]

    share = len(new) / len(rows)
    k_new = round(100 * share)
    return {"town": town, "year": year, "n": len(rows),
            "n_new": len(new), "share": share * 100,
            "old_md": med(sorted(old)), "new_md": med(sorted(new)),
            "all_md": med(allv),
            "dots_old": thin(sorted(old), 100 - k_new),
            "dots_new": thin(sorted(new), k_new)}


def _mx(v: float) -> float:
    t = (v - MIX_LO) / (MIX_HI - MIX_LO)
    return MIX_X0 + max(0.0, min(1.0, t)) * (MIX_X1 - MIX_X0)


def mix_anim(m: dict):
    """선이 **어디서 어디로** 갔는지 한 장면에 남긴다.

    처음엔 움직이는 선 하나만 뒀는데, 다 옮겨간 뒤 화면을 보면 그냥
    "무리 둘과 선 하나"였다. 어디서 출발했는지가 없으니 움직였다는 걸
    알 수가 없다. 그래서 기존 중위값 자리에 **점선을 박아 두고**,
    거기서 새 자리까지 화살표를 긋는다.
    """
    def html(p: float) -> str:
        e_old = ease(min(1.0, p / 0.22))
        e_new = ease(max(0.0, min(1.0, (p - 0.30) / 0.34)))
        e_med = ease(max(0.0, min(1.0, (p - 0.44) / 0.34)))
        g = []
        for v in range(1000, MIX_HI, 500):
            g.append(f'<line x1="{_mx(v):.0f}" y1="{MIX_Y - 118}" '
                     f'x2="{_mx(v):.0f}" y2="{MIX_Y + 128}" '
                     f'stroke="{D.LINE}" stroke-width="1.5"/>')
            g.append(f'<text x="{_mx(v):.0f}" y="{MIX_Y + 170}" '
                     f'text-anchor="middle" font-size="25" fill="{D.SUB}">'
                     f'{v:,}</text>')
        g.append(f'<text x="{MIX_X1}" y="{MIX_Y + 208}" text-anchor="end" '
                 f'font-size="23" fill="{D.SUB}">평당 만원</text>')

        def cloud(vals, color, alpha):
            out = []
            for i, v in enumerate(vals):
                y = MIX_Y + ((i % MIX_ROWS) - (MIX_ROWS - 1) / 2) * 20
                out.append(f'<circle cx="{_mx(v):.1f}" cy="{y:.1f}" r="8" '
                           f'fill="{color}" opacity="{alpha:.3f}"/>')
            return "".join(out)

        g.append(cloud(m["dots_old"], GREY, e_old * .95))
        if e_new > 0:
            n = max(1, round(len(m["dots_new"]) * e_new))
            g.append(cloud(m["dots_new"][:n], GOLD, .95))

        ox = _mx(m["old_md"])
        mv = m["old_md"] + (m["all_md"] - m["old_md"]) * e_med
        mx = _mx(mv)
        TOP = MIX_Y - 118
        # ① 출발점 — 기존만 보던 자리. 끝까지 남는다.
        g.append(f'<line x1="{ox:.1f}" y1="{TOP}" x2="{ox:.1f}" '
                 f'y2="{MIX_Y + 128}" stroke="{GREY}" stroke-width="4" '
                 f'stroke-dasharray="9 8" opacity="{e_old:.2f}"/>')
        g.append(f'<text x="{ox:.1f}" y="{TOP - 54}" text-anchor="middle" '
                 f'font-size="26" font-weight="700" fill="{GREY}" '
                 f'opacity="{e_old:.2f}">기존만 보면</text>')
        g.append(f'<text x="{ox:.1f}" y="{TOP - 22}" text-anchor="middle" '
                 f'font-size="30" font-weight="800" fill="{GREY}" '
                 f'opacity="{e_old:.2f}">{m["old_md"]:,.0f}만원</text>')
        # ② 옮겨간 거리 — 화살표로 눈에 박는다.
        if e_med > 0.02:
            ay = TOP - 92
            g.append(f'<line x1="{ox:.1f}" y1="{ay}" x2="{mx - 14:.1f}" '
                     f'y2="{ay}" stroke="{D.INK}" stroke-width="4"/>')
            g.append(f'<path d="M{mx:.1f},{ay} l-20,-10 l0,20 Z" '
                     f'fill="{D.INK}"/>')
            g.append(f'<text x="{(ox + mx) / 2:.1f}" y="{ay - 18}" '
                     f'text-anchor="middle" font-size="30" font-weight="800" '
                     f'fill="{D.INK}">+{mv - m["old_md"]:,.0f}만원</text>')
        # ③ 지금 자리
        g.append(f'<line x1="{mx:.1f}" y1="{TOP}" x2="{mx:.1f}" '
                 f'y2="{MIX_Y + 128}" stroke="{D.INK}" stroke-width="5"/>')
        g.append(f'<rect x="{mx - 155:.1f}" y="{TOP - 48}" width="310" '
                 f'height="54" rx="11" fill="{D.INK}"/>')
        g.append(f'<text x="{mx:.1f}" y="{TOP - 12}" text-anchor="middle" '
                 f'font-size="30" font-weight="800" fill="#FFFFFF">'
                 f'동네 중위 {mv:,.0f}만원</text>')

        svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
               f'style="position:absolute;inset:0">{"".join(g)}</svg>')
        n_old, n_new = len(m["dots_old"]), len(m["dots_new"])
        # 축 숫자와 겹치지 않게 제목 밑으로. 그림을 보기 전에 읽는 게 맞다.
        leg = (f'<div style="position:absolute;left:92px;top:196px;'
               f'display:flex;gap:40px;font-size:28px;font-weight:700">'
               f'<span style="color:{GREY};opacity:{e_old:.2f}">'
               f'● 기존 {n_old}채 <b style="color:{LOSE}">그대로</b></span>'
               f'<span style="color:{GOLD};opacity:{e_new:.2f}">'
               f'● 2020년 이후 새 집 {n_new}채가 섞임</span></div>')
        return page(svg + leg,
                    f'{m["town"]} · {m["year"]}년 30평대 거래 '
                    f'{m["n"]:,}건을 100채로 줄여 그렸습니다',
                    '기존 집값은 그대로인데 <em>동네 중위값만</em> '
                    '올라갑니다', 1.0)
    return html


# ── 입주가 몰린 해 (본편 7:39) ──────────────────────────────────────────
# "2.4배, 그중 81개가 한꺼번에"를 글자로만 말하고 있었다. 연도축에
# 쌓아 올리면 **몰렸다는 사실 자체가 그림**이 된다.
MV_Y0, MV_Y1 = 2003, 2023
MV_X0, MV_X1 = 230, 1430
MV_AXIS = 408                        # 가운데 축 (위: 동탄1, 아래: 동탄2)
MV_UP, MV_DN = 26, 58                # 축에서 띄우는 거리
#   아래쪽은 연도 글자가 먼저 오므로 더 띄운다. 2018년 29칸이
#   제일 긴 기둥이라 칸을 7px 로 줄여야 자막 자리를 안 밟는다.
MV_CELL, MV_GAP = 7, 1


def load_movein(towns=("동탄1", "동탄2")) -> list[dict]:
    c = con()
    out = []
    for t in towns:
        rows = c.execute(f"""
            {trades_cte(TRADE)}
            SELECT build_year y, count(DISTINCT apt_id) n
            FROM trades WHERE pyeong_bucket='30P' AND build_year IS NOT NULL
              AND ({town_where(t)})
            GROUP BY 1 ORDER BY 1
        """).fetchall()
        out.append({"town": t, "by_year": {int(y): n for y, n in rows},
                    "total": sum(n for _, n in rows)})
    return out


def movein_anim(rows: list[dict], burst=(2015, 2019)):
    up, dn = rows[0], rows[1]
    span = MV_Y1 - MV_Y0

    def _x(y: float) -> float:
        return MV_X0 + (y - MV_Y0) / span * (MV_X1 - MV_X0)

    def html(p: float) -> str:
        e = ease(min(1.0, p / 0.86))
        cur = MV_Y0 + span * e                 # 시간 커서
        g, step = [], MV_CELL + MV_GAP
        bw = _x(burst[1]) - _x(burst[0]) + step * 2
        hit = ease(max(0.0, min(1.0, (cur - burst[1]) / 2.0)))
        if hit > 0:
            g.append(f'<rect x="{_x(burst[0]) - step:.0f}" y="196" '
                     f'width="{bw:.0f}" height="510" rx="14" '
                     f'fill="{D.ACCENT}" opacity="{hit * .28:.3f}"/>')
        g.append(f'<line x1="{MV_X0 - 30}" y1="{MV_AXIS}" x2="{MV_X1 + 30}" '
                 f'y2="{MV_AXIS}" stroke="{D.SUB}" stroke-width="2"/>')
        for y in range(MV_Y0, MV_Y1 + 1, 4):
            g.append(f'<text x="{_x(y):.0f}" y="{MV_AXIS + 36}" '
                     f'text-anchor="middle" font-size="25" fill="{D.SUB}">'
                     f'{y}</text>')

        seen = []
        for side, r, col in ((-1, up, WIN), (1, dn, LOSE)):
            tot = 0
            for y, n in sorted(r["by_year"].items()):
                if y > cur:
                    break
                tot += n
                for k in range(n):
                    oy = (MV_AXIS - MV_UP - k * step - MV_CELL
                          if side < 0 else MV_AXIS + MV_DN + k * step)
                    g.append(f'<rect x="{_x(y) - MV_CELL / 2:.1f}" '
                             f'y="{oy:.1f}" width="{MV_CELL}" '
                             f'height="{MV_CELL}" rx="2" fill="{col}"/>')
            seen.append(tot)

        svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
               f'style="position:absolute;inset:0">{"".join(g)}</svg>')
        side = ""
        for i, (r, col, tot) in enumerate(
                ((up, WIN, seen[0]), (dn, LOSE, seen[1]))):
            top = 258 if i == 0 else 512
            side += (f'<div style="position:absolute;left:68px;top:{top}px;'
                     f'font-size:34px;font-weight:800;color:{col}">'
                     f'{r["town"]}<div style="font-size:46px;margin-top:4px">'
                     f'{tot}개</div></div>')
        bn = sum(n for y, n in dn["by_year"].items()
                 if burst[0] <= y <= burst[1])
        side += (f'<div style="position:absolute;right:68px;top:672px;'
                 f'text-align:right;font-size:31px;font-weight:800;'
                 f'color:{LOSE};opacity:{hit:.2f}">'
                 f'{burst[0]}~{burst[1]}년에만 {bn}개</div>')
        return page(svg + side, "30평대 거래가 있는 단지 · 입주 연도별",
                    '동탄2는 <em>한꺼번에</em> 들어왔습니다', 1.0)
    return html


# ── 강남에서 뻗는 방향 (본편 8:07) ──────────────────────────────────────
# "거리가 아니라 방향"이 주장인데 점만 찍힌 지도를 쓰고 있었다.
# 강남에서 선이 뻗어 나가면 남/북이 **눈으로** 갈린다.
DIRS = [
    ("광교", 37.2860, 127.0530, True),
    ("동탄", 37.2010, 127.1050, True),
    ("검단", 37.6060, 126.6650, False),
    ("김포한강", 37.6430, 126.6680, False),
    ("운정", 37.7250, 126.7500, False),
    ("옥정", 37.8220, 127.0620, False),
]


def direction_map(static: bool = False):
    """static 이면 다 그려진 채로 시작한다. 같은 지도를 두 토막에 걸쳐
    쓸 때, 두 번째에서 선을 다시 그리면 화면이 되감긴 것처럼 보인다."""
    def html(p: float) -> str:
        if static:
            p = 1.0
        pos = ease(min(1.0, p / 0.88)) * len(DIRS)
        arcs, pins = [], [dict(GANGNAM, label="강남")]
        for k, (nm, lat, lng, win) in enumerate(DIRS):
            t = max(0.0, min(1.0, pos - k))
            if t <= 0:
                continue
            arcs.append({"a": (GANGNAM["lat"], GANGNAM["lng"]),
                         "b": (lat, lng), "color": WIN if win else LOSE,
                         "t": t, "width": 6, "dot": True})
            if t > 0.8:
                pins.append({"label": nm, "lat": lat, "lng": lng})
        svg = G.svg({"강남구": "#111111"}, width=MAP_W, height=MAP_H,
                    line=D.SUB, fill=D.NEUTRAL, label_color=D.INK,
                    label_halo="#FFFFFF", pins=pins, arcs=arcs,
                    show_labels=False) or ""
        done = ease(max(0.0, min(1.0, (p - 0.82) / 0.18)))
        body = (f'<div data-bleed style="position:absolute;left:62px;top:212px">'
                f'{svg}</div>'
                f'<div class="p1s">'
                f'<div style="font-size:34px;font-weight:800;color:{WIN};'
                f'line-height:1.6">남쪽으로 간 길<br>광교 · 동탄</div>'
                f'<div style="font-size:34px;font-weight:800;color:{LOSE};'
                f'line-height:1.6;margin-top:26px">서쪽 · 북쪽으로 간 길'
                f'<br>검단 · 김포한강<br>운정 · 옥정</div>'
                f'<div style="font-size:28px;color:{D.SUB};line-height:1.6;'
                f'margin-top:30px;opacity:{done:.2f}">직선거리는 비슷합니다.'
                f'<br>갈린 건 <b style="color:{D.INK}">방향</b>입니다.</div>'
                f'</div>')
        return page(body, "2기 신도시 여섯 곳 · 강남 기준",
                    '거리가 아니라 <em>방향</em>이었습니다', 1.0)
    return html


# ── 사정이 다른 곳 (본편 3:52) ──────────────────────────────────────────
COUNTER = [
    ("인천 검단", "검단구", 37.6060, 126.6650),
    ("김포 한강", "김포시", 37.6430, 126.6680),
    ("파주 운정", "파주시", 37.7250, 126.7500),
    ("양주 옥정", "양주시", 37.8220, 127.0620),
]
SHORT = {"인천 검단": "검단", "김포 한강": "김포",
         "파주 운정": "운정", "양주 옥정": "옥정"}
WON = [("광교", "수원영통구", 37.2860, 127.0530),
       ("동탄", "화성시", 37.2010, 127.1050)]


def counter_map():
    def html(p: float) -> str:
        pos = ease(min(1.0, p / 0.86)) * len(COUNTER)
        hl, pins, rows = {}, [], []
        # 오른 곳은 처음부터 옅게 깔아 둔다 — 반례가 어디에 붙는지 보인다.
        for nm, sgg, lat, lng in WON:
            hl[sgg] = G.mix(D.BG, WIN, 0.30)
            pins.append({"label": nm, "lat": lat, "lng": lng})
        for k, (nm, sgg, lat, lng) in enumerate(COUNTER):
            on = min(1.0, max(0.0, pos - k))
            if on <= 0:
                rows.append((nm, D.NEUTRAL, 0.22))
                continue
            hl[sgg] = G.mix(D.BG, LOSE, 0.22 + 0.48 * on)
            if on > 0.35:
                pins.append({"label": SHORT[nm], "lat": lat, "lng": lng})
            rows.append((nm, LOSE, 0.25 + 0.75 * on))
        pins.append(dict(GANGNAM, label="강남"))
        svg = G.svg(hl, width=MAP_W, height=MAP_H, line=D.SUB,
                    fill=D.NEUTRAL, label_color=D.INK,
                    label_halo="#FFFFFF", pins=pins,
                    show_labels=False) or ""
        body = (f'<div data-bleed style="position:absolute;left:62px;top:212px">'
                f'{svg}</div>'
                f'<div class="p1s">'
                f'<div style="font-size:30px;font-weight:700;color:{D.SUB};'
                f'margin-bottom:14px">같은 2기, 사정이 다른 곳</div>'
                f'{_side(rows)}'
                f'<div style="font-size:26px;color:{D.SUB};line-height:1.6;'
                f'margin-top:26px">파란 곳이 지금까지 본 광교·동탄입니다.'
                f'</div></div>')
        return page(body, "2기 신도시 · 같은 시기에 출발",
                    '<em>사정이 다른 곳</em>이 있습니다', 1.0)
    return html


# ── 자라나는 막대 (본편 4:06 · 4:27 · 6:00 · 6:38) ──────────────────────
# 완성된 막대를 툭 띄우면 눈이 제일 긴 것만 보고 끝난다. 0에서 자라면
# 순서가 **차례로** 읽히고, 어디서 갈라지는지가 보인다.
BA_X0, BA_X1 = 400, 1330        # 막대가 놓이는 자리
BA_VAL = BA_X1 + 22             # 값은 늘 같은 칸에 — 0 기준
#   차트에서 막대 끝에 붙이면 긴 막대의 값이 이름표를 덮는다.
BA_TOP = 236                    # 첫 줄 윗변
BA_ROW, BA_TRACK = 60, 20


def bars_anim(rows, *, kick: str, title: str, note: str = "",
              zero: bool = False, legend: str = "", static: bool = False):
    """rows: (라벨, 값, 색, 표시문자열). zero 면 0 을 가운데 두고 좌우로.

    숫자는 **세지 않는다.** 막대가 다 자란 뒤 제 값으로 떠오른다 —
    세는 숫자는 중간에 잘라 가면 틀린 값이 박제된다.
    """
    n = len(rows)
    lim = max(abs(v) for _, v, _, _ in rows) or 1
    span = BA_X1 - BA_X0

    def html(p: float) -> str:
        if static:
            p = 1.0
        out = []
        for i, (lab, v, col, txt) in enumerate(rows):
            e = ease(max(0.0, min(1.0, (p - i * 0.065) / 0.46)))
            y = BA_TOP + i * BA_ROW
            if zero:
                w = abs(v) / lim * span / 2 * e
                x = BA_X0 + span / 2 - (w if v < 0 else 0)
            else:
                w = max(3.0, v / lim * span * e)
                x = BA_X0
            out.append(
                f'<div style="position:absolute;left:92px;top:{y}px;'
                f'width:{BA_X0 - 116}px;text-align:right;font-size:26px;'
                f'font-weight:700;color:{D.INK}">{lab}</div>')
            out.append(
                f'<div style="position:absolute;left:{BA_X0}px;'
                f'top:{y + 5}px;width:{span}px;height:{BA_TRACK}px;'
                f'border-radius:999px;background:#E9E6DE"></div>')
            out.append(
                f'<div style="position:absolute;left:{x:.1f}px;'
                f'top:{y + 5}px;width:{w:.1f}px;height:{BA_TRACK}px;'
                f'border-radius:999px;background:{col}"></div>')
            # 값은 막대가 다 자란 뒤에 뜬다. 자리는 늘 오른쪽 같은 칸 —
            # 막대 끝에 붙이면 긴 막대에서 이름표와 겹친다.
            tv = ease(max(0.0, min(1.0, (p - i * 0.065 - 0.30) / 0.26)))
            out.append(
                f'<div style="position:absolute;left:{BA_VAL}px;top:{y}px;'
                f'font-size:28px;font-weight:800;color:{col};'
                f'opacity:{tv:.3f}">{txt}</div>')
        if zero:
            cx = BA_X0 + span / 2
            out.append(f'<div style="position:absolute;left:{cx:.0f}px;'
                       f'top:{BA_TOP - 12}px;width:2px;'
                       f'height:{n * BA_ROW + 4}px;background:{D.SUB};'
                       f'opacity:.5"></div>')
        if legend:
            out.append(f'<div style="position:absolute;left:92px;'
                       f'top:{BA_TOP + n * BA_ROW + 18}px;display:flex;'
                       f'gap:30px;font-size:23px;color:{D.SUB}">'
                       f'{legend}</div>')
        nt = ""
        if note:
            nt = (f'<div style="position:absolute;left:92px;top:196px;'
                  f'font-size:25px;color:{D.SUB};max-width:1300px;'
                  f'line-height:1.45">{note}</div>')
        return page("".join(out) + nt, kick, title, 1.0)
    return html


def legend_chip(label: str, color: str) -> str:
    return (f'<span><i style="display:inline-block;width:22px;height:22px;'
            f'border-radius:6px;background:{color};margin-right:8px;'
            f'vertical-align:-4px"></i>{label}</span>')


LEGEND_WL = (legend_chip("광교·동탄", WIN)
             + legend_chip("검단·김포·운정·옥정", LOSE)
             + legend_chip("수도권 전체", GREY))


# ── 부진한 쪽 대장 단지 (본편 0:30 차트에 함께) ─────────────────────────
# 오른 두 곳만 그리면 "둘 다 올랐네"로 끝난다. **같은 출발선에서 갈라지는
# 걸** 보여 주려면 안 오른 쪽이 같은 그림 안에 있어야 한다.
# 고를 때 최고가 1위를 쓰지 않았다 — 그런 단지는 2021년 이후 입주라
# 2012년부터의 선이 없다. 이력이 긴 쪽을 쓴다.
LAGGARDS = [
    ("인천 검단", "당하KCC스위첸", LOSE),
    ("김포 한강", "수정마을(쌍용예가)", LOSE),
    ("파주 운정", "한빛마을2단지휴먼빌", LOSE),
    ("양주 옥정", "세창리베하우스", LOSE),
]


def load_all_flags() -> list[dict]:
    """오른 쪽 둘 + 부진한 쪽 넷. 한 그림에 올린다."""
    c = con()
    out = []
    for town, apt, color in FLAGS + LAGGARDS:
        d = flagship(c, apt)
        d["town"], d["color"] = town, color
        out.append(d)
    return out


# ── 단지 한 곳 (본편 1:30) ──────────────────────────────────────────────
def apt_card(f: dict, *, kick: str, title: str):
    """숫자 한 줄만 띄우던 자리에 **그 집이 걸어온 선**을 같이 둔다.

    사진을 붙이고 싶었지만 그 단지 사진을 권리 문제 없이 구할 수 없다.
    대신 우리가 가진 것(실거래가)을 그린다.
    """
    ser = f["series"]
    x0, x1 = ser[0][0], ser[-1][0]
    lo, hi = 0, max(v for _, v in ser) * 1.12
    PX0, PX1, PY0, PY1 = 740, 1480, 300, 640

    def _px(y):
        return PX0 + (y - x0) / max(1, x1 - x0) * (PX1 - PX0)

    def _py(v):
        return PY1 - (v - lo) / (hi - lo) * (PY1 - PY0)

    def html(p: float) -> str:
        e = ease(min(1.0, p / 0.8))
        n = max(2, int(len(ser) * e))
        pts = ser[:n]
        d = " ".join(f'{"M" if i == 0 else "L"}{_px(y):.1f},{_py(v):.1f}'
                     for i, (y, v) in enumerate(pts))
        area = (f'{d} L{_px(pts[-1][0]):.1f},{PY1} '
                f'L{_px(pts[0][0]):.1f},{PY1} Z')
        g = [f'<path d="{area}" fill="{f["color"]}" opacity=".10"/>',
             f'<path d="{d}" fill="none" stroke="{f["color"]}" '
             f'stroke-width="6" stroke-linecap="round" '
             f'stroke-linejoin="round"/>']
        for v in (5, 10, 15, 20):
            if v < hi:
                g.append(f'<line x1="{PX0}" y1="{_py(v):.0f}" x2="{PX1}" '
                         f'y2="{_py(v):.0f}" stroke="{D.LINE}" '
                         f'stroke-width="1.5"/>')
                g.append(f'<text x="{PX0 - 16}" y="{_py(v) + 9:.0f}" '
                         f'text-anchor="end" font-size="23" '
                         f'fill="{D.SUB}">{v}억</text>')
        for y in (x0, (x0 + x1) // 2, x1):
            g.append(f'<text x="{_px(y):.0f}" y="{PY1 + 40}" '
                     f'text-anchor="middle" font-size="24" '
                     f'fill="{D.SUB}">{y}</text>')
        ly, lv = pts[-1]
        g.append(f'<circle cx="{_px(ly):.1f}" cy="{_py(lv):.1f}" r="10" '
                 f'fill="{f["color"]}" stroke="#FFFFFF" stroke-width="4"/>')
        svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
               f'style="position:absolute;inset:0">{"".join(g)}</svg>')
        left = (
            f'<div style="position:absolute;left:92px;top:286px;width:580px">'
            f'<div style="display:inline-block;font-size:25px;font-weight:800;'
            f'color:#FFFFFF;background:{f["color"]};padding:7px 16px;'
            f'border-radius:9px">{f["town"]}</div>'
            f'<div style="font-size:52px;font-weight:800;margin-top:18px;'
            f'letter-spacing:-.03em">{f["name"]}</div>'
            f'<div style="font-size:92px;font-weight:800;color:{f["color"]};'
            f'letter-spacing:-.04em;margin-top:12px">'
            f'{f["first"]:.1f}억</div>'
            f'<div style="font-size:26px;color:{D.SUB}">'
            f'{f["first_y"]}년 입주 첫해 · 30평대</div>'
            f'<div style="width:100%;height:3px;background:{D.LINE};'
            f'margin:22px 0 16px"></div>'
            f'<div style="font-size:29px;color:{D.SUB};line-height:1.45">'
            f'{f["peak_y"]}년 최고 <b style="color:{D.INK}">'
            f'{f["peak"]:.1f}억</b></div></div>')
        return page(svg + left, kick, title, 1.0)
    return html


# ── 오른 이유 셋 (본편 1:49 · 3:27) ─────────────────────────────────────
def reason_card(icon: str, kick: str, title: str, items: list[tuple[str, str]],
                color: str = WIN):
    """퍼즐 조각 하나만 띄우고 "세 가지"라고 말하던 자리.

    말로만 셋이라고 하면 뒤따르는 세 장면이 따로 논다. **목록을 먼저
    펼쳐 두고** 하나씩 설명하러 가야 어디쯤인지 안다.
    """
    def html(p: float) -> str:
        e = ease(min(1.0, p / 0.5))
        ico = EM.img(icon, 300)
        rows = []
        for k, (head, sub) in enumerate(items):
            t = ease(max(0.0, min(1.0, (p - 0.2 - k * 0.16) / 0.45)))
            rows.append(
                f'<div style="display:flex;align-items:flex-start;gap:24px;'
                f'margin-bottom:30px;opacity:{t:.3f};'
                f'transform:translateX({(1 - t) * 24:.1f}px)">'
                f'<div style="flex:none;width:56px;height:56px;'
                f'border-radius:50%;background:{color};color:#FFFFFF;'
                f'font-size:28px;font-weight:800;display:flex;'
                f'align-items:center;justify-content:center">{k + 1}</div>'
                f'<div><div style="font-size:44px;font-weight:800;'
                f'letter-spacing:-.03em;line-height:1.2">{head}</div>'
                f'<div style="font-size:27px;color:{D.SUB};margin-top:6px;'
                f'line-height:1.4">{sub}</div></div></div>')
        body = (
            f'<div style="position:absolute;left:112px;top:304px;'
            f'opacity:{e:.3f};transform:scale({0.78 + 0.22 * e:.3f})">'
            f'{ico}</div>'
            f'<div style="position:absolute;left:500px;top:262px;'
            f'right:92px">{"".join(rows)}</div>')
        return page(body, kick, title, 1.0)
    return html


# ── 주변에서 광교로 (본편 2:05) ─────────────────────────────────────────
# 앞 장면과 같은 노선도를 두 번 쓰고 있었다. 같은 그림이 두 번 뜨면
# 이야기가 멈춘 것처럼 보인다. **수요가 어디서 옮겨왔는지**를 그린다.
INBOUND = [
    ("수원 영통", 37.2520, 127.0710),
    ("수원 권선", 37.2580, 126.9720),
    ("용인 수지", 37.3220, 127.0970),
    ("강남", 37.4979, 127.0276),
]
GWANGGYO = (37.2860, 127.0530)


def inbound_map():
    def html(p: float) -> str:
        pos = ease(min(1.0, p / 0.84)) * len(INBOUND)
        arcs, pins = [], [{"label": "광교", "lat": GWANGGYO[0],
                           "lng": GWANGGYO[1], "primary": True}]
        for k, (nm, lat, lng) in enumerate(INBOUND):
            t = max(0.0, min(1.0, pos - k))
            if t <= 0:
                continue
            # 바깥에서 광교로 들어온다. 방향이 반대라 화살머리도 안쪽이다.
            arcs.append({"a": (lat, lng), "b": GWANGGYO, "color": WIN,
                         "t": t, "width": 6, "dot": True})
            if t > 0.5:
                pins.append({"label": nm, "lat": lat, "lng": lng})
        hl = {"수원영통구": G.mix(D.BG, WIN, 0.45)}
        svg = G.svg(hl, width=MAP_W, height=MAP_H, line=D.SUB,
                    fill=D.NEUTRAL, label_color=D.INK, label_halo="#FFFFFF",
                    pins=pins, arcs=arcs, show_labels=False) or ""
        body = (f'<div data-bleed style="position:absolute;left:62px;'
                f'top:212px">{svg}</div>'
                f'<div class="p1s">'
                f'<div style="font-size:34px;font-weight:800;color:{WIN};'
                f'line-height:1.5">강남으로 출퇴근하던<br>수원 수요가'
                f'<br>광교로 옮겨갔습니다</div>'
                f'<div style="font-size:27px;color:{D.SUB};line-height:1.6;'
                f'margin-top:24px">2016년 신분당선 연장으로<br>'
                f'강남까지 40분 안팎이 됐습니다.</div></div>')
        return page(body, "2016년 신분당선 광교 연장 이후",
                    '수요가 <b>안쪽으로</b> 모였습니다', 1.0)
    return html


# ── 일자리 (본편 3:30) ──────────────────────────────────────────────────
# 선으로 잇던 걸 그만둔다. 반도체 공장은 동탄에서 "이어지는" 게 아니라
# 그 자리에 **있는** 것이다. 자리에 바로 표를 올린다.
FABS = [
    ("삼성전자 화성", 37.2050, 127.0470, "약 6km"),
    ("삼성전자 기흥", 37.2560, 127.0560, "약 9km"),
    ("삼성전자 평택", 36.9930, 127.0280, "약 25km"),
    ("SK하이닉스 이천", 37.2420, 127.4650, "약 32km"),
]
DONGTAN = (37.2010, 127.1050)


def jobs_map():
    def html(p: float) -> str:
        pos = ease(min(1.0, p / 0.86)) * len(FABS)
        pins = [{"label": "동탄", "lat": DONGTAN[0], "lng": DONGTAN[1],
                 "primary": True}]
        rows = []
        for k, (nm, lat, lng, dist) in enumerate(FABS):
            on = min(1.0, max(0.0, pos - k))
            if on > 0.35:
                pins.append({"label": nm.replace("삼성전자 ", "")
                             .replace("SK하이닉스 ", ""), "lat": lat,
                             "lng": lng})
            rows.append((f'{nm} <small style="color:{D.SUB}">{dist}</small>',
                         LOSE if on > 0 else D.NEUTRAL,
                         0.22 + 0.78 * on))
        hl = {"화성시": G.mix(D.BG, WIN, 0.34),
              "용인시 기흥구": G.mix(D.BG, LOSE, 0.30),
              "평택시": G.mix(D.BG, LOSE, 0.30),
              "이천시": G.mix(D.BG, LOSE, 0.30)}
        svg = G.svg(hl, width=1120, height=512, line=D.SUB,
                    fill=D.NEUTRAL, label_color=D.INK, label_halo="#FFFFFF",
                    pins=pins, show_labels=False) or ""
        side = "".join(
            f'<div style="opacity:{op:.2f};font-size:30px;font-weight:800;'
            f'color:{col};line-height:1.75">{nm}</div>'
            for nm, col, op in rows)
        body = (f'<div data-bleed style="position:absolute;left:52px;'
                f'top:204px">{svg}</div>'
                f'<div style="position:absolute;right:84px;top:258px;'
                f'width:400px">'
                f'<div style="font-size:28px;font-weight:700;color:{D.SUB};'
                f'margin-bottom:14px">동탄에서 출퇴근권인 일자리</div>'
                f'{side}</div>')
        return page(body, "반도체 생산단지 · 동탄 기준 직선거리",
                    '일자리는 <b>광교보다 강합니다</b>', 1.0)
    return html


# ── 동탄이 얼마나 많은가 (본편 2:56 · 3:10) ────────────────────────────
# "2,779건"만 띄우면 많은 건지 적은 건지 알 수가 없다. 옆에 다른 곳을
# 세워야 비로소 숫자가 말을 한다.
CMP_TOWNS = ("동탄1", "동탄2", "광교", "인천 검단",
             "김포 한강", "파주 운정", "양주 옥정")


def load_compare(year: int = 2026) -> dict:
    c = con()
    out = {}
    for t in CMP_TOWNS:
        r = c.execute(f"""
            {trades_cte(TRADE)}
            SELECT count(*) n,
              sum(CASE WHEN deal_amount>=100000 THEN 1 ELSE 0 END) hi,
              round(median(deal_amount)/10000, 1) md
            FROM trades WHERE year(deal_date)={year} AND pyeong_bucket='30P'
              AND deal_amount>0 AND ({town_where(t)})
        """).fetchone()
        out[t] = {"n": int(r[0]), "hi": int(r[1] or 0), "md": float(r[2] or 0)}
    # 동탄1·2 를 합쳐 "화성 동탄"으로도 둔다 (대본이 그렇게 말한다)
    a, b = out["동탄1"], out["동탄2"]
    out["화성 동탄"] = {"n": a["n"] + b["n"], "hi": a["hi"] + b["hi"],
                      "md": None}
    return out


def compare_rows(cmp: dict, field: str, fmt) -> list[tuple]:
    """막대 행으로. 동탄을 파랗게 세우고 나머지는 회색으로 눕힌다."""
    keys = ["화성 동탄"] + [t for t in CMP_TOWNS
                          if t not in ("동탄1", "동탄2")]
    rows = [(t, cmp[t][field], WIN if t == "화성 동탄" else GREY,
             fmt(cmp[t][field])) for t in keys]
    rows.sort(key=lambda r: -r[1])
    return rows


# ── 광교호수공원 (본편 2:20) ────────────────────────────────────────────
# 카카오맵·구글 상공뷰를 쓸 수 없어서(약관), OSM 에서 **좌표만** 받아
# 우리 색으로 그린다. 시군구 경계를 SGIS 에서 받아 그리는 것과 같은 방식.
PARK_W, PARK_H = 1060, 500
# (이름, 위도, 경도, 큰점, 라벨 가로밀기, 라벨 세로밀기)
# 셋이 300m 안에 모여 있어 그냥 찍으면 글자가 겹친다.
PARK_PINS = [
    ("광교호수공원", 37.2838, 127.0631, True, 120, 8),
    ("자연앤힐스테이트", 37.2893, 127.0565, False, -40, -30),
    ("광교중앙역", 37.2873, 127.0548, False, -118, 34),
]


def park_card(name: str = "광교호수공원"):
    from content import osm as OSM
    d = OSM.load(name)

    def html(p: float) -> str:
        if not d:
            return page('<div style="font-size:44px;color:#E5484D">'
                        'OSM 자료 없음 — python -m content.osm 먼저</div>',
                        "", "", 1.0)
        xs = [x for el in d["elements"] for x, _ in el["pts"]]
        ys = [y for el in d["elements"] for _, y in el["pts"]]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        # 위도만큼 가로가 줄어든다. 안 고치면 지도가 옆으로 늘어난다.
        import math
        kx = math.cos(math.radians((y0 + y1) / 2))
        sw, sh = (x1 - x0) * kx, (y1 - y0)
        sc = min(PARK_W / sw, PARK_H / sh) * 0.96
        ox = (PARK_W - sw * sc) / 2
        oy = (PARK_H - sh * sc) / 2

        def P(lon, lat):
            return (ox + (lon - x0) * kx * sc, oy + (y1 - lat) * sc)

        e = ease(min(1.0, p / 0.6))
        g = [f'<rect width="{PARK_W}" height="{PARK_H}" rx="18" '
             f'fill="{G.mix(D.BG, D.NEUTRAL, .35)}"/>']
        order = {"road": 0, "park": 1, "water": 2}
        for el in sorted(d["elements"], key=lambda x: order[x["kind"]]):
            pts = [P(*q) for q in el["pts"]]
            if len(pts) < 2:
                continue
            dd = "M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts)
            if el["kind"] == "road":
                g.append(f'<path d="{dd}" fill="none" stroke="#FFFFFF" '
                         f'stroke-width="3" opacity=".75"/>')
            elif el["kind"] == "park":
                g.append(f'<path d="{dd}Z" fill="#9FC79A" opacity=".55"/>')
            else:
                g.append(f'<path d="{dd}Z" fill="#7FB3D5" opacity=".9"/>')
        for k, (nm, lat, lng, big, dx, dy) in enumerate(PARK_PINS):
            t = ease(max(0.0, min(1.0, (p - 0.3 - k * 0.14) / 0.4)))
            if t <= 0.02:
                continue
            px, py = P(lng, lat)
            r = 13 if big else 8
            g.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" '
                     f'fill="{WIN if big else D.INK}" stroke="#FFFFFF" '
                     f'stroke-width="4" opacity="{t:.2f}"/>')
            lx, ly = px + dx, py + dy - r - 6
            if abs(dx) > 8 or abs(dy) > 8:
                g.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{lx:.1f}" '
                         f'y2="{ly + 8:.1f}" stroke="{D.INK}" '
                         f'stroke-width="1.6" opacity="{t * .45:.2f}"/>')
            g.append(f'<text x="{lx:.1f}" y="{ly:.1f}" '
                     f'text-anchor="middle" font-size="26" font-weight="800" '
                     f'fill="{D.INK}" stroke="#FFFFFF" stroke-width="6" '
                     f'paint-order="stroke" opacity="{t:.2f}">{nm}</text>')
        svg = (f'<svg width="{PARK_W}" height="{PARK_H}" '
               f'viewBox="0 0 {PARK_W} {PARK_H}" style="opacity:{e:.2f}">'
               f'{"".join(g)}</svg>')
        body = (f'<div data-bleed style="position:absolute;left:70px;'
                f'top:218px">{svg}</div>'
                f'<div style="position:absolute;right:84px;top:252px;'
                f'width:400px">'
                f'<div style="font-size:34px;font-weight:800;color:{WIN};'
                f'line-height:1.5">호수를 가운데 두고<br>상권이 둘러쌌습니다'
                f'</div>'
                f'<div style="font-size:27px;color:{D.SUB};line-height:1.6;'
                f'margin-top:22px">원천저수지를 공원으로 바꾸고<br>'
                f'그 둘레에 단지와 상가를 앉혔습니다.</div>'
                f'<div style="font-size:21px;color:{D.SUB};margin-top:26px">'
                f'{OSM.CREDIT}</div></div>')
        return page(body, "셋째, 생활 인프라",
                    '<b>광교호수공원</b>을 중심으로', 1.0)
    return html


# ── 두 번 벌어졌다 (본편 7:14) ──────────────────────────────────────────
# 표로 두면 숫자 열두 개를 눈으로 비교해야 한다. **선 하나로 이으면**
# "오를 때 덜 오르고 내릴 때 더 빠졌다"가 한 번에 읽힌다.
SL_X0, SL_X1 = 560, 1140
SL_Y0, SL_Y1 = 244, 560


def load_split() -> list[dict]:
    from analysis.newtown_charts import same_apt, TOWNS, WINNERS
    c = con()
    out = []
    order = list(WINNERS) + [t for t in TOWNS if t not in WINNERS]
    for t in order:
        up = same_apt(c, town_where(t), 2015, 2021)
        dn = same_apt(c, town_where(t), 2021, 2026)
        if up and dn:
            out.append({"town": t, "up": up[1], "dn": dn[1],
                        "n": min(up[0], dn[0]),
                        "color": WIN if t in WINNERS else LOSE})
    bu = same_apt(c, "1=1", 2015, 2021)
    bd = same_apt(c, "1=1", 2021, 2026)
    out.append({"town": "수도권 전체", "up": bu[1], "dn": bd[1],
                "n": bu[0], "color": GREY})
    return out


def slope_anim(rows: list[dict]):
    ups = [r["up"] for r in rows]
    dns = [r["dn"] for r in rows]
    lo, hi = min(dns + [0]) - 8, max(ups) + 10

    def _y(v: float) -> float:
        return SL_Y1 - (v - lo) / (hi - lo) * (SL_Y1 - SL_Y0)

    def html(p: float) -> str:
        e = ease(min(1.0, p / 0.72))
        g = [f'<line x1="{SL_X0}" y1="{SL_Y0 - 16}" x2="{SL_X0}" '
             f'y2="{SL_Y1 + 16}" stroke="{D.LINE}" stroke-width="2"/>',
             f'<line x1="{SL_X1}" y1="{SL_Y0 - 16}" x2="{SL_X1}" '
             f'y2="{SL_Y1 + 16}" stroke="{D.LINE}" stroke-width="2"/>',
             f'<line x1="{SL_X0 - 40}" y1="{_y(0):.1f}" x2="{SL_X1 + 40}" '
             f'y2="{_y(0):.1f}" stroke="{D.SUB}" stroke-width="2" '
             f'stroke-dasharray="7 7" opacity=".5"/>',
             f'<text x="{SL_X0}" y="{SL_Y0 - 36}" text-anchor="middle" '
             f'font-size="27" font-weight="700" fill="{D.SUB}">'
             f'상승기 2015 → 2021</text>',
             f'<text x="{SL_X1}" y="{SL_Y0 - 36}" text-anchor="middle" '
             f'font-size="27" font-weight="700" fill="{D.SUB}">'
             f'조정기 2021 → 2026</text>']
        # 값이 겹치면 이름표를 아래로 밀어 떼어 놓는다. 다 민 뒤에
        # 바닥(자막 자리)을 넘었으면 **무리째 위로 되올린다** — 아래로만
        # 밀다가 마지막 둘이 자막을 밟았다.
        FLOOR = H - 196 - 16
        STEP = 38.0

        def stack(key):
            order = sorted(rows, key=lambda r: -r[key])
            pos, prev = {}, -1e9
            for r in order:
                y = max(_y(r[key]), prev + STEP)
                pos[r["town"]] = y
                prev = y
            over = prev - FLOOR
            if over > 0:
                for k in pos:
                    pos[k] -= over
            return pos

        ly, ry = stack("up"), stack("dn")
        for r in rows:
            y0, y1 = _y(r["up"]), _y(r["dn"])
            x1e = SL_X0 + (SL_X1 - SL_X0) * e
            y1e = y0 + (y1 - y0) * e
            g.append(f'<line x1="{SL_X0}" y1="{y0:.1f}" x2="{x1e:.1f}" '
                     f'y2="{y1e:.1f}" stroke="{r["color"]}" '
                     f'stroke-width="5" stroke-linecap="round" '
                     f'opacity=".92"/>')
            g.append(f'<circle cx="{SL_X0}" cy="{y0:.1f}" r="9" '
                     f'fill="{r["color"]}" stroke="#FFFFFF" '
                     f'stroke-width="3"/>')
            g.append(f'<text x="{SL_X0 - 24}" y="{ly[r["town"]] + 9:.1f}" '
                     f'text-anchor="end" font-size="26" font-weight="800" '
                     f'fill="{r["color"]}">{r["town"]} '
                     f'+{r["up"]:.0f}%</text>')
            if e > 0.97:
                g.append(f'<circle cx="{SL_X1}" cy="{y1:.1f}" r="9" '
                         f'fill="{r["color"]}" stroke="#FFFFFF" '
                         f'stroke-width="3"/>')
                g.append(f'<text x="{SL_X1 + 24}" '
                         f'y="{ry[r["town"]] + 9:.1f}" font-size="26" '
                         f'font-weight="800" fill="{r["color"]}">'
                         f'{r["dn"]:+.0f}%</text>')
        svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
               f'style="position:absolute;inset:0">{"".join(g)}</svg>')
        return page(svg, "같은 단지 기준 · 30평대 상승률",
                    '<b>두 번</b> 벌어졌습니다', 1.0)
    return html


# ── 신축과 기존은 다른 집 (본편 5:55) ──────────────────────────────────
# 같은 막대 그림을 두 번 쓰고 있었다. 두 번째는 **평당가 차이**가
# 주인공이므로 그림도 달라야 한다.
def newold_card(m: dict):
    def html(p: float) -> str:
        a = ease(min(1.0, p / 0.5))
        b = ease(max(0.0, min(1.0, (p - 0.22) / 0.5)))
        gap = m["new_md"] - m["old_md"]

        def box(lab, v, col, op, sub):
            return (f'<div style="flex:1;border-radius:22px;padding:34px 38px;'
                    f'border:3px solid {D.LINE};background:rgba(0,0,0,.022);'
                    f'opacity:{op:.3f};transform:translateY('
                    f'{(1 - op) * 24:.1f}px)">'
                    f'<div style="display:inline-block;font-size:25px;'
                    f'font-weight:800;color:#FFFFFF;background:{col};'
                    f'padding:7px 16px;border-radius:9px">{lab}</div>'
                    f'<div style="font-size:92px;font-weight:800;color:{col};'
                    f'letter-spacing:-.04em;margin-top:16px">'
                    f'{v:,.0f}<span style="font-size:40px">만원</span></div>'
                    f'<div style="font-size:27px;color:{D.SUB};'
                    f'margin-top:2px">{sub}</div></div>')
        body = (
            f'<div style="position:absolute;left:92px;right:92px;top:270px;'
            f'display:flex;gap:46px;align-items:stretch">'
            f'{box("기존", m["old_md"], GREY, a, "2020년 이전에 지은 집")}'
            f'{box("새 집", m["new_md"], GOLD, b, "2020년 이후에 지은 집")}'
            f'</div>'
            f'<div style="position:absolute;left:92px;right:92px;top:566px;'
            f'text-align:center;font-size:40px;font-weight:800;'
            f'color:{D.INK};opacity:{b:.2f}">평당 '
            f'<span style="color:{LOSE}">{gap:,.0f}만원</span> 차이 · '
            f'<span style="color:{LOSE}">{m["new_md"] / m["old_md"]:.1f}배'
            f'</span></div>')
        return page(body, f'{m["town"]} · {m["year"]}년 30평대 평당가',
                    '<em>다른 집</em>이 섞인 겁니다', 1.0)
    return html
