"""T16 — 인스타 캐러셀 + 유튜브 썸네일.

한글 문구를 이미지에 얹어야 해서 HTML/CSS 로 조판하고 크로미움으로 찍는다.
matplotlib 으로 글자를 그리면 줄바꿈·자간·굵기 통제가 어렵다.

**실사풍 건물·아파트 이미지는 만들지 않는다.** 생성 이미지를 쓰면 보는 사람이
실제 그 단지로 오인한다. 배경은 차트이거나 추상 도형이다 (로드맵 규칙).

입력은 T9 지표 JSON 과 T11 차트 PNG. 글의 숫자는 T12 검증기를 통과한다 —
이미지에 박힌 숫자도 발행되는 숫자다.

실행:
  .venv\\Scripts\\python.exe -m content.carousel
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content.validator import validate  # noqa: E402
from templates.disclaimers import DISCLAIMER_SOCIAL, SOURCE_NOTE  # noqa: E402

CARD = 1080                 # 인스타 1:1
THUMB_W, THUMB_H = 1280, 720  # 유튜브 16:9

# T11 과 같은 팔레트. 발산 축은 한국 관례(상승 빨강 / 하락 파랑).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#898781"
LINE = "#e1e0d9"
POS = "#e34948"
NEG = "#2a78d6"
ACCENT = "#2a78d6"

FONT_STACK = "'Pretendard','Malgun Gothic','맑은 고딕',sans-serif"


def won(man) -> str:
    if man is None:
        return "-"
    man = float(man)
    if abs(man) >= 10000:
        v = man / 10000
        return f"{v:.0f}억" if abs(v) >= 100 else f"{v:.1f}억"
    return f"{man:,.0f}만"


def num(v) -> str:
    if v is None:
        return "-"
    f = float(v)
    return f"{f:,.0f}" if f == int(f) else f"{f:,.1f}"


def _img_uri(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


# ── 카드 조판 ────────────────────────────────────────────────────────────
_CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:{FONT_STACK}; background:{SURFACE}; color:{INK};
        -webkit-font-smoothing:antialiased; }}
/* 내용을 수직 가운데로 모은다. margin-top:auto 로 본문만 바닥에 붙이면
   제목과 본문 사이가 휑하게 빈다. 아래 여백은 푸터 자리로 크게 둔다. */
.card {{ width:{CARD}px; height:{CARD}px; padding:84px 76px 164px;
         display:flex; flex-direction:column; justify-content:center;
         position:relative; }}
.kicker {{ font-size:30px; color:{INK_MUTED}; letter-spacing:-.4px; }}
.title {{ font-size:72px; font-weight:800; line-height:1.18;
          letter-spacing:-2.2px; margin-top:18px; }}
.title .hl {{ color:{ACCENT}; }}
.body {{ margin-top:44px; }}
.rows {{ display:flex; flex-direction:column; gap:26px; }}
.row {{ display:flex; align-items:baseline; justify-content:space-between;
        border-bottom:2px solid {LINE}; padding-bottom:20px; }}
.row .k {{ font-size:34px; color:{INK_2}; }}
.row .v {{ font-size:50px; font-weight:800; letter-spacing:-1.2px; }}
.big {{ font-size:148px; font-weight:800; letter-spacing:-5px; line-height:1; }}
.big.pos {{ color:{POS}; }} .big.neg {{ color:{NEG}; }}
.note {{ font-size:27px; color:{INK_2}; line-height:1.6; margin-top:34px; }}
.foot {{ position:absolute; left:76px; right:76px; bottom:52px;
         font-size:21px; color:{INK_MUTED}; line-height:1.5; }}
.pill {{ display:inline-block; font-size:24px; padding:10px 22px;
         border-radius:999px; background:#f0efec; color:{INK_2}; }}
.chart {{ width:100%; border-radius:18px; border:1px solid {LINE};
          margin-top:30px; }}
.disc {{ font-size:19px; color:{INK_MUTED}; line-height:1.55; }}
.idx {{ position:absolute; top:60px; right:76px; font-size:24px;
        color:{INK_MUTED}; }}
"""


