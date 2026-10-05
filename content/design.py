"""SNS 이미지 디자인 시스템.

`docs/02_CLI_디자인지시사항.md` 의 규칙을 코드로 옮긴 것이다. 카드·차트·썸네일이
전부 여기서 토큰과 헬퍼를 가져다 쓴다. 값을 바꿀 일이 생기면 여기만 고친다.

핵심 규칙 세 가지는 코드로 강제한다 (주석으로만 두면 지켜지지 않는다).
  1) 빨강/파랑은 증감 전용. 일반 강조는 형광펜 띠
  2) σ·표준편차·z-score 는 본문에 쓰지 않는다 — 배수·건수로 번역
  3) 표본이 적은 값은 큰 숫자 장에 쓰지 않는다
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"

# ── 캔버스 ───────────────────────────────────────────────────────────────
# 1080x1350(4:5). 인스타 피드에서 1:1 보다 세로를 20% 더 차지하고, 3:4 그리드
# 에서도 가운데가 살아남는다. 스레드는 원본 비율을 그대로 보여주므로 공용이다.
W, H = 1080, 1350
PAD_X, PAD_TOP, PAD_BOTTOM = 72, 96, 112
# 프로필 그리드 3:4 크롭을 감안해 핵심 요소는 가운데 1000px 안에 둔다
SAFE_CORE = 1000

# ── 색 토큰 ──────────────────────────────────────────────────────────────
BG = "#F6F4EF"        # 오프화이트
INK = "#111111"
SUB = "#6E6E6E"
LINE = "#E3E0D8"
UP = "#E5484D"        # 상승·증가 **전용**
DOWN = "#2F6FED"      # 하락·감소 **전용**
ACCENT = "#FFE45C"    # 일반 강조(형광펜 띠) 전용
NEUTRAL = "#C9C6BE"   # 차트 비강조

# ── 브랜드 ───────────────────────────────────────────────────────────────
HANDLE = "@수도권_실거래"
SERIES = "이번 주 실거래"


def font_face_css() -> str:
    """Pretendard 를 data URI 로 심는다.

    시스템 설치에 기대면 렌더 환경이 바뀔 때 조용히 맑은 고딕으로 떨어진다.
    파일을 직접 넣으면 어디서 돌려도 같은 글자가 나온다.
    """
    faces = []
    for name, weight in (("Regular", 400), ("Medium", 500), ("SemiBold", 600),
                         ("Bold", 700), ("ExtraBold", 800)):
        p = FONT_DIR / f"Pretendard-{name}.woff2"
        if not p.exists():
            continue
        b64 = base64.b64encode(p.read_bytes()).decode()
        faces.append(
            f"@font-face{{font-family:'Pretendard';font-style:normal;"
            f"font-weight:{weight};font-display:block;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "".join(faces)


def has_font() -> bool:
    return any((FONT_DIR / f"Pretendard-{n}.woff2").exists()
               for n in ("Regular", "Bold", "ExtraBold"))


# ── 공통 CSS ─────────────────────────────────────────────────────────────
def base_css() -> str:
    return f"""
{font_face_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:{BG};color:{INK};
     font-family:'Pretendard','Malgun Gothic','맑은 고딕',sans-serif;
     font-feature-settings:"tnum" 1;   /* 숫자 폭 고정 — 자리가 흔들리면 싸구려 */
     -webkit-font-smoothing:antialiased;}}
.card{{width:{W}px;height:{H}px;background:{BG};position:relative;
      padding:{PAD_TOP}px {PAD_X}px {PAD_BOTTOM}px;
      display:flex;flex-direction:column;}}

/* 머리·꼬리 — 캡처되어 퍼져도 출처 계정을 알 수 있게 */
.hd{{position:absolute;top:{PAD_TOP - 40}px;left:{PAD_X}px;right:{PAD_X}px;
    display:flex;justify-content:space-between;align-items:baseline;
    font-size:26px;font-weight:500;color:{SUB};}}
.ft{{position:absolute;left:{PAD_X}px;right:{PAD_X}px;bottom:{PAD_BOTTOM - 48}px;
    font-size:24px;font-weight:400;color:{SUB};line-height:1.45;}}

.body{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:24px;}}

/* 타이포 스케일 */
.kicker{{font-size:38px;font-weight:600;color:{SUB};letter-spacing:-.01em;}}
.h1{{font-size:96px;font-weight:800;letter-spacing:-.03em;line-height:1.2;}}
.h1.sm{{font-size:80px;}}
.h1.xs{{font-size:72px;}}
.lead{{font-size:36px;font-weight:500;line-height:1.5;color:{INK};}}
.sub{{font-size:34px;font-weight:500;line-height:1.5;color:{SUB};}}
.label{{font-size:38px;font-weight:600;color:{SUB};letter-spacing:-.01em;}}

/* 대형 숫자 — 표지와 hero 장 전용 */
.big{{font-size:280px;font-weight:800;letter-spacing:-.04em;line-height:.95;}}
.big.sm{{font-size:200px;}}
.big.xs{{font-size:164px;}}
/* 대형 숫자 위에 붙는 작은 말 — "평소의" 같은 수식어가 숫자 크기로 커지면 안 된다 */
.big-pre{{font-size:48px;font-weight:600;color:{SUB};letter-spacing:-.01em;
         margin-bottom:-8px;}}

