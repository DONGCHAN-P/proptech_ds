"""지역·비교 단위 아젠다 (subway · timetravel, 공용 뼈대 agenda).

단지 소개와 가르는 점: 이들은 **모르는 사람에게도 통한다**. 릴스는 나를
모르는 사람에게 노출되는 매체라, 설명이 필요한 소재는 첫 2초를 못 넘긴다.

여기서 지키는 것
  ① 모든 아젠다가 같은 규격을 따른다 (첫 프레임 완성 · 출처 · 면책)
  ② 화면의 숫자는 전부 재료에 근거가 있다
  ③ 착시를 걷어낸 숫자를 쓴다 — 역세권 1.7배는 도심 대 외곽이었다
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import agenda as A  # noqa: E402
from content import design as D  # noqa: E402
from content import reels as R  # noqa: E402
from content import subway as SW  # noqa: E402
from content import timetravel as TT  # noqa: E402


# ── 공용 뼈대 ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("man,want", [
    (60000, "6억"), (31000, "3.1억"), (105000, "10.5억"), (20000, "2억"),
])
def test_억_단위로_적는다(man, want):
    assert A.eok(man) == want


def test_평당가는_만원_단위():
    assert A.man(3222) == "3,222만원"


def test_막대는_가장_큰_값을_채운다():
    h = A.bar_rows([("가", 100, "#f00"), ("나", 50, "#999")])
    assert "100.0%" in h and "50.0%" in h


def test_값이_0이어도_막대가_보인다():
    """0% 막대는 사라져서, 그 줄이 비어 보인다."""
    assert "4.0%" in A.bar_rows([("가", 100, "#f00"), ("나", 0, "#999")])


def test_면책과_팔로우가_마지막_장에_있다():
    sc = A.follow({}, lead="또 올게요", notes=["주의 한 줄"])
    t = R.strip_html(sc["body"](1.0))
    assert D.HANDLE in t and "주의 한 줄" in t
    assert sc["last"] is True


def test_검증은_재료에_없는_숫자를_잡는다():
    bad = [{"facts": {}, "body": lambda p: "<div>갑자기 777건</div>"}]
    assert A.check(bad, "t")


def test_검증은_근거가_있으면_통과시킨다():
    ok = [{"facts": {"n": 777}, "body": lambda p: "<div>777건</div>"}]
    assert A.check(ok, "t") == []


# ── 아젠다 공통 규격 ─────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def sw():
    try:
        return SW.compute()
    except Exception as e:
        pytest.skip(f"역세권 계산 불가: {e}")


@pytest.fixture(scope="module")
def tt():
    try:
        return TT.compute()
    except Exception as e:
        pytest.skip(f"시간여행 계산 불가: {e}")


@pytest.fixture(params=["subway", "timetravel"])
def scs(request, sw, tt):
    return SW.scenes(sw) if request.param == "subway" else TT.scenes(tt)


def test_훅은_첫_프레임부터_완성돼_있다(scs):
    """릴스는 첫 프레임이 전부다. 단지 덱과 같은 규칙."""
    assert scs[0].get("static") is True
    assert R.strip_html(scs[0]["body"](0.01)) == \
        R.strip_html(scs[0]["body"](1.0))


def test_장면이_5에서_8개(scs):
    assert 5 <= len(scs) <= 8


def test_모든_장에_출처가_있다(scs):
    for i, sc in enumerate(scs, 1):
        assert "국토교통부" in sc["foot"], f"{i}장"


def test_마지막_장에_면책과_팔로우(scs):
    t = R.strip_html(scs[-1]["body"](1.0))
    assert D.HANDLE in t
    assert "투자" in t or "책임" in t


def test_통계용어가_없다(scs):
    for i, sc in enumerate(scs, 1):
        D.assert_no_jargon(R.strip_html(sc["body"](1.0)), f"a{i}")


def test_화면의_숫자가_전부_근거가_있다(scs):
    assert A.check(scs, "a") == []


# ── 역세권: 착시를 걷어낸다 ──────────────────────────────────────────────
def test_같은_구_안에서_다시_잰다(sw):
    """전체 비교(1.7배)는 역세권 효과가 아니라 도심 대 외곽이다.
    역은 사람 많은 곳에 놓이니 역 근처가 비싼 게 당연하다."""
    assert sw["median_gap"] < sw["naive"], \
        "통제한 값이 더 커지면 전제가 틀린 것"


def test_통념이_틀리는_곳을_센다(sw):
    """'역세권은 비싸다'가 모든 곳에서 참은 아니다. 그 수를 밝힌다."""
    assert sw["cheaper_n"] == sum(1 for r in sw["rows"] if r["gap"] < 1)


def test_착시_장면이_두_숫자를_같이_보여준다(sw):
    t = R.strip_html(SW.scenes(sw)[2]["body"](1.0))
    assert str(sw["naive"]) in t and str(sw["median_gap"]) in t


def test_직선거리임을_밝힌다(sw):
    t = R.strip_html(SW.scenes(sw)[-1]["body"](1.0))
    assert "직선거리" in t


def test_표본이_얇은_시군구는_뺀다(sw):
    for r in sw["rows"]:
        assert r["near_n"] >= SW.SGG_MIN and r["far_n"] >= SW.SGG_MIN


# ── 시간여행 ─────────────────────────────────────────────────────────────
def test_같은_값에서_갈라진_짝을_찾는다(tt):
    """'그때 같은 값이었다'가 성립해야 이야기가 선다."""
    if not tt["pair"]:
        pytest.skip("짝 없음")
    hi, lo = tt["pair"]
    lo_p, hi_p = sorted((hi["old"], lo["old"]))
    assert hi_p <= lo_p * (1 + TT.SAME_TOL), "출발값이 같지 않다"
    assert hi["new"] >= lo["new"]


def test_같은_집을_따라간_게_아님을_밝힌다(tt):
    """중위가는 그해 거래된 집들의 가운데 값이다. 재건축·신축이 섞인다."""
    t = R.strip_html(TT.scenes(tt)[-1]["body"](1.0))
    assert "같은 집" in t


def test_물가도_올랐다는_것을_밝힌다(tt):
    """배수만 보면 과장된다."""
    t = R.strip_html(TT.scenes(tt)[-1]["body"](1.0))
    assert "물가" in t


def test_표본이_얇은_해는_뺀다(tt):
    for r in tt["rows"]:
        assert r["n_old"] >= tt["min_deals"] and r["n_new"] >= tt["min_deals"]


def test_배수가_큰_순으로_줄_세운다(tt):
    times = [r["times"] for r in tt["rows"]]
    assert times == sorted(times, reverse=True)
