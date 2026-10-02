"""T6 — 단지 식별키 검증.

핵심 질문 둘:
  1) 정규화가 단지를 가르는 정보(건설사명·차수)를 버리지 않는가
  2) 같은 단지의 표기 흔들림(동 번호·지번)으로 쪼개지지 않는가
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DIRS, make_apt_id, normalize_apt_name  # noqa: E402

TRADE = DIRS["master"] / "trade_events.parquet"


# ── 정규화 규칙 ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw,expected", [
    # 괄호가 단지를 가르는 정보 — 반드시 남아야 한다
    ("후곡마을(건영15)", "후곡마을건영15"),
    ("후곡마을(동성)", "후곡마을동성"),
    ("진주(5차)", "진주5차"),
    ("진주(일차)", "진주1차"),
    ("반달마을(동아)", "반달마을동아"),
    ("성산시영(대우)", "성산시영대우"),
    ("연수1차시영(영구임대)", "연수1차시영영구임대"),
    # 괄호가 위치 표기 — 버려야 한다
    ("구로두산(201동)", "구로두산"),
    ("한진(609-1)", "한진"),
    ("퇴계주공(351~359동)", "퇴계주공"),
    ("월드스테이트(101~111,124~132)", "월드스테이트"),
    ("송현주공솔빛마을(154)", "송현주공솔빛마을"),
    ("한진임대아파트(301동)(609-1)", "한진임대아파트"),
    ("삼성(550-0)", "삼성"),
    # 괄호 없음
    ("래미안대치팰리스", "래미안대치팰리스"),
    ("e-편한세상", "e-편한세상"),
])
def test_정규화_규칙(raw, expected):
    assert normalize_apt_name(raw) == expected


def test_빈값_처리():
    assert normalize_apt_name(None) == ""
    assert normalize_apt_name("") == ""
    assert normalize_apt_name("   ") == ""


def test_서로_다른_단지는_다른_id():
    """후곡마을의 건영15·동성·현대18 은 별개 단지다."""
    ld, addr = "4128510300", "후곡로 00010"
    ids = {make_apt_id(ld, f"후곡마을({c})", addr)
           for c in ("건영15", "동성", "현대18", "럭키", "롯데")}
    assert len(ids) == 5, "서로 다른 단지가 같은 id 를 받았다"


def test_같은_단지의_동번호_표기차이는_같은_id():
    ld, addr = "1153010200", "도림로 00059"
    a = make_apt_id(ld, "구로두산", addr)
    b = make_apt_id(ld, "구로두산(201동)", addr)
    c = make_apt_id(ld, "구로두산(202동)", addr)
    assert a == b == c


# ── 실제 데이터 ──────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def trades() -> pd.DataFrame:
    if not TRADE.exists():
        pytest.skip("trade_events.parquet 없음")
    return pd.read_parquet(TRADE, columns=[
        "apt_id", "apt_name_raw", "apt_name_norm",
        "legal_dong_code", "legal_dong_name", "road_address"])


def test_한_apt_id가_여러_정규화명을_삼키지_않는다(trades):
    """정규화명이 둘 이상이면 서로 다른 단지가 한 id 에 묶인 것이다."""
    g = trades.groupby("apt_id")["apt_name_norm"].nunique()
    bad = g[g > 1]
    assert len(bad) == 0, (
        f"과병합 {len(bad):,}건. 예: "
        f"{trades[trades.apt_id.isin(bad.index[:2])].apt_name_raw.unique()[:6]}")


def test_알려진_단지_5곳이_단일_키로_묶인다(trades):
    """표기가 흔들려도 한 단지는 한 id 여야 한다."""
    표본 = ["래미안대치팰리스", "도곡렉슬", "은마", "잠실엘스", "헬리오시티"]
    for 이름 in 표본:
        sub = trades[trades["apt_name_norm"] == 이름]
        if sub.empty:
            continue
        # 같은 (법정동, 주소) 안에서는 id 가 하나여야 한다
        n = sub.groupby(["legal_dong_code", "road_address"])["apt_id"].nunique()
        assert (n == 1).all(), f"{이름}: 같은 주소인데 id 가 갈림"


def test_apt_id_형식(trades):
    s = trades["apt_id"].drop_duplicates()
    assert s.str.len().eq(16).all()
    assert s.str.match(r"^[0-9a-f]{16}$").all()
