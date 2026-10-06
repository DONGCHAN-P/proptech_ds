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
import os
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
# 본문 시작 y. 지시사항 5항 "상단 정보줄 아래 y=200부터 시작".
BODY_TOP = 200
# 콘텐츠 하단과 출처 사이가 이보다 비면 실패로 본다 (5항).
MAX_BOTTOM_GAP = 300
# 표지 대형 숫자는 가로 폭의 이 비율 이상 (5항).
COVER_NUM_RATIO = 0.70

# ── 색 토큰 ──────────────────────────────────────────────────────────────
BG = "#F6F4EF"        # 오프화이트
INK = "#111111"
SUB = "#6E6E6E"
LINE = "#E3E0D8"
UP = "#E5484D"        # 상승·증가 **전용**
DOWN = "#2F6FED"      # 하락·감소 **전용**
ACCENT = "#FFE45C"    # 일반 강조(형광펜 띠) 전용
NEUTRAL = "#C9C6BE"   # 차트 비강조
COVER_INK = "#FFFFFF"  # 사진 표지 본문
COVER_KEY = "#FFE45C"  # 사진 표지 키워드(첫 줄)

# ── 브랜드 ───────────────────────────────────────────────────────────────
# 인스타 사용자명은 영문·숫자·_·. 만 쓸 수 있다. 공백·한글은 들어가지 않는다.
# 이미지 상단에 박히는 값이라 실제 핸들과 달라지면 유입이 끊긴다.
HANDLE = os.environ.get("SNS_HANDLE", "@proptech_ds")
# 로고 파일이 없으면 계정명 워드마크 박스로 대신한다 (지시사항 4항).
LOGO = ROOT / "assets" / "brand" / "logo.png"
MARK = 64            # 브랜드 마크 한 변
WORDMARK = os.environ.get("SNS_WORDMARK", HANDLE)
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

/* 세로 중앙 정렬을 쓰지 않는다 (지시사항 5항).
   중앙에 띄우면 위아래가 똑같이 비어서 "덜 채운 장"처럼 보인다. 상단 정보줄
   아래 BODY_TOP 에서 시작하고, 남는 공간은 글자·숫자를 키워 채운다. */
.body{{flex:1;display:flex;flex-direction:column;justify-content:flex-start;
      gap:32px;padding-top:{BODY_TOP - PAD_TOP}px;}}

/* 타이포 스케일 */
.kicker{{font-size:38px;font-weight:600;color:{SUB};letter-spacing:-.01em;}}
/* 헤드라인 88~104px (지시사항 2항). 그 아래로는 **넘칠 때만** 내려간다
   — 9항이 재시도 하한으로 72px 를 따로 정해 뒀다. */
.h1{{font-size:104px;font-weight:800;letter-spacing:-.03em;line-height:1.2;}}
.h1.sm{{font-size:88px;}}
.h1.xs{{font-size:88px;}}
.lead{{font-size:36px;font-weight:500;line-height:1.5;color:{INK};}}
.sub{{font-size:34px;font-weight:500;line-height:1.5;color:{SUB};}}
.label{{font-size:38px;font-weight:600;color:{SUB};letter-spacing:-.01em;}}

/* 대형 숫자 — 표지와 hero 장 전용 */
/* 대형 숫자 220~280px (2항). 표지는 가로 폭 70% 이상이어야 해서(5항)
   렌더 단계에서 따로 키운다 — carousel.fit_cover() */
