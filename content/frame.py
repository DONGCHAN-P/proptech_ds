"""시그니처 프레임 — 어느 한 장을 잘라 가도 우리 영상인 게 보이게.

유튜브에서 정보 영상은 **캡처로 돌아다닌다.** 차트 한 장이 커뮤니티에 올라갈
때 계정 이름이 안 붙어 있으면 그냥 "어디서 본 자료"가 된다. 그래서 모든
프레임에 같은 자리, 같은 모양으로 신원을 박는다.

구성
    ┌──────────────────────────────────────────┐  진한 바탕 + 아주 옅은 모눈
    │ ▌@proptech_ds      신도시 시리즈 · 05 ─── │  머리띠
    │ ╭────────────────────────────────────╮   │
    │ │          차트 · 지도 · 카드            │   │  밝은 본문 판
    │ ╰────────────────────────────────────╯   │
    │ 국토교통부 실거래가              ▬▬▬▭▭▭ │  꼬리띠 + 진행 표시
    └──────────────────────────────────────────┘

왜 이렇게 나누나
    본문만 움직이고 테두리는 **고정**이다. 켄번즈로 그림을 당길 때 테두리까지
    같이 움직이면 멀미가 나고, 계정 이름이 흔들려 읽히지도 않는다. 그래서
    테두리는 알파가 뚫린 한 장으로 따로 만들어 위에 얹는다.

모눈은 "데이터를 다룬다"는 신호다. 눈에 띄면 안 되므로 거의 안 보일 만큼만
깐다 (3% 불투명도).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402

W, H = 1920, 1080

# 본문 판. 16:9 를 유지해야 차트 레이아웃을 그대로 쓴다.
CONTENT_W, CONTENT_H = 1650, 928
CONTENT_X, CONTENT_Y = (W - CONTENT_W) // 2, 76
RADIUS = 22

SHELL = "#15161A"       # 바깥 바탕
SHELL_2 = "#1E2026"     # 모눈
RAIL = D.ACCENT         # 왼쪽 세로 띠
ON = "#FFFFFF"
OFF = "rgba(255,255,255,.28)"


def css() -> str:
    return f"""
@font-face{{font-family:Pretendard;src:local('Pretendard');}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:{W}px;height:{H}px;background:transparent;
     font-family:Pretendard,system-ui,sans-serif;
     -webkit-font-smoothing:antialiased;}}
.shell{{position:absolute;inset:0;}}
/* 본문 자리를 **진짜로** 뚫는다. 투명한 div 를 얹는 걸로는 아래 칠이
   지워지지 않아서, evenodd 로 구멍 난 한 장을 그린다. */
.ring{{position:absolute;left:{CONTENT_X - 2}px;top:{CONTENT_Y - 2}px;
      width:{CONTENT_W + 4}px;height:{CONTENT_H + 4}px;
      border:2px solid rgba(255,255,255,.12);
      border-radius:{RADIUS + 2}px;}}
.head{{position:absolute;left:{CONTENT_X}px;top:0;width:{CONTENT_W}px;
      height:{CONTENT_Y}px;display:flex;align-items:center;
      justify-content:space-between;}}
.who{{display:flex;align-items:center;gap:14px;}}
.rail{{width:7px;height:30px;background:{RAIL};border-radius:4px;}}
.handle{{font-size:27px;font-weight:800;color:{ON};letter-spacing:-.01em;}}
.ep{{display:flex;align-items:center;gap:14px;
    font-size:24px;font-weight:600;color:rgba(255,255,255,.72);}}
.ep b{{color:{RAIL};font-weight:800;}}
.foot{{position:absolute;left:{CONTENT_X}px;
      top:{CONTENT_Y + CONTENT_H}px;width:{CONTENT_W}px;
      height:{H - CONTENT_Y - CONTENT_H}px;
      display:flex;align-items:center;justify-content:space-between;}}
.src{{font-size:21px;color:rgba(255,255,255,.46);}}
.dots{{display:flex;gap:7px;}}
.dots i{{width:26px;height:5px;border-radius:3px;background:{OFF};}}
.dots i.on{{background:{RAIL};}}
"""


def shell_svg() -> str:
    """바깥 바탕. 가운데 둥근 사각형이 뚫려 있다.

    바깥 사각형과 안쪽 둥근 사각형을 한 path 에 넣고 evenodd 를 주면
    안쪽이 구멍이 된다. 모눈도 같은 path 로 칠해 구멍 밖에만 깔린다.
    """
    x, y = CONTENT_X, CONTENT_Y
    w, h, r = CONTENT_W, CONTENT_H, RADIUS
    inner = (f"M{x + r},{y} H{x + w - r} A{r},{r} 0 0 1 {x + w},{y + r} "
             f"V{y + h - r} A{r},{r} 0 0 1 {x + w - r},{y + h} H{x + r} "
             f"A{r},{r} 0 0 1 {x},{y + h - r} V{y + r} "
             f"A{r},{r} 0 0 1 {x + r},{y} Z")
    d = f"M0,0 H{W} V{H} H0 Z {inner}"
    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<defs><pattern id="g" width="48" height="48" '
        f'patternUnits="userSpaceOnUse">'
        f'<path d="M48,0 V48 M0,48 H48" stroke="{SHELL_2}" '
        f'stroke-width="1" fill="none"/></pattern></defs>'
        f'<path d="{d}" fill="{SHELL}" fill-rule="evenodd"/>'
        f'<path d="{d}" fill="url(#g)" fill-rule="evenodd"/>'
        f'</svg>')


def chrome_html(ep: str, chapter: str, total: int, idx: int,
                source: str) -> str:
    dots = "".join(f'<i class="{"on" if k <= idx else ""}"></i>'
                   for k in range(1, total + 1))
    chap = f'<b>{chapter}</b>' if chapter else ""
    return (
        f'<div class="shell">{shell_svg()}</div><div class="ring"></div>'
        f'<div class="head">'
        f'  <div class="who"><div class="rail"></div>'
        f'  <div class="handle">{D.CHANNEL}</div></div>'
        f'  <div class="ep">{ep}{chap}</div></div>'
        f'<div class="foot"><div class="src">{source}</div>'
        f'<div class="dots">{dots}</div></div>')


def build(chapters: list[str], outdir: Path, *, ep: str, source: str,
          ) -> dict[str, Path]:
    """장(章)마다 테두리 한 장. 진행 표시가 달라지므로 장별로 찍는다.

    101 장면마다 찍을 수도 있지만, 점이 한 칸씩 기는 것보다 장이 바뀔 때
    옮겨 가는 쪽이 읽기 쉽다.
    """
    from playwright.sync_api import sync_playwright
    outdir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    n = len(chapters)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H},
                         device_scale_factor=1)
        for i, ch in enumerate(chapters, 1):
            pg.set_content(
                f"<style>{css()}</style>"
                f"{chrome_html(ep, ch, n, i, source)}",
                wait_until="load")
            pg.wait_for_timeout(90)
            p = outdir / f"frame_{i:02d}.png"
            # omit_background 로 본문 자리를 진짜 투명하게 남긴다.
            pg.screenshot(path=str(p), omit_background=True)
            out[ch] = p
        br.close()
    return out
