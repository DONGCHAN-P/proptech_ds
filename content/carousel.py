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
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import cover as CV  # noqa: E402
from content import design as D  # noqa: E402
from content import geo  # noqa: E402
from content import photos  # noqa: E402
from content.validator import validate  # noqa: E402
from templates.disclaimers import DISCLAIMER_SOCIAL  # noqa: E402

MIN_SAMPLE = 10          # 이보다 적으면 큰 숫자 장에 쓰지 않는다
RT_ROWS_MAX, RT_ROWS_MIN = 8, 5   # 순위표 행 수 (지시사항 상한 10)
TILE_MAX, TILE_MIN = 6, 4         # 타일 개수 (2열 × 2~3행)
HEADLINE_MIN = 72        # 넘침 재시도의 하한 (지시사항 9항)
FILL_STEP, FILL_MAX = 0.12, 2.4   # 빈 공간 채우기 반복 폭
HEADLINE_MAX_LINES = 3   # 지시사항 2항
# 콘텐츠와 출처 줄 사이 최소 간격. 0 이면 글자가 겹친다 —
# 안전영역 검사로는 안 잡히는 자리다 (출처는 절대 위치라서).
MIN_FOOT_GAP = 24


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
                    key=lambda r: r["ratio"], reverse=True)[:8]
    # 신고가는 **누적 거래가 두터운** 평형에서 고른다. 지표 JSON 은 편차가
    # 큰 순으로 정렬돼 있어 첫 행이 누적 6건짜리인 경우가 흔한데, 그런
    # "148% 경신"은 시세가 아니라 표본이 만든 숫자다.
    nh = [r for r in (data.get("daily", {}).get("new_high") or [])
          if r.get("history_count", 0) >= MIN_SAMPLE]
    nh.sort(key=lambda r: r["over_peak_pct"], reverse=True)

    # 표지는 5-1항 규칙으로 고른다 — "통계적으로 가장 튄 곳"이 아니라
    # "많은 사람이 아는 곳 중 의미 있는 변화". 고른 이유는 로그로 남긴다.
    picked, top3, notes = CV.choose(data)
    return {"busiest": busiest, "quiet": quiet, "top": top, "ranked": ranked,
            "all_regions": z,
            "new_high": nh[0] if nh else None, "new_highs": nh,
            "cover": picked, "cover_top3": top3, "cover_notes": notes,
            # 표지 소재가 있는 지역의 주간 행. 2~4장이 "그 동네는 어땠나"로
            # 이어지려면 필요하다.
            "cover_region": next(
                (r for r in z if r["sigungu_name"] == picked.region), None)
            if picked else None,
            "params": data.get("params") or {}, "asof": data["asof"]}


# ── 장 ───────────────────────────────────────────────────────────────────
SERIES_COND = "수도권 아파트 · 해제 건 제외"


def cover_copy(c) -> dict:
    """앵글에 맞는 표지 문구. 헤드라인은 질문형·반전형으로 둔다 (5항).

    답(왜 그런지)은 2~3장이 받는다. 표지에서 다 말해 버리면 넘길 이유가 없다.
    """
    d = c.data
    if c.angle == "new_high":
        name, _ = D.split_name(d["apt_name"])
        return {"h1": f'{c.region},<br>종전 최고가가<br>얼마나 깨졌을까요?',
                "h1x": f'{c.region} 종전 최고가가<br>얼마나 깨졌을까요?',
                "pre": "종전 최고 대비",
                "big": D.delta(d["over_peak_pct"], arrow=False),
                "lead": f'{name} {D.pyeong(d["pyeong_bucket"])} · '
                        f'{D.won(d["prev_peak"])} → {D.won(d["deal_amount"])}',
                "cond": f'{SERIES_COND} · 이 평형 누적 {D.num(d["history_count"])}건'}
    if c.angle == "counter":
        name, _ = D.split_name(d["apt_name"])
        return {"h1": f'{c.region}에서<br>값은 올랐는데<br>거래는 줄었어요',
                "h1x": f'{c.region}, 값은 올랐는데<br>거래는 줄었어요',
                "pre": "평단가",
                "big": D.delta(d["change_pct"], arrow=False),
                "lead": f'같은 기간 거래 {d["deals_prior"]}건 → {d["deals_recent"]}건',
                "cond": f'{D.pyeong(d["pyeong_bucket"])} · 최근 90일 vs 직전 90일'}
    return {"h1": f'{c.region} 거래가<br>갑자기 늘었어요.<br>얼마나 늘었을까요?',
            "h1x": f'{c.region} 거래가 갑자기<br>늘었어요. 얼마나요?',
            "pre": "평소의",
            "big": D.times(d["week_deals"], d["deals_avg_52w"]),
            "lead": f'평소 {D.num(d["deals_avg_52w"])}건 → '
                    f'이번 주 {d["week_deals"]}건',
            "cond": f'{SERIES_COND} · {d.get("week_start", "")} 주'}


