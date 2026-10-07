"""T13 — 인스타 릴스 영상.

피드 캐러셀은 **팔로워에게만** 닿는다. 릴스는 추천으로 퍼진다. 그래서 같은
데이터로 세로 영상을 따로 만든다.

    1080×1920 (9:16) · 30fps · 약 20초 · 무음

**피드 카드를 그대로 옮기지 않는다.** 릴스는 인스타 UI 가 위아래를 덮는다 —
위는 계정·추천 영역, 아래는 캡션과 좋아요·댓글·공유 버튼, 오른쪽은 액션 열이다.
그 자리에 글자를 두면 발행 후에야 가려진 걸 알게 된다. 안전 영역을 좁게 잡고
그 안에만 글을 둔다.

**소리는 넣지 않는다.** 음원은 인스타 앱 안에서 고르는 게 저작권상 안전하고,
릴스 노출에도 그쪽이 유리하다. 영상은 무음으로 내보내고 음악은 올릴 때 얹는다.

움직임은 장마다 **들어오는 순간**에만 준다. 글자가 계속 움직이면 읽을 수가
없다. 0.8초 동안 올라오며 나타나고, 나머지는 멈춰서 읽히게 둔다.

실행:
  .venv\\Scripts\\python.exe -m content.reels
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import cover as CV  # noqa: E402
from content import design as D  # noqa: E402
from content import neighbor_map as NM  # noqa: E402
from content.carousel import pick, strip_html  # noqa: E402
from content.validator import validate  # noqa: E402
from templates.disclaimers import DISCLAIMER_SOCIAL  # noqa: E402

W, H = 1080, 1920
FPS = 30
ANIM_S, HOLD_S = 0.8, 2.6      # 들어오는 시간 / 읽는 시간
LAST_HOLD_S = 3.4              # 마지막 장은 조금 더 — 팔로우를 누를 시간

# 인스타 릴스 UI 가 덮는 자리. 실측 기준으로 넉넉히 잡는다.
#   위   계정·추천 배지
#   아래 캡션 2줄 + 음원 + 버튼
#   오른 좋아요·댓글·공유·더보기 열
SAFE_TOP, SAFE_BOTTOM, SAFE_X, SAFE_RIGHT = 300, 460, 72, 160


def ease(t: float) -> float:
    """끝에서 부드럽게 멎는 곡선. 선형으로 움직이면 기계가 민 것처럼 보인다."""
    return 1 - (1 - t) ** 3


def css() -> str:
    return f"""
{D.base_css()}
.card{{width:{W}px;height:{H}px;padding:0;}}
.rv{{position:absolute;left:{SAFE_X}px;right:{SAFE_RIGHT}px;
    top:{SAFE_TOP}px;bottom:{SAFE_BOTTOM}px;
    display:flex;flex-direction:column;justify-content:center;gap:40px;}}
.rv-dark{{background:{D.INK};}}
/* 안전 영역 밖은 비워 둔다. 인스타 UI 가 그 위에 올라온다. */
.rv-brand{{position:absolute;left:{SAFE_X}px;top:{SAFE_TOP - 92}px;
         font-size:32px;font-weight:600;color:{D.SUB};}}
.rv-foot{{position:absolute;left:{SAFE_X}px;right:{SAFE_RIGHT}px;
        bottom:{SAFE_BOTTOM - 96}px;font-size:26px;color:{D.SUB};
        line-height:1.5;}}
.rv-dark .rv-brand,.rv-dark .rv-foot{{color:rgba(255,255,255,.6);}}