def _card(inner: str, idx: str = "", foot: str = "") -> str:
    foot_html = f'<div class="foot">{foot}</div>' if foot else ""
    idx_html = f'<div class="idx">{idx}</div>' if idx else ""
    return f'<div class="card">{idx_html}{inner}{foot_html}</div>'


def build_cards(data: dict, chart_dir: Path) -> list[dict]:
    """캐러셀 5~8장. 각 장의 숫자는 facts 에 담아 검증한다."""
    p = data.get("params") or {}
    z = data.get("weekly", {}).get("sgg_zscore") or []
    surge = data.get("weekly", {}).get("surge_apt") or []
    nh = data.get("daily", {}).get("new_high") or []
    if not z or not surge:
        return []

    busiest = max(z, key=lambda r: r["deals_z"])
    quiet = min(z, key=lambda r: r["deals_z"])
    top = surge[0]
    cards: list[dict] = []
    n_total = 6
    src = f"{SOURCE_NOTE} · {data['asof']} 기준"

    # 1 표지
    cards.append({
        "name": "01_cover",
        "facts": {"busiest": busiest, "top": top},
        "html": _card(
            f'<div class="kicker">{busiest.get("week_start","")} 주 · 수도권 실거래</div>'
            f'<div class="title">이번 주<br><span class="hl">{busiest["sigungu_name"]}</span>의 '
            f'거래가<br>평소보다 많았습니다</div>'
            f'<div class="body"><div class="note">'
            f'거래량 {busiest["week_deals"]}건 · 평소 {num(busiest["deals_avg_52w"])}건<br>'
            f'같은 주, 지역마다 방향은 갈렸습니다.</div></div>',
            foot=src),
    })

    # 2 지역 비교 — 차트
    chart = chart_dir / "chart_region_zscore.png"
    cards.append({
        "name": "02_region",
        "facts": {"busiest": busiest, "quiet": quiet, "params": p},
        "html": _card(
            f'<div class="kicker">지역별 거래량</div>'
            f'<div class="title">지역끼리 비교하지<br>않았습니다</div>'
            f'<div class="note">강남과 가평은 규모가 달라 나란히 두면 의미가 없습니다. '
            f'각 지역의 지난 {p.get("zscore_hist_weeks")}주 평균과 견줬습니다.</div>'
            + (f'<img class="chart" src="{_img_uri(chart)}">' if chart.exists() else ""),
            idx=f"2 / {n_total}", foot=src),
    })

    # 3 가장 많이 늘어난 곳
    cards.append({
        "name": "03_busiest",
        "facts": {"busiest": busiest},
        "html": _card(
            f'<div class="kicker">{busiest["sigungu_name"]}</div>'
            f'<div class="title">평소보다<br>이만큼</div>'
            f'<div class="body">'
            f'<div class="big pos">{busiest["deals_z"]:+.1f}σ</div>'
            f'<div class="rows" style="margin-top:44px">'
            f'<div class="row"><span class="k">이번 주</span>'
            f'<span class="v">{busiest["week_deals"]}건</span></div>'
            f'<div class="row"><span class="k">평소</span>'
            f'<span class="v">{num(busiest["deals_avg_52w"])}건</span></div>'
            f'</div></div>',
            idx=f"3 / {n_total}", foot=src),
    })

    # 4 급등 단지
    cards.append({
        "name": "04_apt",
        "facts": {"top": top, "params": p},
        "html": _card(
            f'<div class="kicker">{top["sigungu_name"]} {top["legal_dong_name"]}</div>'
            f'<div class="title">{top["apt_name"]}<br>'
            f'<span class="hl">{top["pyeong_bucket"]}</span></div>'
            f'<div class="body"><div class="rows">'
            f'<div class="row"><span class="k">직전 {p.get("surge_window_days")}일 평단</span>'
            f'<span class="v">{num(top["ppy_prior_90d"])}만</span></div>'
            f'<div class="row"><span class="k">최근 {p.get("surge_window_days")}일 평단</span>'
            f'<span class="v">{num(top["ppy_recent_90d"])}만</span></div>'
            f'<div class="row"><span class="k">차이</span>'
            f'<span class="v" style="color:{POS}">{top["change_pct"]}%</span></div>'
            f'</div></div>',
            idx=f"4 / {n_total}", foot=src),
    })

    # 5 반대로 읽히는 신호 — 이 장이 빠지면 투자 권유처럼 읽힌다
    cards.append({
        "name": "05_counter",
        "facts": {"top": top, "params": p},
        "html": _card(
            f'<div class="kicker">같이 봐야 할 것</div>'
            f'<div class="title">거래는<br><span class="hl">줄었습니다</span></div>'
            f'<div class="body"><div class="rows">'
            f'<div class="row"><span class="k">직전 거래</span>'
            f'<span class="v">{top["deals_prior"]}건</span></div>'
            f'<div class="row"><span class="k">최근 거래</span>'
            f'<span class="v" style="color:{NEG}">{top["deals_recent"]}건</span></div>'
            f'</div>'
            f'<div class="note">오른 가격에 실제로 사고판 사람이 더 많아진 건 아닙니다. '
            f'거래가 적을 때는 어떤 집이 팔렸느냐가 평균을 크게 흔듭니다.</div></div>',
            idx=f"5 / {n_total}", foot=src),
    })

    # 6 마무리 + 면책
    extra = ""
    if nh:
        extra = (f'<div class="row"><span class="k">신고가 경신</span>'
                 f'<span class="v">{len(nh)}건</span></div>')
    cards.append({
        "name": "06_outro",
        "facts": {"params": p, "new_high_n": len(nh)},
        "html": _card(
            f'<div class="kicker">정리</div>'
            f'<div class="title">숫자는 그대로,<br>해석은 각자</div>'
            f'<div class="body"><div class="rows">{extra}'
            f'<div class="row"><span class="k">집계 기준</span>'
            f'<span class="v">{p.get("weekly_lag_days")}일 물린 주</span></div>'
            f'</div>'
            f'<div class="note">계약 후 {p.get("report_deadline_days")}일 안에 신고합니다. '
            f'최근 주는 집계가 덜 차 있어 뒤로 물려 봅니다.</div>'
            f'<div class="note disc" style="margin-top:30px">{DISCLAIMER_SOCIAL}</div>'
            f'</div>',
            idx=f"6 / {n_total}"),
    })
    return cards


