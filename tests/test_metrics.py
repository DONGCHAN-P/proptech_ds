"""T9 — 지표 계산 검증.

발행될 숫자를 만드는 곳이라 틀리면 바로 콘텐츠 사고다. 특히 두 가지를 본다.
  - 해제 건이 지표에 섞이지 않는가 (T8 공통 관문이 실제로 작동하는가)
  - 신고 지연을 시장 신호로 오해하지 않는가 (주간 지표의 기준 주)
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import DIRS  # noqa: E402
from metrics import build_metrics as M  # noqa: E402

TRADE = DIRS["master"] / "trade_events.parquet"
ASOF = date(2026, 10, 1)


@pytest.fixture(scope="module")
def con():
    if not TRADE.exists():
        pytest.skip("trade_events 없음")
    c = duckdb.connect()
    c.execute("SET memory_limit = '2GB'")
    yield c
    c.close()


@pytest.fixture(scope="module")
def asof(con) -> date:
    return con.execute(f"SELECT max(deal_date) FROM '{M.TRADE}'").fetchone()[0].date()


# ── 신고가 ───────────────────────────────────────────────────────────────
def test_신고가는_전고점을_넘어야_한다(con, asof):
    for r in M.new_high(con, asof):
        assert r["deal_amount"] > r["prev_peak"], r


def test_신고가는_이력이_충분한_단지만(con, asof):
    for r in M.new_high(con, asof):
        assert r["history_count"] >= M.RARE_AREA_MIN, r


def test_신고가에_해제건이_없다(con, asof):
    """공통 CTE 가 실제로 작동하는지 — 결과를 원본과 다시 대조한다."""
    rows = M.new_high(con, asof)
    if not rows:
        pytest.skip("신고가 없음")
    pairs = [(r["apt_name"], r["deal_date"], r["deal_amount"]) for r in rows]
    vals = ", ".join(
        f"('{n}', DATE '{d}', {a})" for n, d, a in pairs)
    n = con.execute(f"""
        SELECT count(*) FROM '{M.TRADE}'
        WHERE coalesce(is_canceled, false)
          AND (apt_name_raw, deal_date, deal_amount) IN ({vals})
    """).fetchone()[0]
    assert n == 0, f"신고가 결과에 해제건 {n}건"


# ── 전고점 이격 ──────────────────────────────────────────────────────────
def test_전고점_이격은_0이하여야_한다(con, asof):
    """전고점을 넘었으면 그건 신고가지 '이격'이 아니다."""
    for r in M.vs_peak(con, asof):
        assert r["vs_peak_pct"] <= 0.01, r


# ── 특이 거래 ────────────────────────────────────────────────────────────
def test_특이거래는_임계를_넘는다(con, asof):
    for r in M.outliers(con, asof):
        assert abs(r["deviation_pct"]) >= M.OUTLIER_PCT, r
        assert r["ref_count"] >= M.OUTLIER_MIN_REF, r


def test_특이거래에_층이_구간으로만_나온다(con, asof):
    """정확한 층을 발행하면 특정 세대가 식별된다."""
    for r in M.outliers(con, asof):
        assert r["floor_band"] in ("저층", "중층", "고층", "미상"), r
        assert "floor" not in r, "원시 층수가 노출됐다"


# ── 주간 ─────────────────────────────────────────────────────────────────
def test_주간_기준주가_충분히_물려있다(con, asof):
    """신고 지연을 시장 신호로 읽지 않도록 기준 주를 뒤로 민다."""
    rows = M.sgg_zscore(con, asof)
    if not rows:
        pytest.skip("Z-score 없음")
    wk = date.fromisoformat(rows[0]["week_start"])
    assert (asof - wk).days >= M.WEEKLY_LAG_DAYS, (
        f"기준 주 {wk} 가 기준일 {asof} 에 너무 가깝다")


def test_주간_표본이_부족한_시군구는_제외(con, asof):
    for r in M.sgg_zscore(con, asof):
        assert r["week_deals"] >= M.WEEK_MIN_DEALS, r
        assert r["hist_weeks"] >= M.ZSCORE_MIN_WEEKS, r


def test_거래량_z가_한쪽으로_쏠리지_않는다(con, asof):
    """전부 음수면 신고 지연을 보고 있는 것이다 (기준 주를 안 물린 상태).

    우편향 분포라 중앙값은 -0.4 근처가 정상이다. -1.0 아래면 의심한다.
    """
    zs = [r["deals_z"] for r in M.sgg_zscore(con, asof) if r["deals_z"] is not None]
    if len(zs) < 10:
        pytest.skip("표본 부족")
    zs.sort()
    med = zs[len(zs) // 2]
    assert med > -1.0, f"거래량 z 중앙값 {med:.2f} — 기준 주가 덜 물린 듯"
    assert max(zs) > 0, "양의 z 가 하나도 없다"


def test_급등단지는_양쪽_구간에_거래가_있다(con, asof):
    for r in M.surge_apt(con, asof):
        assert r["deals_recent"] >= M.OUTLIER_MIN_REF, r
        assert r["deals_prior"] >= M.OUTLIER_MIN_REF, r


# ── 산출물 ───────────────────────────────────────────────────────────────
def test_JSON_산출물_구조():
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("산출물 없음")
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    assert {"generated_at", "asof", "params", "daily", "weekly"} <= set(d)
    assert {"new_high", "vs_peak", "outlier"} <= set(d["daily"])
    assert {"sgg_zscore", "surge_apt"} <= set(d["weekly"])
    assert d["params"]["min_households"] is None, (
        "세대수 필터가 켜졌다 — T6b 수집 전이면 결과가 왜곡된다")


def test_피크_RAM이_기준_이내():
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("산출물 없음")
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    ram = d.get("peak_ram_mb")
    assert ram is not None, "피크 RAM 이 기록되지 않았다"
    assert ram <= 2048, f"피크 RAM {ram}MB > 2048MB"
