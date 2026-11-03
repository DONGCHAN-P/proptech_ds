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
from content import emoji as EM  # noqa: E402
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
    audio: Path | None = field(default=None, init=False)
    adur: float = field(default=0.0, init=False)

    def measure(self) -> float:
        """음성이 있으면 **읽은 길이**가 장면 길이다.

        글자 수로 어림잡던 것(초당 5.6자)은 녹음이 없을 때의 임시방편이다.
        실제로 읽으면 문장마다 빠르고 느린 데가 있어 그림과 말이 어긋난다.
        """
        if self.adur > 0:
            self.dur = self.adur + PAD + self.hold
        else:
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
/* 아래 {SUB_ZONE}px 은 자막 띠 자리다. 그걸 패딩으로 떼어 놓으면
   세로 가운데 정렬이 **남은 자리 기준**으로 잡힌다. 카드마다 좌표를
   밀어 올리며 때우던 걸 한 번에 없앤다. */
.pg{{width:{W}px;height:{H}px;background:{D.BG};position:relative;
    display:flex;flex-direction:column;justify-content:center;
    padding:0 150px {SUB_ZONE}px;box-sizing:border-box;
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
/* 장 표지 — 글자 두 줄만 놓인 빈 들판이 되지 않게. 장 번호를 배경에
   크게 깔고 왼쪽에 기둥을 세운다. 기둥은 머리띠의 노란 띠와 같은 모양이라
   표지 한 장만 잘라 가도 같은 영상인 게 보인다. */
.pg.ch{{padding-left:190px;}}
.pg.ch:before{{content:"";position:absolute;left:150px;top:calc((100% - {SUB_ZONE}px) / 2);
    transform:translateY(-50%);width:10px;height:230px;
    background:#FFE45C;border-radius:6px;}}
.pg.ch .sec{{font-size:38px;}}
.pg.ch .big{{font-size:128px;}}
.ghost{{position:absolute;right:92px;top:calc((100% - {SUB_ZONE}px) / 2);
    transform:translateY(-50%);font-size:500px;font-weight:800;
    line-height:.76;letter-spacing:-.06em;color:rgba(17,17,17,.06);}}
.pg.dark .ghost{{color:rgba(255,255,255,.075);}}
/* 이모지 카드 — 참고한 쇼츠처럼 그림 하나가 주인공이고 글자는 거든다.
   가로 판이라 이모지를 왼쪽에 세우고 글자를 오른쪽에 붙인다. */
.row{{display:flex;align-items:center;gap:72px;}}
.icon{{flex:none;}}
.txt{{flex:1;min-width:0;}}
.txt .big{{margin-top:0;font-size:84px;}}
.txt .cap{{font-size:36px;margin-top:20px;}}
/* 설명 줄이 없는 짧은 한 방은 가운데로 쌓는다. 45장이 모두 같은 배치면
   그림을 넣어도 12분 내내 같은 화면으로 느껴진다. 두 틀을 번갈아 쓰면
   카드가 바뀐 게 보인다. */
.row.mid{{flex-direction:column;gap:30px;text-align:center;}}
.row.mid .txt{{flex:none;}}
.row.mid .txt .big{{font-size:78px;}}
/* 순차 점등 — 목록을 한꺼번에 띄우면 눈이 어디를 봐야 할지 모른다.
   내레이션이 짚는 항목만 밝히고 나머지는 어둡게 둔다. */
.steps{{display:flex;flex-direction:column;}}
.step{{display:flex;align-items:center;border-radius:18px;
      border:3px solid transparent;}}
.step .n{{flex:none;border-radius:50%;display:flex;
         align-items:center;justify-content:center;
         font-weight:800;background:{D.INK};color:#FFFFFF;}}
.pg.dark .step .n{{background:#FFFFFF;color:{D.INK};}}
.step .t{{font-weight:800;letter-spacing:-.03em;line-height:1.25;}}
.step .t b{{color:#2F6FED;}}
.step .t em{{font-style:normal;color:#E5484D;}}
.pg.dark .step .t b{{color:#8FB6FF;}}
.pg.dark .step .t em{{color:#FF8A8F;}}
/* 2열 비교 — "바꾸기 전 / 바꾼 뒤"처럼 **나란히 놓아야 뜻이 생기는**
   짝은 두 장에 나눠 보여 주면 앞 장을 기억해야 한다. 한 화면에 둔다. */
.vs{{display:flex;align-items:stretch;gap:0;}}
.vs .col{{flex:1;min-width:0;border-radius:20px;padding:34px 38px;
         border:3px solid {D.LINE};background:rgba(0,0,0,.025);}}
.pg.dark .vs .col{{border-color:rgba(255,255,255,.16);
                  background:rgba(255,255,255,.05);}}
.vs .tag{{display:inline-block;font-size:24px;font-weight:800;
         padding:7px 16px;border-radius:9px;color:#FFFFFF;}}
.vs .ttl{{font-size:52px;font-weight:800;letter-spacing:-.03em;
         line-height:1.22;margin-top:20px;}}
.vs .sub{{font-size:29px;color:{D.SUB};line-height:1.5;margin-top:16px;}}
.pg.dark .vs .sub{{color:rgba(255,255,255,.66);}}
.vs .mid{{flex:none;width:104px;display:flex;align-items:center;
         justify-content:center;font-size:46px;font-weight:800;
         color:{D.SUB};}}
/* 픽토그램 — 「39 대 92」는 숫자로 읽으면 2.4배인 줄만 알고,
   늘어놓으면 **양이 보인다**. */
.units{{display:flex;flex-direction:column;gap:30px;}}
.unit{{display:flex;align-items:center;gap:26px;}}
.unit .nm{{flex:none;width:168px;font-size:36px;font-weight:800;
          text-align:right;}}
.unit .grid{{flex:1;display:flex;flex-wrap:wrap;gap:7px;
            align-content:center;}}
.unit .grid i{{display:block;width:30px;height:30px;}}
.unit .ct{{flex:none;width:150px;font-size:44px;font-weight:800;
          text-align:right;}}
"""


CARD_ANIM_S = 0.62          # 들어오는 시간
CARD_ANIM_N = 19            # 그 동안 찍는 장 수 (0.62 x 30fps)
STEP_ANIM_N = 48            # fit_anim 이 못 고칠 때의 보루
ANIM_SPAN = 0.82            # 장면의 몇 할을 움직임에 쓰나
MAX_ANIM_N = 340            # 한 장면에 찍을 장 수 상한
#   240 으로 두었더니 10초가 넘는 장면이 상한에 걸려 한 장을 2프레임씩
#   쓰게 됐다 — 15fps 라 눈에 띄게 버벅인다. 긴 장면도 30fps 가 되게
#   올린다. 장 수가 늘어 렌더가 길어지는 건 감수한다.


def fit_anim(beats: list, cards: dict) -> None:
    """장면 길이에 맞춰 **장 수를 다시 정한다.**

    장 수를 손으로 박아 두면 한 장이 1.9프레임, 2.5프레임처럼 어중간하게
    걸린다. ffmpeg 는 정수 프레임으로만 끊으므로 2-2-1-2-2-1 로 들쭉날쭉
    멈추고, 이게 **재생이 끊기는 것처럼** 보인다. 실제로 그렇게 나갔다.

    그래서 한 장이 영상 프레임의 **정수 배**를 차지하도록 장 수를 맞춘다.
    장면이 길어 장 수가 상한을 넘으면 한 장을 두 프레임씩 쓴다(15fps) —
    느려도 고르면 끊겨 보이지 않는다.
    """
    for b in beats:
        if not str(b.visual).startswith("cards/"):
            continue
        hit = cards.get(str(b.visual).split("/")[-1])
        if not hit:
            continue
        kind, kw = hit
        if kind != "steps" and not kw.get("anim"):
            continue
        d = b.dur or b.measure()
        span = d * ANIM_SPAN
        step = 1
        n = int(round(span * FPS))
        while n > MAX_ANIM_N:
            step += 1
            n = int(round(span * FPS / step))
        kw["n"] = max(CARD_ANIM_N + 1, n)

# 픽토그램 한 칸. 집 모양이라야 "단지 수"로 읽힌다.
# style 속성 안에서는 HTML 엔티티가 풀리므로 따옴표가 든 SVG 를
# 그대로 넣으면 CSS url() 이 깨진다 (네모로 나왔다). base64 로 둔다.
UNIT_SVG = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDIuNiAyLjQgMTAuMmgyLjNWMjFoNS4xdi01LjloNC40VjIxaDUuMVYxMC4yaDIuM3oiLz48L3N2Zz4="


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
    if kind == "custom":
        # 그리는 법을 호출한 쪽이 들고 있는 장면 — 차트가 자라나거나
        # 지도에 점이 하나씩 찍히는 것들. 도메인 코드를 여기 끌어오지
        # 않으려고 함수를 그대로 받는다.
        return kw["html"](p)
    if kind == "title":
        # 노란 띠는 왼쪽에서 자라난다. 제목이 다 올라온 뒤에 긋는다.
        w = 120 * ease((p - 0.33) / 0.5)
        sec = str(kw["sec"])
        # 번호가 붙은 장만 배경 숫자를 깐다. "정리하면" 같은 말은 크게
        # 깔아 봐야 제목과 두 번 읽힐 뿐이다.
        num = sec.isdigit()
        # 세 줄짜리 제목까지 128px 로 키우면 노란 밑줄이 자막 띠 뒤로
        # 밀려 들어간다. 줄 수에 따라 크기를 내린다.
        rows = kw["big"].count("<br>") + 1
        fs = 128 if rows <= 2 else 98
        ghost = (f'<div class="ghost" style="opacity:{ease(p / .7):.3f}">'
                 f'{sec}</div>' if num else "")
        # 번호를 작게도 적고 크게도 깔면 같은 글자를 두 번 읽힌다.
        # 배경 숫자가 있으면 위의 작은 번호는 뺀다.
        head = ("" if num else
                f'<div class="sec" style="{_in(p, 0)}">{sec}</div>')
        return (f'<div class="pg ch{dark}">{ghost}{head}'
                f'<div class="big" style="{_in(p, 1)};font-size:{fs}px">'
                f'{kw["big"]}</div>'
                f'<div class="rule" style="width:{w:.0f}px"></div></div>')
    if kind == "stat":
        cls = " l" if kw.get("down") else ""
        return (f'<div class="pg{dark}">'
                f'<div class="sec" style="{_in(p, 0)}">{kw["sec"]}</div>'
                f'<div class="num{cls}" style="{_pop(p, 1)}">{kw["num"]}</div>'
                f'<div class="cap" style="{_in(p, 2)}">{kw["cap"]}</div></div>')
    if kind == "versus":
        L, R = kw["left"], kw["right"]
        e0, e1 = ease(p / 0.55), ease((p - 0.22) / 0.55)
        def col(c, o, sh):
            return (f'<div class="col" style="opacity:{o:.3f};'
                    f'transform:translateY({(1 - o) * 28:.1f}px)">'
                    f'<div class="tag" style="background:{c["color"]}">'
                    f'{c["tag"]}</div>'
                    f'<div class="ttl">{c["title"]}</div>'
                    f'<div class="sub">{c["sub"]}</div></div>')
        sec = (f'<div class="sec" style="{_in(p, 0)};margin-bottom:30px">'
               f'{kw["sec"]}</div>' if kw.get("sec") else "")
        return (f'<div class="pg{dark}">{sec}<div class="vs">'
                f'{col(L, e0, 0)}'
                f'<div class="mid" style="opacity:{e1:.3f}">'
                f'{kw.get("mark", "→")}</div>'
                f'{col(R, e1, 1)}</div></div>')
    if kind == "units":
        rows = kw["rows"]          # (이름, 개수, 색)
        mx = max(r[1] for r in rows)
        e = ease(p / 0.75)
        mask = (f"-webkit-mask:url('{UNIT_SVG}') center/contain no-repeat;"
                f"mask:url('{UNIT_SVG}') center/contain no-repeat")
        dim = "rgba(255,255,255,.14)" if dark else D.LINE
        out = []
        for nm, cnt, col_ in rows:
            on = round(cnt * e)
            cells = []
            for k in range(mx):
                # 그 줄에 없는 칸은 아예 비운다. 흐리게 깔면 "더 있는데
                # 안 센 것"처럼 읽힌다.
                if k >= cnt:
                    bg = "transparent"
                elif k < on:
                    bg = col_
                else:
                    bg = dim
                cells.append(f'<i style="background:{bg};{mask}"></i>')
            out.append(f'<div class="unit"><div class="nm">{nm}</div>'
                       f'<div class="grid">{"".join(cells)}</div>'
                       f'<div class="ct" style="color:{col_}">{on}개</div>'
                       f'</div>')
        sec = (f'<div class="sec" style="{_in(p, 0)};margin-bottom:34px">'
               f'{kw["sec"]}</div>' if kw.get("sec") else "")
        return f'<div class="pg{dark}">{sec}<div class="units">{"".join(out)}</div></div>'
    if kind == "steps":
        items = kw["items"]
        n = len(items)
        # 항목 수에 맞춰 줄인다. 네 줄짜리를 세 줄 크기로 두면 자막 띠를
        # 밟는다 — 제목 카드에서 이미 한 번 밟았다.
        fs, dia, pad, gap = ((62, 76, 22, 26) if n <= 3
                             else (52, 64, 16, 18))
        # 마지막 항목이 켜진 뒤에도 조금 머물도록 +0.5 칸을 둔다.
        pos = p * (n + 0.5)
        rows = []
        for k, it in enumerate(items):
            d = pos - k
            # 마지막 항목은 물러나지 않는다. 장면이 끝날 때 화면에 남아
            # 있어야 할 게 바로 그 줄이다.
            if k == n - 1:
                d = min(d, 1.0)
            if d <= 0:                       # 아직
                op, ring = 0.14, 0.0
            elif d < 1.0:                    # 지금 켜지는 중
                e = ease(d)
                op, ring = 0.14 + 0.86 * e, e
            else:                            # 지나간 것 — 남기되 물러난다
                f = ease(min(1.0, d - 1.0))
                op, ring = 1 - 0.3 * f, 1 - f
            rows.append(
                f'<div class="step" style="opacity:{op:.3f};'
                f'padding:{pad}px 30px;margin-bottom:{gap}px;'
                f'border-color:rgba(255,228,92,{ring:.3f})">'
                f'<div class="n" style="width:{dia}px;height:{dia}px;'
                f'font-size:{int(dia * .5)}px;margin-right:28px">{k + 1}</div>'
                f'<div class="t" style="font-size:{fs}px">{it}</div></div>')
        sec = (f'<div class="sec" style="{_in(p, 0)};margin-bottom:26px">'
               f'{kw["sec"]}</div>' if kw.get("sec") else "")
        return (f'<div class="pg{dark}">{sec}'
                f'<div class="steps">{"".join(rows)}</div></div>')
    cap = kw.get("cap")
    if kind == "emoji":
        # 그림이 먼저 튀어 오르고 글자가 따라 올라온다.
        e = ease((p - 0.0) / 0.5)
        mid = "" if cap else " mid"
        ico = EM.img(kw["icon"], 340 if mid else 300)
        cap_html = (f'<div class="cap" style="{_in(p, 2)}">{cap}</div>'
                    if cap else "")
        return (
            f'<div class="pg{dark}"><div class="row{mid}">'
            f'<div class="icon" style="opacity:{e:.3f};'
            f'transform:scale({0.72 + 0.28 * e:.3f}) '
            f'rotate({(1 - e) * -9:.1f}deg)">{ico}</div>'
            f'<div class="txt">'
            f'<div class="big" style="{_in(p, 1)}">{kw["big"]}</div>'
            f'{cap_html}</div></div></div>')
    cap_html = (f'<div class="cap" style="{_in(p, 1)}">{cap}</div>'
                if cap else "")
    return (f'<div class="pg{dark}">'
            f'<div class="big" style="{_in(p, 0)}">{kw["big"]}</div>'
            f'{cap_html}</div>')


# 자막 띠가 카드 아래쪽을 쓴다. 세 줄까지 늘어날 수 있으므로 이만큼은
# 비워 둬야 한다. 차트에는 이 검사가 걸려 있었는데 새로 만든 장면에는
# 걸지 않아, 범례가 축 숫자를 덮고 기둥이 자막을 밟고 값이 판 밖으로
# 나가는 걸 **사장님이 눈으로 찾아내야 했다.** 이제 빌드가 멈춘다.
SAFE_JS = """() => {
  const W = %d, H = %d, SUB = %d, PAD = 8;
  const bad = [];
  const put = m => { if (bad.length < 8 && !bad.includes(m)) bad.push(m); };
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || parseFloat(cs.opacity || 1) < 0.08)
      continue;
    const tag = el.tagName.toUpperCase();
    const leaf = el.children.length === 0;
    const txt = leaf ? (el.textContent || '').trim() : '';
    const mark = /^(IMG|CIRCLE|RECT|PATH|LINE|POLYLINE|TEXT|POLYGON)$/
                 .test(tag);
    if (!txt && !mark) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const nm = (txt || tag).slice(0, 20);
    // 글자는 어디서든 안 된다. 도형은 배경으로 깔리는 경우가 있어
    // data-bleed 를 단 것만 아래쪽 검사를 면제한다.
    const bleed = !txt && el.closest('[data-bleed]');
    if (!bleed && r.bottom > H - SUB + 1)
      put(`「${nm}」가 자막 자리를 ${Math.round(r.bottom - (H - SUB))}px 침범`);
    if (r.right > W + PAD)
      put(`「${nm}」가 오른쪽으로 ${Math.round(r.right - W)}px 넘침`);
    if (r.left < -PAD) put(`「${nm}」가 왼쪽으로 ${Math.round(-r.left)}px 넘침`);
    if (r.top < -PAD) put(`「${nm}」가 위로 ${Math.round(-r.top)}px 넘침`);
  }
  return bad;
}"""
SUB_ZONE = 196


def build_cards(cards: dict[str, tuple], outdir: Path,
                css: str | None = None, *, check: bool = True,
                ) -> dict[str, list[Path]]:
    """카드마다 **등장 장면들**을 찍는다.

    한 장만 찍어 ffmpeg 로 밀던 것을 바꿨다. 드리프트는 "안 멈춘 것처럼"
    보이게 할 뿐, 들어오는 맛이 없다. 19장이면 0.62초짜리 등장이 된다.
    """
    from playwright.sync_api import sync_playwright
    outdir.mkdir(parents=True, exist_ok=True)
    out: dict[str, list[Path]] = {}
    # 한 페이지에 수천 번 set_content 를 하면 렌더러 메모리가 쌓여
    # 어느 순간 멈춘다. 15분짜리 렌더가 통째로 날아갔다. 일정 장마다
    # 페이지를 새로 연다.
    RECYCLE = 400
    done = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch()

        def fresh():
            pgx = br.new_page(viewport={"width": W, "height": H},
                              device_scale_factor=2)
            pgx.set_default_timeout(90_000)
            return pgx

        pg = fresh()
        for name, (kind, kw) in cards.items():
            # 순차 점등은 0.62초가 아니라 **장면 내내** 진행된다. 장 수를
            # 늘려 두면 seq_input 이 알아서 길이에 맞춰 펴 준다.
            n = kw.get("n") or (STEP_ANIM_N if kind == "steps"
                                else CARD_ANIM_N)
            seq = []
            for k in range(n):
                p = (k + 1) / n
                if done and done % RECYCLE == 0:
                    pg.close()
                    pg = fresh()
                done += 1
                body = (f"<style>{css or card_css()}</style>"
                        f"{card_html(kind, p, **kw)}")
                try:
                    pg.set_content(body, wait_until="load")
                except Exception:
                    # 한 번은 봐준다. 눌린 페이지를 버리고 다시 연다.
                    try:
                        pg.close()
                    except Exception:
                        pass
                    pg = fresh()
                    pg.set_content(body, wait_until="load")
                pg.wait_for_timeout(16)
                # 다 그려진 장(마지막)만 본다. 들어오는 중에는 글자가
                # 아직 제자리가 아니라 거짓 경보가 난다.
                if check and k == n - 1:
                    probs = pg.evaluate(SAFE_JS % (W, H, SUB_ZONE))
                    if probs:
                        br.close()
                        nl = chr(10) + "  "
                        raise RuntimeError(
                            f"{name} ({kind}) 안전구역 침범:{nl}"
                            + nl.join(probs))
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
    # 세로는 **위를 붙박아** 당긴다. 가운데를 기준으로 9% 를 당기면 위아래가
    # 4% 씩 잘리는데, 우리 판은 맨 위에 눈표와 제목이 있어서 그 줄이 먼저
    # 사라진다. 아래쪽은 대개 비어 있고 자막 띠가 덮으므로 거기서 자른다.
    ty = "0"
    step = (ZOOM_MAX - 1) / frames
    if motion == "none":
        # 확대 없음. 우리가 짠 판(차트·기사·지도)은 테두리에 꼭 맞게
        # 그려져 있어서, 9% 를 당기면 좌우 4.5% 가 잘려 **오른쪽 글자가
        # 사라진다.** 사진이 아니라 판이므로 움직일 이유도 없다.
        return (f"{up},scale={W}:{H}:flags=lanczos,fps={FPS},"
                f"format=yuv420p")
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
        x, y = cx, ty
    elif motion == "panL":
        z = f"'{(1 + ZOOM_MAX) / 2:.4f}'"
        x = f"'(iw-iw/zoom)*(1-on/{frames})'"
        y = ty
    elif motion == "panR":
        z = f"'{(1 + ZOOM_MAX) / 2:.4f}'"
        x = f"'(iw-iw/zoom)*(on/{frames})'"
        y = ty
    else:                                   # in
        z = f"'min(1.0+on*{step:.8f},{ZOOM_MAX})'"
        x, y = cx, ty
    return (f"{up},zoompan=z={z}:d={frames}:x={x}:y={y}:"
            f"s={W}x{H}:fps={FPS},format=yuv420p")


def seq_input(seq: list[Path], dur: float, tmp: Path, i: int) -> Path:
    """등장 장면들 + 마지막 장 늘리기. 같은 그림을 수백 장 더 찍지 않는다.

    장 수가 등장 애니메이션보다 많으면 **장면 전체에 걸친 진행**으로 본다
    (순차 점등). 그때는 한 장을 1/30초씩 넘기는 대신 길이를 나눠 갖는다 —
    0.6초 만에 세 항목이 다 켜져 버리면 내레이션과 어긋난다.
    """
    nl = chr(10)
    if len(seq) > CARD_ANIM_N:
        # 한 장이 영상 프레임의 **정수 배**를 차지해야 한다. 나눠서 남는
        # 시간을 그냥 쪼개면 2-3-2-3 으로 걸려 끊겨 보인다.
        step = max(1, round(dur * ANIM_SPAN * FPS / len(seq)))
        per = step / FPS
        hold = max(0.1, dur - per * len(seq))
        lines = [f"file '{f.as_posix()}'{nl}duration {per:.5f}"
                 for f in seq[:-1]]
        lines.append(f"file '{seq[-1].as_posix()}'{nl}"
                     f"duration {per + hold:.5f}")
        lines.append(f"file '{seq[-1].as_posix()}'")
        lst = tmp / f"seq{i:03d}.txt"
        lst.write_text(nl.join(lines), encoding="utf-8")
        return lst
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
        # concat 디먹서에 `duration` 만 적어 주면 안쪽 타임베이스가 25fps
        # 로 잡혀 여섯 프레임마다 한 장이 중복된다 — 그게 "렉"으로 보였다.
        # 입력 프레임률을 먼저 못박아 30fps 로 1:1 대응시킨다.
        ins = ["-f", "concat", "-safe", "0", "-r", str(FPS),
               "-i", str(seq_list), "-loop", "1", "-i", str(chrome)]
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


def audio_track(beats: list[Beat], tmp: Path, out: Path,
                music: Path | None = None) -> Path | None:
    """토막별 음성을 장면 시작에 맞춰 깔고, 음악을 그 아래 받친다.

    음성은 장면보다 PAD 만큼 짧다 (`measure`). 그 여백이 숨 쉬는 자리다.
    음악은 말이 있을 때 **자동으로 수그러들게**(사이드체인) 한다 —
    고정 볼륨으로 깔면 조용한 대목에서는 안 들리고 말 위에서는 거슬린다.
    """
    have = [(i, b) for i, b in enumerate(beats) if b.audio]
    if not have and music is None:
        return None
    ins, fc, tags, t = [], [], [], 0.0
    starts = []
    for b in beats:
        starts.append(t)
        t += b.dur
    total = t
    for k, (i, b) in enumerate(have):
        ins += ["-i", str(b.audio)]
        # 장면이 시작하고 조금 뒤에 말이 나온다. 바로 붙으면 숨이 없다.
        fc.append(f"[{k}:a]aresample=48000,adelay="
                  f"{int((starts[i] + PAD * .45) * 1000)}|"
                  f"{int((starts[i] + PAD * .45) * 1000)}[v{k}]")
        tags.append(f"[v{k}]")
    if tags:
        fc.append("".join(tags) + f"amix=inputs={len(tags)}:normalize=0,"
                  f"atrim=0:{total:.3f},asetpts=N/SR/TB[speech]")
    if music is not None:
        mi = len(have)
        ins += ["-stream_loop", "-1", "-i", str(music)]
        fc.append(f"[{mi}:a]aresample=48000,atrim=0:{total:.3f},"
                  f"volume=0.22,afade=t=in:st=0:d=2,"
                  f"afade=t=out:st={max(0, total - 4):.3f}:d=4[bed]")
        if tags:
            # [speech] 를 사이드체인과 최종 합치기에 **두 번** 쓰면 안 된다.
            # 그렇게 했더니 11dB 가 깎여 나갔다 (말소리 -21dB → -32dB).
            # asplit 으로 갈라 써야 한다.
            fc.append("[speech]asplit=2[sc][sp]")
            fc.append("[bed][sc]sidechaincompress="
                      "threshold=0.035:ratio=8:attack=10:release=450[duck]")
            fc.append("[duck][sp]amix=inputs=2:normalize=0[mixed]")
        else:
            fc.append("[bed]anull[mixed]")
    else:
        fc.append("[speech]anull[mixed]")
    # 귀로 맞추지 말고 방송 기준으로 맞춘다. 유튜브는 -14 LUFS 로
    # 정규화하므로 그보다 낮게 내보내면 그냥 작은 영상이 된다.
    fc.append("[mixed]loudnorm=I=-15:TP=-1.5:LRA=11[out]")
    cmd = ["ffmpeg", "-v", "error", "-y", *ins,
           "-filter_complex", ";".join(fc), "-map", "[out]",
           "-c:a", "aac", "-b:a", "192k", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("소리 합치기 실패: " + r.stderr[-600:])
    return out


def render(beats: list[Beat], assets: Path, out: Path,
           chrome: dict[str, Path],
           subs: dict[int, Path] | None = None,
           card_frames: dict[str, list[Path]] | None = None,
           music: Path | None = None) -> Path:
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
        silent = tmp / "silent.mp4"
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
               "-i", str(lst), "-c", "copy", "-movflags", "+faststart",
               str(silent)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[-600:])
        trk = audio_track(beats, tmp, tmp / "track.m4a", music)
        if trk is None:
            shutil.copy(silent, out)
            return out
        print("  소리 얹는 중...")
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(silent),
               "-i", str(trk), "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-shortest", "-movflags", "+faststart", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[-600:])
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