def c1_cover(t: dict, n: int) -> dict:
    """표지.

    사진이 있으면 `photo_cover`, 없으면 오프화이트 `hero_number` 로 간다
    (5항 폴백). 사진은 라이선스를 통과한 것만 쓴다 — 5-0항은 예외를 두지
    않는다. "일단 쓰고 나중에 확인"은 발행된 뒤에야 문제가 드러난다.
    """
    c = t["cover"]
    cp = cover_copy(c)
    photo, lic_problems = photos.find(CV.resolve(c.region, c.code) or "")
    t.setdefault("photo_problems", []).extend(lic_problems)

    if photo:
        note = ('<div class="pc-note">이미지는 지역 참고용</div>'
                if photo.is_region else "")
        inner = (
            f'<div class="pc">'
            f'<img class="pc-img" src="{photo.data_uri()}" alt="">'
            f'<div class="pc-grad"></div>{note}'
            f'<div class="pc-body">'
            f'<div class="pc-cond">[{cp["cond"]}]</div>'
            f'<div class="pc-h1"><span class="k">{cp["pre"]} {cp["big"]}</span>'
            f'<span class="b">{cp["h1"]}</span></div>'
            f'<div class="pc-ft">{cp["lead"]}<br>'
            f'국토교통부 실거래가 · 해제 건 제외 · {t["asof"]} 기준 · '
            f'{photo.credit}</div>'
            f'</div></div>')
        return {"name": "01_cover", "layout": "photo_cover",
                "facts": cover_facts(c), "photo": str(photo.path),
                "html": D.head(1, n) + inner}

    # 사진이 없으면 지도. 지도도 없으면 오프화이트 (5항 폴백 순서).
    m = map_cover(t, c, cp, n)
    if m:
        return m

    inner = (
        f'<div class="body">'
        f'{D.cond(cp["cond"])}'
        f'<div class="h1 sm">{cp["h1"]}</div>'
        f'<div class="big-pre">{cp["pre"]}</div>'
        f'<div class="big up">{cp["big"]}</div>'
        f'<div class="lead">{cp["lead"]}</div>'
        f'</div>')
    return {"name": "01_cover", "layout": "hero_number", "scope": ("apt" if c.angle in ("new_high", "counter") else "region"),
            "facts": cover_facts(c),
            "html": D.head(1, n) + inner + D.foot(t["asof"])}


MAP_W, MAP_H = 936, 400


def map_cover(t: dict, c, cp: dict, n: int) -> dict | None:
    """지도 표지.

    대형 숫자를 따로 두지 않고 **헤드라인 첫 줄 자리**에 둔다 — `photo_cover`
    가 쓰는 방식이다. 지도가 세로를 많이 먹어서 340px 짜리 숫자까지 넣으면
    둘 다 작아진다.

    칠하는 건 대상 지역 하나뿐이다. 전부 칠하면 어디를 보라는 건지 사라진다.
    """
    if not geo.available():
        return None
    scope = geo.scope_of(CV.resolve(c.region, c.code))
    svg = geo.svg({c.region: D.UP}, width=MAP_W, height=MAP_H,
                  line=D.LINE, fill=geo.mix(D.INK, "#FFFFFF", 0.18),
                  label_color=D.COVER_INK, label_halo=D.INK, scope=scope)
    if not svg:
        return None
    _, approx = geo.geo_name(c.region)
    note = (f" · {c.region}는 행정구역 개편 전 경계로 표시" if approx else "")
    where = {"서울": "서울 25개 구", "인천": "인천", "경기": "경기"}.get(scope, "수도권")
    inner = (
        f'<div class="body">'
        f'{D.cond(cp["cond"], cp["pre"].rstrip(" 의"))}'
        f'<div class="mc-num up">{cp["big"]}</div>'
        f'<div class="mc-h1">{cp["h1x"]}</div>'
        f'<div class="mc-map">{svg}</div>'
        f'<div class="mc-foot">{cp["lead"]} · 지도는 {where}</div>'
        f'</div>')
    return {"name": "01_cover", "layout": "map_cover", "scope": ("apt" if c.angle in ("new_high", "counter") else "region"),
            # 표지만 어둡게. 2장부터는 오프화이트로 돌아간다 (5항) —
            # 일곱 장이 전부 오프화이트면 피드에서 묻힌다.
            "dark": True,
            "facts": cover_facts(c), "approx_boundary": approx,
            "html": D.head(1, n) + inner
                    + D.foot(t["asof"], geo.CREDIT + note)}


