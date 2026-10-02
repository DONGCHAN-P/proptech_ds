"""T5a — 거래 고유 해시키 검증."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DIRS, make_deal_hash  # noqa: E402

TRADE = DIRS["master"] / "trade_events.parquet"


# ── 함수 단위 ────────────────────────────────────────────────────────────
def test_같은_입력은_같은_해시():
    a = make_deal_hash("1168010600", "래미안대치팰리스", "2026-07-09", 470000, 93.18, 4)
    b = make_deal_hash("1168010600", "래미안대치팰리스", "2026-07-09", 470000, 93.18, 4)
    assert a == b


def test_한_필드만_달라도_해시가_달라진다():
    base = ("1168010600", "래미안대치팰리스", "2026-07-09", 470000, 93.18, 4)
    h = make_deal_hash(*base)
    변형 = [
        ("1168010700", *base[1:]),                       # 법정동
        (base[0], "래미안대치팰리스2", *base[2:]),          # 단지명
        (*base[:2], "2026-07-10", *base[3:]),            # 계약일
        (*base[:3], 480000, *base[4:]),                  # 금액
        (*base[:4], 93.19, base[5]),                     # 면적
        (*base[:5], 5),                                  # 층
    ]
    for v in 변형:
        assert make_deal_hash(*v) != h, f"해시가 안 바뀜: {v}"


def test_숫자_표기_차이는_같은_해시():
    """470000 과 470000.0, 93.18 과 93.180 은 같은 거래다."""
    assert (make_deal_hash("1168010600", "A", "2026-07-09", 470000, 93.18, 4)
            == make_deal_hash("1168010600", "A", "2026-07-09", 470000.0, 93.1800, 4))


def test_날짜가_timestamp여도_동작():
    ts = pd.Timestamp("2026-07-09 00:00:00")
    assert (make_deal_hash("1168010600", "A", ts, 470000, 93.18, 4)
            == make_deal_hash("1168010600", "A", "2026-07-09", 470000, 93.18, 4))


def test_결측값이_있어도_예외없이_해시된다():
    assert len(make_deal_hash("1168010600", "A", "2026-07-09", 470000, 93.18, None)) == 16
    assert len(make_deal_hash(None, None, "2026-07-09", None, None, None)) == 16


def test_apt_id_정의와_무관하다():
    """apt_id 가 바뀌어도 deal_hash 는 살아남아야 한다 — 입력에 apt_id 가 없다."""
    import inspect
    src = inspect.getsource(make_deal_hash)
    assert "apt_id" not in src.split('"""')[2], "deal_hash 계산에 apt_id 가 섞였다"


# ── 실제 데이터 ──────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def trades() -> pd.DataFrame:
    if not TRADE.exists():
        pytest.skip("trade_events.parquet 없음")
    df = pd.read_parquet(TRADE, columns=[
        "deal_hash", "first_seen_date", "first_seen_is_estimate",
        "legal_dong_code", "apt_name_norm", "deal_date",
        "deal_amount", "area_m2", "floor"])
    return df


def test_컬럼이_존재한다(trades):
    for c in ("deal_hash", "first_seen_date", "first_seen_is_estimate"):
        assert c in trades.columns


def test_deal_hash_중복_0건(trades):
    dup = len(trades) - trades["deal_hash"].nunique()
    assert dup == 0, f"deal_hash 중복 {dup:,}건"


def test_deal_hash_결측_0건(trades):
    assert trades["deal_hash"].isna().sum() == 0
    assert (trades["deal_hash"].str.len() == 16).all()


def test_저장된_해시가_재계산과_일치(trades):
    s = trades.head(500)
    calc = [make_deal_hash(r.legal_dong_code, r.apt_name_norm, r.deal_date,
                           r.deal_amount, r.area_m2, r.floor)
            for r in s.itertuples()]
    assert (pd.Series(calc, index=s.index) == s["deal_hash"]).all()


def test_first_seen이_계약일보다_빠르지_않다(trades):
    """우리가 계약일 이전에 그 거래를 알 수는 없다."""
    bad = trades[trades["first_seen_date"] < trades["deal_date"]]
    assert len(bad) == 0, f"계약일보다 먼저 관측된 거래 {len(bad):,}건"
