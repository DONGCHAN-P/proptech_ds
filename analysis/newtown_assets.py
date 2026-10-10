"""신도시 1편 — 대본의 '직접 구할 자료'를 우리가 만든 것으로 대체한다.

사진은 못 만들지만 **도식·지도·인용 카드**는 만들 수 있다. 그리고 그 편이
낫다. 차트와 같은 색·같은 글꼴이라 화면이 끊기지 않고, 저작권이 깨끗하다.

특히 뉴스 캡처는 만들지 않고 **인용 카드**로 바꿨다. 기사 화면을 통째로
띄우는 건 전재에 가깝지만, 제목·매체·날짜만 옮겨 적는 건 인용이다. 보기에도
더 정리돼 보인다.

실행:  python analysis/newtown_assets.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis.newtown_charts import (GOLD, GREY, LOSE, OUT, W, WIN,  # noqa
                                     css, page, render)
from content import design as D  # noqa: E402
from content import geo as G  # noqa: E402

# ── 인용 카드에 쓰는 기사. 제목·매체·날짜는 웹에서 확인한 그대로다. ──────
DONGTAN_NEWS = [
    ("동탄2신도시 위기감 고조…미분양 급증에 할인분양까지",
     "뉴데일리경제", "2016.02.02"),
    ("'청약경쟁률 100대1' 동탄2에 미분양 경보라니",
     "비즈워치", "2017.03.03"),
    ("미분양 쌓인 동탄2신도시 또다시 분양… 공급 폭탄 터지나",
     "경기일보", "2017.03.26"),
    ("동탄2 아파트 분양 봇물…'미분양 무덤' 되나",
     "뉴스핌", "2017.11.10"),
]

CHANGNEUNG_NEWS = [
    ("\"3기 신도시 반대\"…일산·운정·검단 신도시 주민들 집회",
     "서울신문", "2019.05.12"),
    ("\"3기 신도시 지정 철회하라\"… 일산·파주 주민 첫 반대 집회",
     "한국일보", "2019.05.12"),
    ("더 높아진 '3기 신도시 반대 함성'",
     "서울신문", "2019.05.19"),
]

# 신분당선 — 2016년 광교 연장 뒤 기준. 가운데 역 일부는 생략했다.
SHINBUNDANG = ["강남", "양재", "판교", "정자", "수지구청", "광교중앙", "광교"]

# 반도체 일자리. 대략적 위치다 (도식용).
FABS = [
    {"label": "삼성 기흥", "lat": 37.2300, "lng": 127.0770},
    {"label": "삼성 화성", "lat": 37.2070, "lng": 127.0530},
    {"label": "삼성 평택", "lat": 36.9930, "lng": 127.1030},
    {"label": "SK 이천", "lat": 37.2690, "lng": 127.4440},
    {"label": "SK 용인 원삼", "lat": 37.1550, "lng": 127.3330},
    {"label": "용인 이동 국가산단", "lat": 37.1180, "lng": 127.1680},
]

# 3기 신도시. 대본에서 다루는 네 곳 + 나머지.
GEN3 = [
    {"label": "고양 창릉", "lat": 37.6480, "lng": 126.8700, "pick": True},
    {"label": "남양주 왕숙", "lat": 37.6230, "lng": 127.1550, "pick": True},
    {"label": "하남 교산", "lat": 37.5150, "lng": 127.2110, "pick": True},
    {"label": "용인 이동", "lat": 37.1180, "lng": 127.1680, "pick": True},
    {"label": "인천 계양", "lat": 37.5420, "lng": 126.7400},
    {"label": "부천 대장", "lat": 37.5330, "lng": 126.7700},
    {"label": "광명 시흥", "lat": 37.4300, "lng": 126.8600},
]

GEN2 = [
    {"label": "광교", "lat": 37.2860, "lng": 127.0530, "win": True},
    {"label": "동탄", "lat": 37.2010, "lng": 127.1050, "win": True},
    {"label": "검단", "lat": 37.6060, "lng": 126.6650},
    {"label": "김포한강", "lat": 37.6430, "lng": 126.6680},
    {"label": "운정", "lat": 37.7250, "lng": 126.7500},
    {"label": "옥정", "lat": 37.8220, "lng": 127.0620},
]

GANGNAM = {"lat": 37.4979, "lng": 127.0276}


def news_card(name: str, kick: str, ttl: str, items, note: str):
    rows = []
    for title, outlet, date in items:
        rows.append(
            f'<div style="border-left:7px solid {LOSE};padding:4px 0 4px 30px;'
            f'margin-bottom:30px">'
            f'<div style="font-size:42px;font-weight:800;line-height:1.3;'
            f'letter-spacing:-.02em">{title}</div>'
            f'<div style="font-size:27px;color:{D.SUB};margin-top:11px">'
            f'{outlet} · {date}</div></div>')
    return name, page(kick, ttl, "".join(rows), note)


def line_map() -> tuple[str, str]:
    """신분당선 도식. 역 이름과 개통 연도만."""
    n = len(SHINBUNDANG)
    w, h = 1700, 300
    pad = 90
    step = (w - pad * 2) / (n - 1)
    parts = [f'<line x1="{pad}" y1="150" x2="{w - pad}" y2="150" '
             f'stroke="#A2C4A0" stroke-width="12" stroke-linecap="round"/>']
    for i, st in enumerate(SHINBUNDANG):
        x = pad + step * i
        end = i in (0, n - 1)
        r, fillc = (22, WIN) if end else (14, "#FFFFFF")
        parts.append(f'<circle cx="{x:.0f}" cy="150" r="{r}" fill="{fillc}" '
                     f'stroke="{WIN if end else "#7FAE7C"}" stroke-width="6"/>')
        parts.append(
            f'<text x="{x:.0f}" y="{95 if i % 2 == 0 else 232}" '
            f'text-anchor="middle" font-size="{34 if end else 29}" '
            f'font-weight="{800 if end else 600}" '
            f'fill="{D.INK if end else D.SUB}">{st}</text>')
    svg = f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">' \
          f'{"".join(parts)}</svg>'
    body = (f'<div style="margin-top:60px">{svg}</div>'
            f'<div style="font-size:34px;color:{D.SUB};margin-top:46px;'
            f'text-align:center">2016년 1월 광교 연장 개통 · '
            f'가운데 일부 역은 생략했습니다</div>')
    return "A2_shinbundang", page(
        "신분당선", '<b>강남</b>에서 <b>광교</b>까지 한 번에 이어졌습니다',
        body, "역 순서는 실제 노선 기준 · 소요시간은 내레이션 참고")


def fab_map() -> tuple[str, str]:
    """동탄 주변 반도체 일자리."""
    pins = [{"label": "동탄", "lat": 37.2010, "lng": 127.1050,
             "primary": True}]
    pins += [dict(f) for f in FABS]
    hl = {"화성동탄구": G.mix(D.BG, WIN, 0.5),
          "용인처인구": G.mix(D.BG, GOLD, 0.35),
          "평택시": G.mix(D.BG, GOLD, 0.35),
          "이천시": G.mix(D.BG, GOLD, 0.35),
          "용인기흥구": G.mix(D.BG, GOLD, 0.35)}
    svg = G.svg(hl, width=1180, height=638, line=D.SUB, fill=D.NEUTRAL,
                label_color=D.INK, label_halo="#FFFFFF", pins=pins,
                show_labels=False) or ""
    side = (f'<div class="cap">동탄에서 출퇴근권</div>'
            f'<div style="font-size:31px;font-weight:700;line-height:1.85">'
            + "<br>".join(f["label"] for f in FABS) +
            f'</div><div style="font-size:26px;color:{D.SUB};margin-top:34px;'
            f'line-height:1.6">파란 점이 동탄입니다.<br>'
            f'반도체 공장이 <b style="color:{GOLD}">남쪽으로</b> 줄지어 '
            f'있습니다.</div>')
    body = (f'<div class="two"><div style="flex:3">{svg}</div>'
            f'<div style="flex:1">{side}</div></div>')
    return "A5_fabs", page(
        "동탄 주변 반도체 일자리",
        '광교에 없던 것이 동탄에는 <b>있었습니다</b>',
        body, "경계: 통계청 SGIS · 점은 대략적 위치입니다")


def gen23_map() -> tuple[str, str]:
    """2기와 3기를 한 장에. '같은 자리에서 반복되는가'."""
    pins = [dict(GANGNAM, label="강남", primary=True)]
    for g in GEN2:
        pins.append({"label": g["label"], "lat": g["lat"], "lng": g["lng"]})
    # 대본에서 다루는 네 곳만 이름을 단다. 계양·대장·광명시흥은 이번
    # 기준에서 뺀 곳이라, 라벨까지 달면 남쪽이 글자로 덮인다.
    for g in GEN3:
        if g.get("pick"):
            pins.append({"label": "▲ " + g["label"], "lat": g["lat"],
                         "lng": g["lng"]})
    hl = {"수원영통구": G.mix(D.BG, WIN, 0.45),
          "화성동탄구": G.mix(D.BG, WIN, 0.45),
          "검단구": G.mix(D.BG, LOSE, 0.45),
          "김포시": G.mix(D.BG, LOSE, 0.45),
          "파주시": G.mix(D.BG, LOSE, 0.45),
          "양주시": G.mix(D.BG, LOSE, 0.45),
          "고양덕양구": G.mix(D.BG, GOLD, 0.4),
          "인천계양구": G.mix(D.BG, D.NEUTRAL, 0.0),
          "남양주시": G.mix(D.BG, GOLD, 0.4),
          "하남시": G.mix(D.BG, GOLD, 0.4),
          "용인처인구": G.mix(D.BG, GOLD, 0.4)}
    svg = G.svg(hl, width=1180, height=638, line=D.SUB, fill=D.NEUTRAL,
                label_color=D.INK, label_halo="#FFFFFF", pins=pins,
                show_labels=False) or ""
    side = (
        f'<div class="cap">2기 · 오늘 본 곳</div>'
        f'<div style="font-size:29px;font-weight:700;color:{WIN};'
        f'line-height:1.7">광교 · 동탄</div>'
        f'<div style="font-size:29px;font-weight:700;color:{LOSE};'
        f'line-height:1.7">검단 · 김포한강<br>운정 · 옥정</div>'
        f'<div class="cap" style="margin-top:32px">3기 · 다음 편 후보</div>'
        f'<div style="font-size:29px;font-weight:700;color:{GOLD};'
        f'line-height:1.7">▲ 하남 교산<br>▲ 고양 창릉<br>'
        f'▲ 남양주 왕숙<br>▲ 용인 이동</div>'
        f'<div style="font-size:25px;color:{D.SUB};margin-top:30px;'
        f'line-height:1.6">창릉은 운정 바로 아래,<br>'
        f'교산은 강남 바로 옆입니다.</div>'
        f'<div style="font-size:23px;color:{D.SUB};margin-top:16px">'
        f'인천 계양·부천 대장·광명 시흥은 이번 기준에서 뺐습니다.</div>')
    body = (f'<div class="two"><div style="flex:3">{svg}</div>'
            f'<div style="flex:1">{side}</div></div>')
    return "A7_gen2_gen3", page(
        "2기와 3기를 한 장에",
        '같은 자리에서 <em>반복될까요</em>',
        body, "경계: 통계청 SGIS · 점은 대략적 위치 · ▲ 가 3기입니다")


def woncheon() -> tuple[str, str]:
    """자료 1 대체 — 원천유원지가 있던 자리.

    옛 사진은 상업적 이용이 가능한 것을 찾지 못했다. 사진 대신 '그 자리에
    무엇이 있었고 지금 무엇이 있는가'를 글자와 지도로 보여 준다.
    """
    hl = {"수원영통구": G.mix(D.BG, WIN, 0.5)}
    svg = G.svg(hl, width=880, height=600, line=D.SUB, fill=D.NEUTRAL,
                label_color=D.INK, label_halo="#FFFFFF",
                pins=[{"label": "광교", "lat": 37.2860, "lng": 127.0530,
                       "primary": True},
                      dict(GANGNAM, label="강남")],
                show_labels=False) or ""
    right = (
        f'<div style="font-size:30px;color:{D.SUB};font-weight:700">'
        f'~ 2008년</div>'
        f'<div style="font-size:64px;font-weight:800;letter-spacing:-.03em;'
        f'margin-top:10px">원천유원지</div>'
        f'<div style="font-size:30px;color:{D.SUB};line-height:1.6;'
        f'margin-top:14px">1977년 국민관광유원지 지정<br>'
        f'호수 둘레에 놀이시설과 식당</div>'
        f'<div style="height:2px;background:{D.LINE};margin:40px 0"></div>'
        f'<div style="font-size:30px;color:{D.SUB};font-weight:700">'
        f'2011년 ~</div>'
        f'<div style="font-size:64px;font-weight:800;letter-spacing:-.03em;'
        f'margin-top:10px;color:{WIN}">광교신도시</div>'
        f'<div style="font-size:30px;color:{D.SUB};line-height:1.6;'
        f'margin-top:14px">같은 호수가 광교호수공원이 되었습니다</div>')
    body = (f'<div class="two"><div style="flex:2">{svg}</div>'
            f'<div style="flex:3;padding-top:30px">{right}</div></div>')
    return "A1_woncheon", page(
        "광교가 들어서기 전",
        '여기엔 <b>유원지</b>가 있었습니다',
        body, "옛 사진은 상업적 이용이 가능한 자료를 찾지 못해 도식으로 "
              "대체했습니다")


def main() -> int:
    pages = [
        woncheon(),
        line_map(),
        news_card("A4_dongtan_news", "2016 ~ 2017년 보도",
                  '그때는 <em>미분양</em>이 문제였습니다',
                  DONGTAN_NEWS,
                  "기사 제목·매체·날짜만 인용했습니다"),
        fab_map(),
        news_card("A6_changneung_news", "2019년 5월 · 창릉 발표 직후",
                  '옆에 신도시가 생긴다고 하자 <em>집회</em>가 열렸습니다',
                  CHANGNEUNG_NEWS,
                  "기사 제목·매체·날짜만 인용했습니다"),
        gen23_map(),
    ]
    made = render(pages, OUT)
    print(f"  저장: {OUT}")
    for p in made:
        print(f"    {p.name}  {p.stat().st_size / 1024:.0f}KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