def with_label(row: dict) -> dict:
    """평형 라벨을 facts 에 같이 넣는다.

    "25P" → "20평대 후반" 으로 옮기면 화면에 **20** 이라는 숫자가 새로 생긴다.
    원본에 없는 숫자라 T12 검증기가 바로 잡는데, 옳은 동작이다. 라벨도
    발행되는 값이므로 facts 에 남겨 추적 가능하게 만든다 — 검증을 끄는 게
    아니라 출처를 대는 쪽으로 푼다.
    """
    if not row:
        return row
    out = dict(row)
    if row.get("pyeong_bucket"):
        out["pyeong_label"] = D.pyeong(row["pyeong_bucket"])
    return out


def cover_facts(c) -> dict:
    return {"cover": with_label(c.data)}


def c2_ranking(t: dict, n: int, rows_max: int = RT_ROWS_MAX) -> dict:
    """지역 순위표.

    막대 대신 표를 쓰는 이유는 **값을 정확히 읽히게** 하기 위해서다. 배수가
    1.0~1.7 처럼 좁은 범위에 몰려 있으면 막대 길이 차이로는 구별이 안 되는데,
    숫자를 오른쪽 정렬로 세워두면 바로 비교된다.

    강조 행은 하나뿐이다 (5항). 여러 행을 칠하면 "강조"가 아니게 된다.
    """
    rows = t["ranked"][:rows_max]
    # 막대는 표 안에서 서로 비교되게 같은 축을 쓴다. 행마다 최대치를 다시
    # 잡으면 1.7배와 1.2배가 같은 길이로 보인다.
    mx = max(r["ratio"] for r in rows) or 1
    base = 1.0 / mx * 100
    out = []
    for i, r in enumerate(rows, 1):
        thin = (f'<span class="badge">거래 {r["week_deals"]}건</span>'
                if r["week_deals"] < MIN_SAMPLE else "")
        w = r["ratio"] / mx * 100
        over = max(0.0, w - base)
        # 기준선(평소)을 넘은 부분만 의미색. 막대 전체를 칠하면 평소만큼
        # 거래된 것까지 "성과"처럼 보인다 (지시사항 5항).
        bar = (f'<div class="rt-bar">'
               f'<b style="left:0;width:{min(w, base):.1f}%;'
               f'background:{D.NEUTRAL};opacity:.5"></b>'
               + (f'<b style="left:{base:.1f}%;width:{over:.1f}%;'
                  f'background:{D.UP if i == 1 else D.NEUTRAL}"></b>'
                  if over > 0 else "")
               + f'<i style="left:{base:.1f}%"></i></div>')
        out.append(
            f'<div class="rt-row{" hi" if i == 1 else ""}">'
            f'<div class="rt-rank">{i}</div>'
            f'<div class="rt-name">{r["sigungu_name"]}{thin}'
            f'<small>평소 {D.num(r["deals_avg_52w"])}건</small></div>'
            f'{bar}'
            f'<div class="rt-val">{r["week_deals"]}건</div>'
            f'<div class="rt-chg {D.delta_color(r["ratio"] - 1)}">'
            f'{r["ratio"]:.1f}배</div></div>')
    inner = (
        f'<div class="body">'
        f'<div class="rt-eyebrow">RANKING</div>'
        f'{D.cond("수도권 시군구 · 이번 주 · 거래 10건 이상")}'
        f'<div class="h1 sm">평소보다<br>붐빈 지역</div>'
        f'<div class="rt">{"".join(out)}</div>'
        f'<div class="rt-note">평소 = 지난 52주 평균 · 평소 대비 배수 순</div>'
        f'</div>')
    return {"name": "02_ranking", "layout": "ranking_table", "scope": "metro",
            "facts": {"ranked": rows}, "rows_max": rows_max, "rows_min": RT_ROWS_MIN,
            # 표가 안전 영역을 넘으면 렌더러가 행을 줄여 다시 만든다 (9항).
            # 글자를 줄이는 쪽으로 풀면 28px 하한을 깨게 된다.
            "rebuild": lambda k: c2_ranking(t, n, k),
            "html": D.head(2, n) + inner + D.foot(t["asof"])}


def c4_counter(t: dict, n: int) -> dict:
    """반전. 1~3장은 앞 장을 안 봐도 이해되게 쓴다."""
    s = t["top"]
    drop = (s["deals_recent"] / s["deals_prior"] - 1) * 100
    cond = D.cond(f'{s["sigungu_name"]} {s["legal_dong_name"]}',
                  D.pyeong(s["pyeong_bucket"]),
                  f'최근 {t["params"].get("surge_window_days", 90)}일 vs 직전 동기간')
    inner = (
        f'<div class="body">'
        f'<div class="kicker">같이 봐야 할 것</div>'
        f'{cond}'
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
            "facts": {"top": with_label(s), "drop_pct": round(drop, 1)},
            "html": D.head(4, n) + inner + D.foot(t["asof"])}


HEAT_W, HEAT_H = 936, 400