.big{{font-size:280px;font-weight:800;letter-spacing:-.04em;line-height:.95;}}
.big.sm{{font-size:248px;}}
.big.xs{{font-size:220px;}}
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
.bars{{display:flex;flex-direction:column;gap:32px;}}
.bar-row{{display:flex;flex-direction:column;gap:8px;}}
.bar-top{{display:flex;justify-content:space-between;align-items:baseline;}}
.bar-name{{font-size:34px;font-weight:600;}}
.bar-val{{font-size:38px;font-weight:800;letter-spacing:-.02em;}}
.bar-track{{height:30px;border-radius:15px;background:#EDEAE2;overflow:hidden;}}
.bar-fill{{height:100%;border-radius:15px;}}

/* 순위 막대 */
.rank{{display:flex;flex-direction:column;gap:16px;}}
.rank-row{{display:flex;align-items:center;gap:24px;}}
.rank-name{{width:280px;font-size:32px;font-weight:600;text-align:right;
           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
/* 배수 막대는 1.0~1.7 처럼 범위가 좁아 0 부터 그리면 차이가 안 보인다.
   "평소=1.0" 자리에 기준선을 그어 초과분이 읽히게 한다. */
.rank-track{{flex:1;height:24px;position:relative;
            background:#EDEAE2;border-radius:999px;}}
/* 기준선은 굵게. 가늘면 "평소"가 어디인지 안 보여서 막대 길이만 남는다. */
.rank-base{{position:absolute;top:-8px;bottom:-8px;width:4px;
           background:{INK};opacity:.8;border-radius:2px;}}
.rank-baselabel{{font-size:24px;color:{SUB};margin-top:8px;line-height:1.45;}}
/* 기준선까지는 중립색, 기준선을 넘은 부분만 의미색 (지시사항 5항).
   막대 전체를 칠하면 "평소만큼 거래된 것"까지 빨갛게 보인다. */
.rank-fill{{position:absolute;left:0;top:0;height:100%;
           border-radius:999px;background:{NEUTRAL};opacity:.55;}}
.rank-over{{position:absolute;top:0;height:100%;
           border-radius:0 999px 999px 0;}}
.rank-val{{width:150px;font-size:30px;font-weight:700;}}

/* 수치 행 */
.rows{{display:flex;flex-direction:column;gap:0;}}
.row{{display:flex;justify-content:space-between;align-items:baseline;
     padding:24px 0;border-bottom:2px solid {LINE};}}
.row:last-child{{border-bottom:none;}}
.row .k{{font-size:34px;font-weight:500;color:{SUB};}}
.row .v{{font-size:46px;font-weight:800;letter-spacing:-.02em;}}

/* 표본 배지 — 적은 표본을 숨기지 않고 드러낸다 */
.badge{{display:inline-block;font-size:26px;font-weight:600;color:{SUB};
       background:#EDEAE2;border-radius:999px;padding:8px 16px;}}


/* 브랜드 마크 — 출처 줄과 같은 높이, 안전 영역 안 */
/* 로고가 있으면 정사각 64×64, 없으면 계정명이 들어가야 해서 높이만 맞춘
   알약 박스로 쓴다. **기준점(오른쪽·아래)은 어느 쪽이든 같다** — 9항이
   요구하는 건 "모든 장의 같은 좌표"지 같은 크기가 아니다. */
.mark-brand{{position:absolute;right:{PAD_X}px;bottom:{PAD_BOTTOM - 48}px;
            height:{MARK}px;min-width:{MARK}px;border-radius:14px;padding:0 16px;
            display:flex;align-items:center;justify-content:center;
            background:{INK};overflow:hidden;}}
.mark-brand.logo{{width:{MARK}px;padding:0;}}
.mark-brand img{{width:100%;height:100%;object-fit:cover;}}
.mark-brand span{{color:#FFFFFF;font-size:22px;font-weight:800;
                 letter-spacing:-.02em;white-space:nowrap;}}
/* 출처 줄이 마크와 겹치지 않게 폭을 비워 둔다 */
.ft{{padding-right:260px;}}   /* 워드마크 자리를 비워 둔다 */

/* 조건 라벨 — 헤드라인 바로 위 */
.cond{{font-size:28px;font-weight:600;color:{SUB};letter-spacing:-.01em;}}

.quote{{font-size:64px;font-weight:700;line-height:1.35;letter-spacing:-.02em;}}
.cta{{font-size:34px;font-weight:600;line-height:1.5;}}
.disc{{font-size:24px;font-weight:400;color:{SUB};line-height:1.5;}}

/* ── 온도지도 ──────────────────────────────────────────────────────
   대상 하나만 칠하는 map_cover 와 달리 전부 칠한다. 어디가 뜨겁고 어디가
   식었는지를 한 장에 보여주는 게 목적이라, 전부 칠해야 그림이 된다. */
.heat{{display:flex;justify-content:center;}}
.heat-legend{{display:flex;align-items:center;gap:0;margin-top:8px;}}
.heat-legend i{{flex:1;height:24px;}}
.heat-legend i:first-child{{border-radius:12px 0 0 12px;}}
.heat-legend i:last-child{{border-radius:0 12px 12px 0;}}
.heat-ticks{{display:flex;justify-content:space-between;margin-top:8px;
            font-size:24px;color:{SUB};}}

/* ── ranking_table ─────────────────────────────────────────────────
   명단형 장. 막대보다 **값을 정확히 읽히게** 하는 게 목적이라 숫자 열을
   오른쪽 정렬하고 tnum 으로 자릿수를 고정한다. */
.rt-eyebrow{{font-size:24px;font-weight:700;letter-spacing:.08em;color:{SUB};}}
.rt{{display:flex;flex-direction:column;}}
.rt-row{{display:grid;grid-template-columns:56px 260px 1fr 120px 120px;
        align-items:center;gap:16px;min-height:80px;padding:8px 16px;
        border-bottom:1px solid {LINE};border-radius:12px;}}
.rt-row:last-child{{border-bottom:none;}}
/* 강조 행은 **하나만**. 형광펜 배경을 쓰고 글자색은 건드리지 않는다. */
.rt-row.hi{{background:{ACCENT};}}
.rt-rank{{font-size:28px;font-weight:700;color:{SUB};text-align:center;}}
.rt-name{{font-size:32px;font-weight:700;letter-spacing:-.01em;line-height:1.25;}}
.rt-name small{{display:block;font-size:24px;font-weight:500;color:{SUB};
               margin-top:8px;}}
.rt-val{{font-size:32px;font-weight:800;text-align:right;letter-spacing:-.02em;}}
.rt-chg{{font-size:30px;font-weight:800;text-align:right;letter-spacing:-.02em;}}
.rt-note{{font-size:24px;color:{SUB};line-height:1.45;}}
/* 행마다 "평소=1.0" 기준선과 초과분. 표는 값을 정확히 읽히게 하고,
   막대는 한눈에 비교되게 한다. 둘 다 필요하다. */
.rt-bar{{position:relative;height:20px;background:#EDEAE2;border-radius:999px;}}
.rt-bar b{{position:absolute;top:0;height:100%;border-radius:999px;}}
.rt-bar i{{position:absolute;top:-5px;bottom:-5px;width:3px;
          background:{INK};opacity:.7;border-radius:2px;}}

/* ── tile_grid ─────────────────────────────────────────────────────
   "모음"형 장. 2열 고정 — 3열로 늘리면 단지명이 줄바꿈돼 읽기가 끊긴다. */
.tiles{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
.tile{{background:#FFFFFF;border:1px solid {LINE};border-radius:24px;
      padding:24px;display:flex;flex-direction:column;gap:8px;}}
.tile .t-nm{{font-size:30px;font-weight:700;letter-spacing:-.01em;
            line-height:1.25;word-break:keep-all;}}
.tile .t-sub{{font-size:24px;font-weight:500;color:{SUB};}}
.tile .t-val{{font-size:44px;font-weight:800;letter-spacing:-.03em;}}
.tile .t-chg{{font-size:28px;font-weight:700;}}

/* ── 어두운 표지 ───────────────────────────────────────────────────
   피드에서 오프화이트만 일곱 장이면 묻힌다. **표지만** 어둡게 해서 눈에
   걸리게 하고, 2장부터는 다시 오프화이트로 돌아간다 — 지시사항 5항이
   "어두운 사진은 표지에만, 2장부터 오프화이트"라고 못 박은 그 이유다.
   토큰은 photo_cover 와 같은 걸 쓴다(--cover-ink / --cover-key). */
.card.dark{{background:{INK};}}
.card.dark .hd,.card.dark .ft,.card.dark .cond,.card.dark .mc-foot{{
  color:rgba(255,255,255,.62);}}
.card.dark .mc-h1{{color:{COVER_INK};}}
.card.dark .mc-num{{color:{COVER_KEY};}}
.card.dark .mark-brand{{background:{COVER_INK};}}
.card.dark .mark-brand span{{color:{INK};}}

/* ── map_cover ─────────────────────────────────────────────────────
   사진의 대안. 사진은 "마포구 ○○아파트 +53.5%" 옆에 두면 보는 사람이 그게
   그 단지라고 믿는다. 지도는 그 오인이 없고 데이터에서 바로 나온다. */
.mc-num{{font-size:148px;font-weight:800;letter-spacing:-.04em;line-height:1;}}
.mc-h1{{font-size:88px;font-weight:800;letter-spacing:-.03em;line-height:1.2;}}
.mc-map{{display:flex;justify-content:center;align-items:center;}}
.mc-foot{{font-size:24px;color:{SUB};line-height:1.45;}}

/* ── photo_cover ───────────────────────────────────────────────────
   사진은 **표지에만** 쓴다. 2장부터 오프화이트로 돌아가야 계정 정체성이
   유지된다 (지시사항 5항). */
.pc{{position:absolute;inset:0;overflow:hidden;background:{INK};}}
.pc-img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;}}
.pc-grad{{position:absolute;left:0;right:0;bottom:0;height:60%;}}
.pc-body{{position:absolute;left:{PAD_X}px;right:{PAD_X}px;
         bottom:{PAD_BOTTOM}px;display:flex;flex-direction:column;gap:16px;}}
.pc-cond{{font-size:28px;font-weight:600;color:rgba(255,255,255,.7);}}
.pc-h1{{font-size:96px;font-weight:800;letter-spacing:-.03em;line-height:1.15;}}
.pc-h1 .k{{color:{COVER_KEY};display:block;}}
.pc-h1 .b{{color:{COVER_INK};display:block;}}
.pc-ft{{font-size:24px;color:rgba(255,255,255,.75);line-height:1.45;
       padding-right:{MARK + 24}px;}}
/* 지역 풍경 사진이면 특정 단지로 오인되지 않게 밝힌다 (5-0항) */
.pc-note{{position:absolute;top:{PAD_TOP - 40}px;right:{PAD_X}px;
         font-size:20px;color:rgba(255,255,255,.8);}}
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


def pyeong(bucket: str) -> str:
    """'15P' → '10평대 후반'. 내부 코드를 화면에 그대로 내보내지 않는다.

    평형 버킷은 지표 계산용 식별자다. "15P"가 무슨 뜻인지 아는 건 이 파이프라인을
    만든 사람뿐이다.
    """
    if not bucket:
        return ""
    if bucket.endswith("+"):
        return f"{bucket[:-2]}평 이상"
    n = bucket.rstrip("P")
    if not n.isdigit():
        return bucket
    v = int(n)
    return f"{v - 5}평대 후반" if v % 10 else f"{v}평대"


def split_name(name: str, limit: int = 12) -> tuple[str, str]:
    """긴 단지명을 본체와 괄호로 가른다.

    '한라마을(주공2)' 같은 이름이 큰 폰트에서 줄을 넘긴다. 괄호를 떼어
    작은 글씨로 다음 줄에 둔다.
    """
    m = re.match(r"^(.*?)(\([^)]*\))\s*$", name.strip())
    if m and len(name) > limit:
        return m.group(1).strip(), m.group(2)
    return name, ""


def brand_mark() -> str:
    """모든 장 우하단 같은 자리에 찍는다 (지시사항 4항).

    캡처되어 돌아다닐 때 출처 계정을 알 수 있어야 한다. 장마다 위치가 달라지면
    여러 장을 이어 봤을 때 눈에 걸린다 — 9항이 "같은 좌표"를 요구하는 이유다.
    로고 파일이 없으면 워드마크 박스로 대신한다.
    """
    if LOGO.exists():
        b64 = base64.b64encode(LOGO.read_bytes()).decode()
        return (f'<div class="mark-brand logo">'
                f'<img src="data:image/png;base64,{b64}" alt=""></div>')
    return f'<div class="mark-brand"><span>{WORDMARK}</span></div>'


def cond(*parts: str) -> str:
    """헤드라인 위 대괄호 조건 라벨 (지시사항 4항).

    독자가 알아야 할 **조건·범위**만 쓴다. "지금 꼭 보세요" 같은 마케팅 문구는
    넣지 않는다 — 그 자리는 숫자가 어떤 범위에서 나온 값인지 알리는 자리다.
    """
    text = " · ".join(p for p in parts if p)
    return f'<div class="cond">[{text}]</div>' if text else ""


def head(page: int, total: int) -> str:
    return (f'<div class="hd"><span>{HANDLE} · {SERIES}</span>'
            f'<span>{page}/{total}</span></div>')


def foot(asof: str, extra: str = "") -> str:
    base = f"국토교통부 실거래가 · 해제 건 제외 · {asof} 기준"
    return f'<div class="ft">{extra + "<br>" if extra else ""}{base}</div>'
