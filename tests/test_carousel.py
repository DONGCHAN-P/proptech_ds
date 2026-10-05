"""T16 — 캐러셀·썸네일 검증.

이미지에 박히는 글자도 발행되는 문구다. 텍스트와 같은 기준으로 검사한다.

특히 **썸네일에서 반대 지표가 묻히지 않는지**를 본다. 본문에서 반대 지표를
같은 비중으로 싣는데 썸네일에서 오른 숫자만 키우면 의미가 없다.
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


@pytest.fixture(scope="module")
def thumbs(data, outdir) -> list[dict]:
    t = C.build_thumbnails(data, outdir)
    if not t:
        pytest.skip("재료 부족")
    return t


# ── 장수·규격 ────────────────────────────────────────────────────────────
def test_캐러셀은_5에서_8장(cards):
    """로드맵 규격. 너무 적으면 밀도가 없고 많으면 안 넘긴다."""
    assert 5 <= len(cards) <= 8, len(cards)


def test_썸네일은_2안(thumbs):
    assert len(thumbs) == 2


def test_카드_규격이_정사각(cards):
    assert C.CARD == 1080


def test_썸네일_규격이_16대9():
    assert (C.THUMB_W, C.THUMB_H) == (1280, 720)
    assert abs(C.THUMB_W / C.THUMB_H - 16 / 9) < 0.01


# ── 문구 안전 ────────────────────────────────────────────────────────────
def test_이미지_문구에_금지표현이_없다(cards, thumbs):
    for it in cards + thumbs:
        t = C.strip_html(it["html"])
        assert not check_banned(t), f"{it['name']}: {check_banned(t)}"


def test_이미지_문구에_정확한_층수가_없다(cards, thumbs):
    for it in cards + thumbs:
        t = C.strip_html(it["html"])
        assert not check_floor_exposure(t), it["name"]


def test_이미지_숫자가_전부_출처가_있다(cards, thumbs):
    for it in cards + thumbs:
        t = C.strip_html(it["html"])
        r = validate(t, it["facts"], require_disclaimer=False)
        assert r.ok, f"{it['name']}: {r.reasons}"


def test_마지막_카드에_면책이_있다(cards):
    from templates.disclaimers import DISCLAIMER_SOCIAL
    last = C.strip_html(cards[-1]["html"])
    assert DISCLAIMER_SOCIAL.replace(" ", "") in last.replace(" ", "")


def test_출처가_모든_카드에_있다(cards):
    """마지막 장은 면책이 출처를 대신한다."""
    for c in cards[:-1]:
        assert "국토교통부" in C.strip_html(c["html"]), c["name"]


# ── 반대 지표 (핵심) ─────────────────────────────────────────────────────
def test_캐러셀에_반대지표_카드가_있다(cards):
    names = [c["name"] for c in cards]
    assert any("counter" in n for n in names), names


def test_썸네일이_오른숫자만_키우지_않는다(thumbs):
    """단지 썸네일은 가격과 거래를 같은 글자 크기로 둬야 한다.

    오른 숫자만 크면 썸네일에서는 그것만 보이고 반대 지표가 묻힌다.
    """
    apt = next((t for t in thumbs if "apt" in t["name"]), None)
    if apt is None:
        pytest.skip("단지 썸네일 없음")
    html = apt["html"]
    # .vl(큰 수치)이 두 개여야 하고, 둘 다 같은 클래스 크기를 쓴다
    assert html.count('class="vl') == 2, "큰 수치가 두 개가 아니다"
    assert "up" in html and "dn" in html, "상승/하락 양쪽이 없다"


def test_썸네일에_차트를_넣지_않는다(thumbs):
    """썸네일 크기에선 축 라벨이 안 읽히고 숫자 자리만 먹는다."""
    for t in thumbs:
        assert "<img" not in t["html"], f"{t['name']} 에 이미지가 들어갔다"


# ── 실사 이미지 금지 ─────────────────────────────────────────────────────
def test_생성_이미지를_쓰지_않는다():
    """실사풍 건물 이미지는 실제 단지 오인을 부른다 (로드맵 규칙)."""
    src = (ROOT / "content" / "carousel.py").read_text(encoding="utf-8")
    for 금지 in ("fal.ai", "fal_client", "FAL_KEY", "dall-e", "midjourney",
                 "stable-diffusion", "text2img"):
        assert 금지 not in src, f"이미지 생성 흔적: {금지}"


def test_차트는_우리가_만든_PNG만_쓴다(cards, outdir):
    """카드에 들어가는 이미지는 T11 산출물이어야 한다."""
    for c in cards:
        for m in re.finditer(r'src="([^"]+)"', c["html"]):
            assert m.group(1).startswith("data:image/png;base64,"), (
                f"{c['name']} 외부 이미지 참조")


# ── 렌더 산출물 ──────────────────────────────────────────────────────────
def test_렌더된_파일이_존재한다(outdir, cards, thumbs):
    missing = [it["name"] for it in cards + thumbs
               if not (outdir / f"{it['name']}.png").exists()]
    if missing:
        pytest.skip(f"아직 렌더 안 됨: {missing[:3]}")
    for it in cards + thumbs:
        p = outdir / f"{it['name']}.png"
        assert p.stat().st_size > 8_000, f"{p.name} 이 너무 작다 (빈 이미지?)"