def c3_heat(t: dict, n: int) -> dict:
    """수도권 온도지도.

    순위표(2장)는 위에서 여덟 곳만 보여준다. 거기서 끊으면 "수도권 거래가
    늘었다"로 읽히는데, 같은 주에 평소의 절반만 거래된 곳도 있다. 지도는
    **양쪽을 동시에** 보여준다 — 빨강과 파랑이 한 화면에 같이 있어야
    "동네마다 다르다"가 설명 없이 읽힌다.

    표본이 부족한 곳은 칠하지 않고 비운다. 회색으로 칠해 버리면 "데이터가
    없다"가 "변화가 없다"로 읽힌다.
    """
    z = t["all_regions"]
    vals = {r["sigungu_name"]: r["ratio"] for r in z
            if r.get("ratio") and r["week_deals"] >= MIN_SAMPLE}
    # 지도 위에 이름을 얹지 않는다. 서울 구는 면이 작아 라벨끼리 겹치고,
    # 겹친 글자는 지도까지 가린다. 양 끝은 아래 캡션에서 말한다.
    svg = geo.heat(vals, width=HEAT_W, height=HEAT_H, bg=D.BG,
                   up=D.UP, down=D.DOWN, dim=geo.mix(D.BG, "#000000", 0.03))
    ends = ""
    if vals:
        hi, lo = max(vals, key=vals.get), min(vals, key=vals.get)
        ends = (f'<div class="lead">가장 붐빈 곳 <span class="up">{hi} '
                f'{vals[hi]:.1f}배</span> · 가장 조용한 곳 '
                f'<span class="down">{lo} {vals[lo]:.1f}배</span></div>')
    legend = "".join(f'<i style="background:{c}"></i>'
                     for c, _ in geo.legend_colors(D.BG, D.UP, D.DOWN))
    ticks = geo.BIN_LABELS
    inner = (
        f'<div class="body">'
        f'{D.cond("수도권 시군구 · 이번 주 · 거래 10건 이상")}'
        f'<div class="h1 sm">한 주에도<br>동네마다 달라요</div>'
        f'<div class="heat">{svg}</div>'
        f'{ends}'
        f'<div><div class="heat-legend">{legend}</div>'
        f'<div class="heat-ticks"><span>{ticks[0]}</span>'
        f'<span>{ticks[2]}</span><span>{ticks[-1]}</span></div></div>'
        f'<div class="rt-note">색이 없는 곳은 거래가 적어 판단하지 않았어요 · '
        f'평소 = 지난 52주 평균</div>'
        f'</div>')
    return {"name": "03_heat", "layout": "map_heat", "scope": "metro",
            "facts": {"regions": [
                {"sigungu_name": r["sigungu_name"],
                 "week_deals": r["week_deals"],
                 "deals_avg_52w": r["deals_avg_52w"],
                 "ratio": round(r["ratio"], 2)} for r in z if r.get("ratio")]},
            "html": D.head(3, n) + inner + D.foot(t["asof"], geo.CREDIT)}


def c5_compare(t: dict, n: int) -> dict:
    s = t["top"]
    prior, recent = s["ppy_prior_90d"], s["ppy_recent_90d"]
    mx = max(prior, recent) or 1
    name, paren = D.split_name(s["apt_name"])
    paren_html = (f'<div class="sub" style="font-size:30px">{paren}</div>'
                  if paren else "")
    win = t["params"].get("surge_window_days", 90)
    cond = D.cond(D.pyeong(s["pyeong_bucket"]), f"최근 {win}일 vs 직전 동기간")
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
        f'<div class="kicker">{s["sigungu_name"]} {s["legal_dong_name"]}</div>'
        f'{cond}'
        f'<div class="h1 sm">{name}</div>{paren_html}'
        f'<div class="sub">평당가, 3개월 전과 비교</div>'
        f'<div class="bars">'
        f'{bar("직전 3개월", prior, D.NEUTRAL)}{bar("최근 3개월", recent, D.UP)}'
        f'</div>{sample}</div>')
    return {"name": "05_compare", "layout": "compare_bars",
            "facts": {"top": with_label(s)},
            "html": D.head(5, n) + inner + D.foot(t["asof"])}


