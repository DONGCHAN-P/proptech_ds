"""T10 — 단지 묶음(apt_group_id) 검증.

apt_id 는 주소 단위라 출입구가 여럿인 단지가 쪼개진다. apt_group_id 가 그걸
다시 묶는다. 묶을 때 **옆 단지를 삼키지 않는 것**이 핵심이다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import DIRS  # noqa: E402
from run_build_apt_groups import MAX_DIST_M, haversine_m  # noqa: E402

GROUPS = DIRS["master"] / "apt_groups.parquet"
TRADE = DIRS["master"] / "trade_events.parquet"
GEO = ROOT / "web" / "cache" / "apt_geo.parquet"


# ── 거리 계산 ────────────────────────────────────────────────────────────
def test_haversine_기본():
    # 서울시청 -> 강남역 약 8.3km
    d = float(haversine_m(37.5663, 126.9779, 37.4979, 127.0276))
    assert 7500 < d < 9000, d


def test_haversine_같은점은_0():
    assert float(haversine_m(37.5, 127.0, 37.5, 127.0)) == pytest.approx(0, abs=1)


# ── 묶음 결과 ────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def groups() -> pd.DataFrame:
    if not GROUPS.exists():
        pytest.skip("apt_groups.parquet 없음")
    return pd.read_parquet(GROUPS)


def test_모든_단지에_묶음id가_있다(groups):
    tr = pd.read_parquet(TRADE, columns=["apt_id"])
    missing = set(tr["apt_id"].unique()) - set(groups["apt_id"])
    assert not missing, f"묶음 id 없는 단지 {len(missing):,}개"
    assert groups["apt_group_id"].notna().all()


def test_묶음id는_실재하는_apt_id다(groups):
    """대표를 임의 문자열로 만들면 조인이 깨진다."""
    orphan = set(groups["apt_group_id"]) - set(groups["apt_id"])
    assert not orphan, f"실재하지 않는 대표 id {len(orphan)}개"


def test_apt_id는_중복되지_않는다(groups):
    assert groups["apt_id"].is_unique


def test_대표는_자기자신을_가리킨다(groups):
    """대표 id 의 행은 apt_group_id == apt_id 여야 한다 (체인 금지)."""
    reps = set(groups["apt_group_id"])
    rows = groups[groups["apt_id"].isin(reps)]
    bad = rows[rows["apt_id"] != rows["apt_group_id"]]
    assert bad.empty, f"대표가 또 다른 대표를 가리킨다: {len(bad)}건"


# ── 병합 품질 ────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def merged_detail(groups) -> pd.DataFrame:
    if not GEO.exists():
        pytest.skip("좌표 없음")
    # build_year 는 max 로 모은다. 같은 단지인데 신고마다 준공년이 다른 건이
    # 76개 있어서 first() 를 쓰면 그룹 생성 로직과 어긋난다.
    tr = (pd.read_parquet(TRADE, columns=[
            "apt_id", "legal_dong_code", "apt_name_norm", "build_year"])
          .groupby("apt_id")
          .agg(legal_dong_code=("legal_dong_code", "first"),
               apt_name_norm=("apt_name_norm", "first"),
               build_year=("build_year", "max"))
          .reset_index())
    geo = pd.read_parquet(GEO, columns=["apt_id", "lat", "lng"])
    d = groups.merge(tr, on="apt_id", how="left").merge(geo, on="apt_id", how="left")
    return d[d["apt_group_id"].map(d["apt_group_id"].value_counts()) > 1]


def test_같은_묶음은_같은_법정동_이름_준공년(merged_detail):
    """묶음 기준을 벗어난 병합이 있으면 안 된다."""
    g = merged_detail.groupby("apt_group_id")[
        ["legal_dong_code", "apt_name_norm", "build_year"]].nunique()
    bad = g[(g > 1).any(axis=1)]
    assert bad.empty, f"기준이 다른데 묶인 묶음 {len(bad)}개"


def test_묶인_단지는_서로_가깝다(merged_detail):
    """단일 연결이라 끝점끼리는 임계를 넘을 수 있지만, 상식 밖이면 안 된다."""
    worst = 0.0
    for _, g in merged_detail.groupby("apt_group_id"):
        g = g.dropna(subset=["lat", "lng"])
        if len(g) < 2:
            continue
        lat, lng = g["lat"].to_numpy(), g["lng"].to_numpy()
        for a in range(len(g)):
            for b in range(a + 1, len(g)):
                worst = max(worst, float(haversine_m(lat[a], lng[a], lat[b], lng[b])))
    assert worst <= MAX_DIST_M * 4, f"묶음 내 최대 거리 {worst:.0f}m — 과병합 의심"


def test_과분할이_충분히_해소됐다(groups):
    """로드맵 기준: 1차 충돌 목록의 90% 이상 해소."""
    tr = (pd.read_parquet(TRADE, columns=[
            "apt_id", "legal_dong_code", "apt_name_norm", "build_year"])
          .groupby("apt_id")
          .agg(legal_dong_code=("legal_dong_code", "first"),
               apt_name_norm=("apt_name_norm", "first"),
               build_year=("build_year", "max"))
          .reset_index())
    d = tr.merge(groups, on="apt_id")
    keys = ["legal_dong_code", "apt_name_norm", "build_year"]
    before = d.groupby(keys)["apt_id"].nunique()
    after = d.groupby(keys)["apt_group_id"].nunique()
    split_before = int((before > 1).sum())
    split_after = int((after > 1).sum())
    if split_before == 0:
        pytest.skip("과분할 없음")
    rate = 1 - split_after / split_before
    assert rate >= 0.90, (
        f"해소율 {rate * 100:.1f}% < 90% "
        f"({split_before:,} -> {split_after:,})")
