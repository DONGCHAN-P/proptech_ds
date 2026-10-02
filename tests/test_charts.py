"""T11 — 차트 템플릿 검증.

완료 기준이 "한글 깨짐 0". 폰트가 없으면 글자가 전부 두부(□)로 나오는데
PNG 만 봐서는 파이프라인이 알 수 없으므로 여기서 막는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

matplotlib = pytest.importorskip("matplotlib")
from content import charts as C  # noqa: E402


# ── 폰트 ─────────────────────────────────────────────────────────────────
def test_한글_폰트가_잡힌다():
    name = C.setup_font()
    assert "기본 폰트" not in name, f"한글 폰트 없음 — 글자가 두부로 나온다 ({name})"


def test_한글_글리프가_실제로_있다():
    """폰트 이름만 맞고 글리프가 없으면 그래도 두부가 된다."""
    from matplotlib.font_manager import FontProperties, findfont
    from matplotlib.ft2font import FT2Font

    C.setup_font()
    import matplotlib.pyplot as plt
    path = findfont(FontProperties(family=plt.rcParams["font.family"][0]))
    f = FT2Font(path)
    for ch in "시군구거래량단지억만원평":
        assert f.get_char_index(ord(ch)) != 0, f"'{ch}' 글리프 없음 ({path})"


def test_마이너스_기호가_깨지지_않는다():
    """axes.unicode_minus 를 끄지 않으면 음수 축 라벨이 네모로 나온다."""
    import matplotlib.pyplot as plt
    C.setup_font()
    assert plt.rcParams["axes.unicode_minus"] is False


# ── 팔레트 ───────────────────────────────────────────────────────────────
def test_발산축이_한국_관례를_따른다():
    """상승·증가가 빨강, 하락·감소가 파랑. 뒤집으면 국내 독자가 오독한다."""
    def warmth(hex_: str) -> int:
        r, _, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
        return r - b
    assert warmth(C.DIVERGE_POS) > 0, "증가가 따뜻한 색이 아니다"
    assert warmth(C.DIVERGE_NEG) < 0, "감소가 차가운 색이 아니다"


def test_축과_격자가_데이터보다_연하다():
    """격자가 선보다 진하면 데이터가 뒤로 밀린다."""
    def lum(hex_: str) -> float:
        r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    assert lum(C.GRID) > lum(C.SERIES_1)
    assert lum(C.AXIS) > lum(C.SERIES_1)
    assert lum(C.INK_MUTED) > lum(C.INK)


# ── 포맷 ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("man,expected", [
    (103000, "10.3억"), (10000, "1.0억"), (9999, "9,999만"),
    (1234567, "123억"), (0, "0만"), (None, "-"),
])
def test_금액_포맷(man, expected):
    assert C.won(man) == expected


# ── 렌더 ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def metrics() -> dict:
    p = C.latest_metrics()
    if p is None:
        pytest.skip("지표 JSON 없음")
    return json.loads(p.read_text(encoding="utf-8"))


def test_단지추이_차트가_생성된다(metrics, tmp_path):
    s = metrics.get("series") or []
    if not s:
        pytest.skip("시계열 없음")
    C.setup_font()
    out = C.chart_apt_trend(s[0], tmp_path / "t.png")
    assert out.exists() and out.stat().st_size > 10_000


def test_지역비교_차트가_생성된다(metrics, tmp_path):
    z = metrics.get("weekly", {}).get("sgg_zscore") or []
    if not z:
        pytest.skip("Z-score 없음")
    C.setup_font()
    out = C.chart_region_zscore(z, tmp_path / "r.png")
    assert out.exists() and out.stat().st_size > 10_000


def test_차트는_지표JSON_안의_숫자만_쓴다(metrics):
    """차트가 DB 를 따로 뒤지면 발행된 그림과 T12 숫자 검증기가 어긋난다."""
    src = (ROOT / "content" / "charts.py").read_text(encoding="utf-8")
    for 금지 in ("duckdb", "read_parquet", "sqlite3", "trade_events"):
        assert 금지 not in src, f"차트 모듈이 {금지} 를 직접 쓴다"


def test_시계열은_실제_날짜축을_쓴다():
    """거래가 있는 달만 등간격으로 찍으면 13개월 공백이 1개월처럼 보인다."""
    src = (ROOT / "content" / "charts.py").read_text(encoding="utf-8")
    assert "mdates" in src, "날짜 축(mdates)을 쓰지 않는다"
    assert "strptime" in src, "ym 문자열을 날짜로 바꾸지 않는다"