def c6_tiles(t: dict, n: int, rows_max: int = TILE_MAX) -> dict | None:
    """신고가 단지 **모음**.

    한 단지만 크게 보여주던 걸 타일로 바꿨다. 표지가 이미 한 단지를 깊게
    다루므로, 여기서 또 한 단지를 크게 쓰면 "이 주의 신고가는 한 곳뿐"처럼
    읽힌다. 실제로는 여러 곳에서 동시에 일어난다.

    표지에 쓴 단지는 뺀다 — 같은 단지를 두 번 보여줄 자리가 아니다.
    """
    cov = (t["cover"].data or {}).get("apt_name")         if t["cover"].angle == "new_high" else None
    rows = [r for r in t.get("new_highs") or [] if r["apt_name"] != cov][:rows_max]
    if len(rows) < 2:
        return None
    tiles = []
    for r in rows:
        name, _ = D.split_name(r["apt_name"], limit=10)
        tiles.append(
            f'<div class="tile">'
            f'<div class="t-nm">{name}</div>'
            f'<div class="t-sub">{r["sigungu_name"]} · '
            f'{D.pyeong(r["pyeong_bucket"])}</div>'
            f'<div class="t-val">{D.won(r["deal_amount"])}</div>'
            f'<div class="t-chg up">{D.delta(r["over_peak_pct"])}</div>'
            f'</div>')
    days = t["params"].get("daily_window_days", 7)
    label = D.cond(f"수도권 아파트 · 최근 {days}일",
                   f"이 평형 누적 {MIN_SAMPLE}건 이상")
    inner = (
        f'<div class="body">'
        f'{label}'
        f'<div class="h1 sm">종전 최고가를<br>넘은 단지들</div>'
        f'<div class="tiles">{"".join(tiles)}</div>'
        f'<div class="rt-note">종전 최고 대비 상승률 순 · 같은 단지·같은 평형 '
        f'기록과 견준 값</div>'
        f'</div>')
    return {"name": "06_tiles", "layout": "tile_grid", "scope": "metro",
            "facts": {"new_highs": [with_label(r) for r in rows]},
            # 타일도 넘치면 글자가 아니라 **개수**를 줄인다 (글자 하한이 있다)
            "rows_max": rows_max, "rows_min": TILE_MIN,
            "rebuild": lambda k: c6_tiles(t, n, k),
            "html": D.head(6, n) + inner + D.foot(t["asof"])}


def c7_outro(t: dict, page: int, n: int) -> dict:
    """정리 — **앞 장들을 순서대로** 되짚는다.

    새 숫자를 쓰지 않는다 (5항). 세 줄이 곧 이 캐러셀의 줄거리라, 여기가
    앞 장과 다른 얘기를 하면 그동안 쌓은 흐름이 마지막에 흩어진다.
    """
    c = t["cover"]
    d = c.data
    if c.angle == "new_high":
        one = f'{c.region} {d["apt_name"]}가 종전 최고가를 넘었어요'
    elif c.angle == "counter":
        one = f'{c.region} {d["apt_name"]}는 값이 올랐는데 거래는 줄었어요'
    else:
        one = f'{c.region} 거래가 평소와 달랐어요'

    r = t.get("cover_region")
    if r and r.get("deals_avg_52w"):
        ratio = r["week_deals"] / r["deals_avg_52w"]
        two = (f'그런데 {c.region} 전체는 '
               + ("평소보다 붐볐어요" if ratio >= 1.1 else
                  "평소보다 조용했어요" if ratio <= 0.9 else "평소와 비슷했어요"))
    else:
        two = f'다만 {c.region} 전체가 그런 건 아니에요'

    inner = (
        f'<div class="body">'
        f'<div class="kicker">정리</div>'
        f'{D.cond("수도권 아파트 · 해제 건 제외")}'
        f'<div class="h1 sm">세 줄 요약</div>'
        f'<div class="lead">'
        f'· {one}<br>'
        f'· {two}<br>'
        f'· 수도권 전체로 보면 동네마다 방향이 달랐어요</div>'
        f'<div class="cta">저장해두고 <span class="mark">다음 주와 비교</span>해보세요.<br>'
        f'여러분 동네는 이번 주 어땠나요?</div>'
        f'<div class="disc">{DISCLAIMER_SOCIAL}</div>'
        f'</div>')
    return {"name": "07_outro", "layout": "summary_cta", "scope": "summary",
            "facts": {"cover": with_label(d)},
            "html": D.head(page, n) + inner}