def build_thumbnails(data: dict, chart_dir: Path) -> list[dict]:
    """유튜브 썸네일 2안.

    차트를 넣지 않는다. 썸네일은 작게 표시돼 축 라벨이 안 읽히고, 공간만
    먹으면서 정작 봐야 할 숫자를 밀어낸다.

    **대비되는 두 숫자를 같은 크기로 둔다.** 오른 숫자만 키우면 썸네일에서는
    그것만 보이고 반대 지표가 묻힌다. 콘텐츠 본문에서 반대 지표를 같은 비중으로
    싣는데 썸네일에서 뒤집으면 의미가 없다.
    """
    z = data.get("weekly", {}).get("sgg_zscore") or []
    surge = data.get("weekly", {}).get("surge_apt") or []
    if not z or not surge:
        return []
    busiest = max(z, key=lambda r: r["deals_z"])
    top = surge[0]
    p = data.get("params") or {}

    css = f"""
    .t {{ width:{THUMB_W}px; height:{THUMB_H}px; background:{SURFACE};
          padding:76px 84px; display:flex; flex-direction:column;
          justify-content:center; position:relative; }}
    .t .kick {{ font-size:32px; color:{INK_MUTED}; letter-spacing:-.5px; }}
    .t .hd {{ font-size:86px; font-weight:800; line-height:1.1;
              letter-spacing:-3px; margin-top:12px; }}
    .t .hd .hl {{ color:{ACCENT}; }}
    /* 두 수치를 같은 크기로 나란히 — 한쪽만 키우지 않는다 */
    .t .duo {{ display:flex; gap:64px; margin-top:44px; }}
    .t .duo .c {{ flex:1; }}
    .t .duo .lb {{ font-size:30px; color:{INK_2}; }}
    .t .duo .vl {{ font-size:92px; font-weight:800; letter-spacing:-3px;
                   line-height:1.05; margin-top:6px; }}
    .t .duo .sm {{ font-size:28px; color:{INK_MUTED}; margin-top:8px; }}
    .t .up {{ color:{POS}; }} .t .dn {{ color:{NEG}; }}
    .t .foot {{ position:absolute; left:84px; bottom:46px;
                font-size:23px; color:{INK_MUTED}; }}
    """

    a = f"""<div class="t">
      <div class="kick">{busiest.get('week_start','')} 주 · 수도권 실거래</div>
      <div class="hd"><span class="hl">{busiest['sigungu_name']}</span> 거래량,
        평소와 얼마나 달랐나</div>
      <div class="duo">
        <div class="c"><div class="lb">이번 주</div>
          <div class="vl up">{busiest['week_deals']}건</div>
          <div class="sm">표준편차 {busiest['deals_z']:+.1f}</div></div>
        <div class="c"><div class="lb">평소 ({p.get('zscore_hist_weeks')}주 평균)</div>
          <div class="vl">{num(busiest['deals_avg_52w'])}건</div>
          <div class="sm">같은 지역 과거 기준</div></div>
      </div>
      <div class="foot">{SOURCE_NOTE}</div></div>"""

    drop = round((top['deals_recent'] / top['deals_prior'] - 1) * 100, 1)
    b = f"""<div class="t">
      <div class="kick">{top['sigungu_name']} {top['legal_dong_name']} · {top['pyeong_bucket']}</div>
      <div class="hd">{top['apt_name']}</div>
      <div class="duo">
        <div class="c"><div class="lb">평단가</div>
          <div class="vl up">{top['change_pct']}%</div>
          <div class="sm">{num(top['ppy_prior_90d'])}만 → {num(top['ppy_recent_90d'])}만</div></div>
        <div class="c"><div class="lb">거래 건수</div>
          <div class="vl dn">{drop}%</div>
          <div class="sm">{top['deals_prior']}건 → {top['deals_recent']}건</div></div>
      </div>
      <div class="foot">{SOURCE_NOTE}</div></div>"""

    return [
        {"name": "thumb_a_region", "html": a, "css": css,
         "facts": {"busiest": busiest, "params": p}, "w": THUMB_W, "h": THUMB_H},
        {"name": "thumb_b_apt", "html": b, "css": css,
         "facts": {"top": top, "drop_pct": drop}, "w": THUMB_W, "h": THUMB_H},
    ]