/* 형광펜 띠 — 일반 강조는 전부 이것으로. 빨강/파랑을 강조에 쓰지 않는다 */
.mark{{display:inline;padding:0 .06em;border-radius:3px;
      /* 가상요소 + z-index:-1 은 부모 스태킹 컨텍스트에 따라 배경 뒤로 숨는다.
         글자 높이의 40% 만 칠하는 그라디언트가 안전하다. */
      background:linear-gradient(to top,{ACCENT} 40%,transparent 40%);}}

.up{{color:{UP};}} .down{{color:{DOWN};}}

/* 비교 막대 — 축 없이 값 라벨만 */
.bars{{display:flex;flex-direction:column;gap:28px;}}
.bar-row{{display:flex;flex-direction:column;gap:10px;}}
.bar-top{{display:flex;justify-content:space-between;align-items:baseline;}}
.bar-name{{font-size:34px;font-weight:600;}}
.bar-val{{font-size:38px;font-weight:800;letter-spacing:-.02em;}}
.bar-track{{height:30px;border-radius:15px;background:#EDEAE2;overflow:hidden;}}
.bar-fill{{height:100%;border-radius:15px;}}

/* 순위 막대 */
.rank{{display:flex;flex-direction:column;gap:18px;}}
.rank-row{{display:flex;align-items:center;gap:20px;}}
.rank-name{{width:280px;font-size:32px;font-weight:600;text-align:right;
           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
/* 배수 막대는 1.0~1.7 처럼 범위가 좁아 0 부터 그리면 차이가 안 보인다.
   "평소=1.0" 자리에 기준선을 그어 초과분이 읽히게 한다. */
.rank-track{{flex:1;height:26px;position:relative;}}
.rank-base{{position:absolute;top:-10px;bottom:-10px;width:2px;
           background:{SUB};opacity:.45;}}
.rank-baselabel{{font-size:24px;color:{SUB};margin-top:10px;}}
.rank-fill{{height:100%;border-radius:13px;}}
.rank-val{{width:150px;font-size:30px;font-weight:700;}}

/* 수치 행 */
.rows{{display:flex;flex-direction:column;gap:0;}}
.row{{display:flex;justify-content:space-between;align-items:baseline;
     padding:26px 0;border-bottom:2px solid {LINE};}}
.row:last-child{{border-bottom:none;}}
.row .k{{font-size:34px;font-weight:500;color:{SUB};}}
.row .v{{font-size:46px;font-weight:800;letter-spacing:-.02em;}}

/* 표본 배지 — 적은 표본을 숨기지 않고 드러낸다 */
.badge{{display:inline-block;font-size:26px;font-weight:600;color:{SUB};
       background:#EDEAE2;border-radius:999px;padding:8px 18px;}}

.quote{{font-size:64px;font-weight:700;line-height:1.35;letter-spacing:-.02em;}}
.cta{{font-size:34px;font-weight:600;line-height:1.5;}}
.disc{{font-size:24px;font-weight:400;color:{SUB};line-height:1.5;}}
"""


# ── 카피 헬퍼 ────────────────────────────────────────────────────────────
JARGON = re.compile(r"σ|표준편차|z[-\s]?score|시그마", re.I)


def assert_no_jargon(text: str, where: str = "") -> None:
    """σ·표준편차는 본문에 못 쓴다. 일반 독자가 해석하지 못한다."""
    m = JARGON.search(text)
    if m:
        raise ValueError(f"통계 용어 노출 '{m.group(0)}' ({where}) — 배수·건수로 번역할 것")


def times(cur: float, base: float) -> str:
    """'평소의 1.7배' — σ 대신 쓰는 표현."""
    if not base:
        return "-"
    r = cur / base
    return f"{r:.1f}배"


def delta(pct: float, *, arrow: bool = True) -> str:
    """증감은 항상 부호와 화살표. '▲ +35.2%' / '▼ −35.7%'"""
    sign = "+" if pct >= 0 else "−"
    head = ("▲ " if pct >= 0 else "▼ ") if arrow else ""
    return f"{head}{sign}{abs(pct):.1f}%"


def delta_color(pct: float) -> str:
    return "up" if pct >= 0 else "down"


def diff_count(cur: int, base: float) -> str:
    """'41건 더' / '55건 적게'"""
    d = cur - base
    return f"{abs(d):.0f}건 {'더' if d >= 0 else '적게'}"


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


def split_name(name: str, limit: int = 12) -> tuple[str, str]:
    """긴 단지명을 본체와 괄호로 가른다.

    '한라마을(주공2)' 같은 이름이 큰 폰트에서 줄을 넘긴다. 괄호를 떼어
    작은 글씨로 다음 줄에 둔다.
    """
    m = re.match(r"^(.*?)(\([^)]*\))\s*$", name.strip())
    if m and len(name) > limit:
        return m.group(1).strip(), m.group(2)
    return name, ""


def head(page: int, total: int) -> str:
    return (f'<div class="hd"><span>{HANDLE} · {SERIES}</span>'
            f'<span>{page}/{total}</span></div>')


def foot(asof: str, extra: str = "") -> str:
    base = f"국토교통부 실거래가 · 해제 건 제외 · {asof} 기준"
    return f'<div class="ft">{extra + "<br>" if extra else ""}{base}</div>'