def c8_follow(t: dict, page: int, n: int) -> dict:
    """마지막 장 — 팔로우 유도.

    여기까지 넘긴 사람은 이미 관심이 있는 사람이다. 그래서 설득하지 않고
    **앞으로 뭘 받게 되는지**만 적는다. "놓치면 후회" 같은 말을 넣는 순간
    일곱 장 동안 지킨 톤이 한 장에서 무너진다 (6항 금지 표현).

    새 숫자를 쓰지 않는다 — 7장과 같은 규칙이다. 숫자가 없으니 여기서
    과장할 거리도 없다.
    """
    url = os.environ.get("NEWSLETTER_URL", "").strip()
    mail = (f'<div class="sub">메일로 받고 싶으면 → {url}</div>' if url else "")
    inner = (
        f'<div class="body">'
        f'<div class="kicker">다음 주에도</div>'
        f'{D.cond("수도권 아파트 · 해제 건 제외")}'
        f'<div class="h1 sm">이런 숫자,<br>매주 받아보실래요?</div>'
        f'<div><span class="fl-handle">{D.HANDLE}</span></div>'
        f'<div class="fl-list">'
        f'<div>평소와 <b>달라진 동네</b>를 매주 한 장으로 정리해요</div>'
        f'<div>그 숫자가 <b>몇 건으로 나왔는지</b> 늘 같이 적어요</div>'
        f'<div>앞으로 <b>오를지 내릴지는 말하지 않아요</b></div>'
        f'</div>'
        f'<div class="cta">팔로우해두면 다음 주에 또 만나요.</div>'
        f'{mail}'
        # 면책은 **전문**을 쓴다. 스레드용 1줄 축약은 500자 제한 때문에
        # 만든 것이고, 이미지에는 그런 제한이 없다. 마지막 장은 사람들이
        # 가장 오래 보고 캡처도 하는 자리라 여기서 줄일 이유가 없다.
        f'<div class="disc">{DISCLAIMER_SOCIAL}</div>'
        f'</div>')
    return {"name": f"{page:02d}_follow", "layout": "follow_cta", "scope": "summary",
            "facts": {}, "html": D.head(page, n) + inner + D.foot(t["asof"])}


def n2_detail(t: dict, n: int) -> dict:
    """2장 — 표지에서 던진 사실을 자세히.

    표지는 "얼마나?"를 묻고 끝낸다. 여기서 답한다. 양쪽 값을 모두 쓰고
    (9항), 그 값이 **몇 건으로 나왔는지**를 같은 장에 붙인다 — 숫자를 먼저
    보여주고 표본을 나중 장으로 미루면 그 사이에 믿어버린다.
    """
    c = t["cover"]
    d = c.data
    if c.angle == "new_high":
        name, _ = D.split_name(d["apt_name"])
        head = (f'{d["sigungu_name"]} {d["legal_dong_name"]} · {name}',
                D.cond(D.pyeong(d["pyeong_bucket"]), d["floor_band"],
                       f'{t["params"]["data_start_year"]}년 이후 기록과 견줌'))
        pre, big = "이번 거래", D.won(d["deal_amount"])
        lead = (f'종전 최고 {D.won(d["prev_peak"])} → '
                f'이번 거래 {D.won(d["deal_amount"])}')
        badge = f'이 평형 누적 거래 {D.num(d["history_count"])}건'
    elif c.angle == "counter":
        name, _ = D.split_name(d["apt_name"])
        head = (f'{d["sigungu_name"]} {d["legal_dong_name"]} · {name}',
                D.cond(D.pyeong(d["pyeong_bucket"]),
                       f'최근 {t["params"]["surge_window_days"]}일 vs 직전 동기간'))
        pre, big = "최근 90일 거래", f'{d["deals_recent"]}건'
        lead = f'직전 {d["deals_prior"]}건 → 최근 {d["deals_recent"]}건'
        badge = f'평단가는 {D.delta(d["change_pct"], arrow=False)} 올랐어요'
    else:
        head = (f'{d["sigungu_name"]}',
                D.cond(f'{d.get("week_start", "")} 주',
                       f'평소 = 지난 {t["params"]["zscore_hist_weeks"]}주 평균'))
        pre, big = "이번 주 거래", f'{d["week_deals"]}건'
        lead = (f'평소 {D.num(d["deals_avg_52w"])}건 → '
                f'이번 주 {d["week_deals"]}건')
        badge = f'평소의 {D.times(d["week_deals"], d["deals_avg_52w"])}예요'
    inner = (
        f'<div class="body">'
        f'<div class="kicker">{head[0]}</div>{head[1]}'
        f'<div class="big-pre">{pre}</div>'
        f'<div class="big sm up">{big}</div>'
        f'<div class="lead">{lead}</div>'
        f'<div><span class="badge">{badge}</span></div>'
        f'</div>')
    return {"name": "02_detail", "layout": "hero_number", "scope": ("apt" if c.angle in ("new_high", "counter") else "region"),
            "facts": {"cover": with_label(d)},
            "html": D.head(2, n) + inner + D.foot(t["asof"])}


