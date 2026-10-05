"""T16 — 캐러셀 검증.

이미지에 박히는 글자도 발행되는 문구다. 텍스트와 같은 기준으로 검사한다.

썸네일(16:9)은 이 모듈에서 빠졌다. 지시사항상 16:9 는 유튜브 전용이고,
유튜브는 T13(영상)에서 다룬다. 그 전까지 쓰지 않는 규격을 만들지 않는다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import carousel as C  # noqa: E402
from content import design as D  # noqa: E402
from content.validator import check_banned, check_floor_exposure, validate  # noqa: E402


@pytest.fixture(scope="module")
def data() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def outdir(data) -> Path:
    return ROOT / "output" / data["asof"]


@pytest.fixture(scope="module")
def cards(data, outdir) -> list[dict]:
    c = C.build_cards(data, outdir)
    if not c:
        pytest.skip("재료 부족")
    return c


# ── 장수·규격 ────────────────────────────────────────────────────────────
def test_캐러셀은_5에서_8장(cards):
    """로드맵 규격. 너무 적으면 밀도가 없고 많으면 안 넘긴다."""
    assert 5 <= len(cards) <= 8, len(cards)


def test_캔버스가_4대5():
    """피드에서 1:1 보다 세로를 20% 더 차지한다."""
    assert (D.W, D.H) == (1080, 1350)
    assert abs(D.W / D.H - 4 / 5) < 0.01


def test_핵심요소가_프로필_크롭_안에_들어간다():
    """프로필 그리드는 3:4 로 자른다 — 1350 높이면 가운데 1012px 만 남는다.

    좌우 여백이 그보다 좁으면 글자가 잘린다. 본문 폭이 SAFE_CORE 안에
    들어가는지로 본다.
    """
    assert D.SAFE_CORE <= round(D.H * 3 / 4) + 1, "안전폭이 3:4 크롭보다 넓다"
    assert D.W - 2 * D.PAD_X <= D.SAFE_CORE, "본문이 크롭 밖으로 나간다"


# ── 레이아웃 ─────────────────────────────────────────────────────────────
def test_같은_레이아웃이_연속되지_않는다(cards):
    """7장이 같은 틀이면 넘길 이유가 없어진다."""
    assert not C.check_layout_variety(cards)


def test_레이아웃이_최소_네_종류(cards):
    assert len({c["layout"] for c in cards}) >= 4


# ── 문구 안전 ────────────────────────────────────────────────────────────
def test_이미지_문구에_금지표현이_없다(cards):
    for c in cards:
        t = C.strip_html(c["html"])
        assert not check_banned(t), f"{c['name']}: {check_banned(t)}"


def test_이미지_문구에_정확한_층수가_없다(cards):
    for c in cards:
        t = C.strip_html(c["html"])
        assert not check_floor_exposure(t), c["name"]


def test_이미지_숫자가_전부_출처가_있다(cards):
    for c in cards:
        t = C.strip_html(c["html"])
        r = validate(t, c["facts"], require_disclaimer=False)
        assert r.ok, f"{c['name']}: {r.reasons}"


def test_카드에_통계용어가_없다(cards):
    """σ·표준편차는 '평소의 1.7배'로 번역해 쓴다."""
    for c in cards:
        D.assert_no_jargon(C.strip_html(c["html"]), c["name"])


def test_자극적인_수식어가_없다(cards):
    assert not C.check_copy(cards)


def test_마지막_카드에_면책이_있다(cards):
    from templates.disclaimers import DISCLAIMER_SOCIAL
    last = C.strip_html(cards[-1]["html"])
    assert DISCLAIMER_SOCIAL.replace(" ", "") in last.replace(" ", "")


def test_출처가_모든_카드에_있다(cards):
    """마지막 장은 면책이 출처를 대신한다."""
    for c in cards[:-1]:
        assert "국토교통부" in C.strip_html(c["html"]), c["name"]


def test_모든_카드에_계정_핸들이_있다(cards):
    """캡처되어 퍼져도 출처 계정을 알 수 있어야 한다."""
    for c in cards:
        assert D.HANDLE in c["html"], c["name"]


# ── 반대 지표 (핵심) ─────────────────────────────────────────────────────
def test_캐러셀에_반대지표_카드가_있다(cards):
    names = [c["name"] for c in cards]
    assert any("counter" in n for n in names), names


def test_표본이_적으면_드러낸다(cards):
    """표본 경고를 장으로 따로 둔다. 각주로 숨기면 아무도 안 읽는다."""
    assert any("sample" in c["name"] for c in cards)


def test_큰숫자_장은_표본이_충분한_값만_쓴다(data):
    """연천군 7건으로 '평소의 2.4배'를 뽑으면 거짓말이 된다."""
    t = C.pick(data)
    if t is None:
        pytest.skip("재료 부족")
    z = data["weekly"]["sgg_zscore"]
    if any(r["week_deals"] >= C.MIN_SAMPLE for r in z if r.get("deals_avg_52w")):
        assert t["busiest"]["week_deals"] >= C.MIN_SAMPLE


# ── 이미지 출처 ──────────────────────────────────────────────────────────
def test_생성_이미지를_쓰지_않는다():
    """실사풍 건물 이미지는 실제 단지 오인을 부른다 (로드맵 규칙)."""
    src = (ROOT / "content" / "carousel.py").read_text(encoding="utf-8")
    for 금지 in ("fal.ai", "fal_client", "FAL_KEY", "dall-e", "midjourney",
                 "stable-diffusion", "text2img"):
        assert 금지 not in src, f"이미지 생성 흔적: {금지}"


def test_외부_이미지를_참조하지_않는다(cards):
    """렌더 시점에 네트워크를 타면 그날 발행이 네트워크에 걸린다."""
    for c in cards:
        for m in re.finditer(r'src="([^"]+)"', c["html"]):
            assert not m.group(1).startswith("http"), (
                f"{c['name']} 외부 이미지 참조: {m.group(1)[:40]}")


def test_카드에_차트PNG를_끼우지_않는다(cards):
    """완성된 4:5 차트를 카드에 넣으면 제목·출처가 중복되고 높이가 안 맞는다.

    T11 의 단독 차트는 스레드에 붙이는 1~2장으로 쓴다.
    """
    for c in cards:
        assert "<img" not in c["html"], f"{c['name']} 에 이미지가 들어갔다"


def test_같은_그래프를_두_번_보여주지_않는다(cards):
    """지역 순위를 2장과 4장에 각각 그리던 시절의 회귀를 막는다."""
    bars = [c["name"] for c in cards if c["layout"] == "ranked_bars"]
    assert len(bars) <= 1, bars


def test_양_끝을_같이_보여준다(cards):
    """붐빈 쪽만 보여주면 '수도권 거래가 늘었다'로 읽힌다."""
    ex = next((c for c in cards if c["name"] == "03_extremes"), None)
    assert ex is not None, [c["name"] for c in cards]
    html = ex["html"]
    assert 'class="v up"' in html and 'class="v down"' in html, (
        "증감 양쪽이 같은 장에 없다")


# ── 렌더 산출물 ──────────────────────────────────────────────────────────
def test_렌더된_파일이_존재한다(outdir, cards):
    missing = [c["name"] for c in cards
               if not (outdir / f"{c['name']}.png").exists()]
    if missing:
        pytest.skip(f"아직 렌더 안 됨: {missing[:3]}")
    for c in cards:
        p = outdir / f"{c['name']}.png"
        assert p.stat().st_size > 8_000, f"{p.name} 이 너무 작다 (빈 이미지?)"
