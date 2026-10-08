"""예산 지도 (content/budget.py).

단지 소개와 다른 아젠다다. "부천 보람마을"은 그 단지를 아는 사람에게만 뜻이
통하는데, 릴스는 모르는 사람에게 노출되는 매체다 (실측 평균 시청 2초).
예산은 설명이 필요 없고 보는 사람 모두가 자기 숫자를 갖고 있다.

여기서 막는 것
  ① 얇은 표본으로 비율을 말하는 것 — 12건 중 1건을 8% 로 쓰면 거짓말이다
  ② 화면의 숫자가 재료에 없는 것 — 반올림한 값도 발행되는 값이다
  ③ "거래가 있었다"가 "지금 그 값에 살 수 있다"로 읽히는 것
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import budget as B  # noqa: E402
from content import design as D  # noqa: E402
from content import geo as G  # noqa: E402
from content import reels as R  # noqa: E402


def row(name, deals, under, *, code="11000", mid=60000) -> dict:
    return {"sigungu_name": name, "sigungu_code": code, "deals": deals,
            "under": under, "ratio": round(under / deals, 4), "median": mid}


def fake(cap=60000) -> dict:
    rows = [row("전부구", 500, 500), row("대부분구", 400, 380),
            row("반반구", 300, 150), row("조금구", 200, 20),
            row("없는구", 724, 0)]
    return {"cap": cap, "cap_label": B.won_eok(cap), "asof": "2026-10-06",
            "pyeong_label": B.PYEONG_LABEL, "months": 12,
            "min_deals": B.MIN_DEALS, "rows": rows,
            "none": [r for r in rows if r["under"] == 0],
            "all_": [r for r in rows if r["ratio"] >= 0.9],
            "mid": [r for r in rows if B.MID_LO <= r["ratio"] <= B.MID_HI]}


# ── 금액 표기 ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("man,want", [
    (60000, "6억"), (100000, "10억"), (75000, "7.5억"), (45000, "4.5억"),
])
def test_억_단위로_적는다(man, want):
    assert B.won_eok(man) == want


# ── 비율 표기 ────────────────────────────────────────────────────────────
def test_한_건도_없으면_0퍼센트로_적는다():
    """0.4% 를 반올림해 0% 로 적으면 '한 건도 없다'와 구분되지 않는다."""
    assert B.pct(row("가", 724, 0)) == "0%"
    assert B.pct(row("나", 1000, 2)) != "0%"


def test_거의_전부면_100퍼센트():
    assert B.pct(row("가", 894, 894)) == "100%"


# ── 표본 문턱 ────────────────────────────────────────────────────────────
def test_얇은_시군구는_비율을_말하지_않는다(monkeypatch):
    """12건 중 1건을 8% 로 쓰면 숫자가 거짓말을 한다."""
    assert B.MIN_DEALS >= 30


# ── 재료 ─────────────────────────────────────────────────────────────────
def test_반올림한_비율도_재료에_담는다():
    """비율을 0.77 로만 담으면 화면의 '77%' 가 출처 없는 숫자가 된다."""
    f = B.facts(fake())
    assert all("pct" in r for r in f["rows"])
    assert any(r["pct"] == 50 for r in f["rows"])


def test_평형_라벨의_숫자도_재료에_담는다():
    """'25~35평' 은 화면에 25 와 35 라는 숫자를 새로 만든다."""
    f = B.facts(fake())
    assert f["pyeong_lo"] == 25 and f["pyeong_hi"] == 35


def test_표본_문턱도_재료에_담는다():
    assert B.facts(fake())["min_deals"] == B.MIN_DEALS


def test_세는_값들이_재료에_있다():
    f = B.facts(fake())
    assert f["none_n"] == 1 and f["all_n"] == 2 and f["regions"] == 5


# ── 장면 ─────────────────────────────────────────────────────────────────
@pytest.fixture
def scs():
    return B.scenes(fake())


def test_여섯_장을_만든다(scs):
    assert len(scs) == 6


def test_훅은_첫_프레임부터_완성돼_있다(scs):
    """릴스는 첫 프레임이 전부다. 단지 덱과 같은 규칙."""
    assert scs[0].get("static") is True
    assert R.strip_html(scs[0]["body"](0.01)) == \
        R.strip_html(scs[0]["body"](1.0))


def test_마지막_장에_면책과_팔로우가_있다(scs):
    t = R.strip_html(scs[-1]["body"](1.0))
    assert D.HANDLE in t
    assert "투자" in t or "책임" in t


def test_모든_장에_출처가_있다(scs):
    for i, sc in enumerate(scs, 1):
        assert "국토교통부" in sc["foot"], f"{i}장"


def test_거래가_있었다는_뜻임을_적는다(scs):
    """'거래가 있었다'가 '지금 그 값에 살 수 있다'로 읽히면 안 된다."""
    t = R.strip_html(scs[-1]["body"](1.0))
    assert "실제로 거래된" in t


def test_표본을_비웠다는_사실을_적는다(scs):
    assert "비웠" in R.strip_html(scs[-1]["body"](1.0))


def test_화면_문구에_통계용어가_없다(scs):
    for i, sc in enumerate(scs, 1):
        D.assert_no_jargon(R.strip_html(sc["body"](1.0)), f"budget{i}")


def test_한_건도_없는_장은_건수를_그대로_보여준다(scs):
    """'0%' 보다 '724건 중 0건' 이 세다 — 표본이 작아서가 아님을 보인다."""
    t = R.strip_html(scs[3]["body"](1.0))
    assert "724" in t and "0건" in t


# ── 지도 색 ──────────────────────────────────────────────────────────────
def test_한_건도_없으면_빨강():
    c = G.bin_color(0.0, D.BG, D.UP, D.DOWN, D.NEUTRAL, B.BINS)
    assert c != D.BG and c == G.mix(D.BG, D.UP, 1.0)


def test_많을수록_진한_파랑():
    a = G.bin_color(0.3, D.BG, D.UP, D.DOWN, D.NEUTRAL, B.BINS)
    b = G.bin_color(0.95, D.BG, D.UP, D.DOWN, D.NEUTRAL, B.BINS)
    assert a != b
    assert b == G.mix(D.BG, D.DOWN, 1.0)


def test_표본이_없는_곳은_비운다():
    assert G.bin_color(None, D.BG, D.UP, D.DOWN, D.NEUTRAL,
                       B.BINS) == D.NEUTRAL


def test_구간과_범례가_짝이_맞는다():
    """하나라도 어긋나면 지도와 범례가 다른 말을 한다."""
    assert len(B.BINS) == len(B.LEGEND)


def test_평소_지도의_잣대를_바꾸지_않았다():
    """같은 heat() 를 쓰므로, 구간을 안 넘기면 예전 그대로여야 한다."""
    v = G.bin_color(1.5, D.BG, D.UP, D.DOWN, D.NEUTRAL)
    assert v == G.mix(D.BG, D.UP, 1.0)


# ── 아젠다끼리 파일을 두고 싸우지 않는다 ─────────────────────────────────
def test_렌더러가_파일_이름을_받는다():
    """이름이 고정이면 예산 지도가 단지 영상을 지운다. 실제로 지웠다."""
    import inspect
    sig = inspect.signature(R.render)
    assert "name" in sig.parameters
    assert sig.parameters["name"].default == "reels.mp4"


def test_예산_지도는_제_이름으로_저장한다(monkeypatch, tmp_path):
    got = {}
    def fake_render(scs, outdir, name="reels.mp4"):
        got["name"] = name
        f = tmp_path / name
        f.write_bytes(b"0")      # main 이 크기를 찍는다
        return f

    monkeypatch.setattr(R, "render", fake_render)
    monkeypatch.setattr(B, "compute", lambda *a, **k: fake())
    import sys as _s
    monkeypatch.setattr(_s, "argv", ["x", "--cap", "6"])
    B.main()
    assert got["name"] == "budget_6억.mp4"
