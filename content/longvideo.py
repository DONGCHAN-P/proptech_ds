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


CARD_ANIM_S = 0.62          # 들어오는 시간
CARD_ANIM_N = 19            # 그 동안 찍는 장 수 (0.62 x 30fps)


def ease(t: float) -> float:
    """끝에서 부드럽게 멎는 곡선. 선형이면 기계가 민 것처럼 보인다."""
    return 1 - (1 - max(0.0, min(1.0, t))) ** 3


def _in(p: float, idx: int, *, rise: float = 34.0) -> str:
    """요소 하나의 등장. 순서대로 조금씩 늦게 올라온다.

    글자 카드가 10초씩 멈춰 있으면 재생이 멈춘 것처럼 보인다. 드리프트만
    주던 것을 실제 등장 동작으로 바꾼다 — 한 줄씩 올라오면 눈이 따라간다.
    """
    d = (p - idx * 0.11) / 0.52
    e = ease(d)
    return f'opacity:{e:.3f};transform:translateY({(1 - e) * rise:.1f}px)'


def _pop(p: float, idx: int) -> str:
    """숫자는 밀어 올리지 않고 살짝 커지며 들어온다. 더 세게 보인다."""
    d = (p - idx * 0.11) / 0.52
    e = ease(d)
    return (f'opacity:{e:.3f};'
            f'transform:scale({0.93 + 0.07 * e:.3f});'
            f'transform-origin:left center')


def card_html(kind: str, p: float = 1.0, **kw) -> str:
    dark = " dark" if kw.get("dark") else ""
    if kind == "title":
        # 노란 띠는 왼쪽에서 자라난다. 제목이 다 올라온 뒤에 긋는다.
        w = 120 * ease((p - 0.33) / 0.5)
        return (f'<div class="pg{dark}">'
                f'<div class="sec" style="{_in(p, 0)}">{kw["sec"]}</div>'
                f'<div class="big" style="{_in(p, 1)}">{kw["big"]}</div>'
                f'<div class="rule" style="width:{w:.0f}px"></div></div>')
    if kind == "stat":
        cls = " l" if kw.get("down") else ""
        return (f'<div class="pg{dark}">'
                f'<div class="sec" style="{_in(p, 0)}">{kw["sec"]}</div>'
                f'<div class="num{cls}" style="{_pop(p, 1)}">{kw["num"]}</div>'
                f'<div class="cap" style="{_in(p, 2)}">{kw["cap"]}</div></div>')
    cap = kw.get("cap")
    cap_html = (f'<div class="cap" style="{_in(p, 1)}">{cap}</div>'
                if cap else "")
    return (f'<div class="pg{dark}">'
            f'<div class="big" style="{_in(p, 0)}">{kw["big"]}</div>'
            f'{cap_html}</div>')


def build_cards(cards: dict[str, tuple], outdir: Path) -> dict[str, list[Path]]:
    """카드마다 **등장 장면들**을 찍는다.

    한 장만 찍어 ffmpeg 로 밀던 것을 바꿨다. 드리프트는 "안 멈춘 것처럼"
    보이게 할 뿐, 들어오는 맛이 없다. 19장이면 0.62초짜리 등장이 된다.
    """
    from playwright.sync_api import sync_playwright
    outdir.mkdir(parents=True, exist_ok=True)
    out: dict[str, list[Path]] = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H},
                         device_scale_factor=2)
        for name, (kind, kw) in cards.items():
            seq = []
            for k in range(CARD_ANIM_N):
                p = (k + 1) / CARD_ANIM_N
                pg.set_content(
                    f"<style>{card_css()}</style>{card_html(kind, p, **kw)}",
                    wait_until="load")
                pg.wait_for_timeout(16)
                f = outdir / f"{name}_{k:02d}.png"
                pg.screenshot(path=str(f))
                seq.append(f)
            out[name] = seq
        br.close()
    return out


# ── 자막 띠 ──────────────────────────────────────────────────────────────
# 참고한 포맷(비디오머그 「오그랩」)의 핵심은 **자막이 두 겹**이라는 것이다.
# 평범한 서술은 하단 박스 자막으로 흘리고, 때릴 문장만 큰 카드로 때린다.
# 그 교대가 리듬을 만든다. 우리는 큰 카드를 이미 쓰고 있었으니 띠가 없었다.
SUB_W = FR.CONTENT_W - 180      # 카드 안쪽에서 양옆을 띄운다
SUB_BOTTOM = 26                 # 카드 아래 끝에서 띄우는 거리


def subs_css() -> str:
    return f"""
@font-face{{font-family:Pretendard;src:local('Pretendard');}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:{OUT_W}px;height:{OUT_H}px;background:transparent;
     font-family:Pretendard,system-ui,sans-serif;
     -webkit-font-smoothing:antialiased;}}
.band{{position:absolute;left:50%;transform:translateX(-50%);
      bottom:{OUT_H - FR.CONTENT_Y - FR.CONTENT_H + SUB_BOTTOM}px;
      max-width:{SUB_W}px;
      padding:15px 34px;border-radius:11px;
      background:#FFFFFF;
      /* 테두리를 두 겹으로 둔다. 바깥은 노랑, 안쪽은 먹색 실선 —
         밝은 차트 위에서도 어두운 카드 위에서도 띠가 뜬다. */
      border:3px solid {D.ACCENT};
      box-shadow:0 0 0 1.5px rgba(17,17,17,.82),
                 0 14px 34px rgba(0,0,0,.30);
      font-size:34px;font-weight:700;color:{D.INK};
      line-height:1.42;text-align:center;letter-spacing:-.015em;
      word-break:keep-all;}}
"""


