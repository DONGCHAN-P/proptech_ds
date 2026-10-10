"""롱폼 영상 조립기 — 그래픽 + 대본 → mp4 + 자막.

10분짜리를 프레임마다 그리면 1만 9천 장이다. 그렇게 만들지 않는다.
**정지 그래픽을 ffmpeg 로 움직인다** — 다큐에서 쓰는 방식이다.

  켄번즈   정지 이미지를 아주 천천히 밀고 당긴다. 화면이 살아 있게 된다.
           3840px 로 올려 놓고 1920 으로 잘라내므로 글자가 뭉개지지 않는다.
  컷       같은 단락 안에서는 그냥 자른다. 디졸브를 남발하면 늘어진다.
  디졸브   단락이 바뀔 때만. 배경색이 하나라서 배경을 거쳐 넘어가면
           잘라낸 자국이 안 보인다.
  카드     그래픽이 없는 대목은 글자 카드를 만들어 채운다. 빈 화면이
           10초 지나가면 그게 제일 길게 느껴진다.

**길이는 내레이션이 정한다.** 글자 수를 읽는 속도로 나눠 장면 길이를 잡으면,
사장님이 녹음했을 때 그림이 저절로 맞는다. 자막(.srt)도 같은 값에서 나온다.

실행은 각 회차 모듈이 한다 (analysis/newtown1_video.py 참고).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from content import frame as FR  # noqa: E402

# 바깥 틀은 1920x1080 이고, 그림이 들어가는 안쪽 판은 더 작다.
# 테두리는 고정이고 본문만 움직인다 — 켄번즈로 테두리까지 흔들면
# 멀미가 나고 계정 이름이 안 읽힌다.
W, H, FPS = FR.CONTENT_W, FR.CONTENT_H, 30
OUT_W, OUT_H = FR.W, FR.H
CPS = 5.6              # 초당 읽는 글자 수 (분당 약 336자)
MIN_DUR = 2.6          # 아무리 짧아도 이만큼은 둔다
PAD = 0.45             # 문장 사이 숨 쉬는 시간
FADE = 0.35            # 단락이 바뀔 때 디졸브 길이
ZOOM_MAX = 1.09        # 그림에 주는 켄번즈 폭
DRIFT_MAX = 1.025      # 글자 카드에 주는 아주 느린 움직임


@dataclass
class Beat:
    """한 호흡. 화면 하나 + 내레이션 한 토막."""
    visual: str                  # PNG 경로 또는 카드 정의 키
    text: str = ""               # 내레이션 (자막·길이 계산에 쓴다)
    motion: str = "in"           # in | out | still | panL | panR
    section: bool = False        # 여기서 단락이 바뀌나 (디졸브)
    hold: float = 0.0            # 내레이션 없이 더 두고 싶을 때
    chapter: str = ""            # 테두리 오른쪽 위에 뜨는 장 이름
    dur: float = field(default=0.0, init=False)

    def measure(self) -> float:
        n = len("".join(self.text.split()))
        self.dur = max(MIN_DUR, n / CPS + PAD) + self.hold
        return self.dur


def srt_time(t: float) -> str:
    h, r = divmod(max(0.0, t), 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(s % 1 * 1000):03d}"


def write_srt(beats: list[Beat], out: Path) -> Path:
    """자막. 유튜브에 그대로 올릴 수 있고, 녹음할 때 큐시트로도 쓴다."""
    lines, t = [], 0.0
    n = 0
    for b in beats:
        if b.text.strip():
            n += 1
            lines.append(f"{n}\n{srt_time(t)} --> {srt_time(t + b.dur)}\n"
                         f"{b.text.strip()}\n")
        t += b.dur
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def cue_sheet(beats: list[Beat], out: Path) -> Path:
    """녹음용 큐시트. 어느 시점에 어떤 그림이 뜨는지 한눈에."""
    rows, t = ["| 시작 | 길이 | 화면 | 내레이션 |", "|---|---|---|---|"], 0.0
    for b in beats:
        mm, ss = divmod(int(t), 60)
        name = Path(b.visual).stem if b.visual.endswith(".png") else b.visual
        txt = b.text.strip().replace("|", "/") or "—"
        rows.append(f"| {mm}:{ss:02d} | {b.dur:.1f}s | `{name}` | {txt} |")
        t += b.dur
    mm, ss = divmod(int(t), 60)
    rows.append(f"\n**총 길이 {mm}분 {ss}초**")
    out.write_text("\n".join(rows), encoding="utf-8")
    return out


# ── 글자 카드 ────────────────────────────────────────────────────────────
def card_css() -> str:
    return f"""
{D.base_css()}
.pg{{width:{W}px;height:{H}px;background:{D.BG};position:relative;
    display:flex;flex-direction:column;justify-content:center;
    padding:0 150px;box-sizing:border-box;
    font-family:Pretendard,system-ui,sans-serif;color:{D.INK};}}
