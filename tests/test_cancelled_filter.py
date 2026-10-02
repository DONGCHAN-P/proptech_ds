"""T8 — 계약해제 필터 강제 검증.

해제된 거래가 지표나 발행 콘텐츠에 올라가면 안 된다. 취소된 거래를
"신고가"로 소개하는 건 되돌릴 수 없는 사고다.

실제로 step8 이 필터 없이 돌아서 해제 건 324건이 신규 거래에 섞였고, 그중
하나가 특이거래 Top 100 에 올라가 있었다. 그 재발을 막는 것이 이 파일의 일.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import DIRS  # noqa: E402
from metrics.filters import apply_filters, floor_band, trades_cte  # noqa: E402

TRADE = DIRS["master"] / "trade_events.parquet"
EXPORTS = DIRS["exports_daily"]


# ── 필터 함수 ────────────────────────────────────────────────────────────
def _fake() -> pd.DataFrame:
    return pd.DataFrame({
        "apt_name_raw": ["정상A", "해제B", "정상C", "저가D", "고가E"],
        "deal_amount": [50000, 60000, 70000, 100, 9_000_000],
        "area_m2": [84.0, 84.0, 84.0, 84.0, 84.0],
        "price_per_m2": [595, 714, 833, 1.2, 107_142],
        "floor": [2, 10, 20, None, 5],
        "is_canceled": [False, True, False, False, False],
    })


def test_해제건이_제외된다():
    out = apply_filters(_fake())
    assert "해제B" not in set(out["apt_name_raw"]), "해제된 거래가 남았다"


def test_가격_이상치가_제외된다():
    out = apply_filters(_fake())
    names = set(out["apt_name_raw"])
    assert "저가D" not in names and "고가E" not in names
    assert names == {"정상A", "정상C"}


def test_해제필터_끄기가_명시적이어야_한다():
    """기본값이 '제외'여야 한다. 깜빡하면 섞이는 구조면 안 된다."""
    assert len(apply_filters(_fake(), exclude_price_outliers=False)) == 4
    assert len(apply_filters(_fake(), exclude_cancelled=False,
                             exclude_price_outliers=False)) == 5


def test_세대수_모르는_단지는_남긴다():
    """K-apt 미등록 = 소규모가 아니다. 모르는 걸 작다고 단정하면 안 된다."""
    df = _fake().assign(households=[None, None, 150, 500, 1000])
    out = apply_filters(df, min_households=300)
    assert "정상A" in set(out["apt_name_raw"]), "세대수 미상인데 제외됐다"
    assert "정상C" not in set(out["apt_name_raw"]), "150세대가 안 걸러졌다"


@pytest.mark.parametrize("floor,band", [
    (1, "저층"), (3, "저층"), (4, "중층"), (15, "중층"),
    (16, "고층"), (40, "고층"), (None, "미상")])
def test_층_구간화(floor, band):
    assert floor_band(floor) == band


def test_SQL_CTE에_해제조건이_있다():
    sql = trades_cte("x.parquet")
    assert "is_canceled" in sql and "floor_band" in sql
    assert "deal_amount > 0" in sql


# ── 실제 데이터 ──────────────────────────────────────────────────────────
@pytest.mark.skipif(not TRADE.exists(), reason="trade_events 없음")
def test_SQL_CTE가_해제건을_걸러낸다():
    con = duckdb.connect()
    sql = trades_cte(TRADE.as_posix())
    n = con.execute(f"{sql} SELECT count(*) FROM trades "
                    f"WHERE coalesce(is_canceled, false)").fetchone()[0]
    assert n == 0, f"CTE 통과 후에도 해제건 {n:,}건"


@pytest.mark.skipif(not TRADE.exists(), reason="trade_events 없음")
def test_master에는_해제건이_남아있어야_한다():
    """정본은 해제 여부를 보존한다. 거르는 건 지표 단계의 일이다."""
    con = duckdb.connect()
    n = con.execute(f"SELECT sum(is_canceled::int) FROM "
                    f"'{TRADE.as_posix()}'").fetchone()[0]
    assert n and n > 0, "master 에서 해제 정보가 사라졌다 — 되돌릴 수 없다"


# ── 산출물 ───────────────────────────────────────────────────────────────
def _latest(pattern: str) -> Path | None:
    f = sorted(EXPORTS.glob(pattern))
    return f[-1] if f else None


def test_신규거래_산출물에_해제건이_없다():
    p = _latest("new_trades_*.parquet")
    if p is None:
        pytest.skip("산출물 없음")
    df = pd.read_parquet(p)
    if "is_canceled" not in df.columns:
        pytest.skip("is_canceled 컬럼 없음")
    n = int(df["is_canceled"].fillna(False).sum())
    assert n == 0, f"{p.name} 에 해제건 {n:,}건 — 발행되면 사고다"


def test_특이거래_산출물에_해제건이_없다():
    nb = _latest("new_trades_notable_*.csv")
    tr = _latest("new_trades_*.parquet")
    if nb is None or tr is None:
        pytest.skip("산출물 없음")
    full = pd.read_parquet(tr)
    if "is_canceled" not in full.columns:
        pytest.skip("is_canceled 컬럼 없음")
    cancelled = full[full["is_canceled"].fillna(False)]
    if cancelled.empty:
        return
    notable = pd.read_csv(nb)
    key = lambda d: set(zip(d["apt_name_raw"],                      # noqa: E731
                           d["deal_date"].astype(str).str[:10],
                           d["deal_amount"]))
    hit = key(cancelled) & key(notable)
    assert not hit, f"특이거래에 해제건 {len(hit)}건: {list(hit)[:3]}"