# ── 렌더 ─────────────────────────────────────────────────────────────────
def render(items: list[dict], outdir: Path, w: int, h: int) -> list[Path]:
    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for it in items:
            page = b.new_page(viewport={"width": it.get("w", w),
                                        "height": it.get("h", h)},
                              device_scale_factor=1)
            page.set_content(
                f"<style>{_CSS}{it.get('css','')}</style>{it['html']}",
                wait_until="load")
            out = outdir / f"{it['name']}.png"
            page.screenshot(path=str(out))
            page.close()
            made.append(out)
        b.close()
    return made


def strip_html(h: str) -> str:
    import re
    t = re.sub(r"<br\s*/?>", " ", h)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="T16 캐러셀·썸네일")
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

    cards = build_cards(data, outdir)
    thumbs = build_thumbnails(data, outdir)
    if not cards:
        print("재료 부족 — 이번 주는 만들지 않는다 (폴백)")
        return 0

    print(f"\n{'=' * 60}\n  캐러셀·썸네일  {data['asof']}\n{'=' * 60}")

    # 이미지에 박히는 글자도 발행되는 문구다. 숫자·금지어를 똑같이 검사한다.
    blocked = 0
    for it in cards + thumbs:
        text = strip_html(it["html"])
        r = validate(text, it["facts"], require_disclaimer=False)
        if not r.ok:
            blocked += 1
            print(f"  [차단] {it['name']}")
            for why in r.reasons:
                print(f"      ! {why}")
    if blocked:
        print(f"\n  검증 실패 {blocked}건 — 렌더하지 않는다\n{'=' * 60}\n")
        return 1

    made = render(cards, outdir, CARD, CARD) + render(thumbs, outdir, THUMB_W, THUMB_H)
    print(f"  캐러셀 {len(cards)}장 · 썸네일 {len(thumbs)}안  (검증 통과)")
    for p in made:
        print(f"    {p.name:22s} {p.stat().st_size / 1024:>5.0f}KB")
    print(f"\n  저장: {outdir}\n{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
