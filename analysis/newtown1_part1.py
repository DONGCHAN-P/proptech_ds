"""신도시 1편 **앞 1분** — 기법을 시험해 보는 짧은 판.

전체 12분을 매번 다시 돌리면 한 장면 고치는 데 10분이 든다. 앞 1분만
따로 뽑아 방향을 잡고, 정해지면 본편에 옮긴다.

본편과 다른 점
    · 「기준이 한 번 무너집니다」 토막을 뺐다 (문맥상 겉돈다)
    · 훅의 숫자를 **단지 이름이 붙은 실거래가**로 바꿨다
    · 대장 단지 꺾은선을 2010년부터 **자라나게** 그린다
    · 영통과 1기 신도시를 지도로 보여 준다 (점이 하나씩 찍힌다)
    · 「큰 변화 두 번」 뒤에 급변하는 배경을 깔았다

실행:
  python analysis/newtown1_part1.py
  python analysis/newtown1_part1.py --plan
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis.newtown import con  # noqa: E402
from content import design as D  # noqa: E402
from content import emoji as EM  # noqa: E402
from content import frame as FR  # noqa: E402
from content import geo as G  # noqa: E402
from content import longvideo as LV  # noqa: E402
from metrics.filters import trades_cte  # noqa: E402

TRADE = (ROOT / "master" / "trade_events.parquet").as_posix()
ART = ROOT / "output" / "longform" / "part1"
OUT = ROOT / "output" / "longform" / "newtown1_part1.mp4"

W, H = FR.CONTENT_W, FR.CONTENT_H
WIN, LOSE, GREY = "#2F6FED", "#E5484D", "#9AA0A6"

CHAPTERS = ["여는 말", "영통", "광교", "동탄", "반례", "착시",
            "원인", "다시 재기", "시점", "같은 동탄", "결론",
            "한계", "질문", "후보", "예고"]

# 대장 단지 — 30평대 거래가 20건 이상인 곳 중 **최고 실거래가**가 가장
# 높았던 단지. 이름을 부르지 않으면 "18억"이 어느 집 이야기인지 모른다.
FLAGS = [
    ("광교", "자연앤힐스테이트", WIN),
    ("동탄2", "더샵센트럴시티", LOSE),
]

_cards: dict[str, tuple] = {}
_n = 0
_chap = CHAPTERS[0]


def card(kind: str, **kw) -> str:
    global _n
    _n += 1
    name = f"p{_n:03d}"
    _cards[name] = (kind, kw)
    return f"cards/{name}"


def B(visual: str, text: str = "", motion: str = "in",
      section: bool = False, hold: float = 0.0) -> LV.Beat:
    return LV.Beat(visual=visual, text=text, motion=motion,
                   section=section, hold=hold, chapter=_chap)


def CH(name: str) -> None:
    global _chap
    assert name in CHAPTERS, name
    _chap = name


# ── 데이터 ───────────────────────────────────────────────────────────────
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
    peak_y = max(rows, key=lambda r: r[3])[0]
    return {"name": apt,
            "series": [(r[0], r[2] / 10000) for r in rows],
            "first_y": rows[0][0],
            "first": rows[0][2] / 10000,
            "peak": peak / 10000, "peak_y": peak_y}


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
.pg{{padding:0;}}
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
.p1s{{position:absolute;right:96px;top:290px;width:430px;}}
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
    return f'<div class="pg{" dark" if dark else ""}">{hd}{body}</div>'


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
PX0, PX1 = 182, 1225          # 그림판 가로 (오른쪽은 이름표 자리)
PY0, PY1 = 214, 672           # 세로 (아래가 0원)
Y0, Y1 = 2010, 2026
VMAX = 24.0                   # 억


def _x(y: float) -> float:
    return PX0 + (y - Y0) / (Y1 - Y0) * (PX1 - PX0)


def _y(v: float) -> float:
    return PY1 - min(v, VMAX) / VMAX * (PY1 - PY0)


def _upto(series: list[tuple[int, float]], yc: float):
    """커서 연도까지의 점들. 마지막 한 칸은 사이값으로 끊는다."""
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
        tips.sort(key=lambda t: t[2])
        for k, (f, tx, ty, lv) in enumerate(tips):
            col = f["color"]
            g.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="19" '
                     f'fill="{col}" opacity=".18"/>')
            g.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="10" '
                     f'fill="{col}" stroke="#FFFFFF" stroke-width="4"/>')
            off = -34 if k == 0 else 48
            g.append(f'<text x="{tx + 26:.1f}" y="{ty + off:.1f}" '
                     f'font-size="30" font-weight="800" fill="{col}">'
                     f'{f["town"]} {f["name"]}</text>')
            g.append(f'<text x="{tx + 26:.1f}" y="{ty + off + 36:.1f}" '
                     f'font-size="34" font-weight="800" fill="{col}">'
                     f'{lv:.1f}억</text>')
        svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
               f'style="position:absolute;inset:0">{"".join(g)}</svg>')
        return page(svg, "대장 단지 30평대 · 연도별 중위 실거래가",
                    '같은 출발선에서 <b>이렇게</b> 벌어졌습니다', 1.0)
    return html


# ── ③ 지도 ───────────────────────────────────────────────────────────────
MAP_W, MAP_H = 1120, 606
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
        body = (f'<div style="position:absolute;left:52px;top:224px;'
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
        body = (f'<div style="position:absolute;left:52px;top:224px">'
                f'{_map(hl, pins)}</div>'
                f'<div class="p1s">'
                f'<div style="font-size:30px;font-weight:700;color:{D.SUB};'
                f'margin-bottom:14px">1기 신도시 다섯 곳</div>'
                f'{_side(rows)}'
                f'<div style="font-size:26px;color:{D.SUB};line-height:1.6;'
                f'margin-top:26px">영통은 여기 들어가지 않습니다.</div>'
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


# ── 대본 ─────────────────────────────────────────────────────────────────
def beats(flags: list[dict]) -> list[LV.Beat]:
    b: list[LV.Beat] = []
    g, d = flags[0], flags[1]

    b.append(B(card("emoji", dark=True, icon="생각",
                    big='"거기 누가 사냐"'),
               '분양할 때 "거기 누가 사냐"는 말을 듣던 동네가 있습니다.',
               "still", section=True, hold=1.2))
    b.append(B(card("custom", html=flags_card(flags)),
               f"지금 그 동네 대장 단지는 {g['peak']:.0f}억이 넘습니다. "
               f"광교 {g['name']}, {g['first_y']}년 입주 첫해에 "
               f"{g['first']:.1f}억이던 집입니다. 동탄2 {d['name']}도 "
               f"{d['first_y']}년 {d['first']:.0f}억에서 "
               f"{d['peak']:.1f}억이 됐습니다.", "still"))
    b.append(B(card("custom", html=line_anim(flags), anim=True),
               "같은 말을 듣고 출발했는데, 저는 그 갈림길을 두 번 "
               "바로 옆에서 지켜봤습니다.", "still"))
    b.append(B(card("title", sec="신도시 시리즈 · 1편",
                    big="지나간 신도시로<br><b>다음을 고르는 법</b>"),
               "안녕하세요. 오늘은 지나간 신도시를 데이터로 되짚어서, "
               "앞으로 어디가 오를지 판단하는 기준을 세워보겠습니다.",
               "still"))

    CH("영통")
    b.append(B(card("title", sec="01", big="영통에서 본<br>두 번의 변화"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("custom", html=yeongtong_map(), anim=True),
               "저는 수원 영통에서 오래 살았습니다. 영통은 90년대 후반에 "
               "조성된 택지지구입니다.", "still"))
    b.append(B(card("custom", html=gen1_map(), anim=True),
               "1기 신도시는 아니고요, 분당·일산·평촌·산본·중동 다섯 곳이 "
               "1기입니다.", "still"))
    b.append(B(card("custom", html=surge_card(), anim=True),
               "학군과 상권이 일찍 자리 잡은 동네였고, 여기 살면서 큰 "
               "변화를 두 번 겪었습니다.", "still"))
    return b


def main() -> int:
    ap = argparse.ArgumentParser(description="신도시 1편 앞 1분")
    ap.add_argument("--plan", action="store_true")
    a = ap.parse_args()

    flags = load_flags()
    bs = beats(flags)
    total = sum(x.measure() for x in bs)
    bar = "=" * 62
    print(f"\n{bar}\n  앞 1분  장면 {len(bs)}개 · "
          f"{int(total // 60)}분 {int(total % 60)}초\n{bar}")
    for f in flags:
        print(f"  {f['town']:5} {f['name']:14} "
              f"{f['first_y']}년 {f['first']:5.2f}억 → "
              f"{f['peak_y']}년 최고 {f['peak']:5.2f}억")
    if a.plan:
        return 0

    # 장 수는 장면 길이가 정한다. 손으로 박아 두면 한 장이 1.9프레임처럼
    # 어중간하게 걸려 재생이 끊기는 것처럼 보인다.
    LV.fit_anim(bs, _cards)
    print(f"\n  카드 {len(_cards)}장 만드는 중...")
    frames = LV.build_cards(_cards, ART / "cards", css=css())
    chrome = FR.build(CHAPTERS, ART / "frames", ep="신도시 시리즈 · ",
                      source="국토교통부 실거래가 · 해제 건 제외")
    print("  자막 띠...")
    subs = LV.build_subs(bs, ART / "subs")
    print("  영상...")
    out = LV.render(bs, ART, OUT, chrome, subs, frames)
    LV.write_srt(bs, OUT.with_suffix(".srt"))
    print(f"\n  영상  {out}  ({out.stat().st_size / 1e6:.0f}MB)\n{bar}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
