"""T14 — 주간 롱폼 대본 검증.

완료 기준은 "실제 주간 데이터로 1편 생성(음성 제외), T12 검증기 통과".
여기에 더해 **반대 지표 절이 실제로 반증을 담고 있는지**를 본다. 그 절이
빈 말이 되면 템플릿 전체가 투자 권유처럼 읽힌다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import longform as L  # noqa: E402
from content.validator import validate  # noqa: E402
from templates.disclaimers import DISCLAIMER_YOUTUBE  # noqa: E402


# ── 조사 ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("word,pair,expected", [
    ("황골마을주공1", "은는", "황골마을주공1은"),   # 받침 있는 숫자(일)
    ("주공3", "은는", "주공3은"),                   # 삼
    ("래미안2", "은는", "래미안2는"),               # 이 — 받침 없음
    ("오산시", "은는", "오산시는"),
    ("용인기흥구", "은는", "용인기흥구는"),
    ("강남", "은는", "강남은"),
    ("아파트", "이가", "아파트가"),
    ("단지", "이가", "단지가"),
    ("서울", "을를", "서울을"),
])
def test_조사가_받침에_맞는다(word, pair, expected):
    assert L.J(word, pair) == expected


def test_빈_단어도_터지지_않는다():
    assert L.josa("", "은는") == "는"


# ── 숫자 포맷 ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("v,expected", [
    (3628.0, "3,628"), (2683.0, "2,683"), (57.4, "57.4"),
    (105.3, "105.3"), (0, "0"), (None, "-"),
])
def test_낭독용_숫자_포맷(v, expected):
    assert L.num(v) == expected


# ── 대본 ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def data() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def script(data) -> dict:
    s = L.build(data)
    if s is None:
        pytest.skip("재료 부족")
    return s


def test_구성_순서가_고정이다(script):
    assert [s["id"] for s in script["sections"]] == [
        "hook", "region", "apt", "counter", "wrap"]


def test_T12_검증기를_통과한다(script, data):
    facts = {"params": data.get("params"),
             "sections": [s["facts"] for s in script["sections"]]}
    full = script["narration"] + "\n\n" + script["description"]
    r = validate(full, facts, kind="youtube")
    assert r.ok, r.reasons
    assert r.numbers_checked >= 20, f"검증된 숫자가 {r.numbers_checked}개뿐"


def test_유튜브_면책이_자막과_설명란_모두에_있다(script):
    assert script["burned_in_caption"] == DISCLAIMER_YOUTUBE
    assert DISCLAIMER_YOUTUBE in script["description"]


def test_설명란에_뉴스레터_동선이_있다(script):
    """Phase 7 M0 — Day 1부터 모든 콘텐츠에 가입 동선."""
    assert "뉴스레터" in script["description"] or "메일로" in script["description"]


# ── 반대 지표 (이 템플릿의 핵심) ─────────────────────────────────────────
def test_반대지표_절이_비어있지_않다(script):
    sec = next(s for s in script["sections"] if s["id"] == "counter")
    assert len(sec["narration"]) >= 150, "반대 지표가 한 문장짜리 구색이다"


def test_반대지표가_실제_반증을_담는다(script):
    """보일러플레이트가 아니라 데이터에서 고른 숫자여야 한다."""
    sec = next(s for s in script["sections"] if s["id"] == "counter")
    f = sec["facts"]
    assert f, "반대 지표에 근거 데이터가 없다"

    if "thin_rise" in f:
        r = f["thin_rise"]
        assert r["ppy_z"] >= L.STRONG_Z and r["deals_z"] <= 0, (
            "가격↑·거래↓ 가 아닌데 그렇게 말하고 있다")
    if "shrinking" in f:
        s_ = f["shrinking"]
        assert s_["deals_recent"] < s_["deals_prior"], (
            "거래가 줄었다고 했는데 실제로는 늘었다")


def test_반대지표가_신고지연과_취소를_언급한다(script):
    sec = next(s for s in script["sections"] if s["id"] == "counter")
    t = sec["narration"]
    assert "신고" in t and "취소" in t


# ── 안전 ─────────────────────────────────────────────────────────────────
def test_정확한_층수가_없다(script):
    from content.validator import check_floor_exposure
    assert not check_floor_exposure(script["narration"])


def test_금지표현이_없다(script):
    from content.validator import check_banned
    assert not check_banned(script["narration"])


def test_분량이_롱폼다운_길이다(script):
    """너무 짧으면 롱폼이 아니고, 너무 길면 5분 렌더 기준(T13)을 넘는다."""
    assert 800 <= script["char_count"] <= 2500, script["char_count"]


def test_재료가_없으면_만들지_않는다():
    """콘텐츠 없는 날은 발행하지 않는다 (Phase 6 폴백 규칙)."""
    assert L.build({"asof": "2026-01-01", "weekly": {}, "params": {}}) is None
