"""T11 — 차트 검증.

렌더러가 matplotlib 에서 HTML/SVG + Playwright 로 바뀌었다
(`docs/02_CLI_디자인지시사항.md` 7항). 검사 **의도**는 그대로다.

  · 한글이 두부(□)로 나오지 않는가  — 폰트를 파일로 심었는가로 본다
  · 증가=빨강 / 감소=파랑 (한국 관례)
  · 보조 요소가 데이터보다 연한가
  · 차트가 지표 JSON 밖의 숫자를 쓰지 않는가
  · 시간축이 실제 날짜 간격인가   — 거래가 있는 달만 등간격으로 찍으면
    13개월 공백이 1개월처럼 보인다
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import charts as C  # noqa: E402
from content import design as D  # noqa: E402

SRC = (ROOT / "content" / "charts.py").read_text(encoding="utf-8")


# ── 폰트 ─────────────────────────────────────────────────────────────────
def test_폰트를_파일로_심는다():
    """시스템 설치에 기대면 렌더 환경이 바뀔 때 조용히 대체 폰트로 떨어진다."""
    assert D.has_font(), "assets/fonts 에 Pretendard woff2 가 없다"


def test_폰트가_CSS에_실제로_들어간다():
    css = D.base_css()
    assert "@font-face" in css
    assert "data:font/woff2;base64," in css, "폰트를 외부 URL 에 기대고 있다"
    assert css.count("@font-face") >= 3, "굵기가 모자라면 위계가 안 선다"


def test_차트_SVG가_같은_폰트를_쓴다():
    """SVG 안에서 폰트 지정을 빠뜨리면 그 부분만 다른 글꼴로 나온다."""
    assert "font-family:Pretendard" in SRC


# ── 팔레트 ───────────────────────────────────────────────────────────────
def warmth(hex_: str) -> int:
    r, _, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return r - b


def lum(hex_: str) -> float:
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def test_발산축이_한국_관례를_따른다():
    """상승·증가가 빨강, 하락·감소가 파랑. 뒤집으면 국내 독자가 오독한다."""
    assert warmth(D.UP) > 0, "증가가 따뜻한 색이 아니다"
    assert warmth(D.DOWN) < 0, "감소가 차가운 색이 아니다"


def test_보조요소가_데이터보다_연하다():
    assert lum(D.LINE) > lum(D.UP), "격자가 데이터보다 진하다"
    assert lum(D.NEUTRAL) > lum(D.UP), "비강조가 강조보다 진하다"
    assert lum(D.SUB) > lum(D.INK), "보조 글자가 본문보다 진하다"


def test_강조색은_증감에만_쓴다():
    """빨강/파랑을 일반 강조에 쓰면 증감 신호가 죽는다. 강조는 형광펜 띠."""
    assert f"background:linear-gradient(to top,{D.ACCENT}" in D.base_css()


# ── 포맷 ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("man,expected", [
    (103000, "10.3억"), (10000, "1.0억"), (9999, "9,999만"),
    (1234567, "123억"), (0, "0만"), (None, "-"),
])
def test_금액_포맷(man, expected):
    assert D.won(man) == expected


def test_차트_글자가_26px_이상():
    """지시사항 7항. 그보다 작으면 피드에서 안 읽힌다."""
    small = [int(n) for n in re.findall(r'font-size="(\d+)"', SRC) if int(n) < 26]
    assert not small, f"26px 미만 글자: {small}"


# ── 렌더 ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def metrics() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


def test_지역비교_차트가_만들어진다(metrics):
    ch = C.chart_region(metrics)
    if not ch:
        pytest.skip("재료 부족")
    assert ch["in_card"].startswith("<svg")
    assert ch["title"] and ch["sub"]


def test_단지추이_차트가_만들어진다(metrics):
    ch = C.chart_apt(metrics)
    if not ch:
        pytest.skip("시계열 없음")
    assert ch["in_card"].startswith("<svg")


def test_차트_제목에_통계용어가_없다(metrics):
    """σ·표준편차는 일반 독자가 해석하지 못하고, 해석하려 들면 틀린다."""
    for ch in (C.chart_region(metrics), C.chart_apt(metrics)):
        if ch:
            D.assert_no_jargon(ch["title"] + ch["sub"], ch["name"])


def test_차트는_지표JSON_안의_숫자만_쓴다():
    """차트가 DB 를 따로 뒤지면 발행된 그림과 T12 숫자 검증기가 어긋난다."""
    for 금지 in ("duckdb", "read_parquet", "sqlite3", "trade_events"):
        assert 금지 not in SRC, f"차트 모듈이 {금지} 를 직접 쓴다"


def test_시계열은_실제_날짜축을_쓴다():
    """거래가 있는 달만 등간격으로 찍으면 13개월 공백이 1개월처럼 보인다."""
    assert "strptime" in SRC, "ym 문자열을 날짜로 바꾸지 않는다"
    assert "timestamp()" in SRC, "x 좌표를 실제 시간 간격으로 잡지 않는다"


def test_드문_거래는_선으로_잇지_않는다():
    """공백을 직선으로 이으면 없는 추세가 보인다. 점 + 이동평균만 쓴다."""
    assert "_svg_scatter_ma" in SRC
    assert "circle" in SRC, "거래를 점으로 찍지 않는다"
    assert 'fill="none"' in SRC, "추세선에 면적을 채우고 있다"


def test_단독_차트도_4대5():
    """유튜브(16:9)만 예외다. 피드용은 전부 1080x1350."""
    assert (C.CW, C.CH) == (1080, 1350)
