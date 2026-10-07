"""단지명 정규화 (content/aptname.py).

실거래가 원본은 끝의 '단지'가 빠져 있다. "신트리4" 를 영상에 그대로 띄우면
이름이 잘린 것처럼 읽히고, 숫자가 몇 동인지 몇 단지인지도 알 수 없다.

여기서 더 중요한 건 **모르는 이름을 건드리지 않는 것**이다. 한국어 합성어를
일반 규칙으로 가르려 들면 "한신트리플"이 "한신 트리플"이 된다. 틀리게 고치는
것보다 원본 그대로 두는 쪽이 낫다 — 적어도 검색은 되니까.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import aptname as A  # noqa: E402


# ── 단지 번호 ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw,want", [
    ("신트리4", "신트리 4단지"),
    ("주공1", "주공 1단지"),
    ("상계주공3", "상계주공 3단지"),
    ("황골마을주공1", "황골마을주공 1단지"),
    ("매화마을공무원2", "매화마을공무원 2단지"),
])
def test_맨숫자로_끝나면_단지를_붙인다(raw, want):
    """호갱노노·KB 모두 '신트리4단지' 로 쓴다. 원본만 '단지' 가 없다."""
    assert A.tidy(raw) == want


@pytest.mark.parametrize("raw,want", [
    ("목동신시가지12단지", "목동 신시가지 12단지"),
    ("구월힐스테이트1단지", "구월힐스테이트 1단지"),
    ("반정아이파크캐슬5단지", "반정아이파크캐슬 5단지"),
])
def test_이미_단지면_띄우기만_한다(raw, want):
    assert A.tidy(raw) == want


@pytest.mark.parametrize("raw,want", [
    ("선경2차", "선경 2차"),
    ("e편한세상서울대입구2차", "e편한세상서울대입구 2차"),
    ("호반써밋1차", "호반써밋 1차"),
])
def test_차는_차로_둔다(raw, want):
    """'2차' 를 '2단지' 로 바꾸면 다른 단지가 된다."""
    assert A.tidy(raw) == want


# ── 건드리면 안 되는 것 ──────────────────────────────────────────────────
@pytest.mark.parametrize("raw", [
    "한신트리플",          # 숫자가 없다
    "병점역아이파크캐슬",
    "래미안안양메가트리아",
    "충무주공(872)",       # 괄호로 끝난다 — 번지수지 단지 번호가 아니다
    "신정마을성지",
    "수원센트럴아이파크자이",
])
def test_모르는_이름은_그대로_둔다(raw):
    assert A.tidy(raw) == raw


@pytest.mark.parametrize("raw", [
    "신정7단지(상록)공무원",        # 숫자가 가운데 — 규칙으로는 못 고친다
    "한울마을1단지운정신도시IPARK",  # 지명과 브랜드가 뒤섞여 있다
])
def test_규칙이_못_고치는_이름은_사전에_있다(raw):
    """규칙을 늘려 억지로 맞추면 멀쩡한 이름이 망가진다. 매주 다루는
    단지는 몇 곳뿐이라 손으로 적는 편이 안전하다."""
    assert raw in A.aliases(), f"config/apt_aliases.json 에 {raw} 가 없다"
    assert A.tidy(raw) == A.aliases()[raw]


def test_세자리_숫자는_동_번호일_수_있어_두다():
    """'SK뷰101' 을 '101단지' 로 만들면 없는 단지가 생긴다."""
    assert A.tidy("SK뷰101") == "SK뷰101"
    assert A.tidy("현대아파트205") == "현대아파트205"


def test_빈_값에도_안_터진다():
    assert A.tidy("") == ""
    assert A.tidy(None) == ""


# ── 멱등 ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", [
    "신트리 4단지", "목동 신시가지 12단지", "선경 2차", "병점역아이파크캐슬",
])
def test_두_번_넣어도_같다(name):
    """normalize() 가 pick() 마다 불린다. 부를 때마다 띄어쓰기가 늘면
    "목동  신시가지   12단지" 가 된다."""
    assert A.tidy(A.tidy(name)) == A.tidy(name)


def test_겹친_공백을_정리한다():
    assert A.tidy("신트리  4") == "신트리 4단지"


# ── 아는 합성어 ──────────────────────────────────────────────────────────
def test_아는_앞머리만_가른다():
    assert A.tidy("목동신시가지8") == "목동 신시가지 8단지"
    assert A.tidy("올림픽선수기자촌1") == "올림픽 선수기자촌 1단지"


def test_가를_자리를_어림하지_않는다():
    """앞 두 글자가 동네 이름이라는 식으로 어림하면
    '올림픽선수기자촌' 이 '올림 픽선수기자촌' 이 된다."""
    assert "올림 픽" not in A.tidy("올림픽선수기자촌1")


# ── 수동 사전 ────────────────────────────────────────────────────────────
def test_사전이_규칙을_이긴다(monkeypatch):
    monkeypatch.setattr(A, "_alias", {"신트리4": "신트리 네번째단지"})
    assert A.tidy("신트리4") == "신트리 네번째단지"


def test_사전이_없거나_깨져도_돈다(monkeypatch, tmp_path):
    monkeypatch.setattr(A, "_alias", None)
    monkeypatch.setattr(A, "ALIAS_PATH", tmp_path / "없음.json")
    assert A.aliases() == {}
    assert A.tidy("신트리4") == "신트리 4단지"


def test_실제_사전_파일이_읽힌다():
    """파일이 깨지면 조용히 빈 사전이 되어 아무도 모른다."""
    assert isinstance(A.aliases(), dict)


# ── 지표 전체 ────────────────────────────────────────────────────────────
def test_지표_안의_이름을_빠짐없이_바꾼다():
    """표지만 바꾸고 이웃을 빼먹으면 한 화면에 두 표기가 섞인다."""
    data = {
        "daily": {"new_high": [{"apt_name": "신트리4"}]},
        "weekly": {"surge_apt": [{"apt_name": "주공1"}]},
        "profiles": {"a:20P": {
            "apt_name": "목동신시가지12",
            "neighbors": [{"apt_name": "목동신시가지8"}],
            "around": {"apts": [{"apt_name": "선경2차"}]},
        }},
    }
    A.normalize(data)
    assert data["daily"]["new_high"][0]["apt_name"] == "신트리 4단지"
    assert data["weekly"]["surge_apt"][0]["apt_name"] == "주공 1단지"
    p = data["profiles"]["a:20P"]
    assert p["apt_name"] == "목동 신시가지 12단지"
    assert p["neighbors"][0]["apt_name"] == "목동 신시가지 8단지"
    assert p["around"]["apts"][0]["apt_name"] == "선경 2차"


def test_빈_지표에도_안_터진다():
    A.normalize({})
    A.normalize({"daily": None, "weekly": {}, "profiles": None})


def test_모양이_달라도_안_터진다():
    """지표 JSON 에 리스트가 아닌 값이 섞여 들어와도 멈추면 안 된다."""
    A.normalize({"daily": {"params": 3, "x": [None, "문자열"]},
                 "profiles": {"a": None}})