def n3_region(t: dict) -> dict | None:
    """3장 — 그 단지가 있는 **동네**는 어땠나.

    단지 하나가 움직였다고 동네가 움직인 건 아니다. 이 장이 없으면 표지의
    한 거래가 그 지역 전체를 대표하는 것처럼 읽힌다.
    """
    r = t.get("cover_region")
    if not r or not r.get("deals_avg_52w"):
        return None
    c = t["cover"]
    ratio = r["week_deals"] / r["deals_avg_52w"]
    word = ("더 붐볐어요" if ratio >= 1.1 else
            "더 조용했어요" if ratio <= 0.9 else "평소와 비슷했어요")
    mx = max(r["week_deals"], r["deals_avg_52w"]) or 1
    cond = D.cond(c.region, f'{r.get("week_start", "")} 주')

    def bar(label, val, color):
        return (f'<div class="bar-row"><div class="bar-top">'
                f'<span class="bar-name">{label}</span>'
                f'<span class="bar-val">{D.num(val)}건</span></div>'
                f'<div class="bar-track"><div class="bar-fill" '
                f'style="width:{val / mx * 100:.0f}%;background:{color}"></div>'
                f'</div></div>')

    inner = (
        f'<div class="body">'
        f'<div class="kicker">그 단지가 있는 동네는</div>'
        f'{cond}'
        f'<div class="h1 sm">{c.region}는<br>{word}</div>'
        f'<div class="bars">'
        f'{bar("평소", r["deals_avg_52w"], D.NEUTRAL)}'
        f'{bar("이번 주", r["week_deals"], D.UP if ratio >= 1 else D.DOWN)}'
        f'</div>'
        f'<div class="sub">단지 하나가 움직여도 동네 전체가 '
        f'같이 움직이는 건 아니에요.</div>'
        f'</div>')
    return {"name": "03_region", "layout": "compare_bars", "scope": "region",
            "facts": {"region": r, "ratio": round(ratio, 2)},
            "html": D.head(3, 0) + inner
                    + D.foot(t["asof"], "평소 = 지난 52주 평균")}


def build_cards(data: dict, chart_dir: Path | None = None) -> list[dict]:
    """chart_dir 은 더 이상 읽지 않는다 — 차트 조각을 카드에 넣지 않는다.
    호출부(테스트 포함)가 넘기고 있어 인자만 남긴다."""
    t = pick(data)
    if t is None:
        return []
    # 신고가 재료가 없으면 6장으로 낸다. 억지로 7장을 채우려고 같은 단지를
    # 세 번 쓰지 않는다 (지시사항 5항: 5~8장, 한 대상 최대 2장).
    # 지시사항 5항 레이아웃 조합:
    #   1 표지 → 2 ranking_table → 3 반전/맥락 → 4~6 혼합 → 7 정리
    # 같은 계열(rows·compare_bars)과 (ranking_table·tile_grid)은 붙이지 않는다.
    # 한 소재를 잡고 **점점 넓혀간다.**
    #
    #   표지(한 사실) → 자세히 → 그 동네는 → 수도권에선 → 같은 주 다른 곳
    #   → 정리 → 팔로우
    #
    # 전에는 장마다 각자의 1등을 뽑아 왔다. 표지는 마포구 신고가, 2장은
    # 포천·안성 순위, 4~5장은 수원 영통동 단지… 한 장씩은 다 맞는 말인데
    # 여덟 장이 서로 남남이라 "그래서 무슨 얘기냐"가 안 남는다.
    cards = [c1_cover(t, 0), n2_detail(t, 0)]
    region = n3_region(t)
    if region:
        cards.append(region)
    cards.append(c3_heat(t, 0))
    # 같은 주 다른 곳 — 단지에서 시작했으면 다른 단지, 지역에서 시작했으면
    # 다른 지역으로 받는다. 소재가 바뀌는 자리는 여기 한 장뿐이다.
    others = (c6_tiles(t, 0) if t["cover"].angle in ("new_high", "counter")
              else c2_ranking(t, 0))
    if others:
        cards.append(others)
    cards += [c7_outro(t, 0, 0), c8_follow(t, 0, 0)]

    # 페이지 번호는 장이 다 정해진 뒤에 매긴다. 중간 장이 빠질 수 있어서
    # 각 함수가 자기 번호를 들고 있으면 1,2,4,5… 가 된다.
    n = len(cards)
    for i, c in enumerate(cards, 1):
        c["html"] = re.sub(r'<div class="hd">.*?</div>', D.head(i, n),
                           c["html"], count=1, flags=re.S)
        c["name"] = f"{i:02d}_{c['name'].split('_', 1)[1]}"
    return [finish(c, t["params"]) for c in cards]