.rv-kick{{font-size:40px;font-weight:600;color:{D.SUB};letter-spacing:-.01em;}}
.rv-h1{{font-size:104px;font-weight:800;letter-spacing:-.03em;line-height:1.18;}}
.rv-num{{font-size:210px;font-weight:800;letter-spacing:-.04em;line-height:1;}}
.rv-lead{{font-size:44px;font-weight:600;line-height:1.45;}}
.rv-sub{{font-size:38px;font-weight:500;color:{D.SUB};line-height:1.5;}}
.rv-dark .rv-h1{{color:{D.COVER_INK};}}
.rv-dark .rv-num{{color:{D.COVER_KEY};}}
.rv-dark .rv-lead{{color:{D.COVER_INK};}}
.rv-dark .rv-sub{{color:rgba(255,255,255,.72);}}
.rv-map{{display:flex;justify-content:center;}}

/* 비교 막대 */
.rv-bars{{display:flex;flex-direction:column;gap:30px;}}
.rv-bar .t{{display:flex;justify-content:space-between;align-items:baseline;
           font-size:38px;font-weight:700;}}
.rv-bar .t small{{font-size:28px;font-weight:500;color:{D.SUB};}}
.rv-bar .track{{height:34px;border-radius:999px;background:#EDEAE2;
               margin-top:12px;overflow:hidden;}}
.rv-bar .fill{{height:100%;border-radius:999px;}}

/* 신호 */
.rv-sig{{border-left:6px solid {D.LINE};padding-left:30px;}}
.rv-sig .k{{font-size:30px;font-weight:700;color:{D.SUB};}}
.rv-sig .v{{font-size:44px;font-weight:700;line-height:1.35;margin-top:10px;}}

.rv-handle{{font-size:84px;font-weight:800;letter-spacing:-.03em;
           background:linear-gradient(to top,{D.ACCENT} 40%,transparent 40%);
           display:inline-block;padding:0 .08em;}}
.rv-disc{{font-size:26px;color:{D.SUB};line-height:1.5;}}

/* 진행 표시 — 몇 장 남았는지 보이면 이탈이 준다 */
.rv-dots{{position:absolute;left:{SAFE_X}px;top:{SAFE_TOP - 40}px;
         display:flex;gap:10px;}}