.pg.dark{{background:{D.INK};color:#FFFFFF;}}
.sec{{font-size:34px;font-weight:700;color:{D.SUB};letter-spacing:.02em;}}
.pg.dark .sec{{color:rgba(255,255,255,.55);}}
.big{{font-size:96px;font-weight:800;letter-spacing:-.035em;line-height:1.2;
     margin-top:22px;}}
.big em{{font-style:normal;color:#E5484D;}}
.big b{{color:#2F6FED;}}
.pg.dark .big b{{color:#8FB6FF;}}
.pg.dark .big em{{color:#FF8A8F;}}
.num{{font-size:210px;font-weight:800;letter-spacing:-.045em;line-height:1;
     color:#2F6FED;}}
.num.l{{color:#E5484D;}}
.cap{{font-size:40px;font-weight:600;color:{D.SUB};margin-top:28px;
     line-height:1.5;}}
.pg.dark .cap{{color:rgba(255,255,255,.66);}}
.rule{{width:120px;height:9px;background:#FFE45C;margin-top:40px;
      border-radius:5px;}}
"""


def card_html(kind: str, **kw) -> str:
    dark = " dark" if kw.get("dark") else ""
    if kind == "title":
        return (f'<div class="pg{dark}"><div class="sec">{kw["sec"]}</div>'
                f'<div class="big">{kw["big"]}</div><div class="rule"></div>'
                f'</div>')
    if kind == "stat":
        cls = " l" if kw.get("down") else ""
        return (f'<div class="pg{dark}"><div class="sec">{kw["sec"]}</div>'
                f'<div class="num{cls}">{kw["num"]}</div>'
                f'<div class="cap">{kw["cap"]}</div></div>')
    return (f'<div class="pg{dark}"><div class="big">{kw["big"]}</div>'
            f'{f"<div class=cap>{kw[chr(99)+chr(97)+chr(112)]}</div>" if kw.get("cap") else ""}'
            f'</div>')


def build_cards(cards: dict[str, str], outdir: Path) -> None:
    """카드 HTML 을 PNG 로. 한 번만 찍으면 되므로 금방 끝난다."""
    from playwright.sync_api import sync_playwright
    outdir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H},
                         device_scale_factor=2)
        for name, html in cards.items():
            pg.set_content(f"<style>{card_css()}</style>{html}",
                           wait_until="load")
            pg.wait_for_timeout(120)
            pg.screenshot(path=str(outdir / f"{name}.png"))
        br.close()


# ── 렌더 ─────────────────────────────────────────────────────────────────
def motion_filter(motion: str, dur: float) -> str:
    """켄번즈. 3840 으로 키워 놓고 자르므로 글자가 선명하다."""
    frames = max(1, int(dur * FPS))
    up = "scale=3840:-2:flags=lanczos"
    cx = "iw/2-(iw/zoom/2)"
    cy = "ih/2-(ih/zoom/2)"
    step = (ZOOM_MAX - 1) / frames
    if motion == "still":
        # 완전 정지는 쓰지 않는다. 글자 카드를 10초씩 얼려 두면 재생이
        # 멈춘 것처럼 보인다. 알아채지 못할 만큼만(2.5%) 천천히 당긴다 —
        # 그림에 쓰는 9% 는 글자에서는 어지럽다.
        micro = (DRIFT_MAX - 1) / frames
        return (f"{up},zoompan=z='min(1.0+on*{micro:.8f},{DRIFT_MAX})':"
                f"d={frames}:x={cx}:y={cy}:s={W}x{H}:fps={FPS},"
                f"format=yuv420p")
    if motion == "out":
        z = f"'max({ZOOM_MAX}-on*{step:.8f},1.0)'"
        x, y = cx, cy
    elif motion == "panL":
        z = f"'{(1 + ZOOM_MAX) / 2:.4f}'"
        x = f"'(iw-iw/zoom)*(1-on/{frames})'"
        y = cy
    elif motion == "panR":
        z = f"'{(1 + ZOOM_MAX) / 2:.4f}'"
        x = f"'(iw-iw/zoom)*(on/{frames})'"
        y = cy
    else:                                   # in
        z = f"'min(1.0+on*{step:.8f},{ZOOM_MAX})'"
        x, y = cx, cy
    return (f"{up},zoompan=z={z}:d={frames}:x={x}:y={y}:"
            f"s={W}x{H}:fps={FPS},format=yuv420p")


def clip(src: Path, chrome: Path, dur: float, motion: str, out: Path,
         fade_in: bool, fade_out: bool) -> None:
    """본문을 움직여 안쪽 판에 넣고, 그 위에 고정 테두리를 얹는다."""
    vf = motion_filter(motion, dur)
    if fade_in:
        vf += f",fade=t=in:st=0:d={FADE}:c={D.BG}"
    if fade_out:
        vf += f",fade=t=out:st={max(0, dur - FADE):.3f}:d={FADE}:c={D.BG}"
    fc = (f"color=c={FR.SHELL}:s={OUT_W}x{OUT_H}:r={FPS}[bg];"
          f"[0:v]{vf}[c];"
          f"[bg][c]overlay={FR.CONTENT_X}:{FR.CONTENT_Y}:shortest=1[b];"
          f"[b][1:v]overlay=0:0:format=auto,format=yuv420p[v]")
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-loop", "1", "-i", str(src),
           "-loop", "1", "-i", str(chrome),
           "-filter_complex", fc, "-map", "[v]",
           "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-preset", "medium", "-crf", "19", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{src.name}: {r.stderr[-500:]}")


def render(beats: list[Beat], assets: Path, out: Path,
           chrome: dict[str, Path]) -> Path:
    """장면마다 짧은 클립을 만들고 이어 붙인다."""
    tmp = Path(tempfile.mkdtemp(prefix="longvid_"))
    first = next(iter(chrome.values()))
    try:
        parts = []
        for i, b in enumerate(beats):
            src = assets / b.visual if not Path(b.visual).is_absolute() \
                else Path(b.visual)
            if not src.exists():
                raise FileNotFoundError(src)
            nxt = beats[i + 1] if i + 1 < len(beats) else None
            p = tmp / f"c{i:03d}.mp4"
            clip(src, chrome.get(b.chapter, first), b.dur, b.motion, p,
                 fade_in=b.section or i == 0,
                 fade_out=bool(nxt and nxt.section) or nxt is None)
            parts.append(p)
            print(f"\r  장면 {i + 1}/{len(beats)}", end="", flush=True)
        print()
        lst = tmp / "list.txt"
        lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts),
                       encoding="utf-8")
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
               "-i", str(lst), "-c", "copy", "-movflags", "+faststart",
               str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[-600:])
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