def finish(c: dict, params: dict) -> dict:
    """장 하나를 완성한다 — 브랜드 마크 + facts 포장.

    렌더러가 표·타일을 **다시 만들 때도** 이걸 거쳐야 한다. 처음엔 build 에서만
    해서, 행을 줄여 재생성한 장이 포장 없는 facts 를 들고 나왔다. 그 상태로는
    숫자 검증기가 방법론 상수를 못 찾는다.
    """
    # 브랜드 마크는 한 곳에서 붙인다. 장마다 붙이면 새 장을 만들 때 빠뜨리고,
    # 9항은 "모든 장의 같은 좌표"를 요구한다.
    if 'class="mark-brand' not in c["html"]:
        c["html"] += D.brand_mark()
    # 글에 나오는 방법론 상수(52주, 3개월 등)도 출처가 있어야 한다.
    if "params" not in c["facts"]:
        c["facts"] = {"card": c["facts"], "params": params}
    return c


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
  const PX = %d, W = %d, H = %d, MAXLINE = %d, bad = [];
  document.querySelectorAll('.card .body *, .card .hd, .card .ft').forEach(el => {
    if (!el.textContent.trim() && el.tagName !== 'IMG') return;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    if (r.left < PX - 1 || r.right > W - PX + 1 || r.top < 8 || r.bottom > H - 8)
      bad.push((el.className || el.tagName) + '@box');
    // 글자가 상자 밖으로 흘러넘치는 경우. 상자 자체는 폭 안에 있어서
    // getBoundingClientRect 로는 안 잡힌다 — 큰 숫자에서 실제로 잘렸다.
    if (el.scrollWidth > Math.ceil(el.clientWidth) + 1 && el.clientWidth)
      bad.push((el.className || el.tagName) + '@가로넘침');
  });
  // 헤드라인 최대 3줄 (지시사항 2항)
  document.querySelectorAll('.card .h1, .card .pc-h1').forEach(el => {
    const lh = parseFloat(getComputedStyle(el).lineHeight) || 1;
    const lines = Math.round(el.getBoundingClientRect().height / lh);
    if (lines > MAXLINE) bad.push('headline@' + lines + '줄');
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


def render(cards: list[dict], outdir: Path,
           params: dict | None = None) -> tuple[list[Path], list[str]]:
    """넘치면 줄이고, 비면 키운다.

    두 방향을 다 본다. 넘침만 보면 안전영역은 지키지만 아래가 300px 넘게
    비는 장이 나오고, 그건 지시사항 5항이 실패로 규정한 상태다.
    """
    from playwright.sync_api import sync_playwright

    params = params or {}
    made, problems = [], []
    js = OVERFLOW_JS % (D.PAD_X, D.W, D.H, HEADLINE_MAX_LINES)
    gjs = GEOM_JS % (D.H - D.PAD_BOTTOM + 48)

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for idx, c in enumerate(cards):
            page = br.new_page(viewport={"width": D.W, "height": D.H},
                               device_scale_factor=1)

            def draw(shrink: int, fill: float):
                """(넘침 목록, 기하) — 출처 줄과 겹치는 것도 넘침으로 센다."""
                extra = fill_css(fill)
                if shrink:
                    extra += (f".h1{{font-size:{max(HEADLINE_MIN, 104 - shrink)}px}}"
                              f".big{{font-size:{max(140, 280 - shrink * 3)}px}}"
                              f".quote{{font-size:{max(48, 64 - shrink)}px}}")
                page.set_content(
                    f"<style>{D.base_css()}{extra}</style>"
                    f'<div class="card{" dark" if c.get("dark") else ""}">'
                    f'{c["html"]}</div>', wait_until="load")
                page.wait_for_timeout(120)
                bad, g = page.evaluate(js), page.evaluate(gjs)
                if g and g["gap"] < MIN_FOOT_GAP:
                    bad = list(bad) + [f"출처 줄과 {MIN_FOOT_GAP - g['gap']:.0f}px 겹침"]
                return bad, g

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

            # ③ 표는 글자를 줄이는 대신 **행을 줄인다** (9항).
            #    28px 하한이 따로 있어서 글자로는 못 푼다.
            while over and c.get("rebuild") and c["rows_max"] > c["rows_min"]:
                # 다시 만든 장은 **원래 이름과 머리말**을 들고 온다. 장 번호는
                # build_cards 가 마지막에 매기므로, 그대로 두면 5장이 다시
                # "06_tiles · 6/7" 로 돌아간다.
                nm, hd = c["name"], re.search(
                    r'<div class="hd">.*?</div>', c["html"], re.S).group(0)
                c = finish(dict(c, **c["rebuild"](c["rows_max"] - 1)), params)
                c["name"] = nm
                c["html"] = re.sub(r'<div class="hd">.*?</div>', hd,
                                   c["html"], count=1, flags=re.S)
                cards[idx] = c
                fill, shrink = 1.0, 0
                over, geo = draw(shrink, fill)

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

    # 표지 후보 3개와 선정 이유를 남긴다 (5-1항). 성과와 대조해 규칙을
    # 고칠 때 "그때 왜 이걸 골랐지"를 되짚을 수 있어야 한다.
    t = pick(data)
    CV.log(data["asof"], t["cover"], t["cover_top3"], t["cover_notes"])
    if t.get("photo_problems"):
        print()
        print("  사진 라이선스 문제 — 그 사진은 쓰지 않았다:")
        for w in t["photo_problems"]:
            print(f"    ! {w}")

    made, problems = render(cards, outdir, t["params"])
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