.rv-dots i{{width:46px;height:6px;border-radius:3px;background:{D.LINE};}}
.rv-dots i.on{{background:{D.UP};}}
.rv-dark .rv-dots i{{background:rgba(255,255,255,.25);}}
.rv-dark .rv-dots i.on{{background:{D.COVER_KEY};}}
"""


def chrome(page: int, total: int, foot: str, dark: bool) -> str:
    dots = "".join(f'<i class="{"on" if i <= page else ""}"></i>'
                   for i in range(1, total + 1))
    return (f'<div class="rv-dots">{dots}</div>'
            f'<div class="rv-brand">{D.HANDLE} · {D.SERIES}</div>'
            f'<div class="rv-foot">{foot}</div>')


def anim(idx: int, t: float) -> str:
    """요소 하나의 등장 스타일. 순서대로 조금씩 늦게 들어온다."""
    d = min(1.0, max(0.0, (t - idx * 0.12) / 0.55))
    e = ease(d)
    return (f'style="opacity:{e:.3f};'
            f'transform:translateY({(1 - e) * 36:.1f}px)"')


# ── 장 ───────────────────────────────────────────────────────────────────
def scenes(t: dict, prof: dict) -> list[dict]:
    """영상 장면 목록. 캐러셀과 **같은 줄거리**를 쓴다."""
    d = t["cover"].data
    src = f'국토교통부 실거래가 · 해제 건 제외 · {t["asof"]} 기준'
    out: list[dict] = []

    # 1 훅 — 첫 1초가 전부다. 단지명과 금액을 바로 띄운다.
    name, _ = D.split_name(prof["apt_name"], 11)
    svg = NM.render(prof, width=840, height=520, dark=True,
                    neighbors=prof.get("neighbors"))
    out.append({
        "dark": True, "foot": f'{src} · {NM_credit(prof)}',
        "facts": {"cover": d, "profile": _pf(prof)},
        "body": lambda p, _n=name, _s=svg, _d=d: (
            f'<div class="rv-kick" {anim(0, p)}>'
            f'{prof["sigungu_name"]} {prof["legal_dong_name"]}</div>'
            f'<div class="rv-h1" {anim(1, p)}>{_n},<br>종전 최고가</div>'
            f'<div class="rv-num" {anim(2, p)}>{count(_d["deal_amount"], p)}</div>'
            f'<div class="rv-map" {anim(3, p)}>{_s or ""}</div>'),
    })

    # 2 추이 — 20년 기록 위에 이번 거래
    out.append({
        "dark": False, "foot": src,
        "facts": {"cover": d, "profile": _pf(prof),
                  "months": len(prof["series"])},
        "body": lambda p, _d=d: (
            f'<div class="rv-kick" {anim(0, p)}>'
            f'{D.pyeong(prof["pyeong_bucket"])} 실거래</div>'
            f'<div class="rv-h1" {anim(1, p)}>이번 거래는<br>여기예요</div>'
            f'<div {anim(2, p)}>{trend_svg(prof, p)}</div>'
            f'<div class="rv-sub" {anim(3, p)}>붉은 점이 이번 거래 '
            f'{D.won(_d["deal_amount"])}. 회색은 지난 거래예요.</div>'),
    })

    # 3 주변 — 옆 단지가 눈금이 된다
    rows = nearby_rows(t, prof)
    out.append({
        "dark": False, "foot": src,
        "facts": {"cover": d, "profile": _pf(prof)},
        "body": lambda p, _r=rows: (
            f'<div class="rv-kick" {anim(0, p)}>{prof["legal_dong_name"]} '
            f'{D.pyeong(prof["pyeong_bucket"])}</div>'
            f'<div class="rv-h1" {anim(1, p)}>옆 단지는<br>얼마일까요?</div>'
            f'<div class="rv-bars" {anim(2, p)}>{bars(_r, p)}</div>'),
    })

    # 4 신호 — "원인"이 아니라 "같이 볼 것"
    sg = signals(t, prof)
    out.append({
        "dark": False, "foot": src,
        "facts": {"cover": d, "profile": _pf(prof), **sg["facts"]},
        "body": lambda p, _s=sg["items"]: (
            f'<div class="rv-kick" {anim(0, p)}>왜 올랐는지는 '
            f'거래 기록으로 알 수 없어요</div>'
            f'<div class="rv-h1" {anim(1, p)}>같이 볼 만한 것</div>'
            + "".join(
                f'<div class="rv-sig" {anim(2 + i, p)}>'
                f'<div class="k">{k}</div><div class="v">{v}</div></div>'
                for i, (k, v) in enumerate(_s))),
    })

    # 5 구 전체 — 단지의 일과 동네의 일을 가른다
    r = t.get("cover_region")
    if r and r.get("deals_avg_52w"):
        ratio = r["week_deals"] / r["deals_avg_52w"]
        word = ("평소보다 붐볐어요" if ratio >= 1.1 else
                "평소보다 조용했어요" if ratio <= 0.9 else "평소와 비슷했어요")
        rows2 = [("평소", r["deals_avg_52w"], D.NEUTRAL),
                 ("이번 주", r["week_deals"], D.UP if ratio >= 1 else D.DOWN)]
        out.append({
            "dark": False, "foot": f'{src} · 평소 = 지난 52주 평균',
            "facts": {"region": r, "ratio": round(ratio, 2)},
            "body": lambda p, _r=rows2, _w=word: (
                f'<div class="rv-kick" {anim(0, p)}>단지 말고, 구 전체는</div>'
                f'<div class="rv-h1" {anim(1, p)}>{r["sigungu_name"]}는<br>{_w}</div>'
                f'<div class="rv-bars" {anim(2, p)}>'
                f'{bars([(n, v, c, f"{v:,.0f}건") for n, v, c in _r], p)}</div>'
                f'<div class="rv-sub" {anim(3, p)}>단지 하나가 움직여도 '
                f'동네 전체가 같이 움직이는 건 아니에요.</div>'),
        })

    # 6 팔로우
    out.append({
        "dark": False, "foot": src, "facts": {}, "last": True,
        "body": lambda p: (
            f'<div class="rv-kick" {anim(0, p)}>다음 주에도</div>'
            f'<div class="rv-h1" {anim(1, p)}>이런 숫자,<br>매주 받아보실래요?</div>'
            f'<div {anim(2, p)}><span class="rv-handle">{D.HANDLE}</span></div>'
            f'<div class="rv-sub" {anim(3, p)}>· 평소와 달라진 동네를 한 장으로<br>'
            f'· 몇 건으로 나온 숫자인지 늘 같이<br>'
            f'· 오를지 내릴지는 말하지 않아요</div>'
            # 핸들만 띄워 두면 아무도 누르지 않는다. 영상은 끝나면 사라져서
            # 무엇을 하라는 건지 **말로** 적어야 한다.
            f'<div class="rv-lead" {anim(4, p)}>팔로우해두면 다음 주에 또 만나요.</div>'
            f'<div class="rv-disc" {anim(5, p)}>{DISCLAIMER_SOCIAL}</div>'),
    })
    return out


def NM_credit(prof: dict) -> str:
    a = prof.get("around") or {}
    return a.get("road_credit", "") if a.get("roads") else ""


def _pf(prof: dict) -> dict:
    return {k: v for k, v in prof.items() if k not in ("lat", "lng")}


def count(value: float, p: float) -> str:
    """숫자가 올라가며 멎는다. 릴스에서 큰 숫자는 움직여야 눈이 멈춘다."""
    return D.won(value * ease(min(1.0, p / 0.75)))


def bars(rows, p: float) -> str:
    """rows: (라벨, 값, 색) 또는 (라벨, 값, 색, 표시문자열)"""
    norm = [(r + (None,))[:4] if len(r) == 3 else r for r in rows]
    mx = max(v for _, v, *_ in norm) or 1
    g = ease(min(1.0, max(0.0, (p - 0.25) / 0.6)))
    out = []
    for label, val, color, *rest in norm:
        shown = (rest[0] if rest and rest[0] else D.won(val))
        out.append(
            f'<div class="rv-bar"><div class="t"><span>{label}</span>'
            f'<span>{shown}</span></div>'
            f'<div class="track"><div class="fill" '
            f'style="width:{val / mx * 100 * g:.1f}%;background:{color}"></div>'
            f'</div></div>')
    return "".join(out)


def nearby_rows(t: dict, prof: dict) -> list[tuple]:
    d = t["cover"].data
    me = (D.split_name(prof["apt_name"], 9)[0], d["deal_amount"], D.UP)
    nb = sorted(prof["neighbors"], key=lambda r: r["last_price"], reverse=True)
    rows = [me] + [(D.split_name(r["apt_name"], 9)[0], r["last_price"],
                    D.NEUTRAL) for r in nb[:3]]
    return sorted(rows, key=lambda r: r[1], reverse=True)


def signals(t: dict, prof: dict) -> dict:
    d = t["cover"].data
    items, facts = [], {}
    others = prof.get("other_pyeongs") or []
    if others:
        top = max(others, key=lambda r: r["deals_1y"])
        items.append((f'같은 단지 {D.pyeong(top["pyeong_bucket"])}',
                      f'{D.won(top["last_price"])}에 거래됐어요'))
    nb = prof.get("neighbors") or []
    if nb:
        hi = max(nb, key=lambda r: r["last_price"])
        items.append(("같은 동 최고가",
                      f'{D.split_name(hi["apt_name"], 9)[0]} '
                      f'{D.won(hi["last_price"])}'))
    pts = prof.get("series") or []
    recent = sum(x["deals"] for x in pts[-12:]) if pts else 0
    prior = sum(x["deals"] for x in pts[-24:-12]) if len(pts) > 12 else 0
    if prior:
        items.append(("이 평형 거래",
                      f'직전 1년 {prior}건 → 최근 1년 {recent}건'))
        facts = {"deals_recent_1y": recent, "deals_prior_1y": prior}
    return {"items": items[:3], "facts": facts}


def trend_svg(prof: dict, p: float) -> str:
    """실거래 추이. 점이 왼쪽부터 차례로 찍히고 이번 거래가 마지막에 터진다."""
    pts = [x for x in prof["series"] if x.get("avg_price")]
    xs = [datetime.strptime(x["ym"], "%Y-%m") for x in pts]
    ys = [float(x["avg_price"]) for x in pts]
    w, h = 840, 560
    t0, t1 = xs[0].timestamp(), xs[-1].timestamp()
    span = (t1 - t0) or 1
    lo, hi = min(ys), max(ys)
    pad = (hi - lo) * 0.18 or 1
    lo, hi = lo - pad, hi + pad
    pl, pr, pt, pb = 170, 30, 24, 70
    iw, ih = w - pl - pr, h - pt - pb
    X = lambda dt: pl + (dt.timestamp() - t0) / span * iw      # noqa: E731
    Y = lambda v: pt + (1 - (v - lo) / (hi - lo)) * ih         # noqa: E731

    grid = "".join(
        f'<line x1="{pl}" x2="{w - pr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" '
        f'stroke="{D.LINE}" stroke-width="1"/>'
        f'<text x="{pl - 18}" y="{Y(v) + 11:.1f}" text-anchor="end" '
        f'font-size="30" fill="{D.SUB}">{D.won(v)}</text>'
        for v in (lo + (hi - lo) * (k + .5) / 3 for k in range(3)))
    years = [y for y in range(xs[0].year, xs[-1].year + 1)
             if xs[0] <= datetime(y, 1, 1) <= xs[-1]]
    step = max(1, len(years) // 5)
    ticks = "".join(
        f'<text x="{X(datetime(y, 1, 1)):.1f}" y="{h - 24}" '
        f'text-anchor="middle" font-size="30" fill="{D.SUB}">{y}</text>'
        for i, y in enumerate(years) if i % step == 0)

    # 점이 차례로 찍힌다 — 20년이 흘러가는 느낌
    g = ease(min(1.0, max(0.0, (p - 0.15) / 0.65)))
    shown = int(len(xs) * g)
    dots = "".join(
        f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="8" fill="{D.NEUTRAL}" '
        f'stroke="{D.BG}" stroke-width="2"/>'
        for x, y in list(zip(xs, ys))[:max(0, shown - 1)])
    mark = ""
    if shown >= len(xs):
        pop = ease(min(1.0, max(0.0, (p - 0.8) / 0.2)))
        lx, ly = X(xs[-1]), Y(ys[-1])
        mark = (f'<line x1="{lx:.1f}" x2="{lx:.1f}" y1="{pt}" y2="{h - pb}" '
                f'stroke="{D.UP}" stroke-width="2" stroke-dasharray="6 6" '
                f'opacity="{0.45 * pop:.2f}"/>'
                f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="{10 + 16 * pop:.1f}" '
                f'fill="{D.UP}" opacity="{0.25 * pop:.2f}"/>'
                f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="13" fill="{D.UP}" '
                f'stroke="#FFFFFF" stroke-width="4"/>')
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'style="font-family:Pretendard">{grid}{ticks}{dots}{mark}</svg>')


# ── 렌더 ─────────────────────────────────────────────────────────────────
def render(scs: list[dict], outdir: Path) -> Path:
    """장면을 프레임으로 찍고 ffmpeg 으로 잇는다."""
    from playwright.sync_api import sync_playwright

    tmp = Path(tempfile.mkdtemp(prefix="reels_"))
    n_anim = int(ANIM_S * FPS)
    listing: list[str] = []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            page = br.new_page(viewport={"width": W, "height": H},
                               device_scale_factor=1)
            k = 0
            for i, sc in enumerate(scs, 1):
                for f in range(n_anim):
                    p = (f + 1) / n_anim
                    html = (f'<div class="card{" rv-dark" if sc["dark"] else ""}">'
                            f'{chrome(i, len(scs), sc["foot"], sc["dark"])}'
                            f'<div class="rv">{sc["body"](p)}</div></div>')
                    page.set_content(f"<style>{css()}</style>{html}",
                                     wait_until="load")
                    fp = tmp / f"f{k:05d}.png"
                    page.screenshot(path=str(fp))
                    listing.append(f"file '{fp.as_posix()}'\nduration {1 / FPS:.5f}")
                    k += 1
                # 멈춰서 읽는 구간은 **마지막 프레임을 늘려** 쓴다.
                # 같은 그림을 수십 장 더 찍을 이유가 없다.
                hold = LAST_HOLD_S if sc.get("last") else HOLD_S
                listing[-1] = f"file '{(tmp / f'f{k - 1:05d}.png').as_posix()}'\n" \
                              f"duration {1 / FPS + hold:.5f}"
            br.close()

        lst = tmp / "list.txt"
        lst.write_text("\n".join(listing) + f"\nfile '{(tmp / f'f{k-1:05d}.png').as_posix()}'\n",
                       encoding="utf-8")
        out = outdir / "reels.mp4"
        # concat 목록은 프레임마다 길이가 다르다(멈춤 구간을 마지막 프레임으로
        # 늘려 쓴다). -fps_mode cfr 로 고정 프레임레이트로 다시 샘플링한다 —
        # vfr 과 -r 을 같이 주면 ffmpeg 가 모순이라며 거부한다.
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
               "-i", str(lst),
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-fps_mode", "cfr", "-r", str(FPS),
               "-preset", "medium", "-crf", "20",
               "-movflags", "+faststart", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[-800:])
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="T13 릴스 영상")
    ap.add_argument("--metrics")
    a = ap.parse_args()

    files = sorted((ROOT / "output").glob("metrics_*.json"))
    src = Path(a.metrics) if a.metrics else (files[-1] if files else None)
    if src is None or not src.exists():
        print("지표 JSON 이 없다. 먼저: python -m metrics.build_metrics")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    outdir = ROOT / "output" / data["asof"]
    outdir.mkdir(parents=True, exist_ok=True)

    t = pick(data)
    prof = (t["cover"].data or {}).get("profile") if t else None
    print(f"\n{'=' * 62}\n  릴스  {data['asof']}  ({W}×{H} · {FPS}fps)\n{'=' * 62}")
    if not prof:
        print("  소개할 단지가 없다 — 이번 주는 만들지 않는다 (폴백)")
        return 0

    scs = scenes(t, prof)
    # 영상에 박히는 글자도 발행 문구다. 카드와 같은 검증을 거친다.
    fails = []
    for i, sc in enumerate(scs, 1):
        text = strip_html(sc["body"](1.0))
        D.assert_no_jargon(text, f"scene{i}")
        r = validate(text, {"card": sc["facts"], "params": t["params"]},
                     require_disclaimer=False)
        if not r.ok:
            fails += [f"{i}장: {w}" for w in r.reasons]
    if fails:
        print(f"\n  검증 실패 {len(fails)}건 — 렌더하지 않는다")
        for f in fails:
            print(f"    ! {f}")
        return 1

    secs = len(scs) * (ANIM_S + HOLD_S) + (LAST_HOLD_S - HOLD_S)
    print(f"  {len(scs)}장 · 약 {secs:.0f}초 · 무음 (음악은 인스타에서)")
    out = render(scs, outdir)
    print(f"\n  저장: {out}  ({out.stat().st_size / 1e6:.1f}MB)")
    print(f"{'=' * 62}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