def sub_html(text: str) -> str:
    return f'<div class="band">{text}</div>'


def build_subs(beats: list[Beat], outdir: Path) -> dict[int, Path]:
    """비트마다 자막 띠 한 장. 내레이션이 없는 비트는 만들지 않는다."""
    from playwright.sync_api import sync_playwright
    outdir.mkdir(parents=True, exist_ok=True)
    out: dict[int, Path] = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": OUT_W, "height": OUT_H},
                         device_scale_factor=1)
        for i, b in enumerate(beats):
            t = b.text.strip()
            if not t:
                continue
            pg.set_content(f"<style>{subs_css()}</style>{sub_html(t)}",
                           wait_until="load")
            pg.wait_for_timeout(60)
            f = outdir / f"sub_{i:03d}.png"
            pg.screenshot(path=str(f), omit_background=True)
            out[i] = f
        br.close()
    return out


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


def seq_input(seq: list[Path], dur: float, tmp: Path, i: int) -> Path:
    """등장 장면들 + 마지막 장 늘리기. 같은 그림을 수백 장 더 찍지 않는다."""
    nl = chr(10)
    hold = max(0.1, dur - len(seq) / FPS)
    lines = [f"file '{f.as_posix()}'{nl}duration {1 / FPS:.5f}"
             for f in seq[:-1]]
    lines.append(f"file '{seq[-1].as_posix()}'{nl}duration {hold:.5f}")
    lines.append(f"file '{seq[-1].as_posix()}'")
    lst = tmp / f"seq{i:03d}.txt"
    lst.write_text(nl.join(lines), encoding="utf-8")
    return lst


def clip(src: Path, chrome: Path, dur: float, motion: str, out: Path,
         fade_in: bool, fade_out: bool, sub: Path | None = None,
         seq_list: Path | None = None) -> None:
    """본문을 움직여 안쪽 판에 넣고, 그 위에 고정 테두리를 얹는다.

    seq_list 가 있으면 **등장 애니메이션**이 든 장면 목록을 쓴다. 그때는
    켄번즈를 걸지 않는다 — 이미 움직이는 그림을 또 밀면 어지럽다.
    """
    vf = motion_filter(motion, dur)
    if seq_list is not None:
        vf = f"fps={FPS},scale={W}:{H}:flags=lanczos,format=yuv420p"
    if fade_in:
        vf += f",fade=t=in:st=0:d={FADE}:c={D.BG}"
    if fade_out:
        vf += f",fade=t=out:st={max(0, dur - FADE):.3f}:d={FADE}:c={D.BG}"
    fc = (f"color=c={FR.SHELL}:s={OUT_W}x{OUT_H}:r={FPS}[bg];"
          f"[0:v]{vf}[c];"
          f"[bg][c]overlay={FR.CONTENT_X}:{FR.CONTENT_Y}:shortest=1[b];"
          f"[b][1:v]overlay=0:0:format=auto[t]")
    if seq_list is not None:
        ins = ["-f", "concat", "-safe", "0", "-i", str(seq_list),
               "-loop", "1", "-i", str(chrome)]
    else:
        ins = ["-loop", "1", "-i", str(src),
               "-loop", "1", "-i", str(chrome)]
    if sub is not None:
        ins += ["-loop", "1", "-i", str(sub)]
        fc += f";[t][2:v]overlay=0:0:format=auto,format=yuv420p[v]"
    else:
        fc += ";[t]format=yuv420p[v]"
    cmd = ["ffmpeg", "-v", "error", "-y", *ins,
           "-filter_complex", fc, "-map", "[v]",
           "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-preset", "medium", "-crf", "19", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{src.name}: {r.stderr[-500:]}")


def render(beats: list[Beat], assets: Path, out: Path,
           chrome: dict[str, Path],
           subs: dict[int, Path] | None = None,
           card_frames: dict[str, list[Path]] | None = None) -> Path:
    """장면마다 짧은 클립을 만들고 이어 붙인다."""
    tmp = Path(tempfile.mkdtemp(prefix="longvid_"))
    first = next(iter(chrome.values()))
    try:
        parts = []
        for i, b in enumerate(beats):
            # 카드는 장면 목록으로, 그림은 한 장 + 켄번즈로 만든다.
            key = (b.visual.split("/", 1)[1]
                   if b.visual.startswith("cards/") else None)
            seq = (card_frames or {}).get(key) if key else None
            lst = seq_input(seq, b.dur, tmp, i) if seq else None
            src = Path(b.visual)
            if seq is None:
                src = assets / b.visual if not src.is_absolute() else src
                if not src.exists():
                    raise FileNotFoundError(src)
            nxt = beats[i + 1] if i + 1 < len(beats) else None
            p = tmp / f"c{i:03d}.mp4"
            clip(src, chrome.get(b.chapter, first), b.dur, b.motion, p,
                 fade_in=b.section or i == 0,
                 fade_out=bool(nxt and nxt.section) or nxt is None,
                 sub=(subs or {}).get(i), seq_list=lst)
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
