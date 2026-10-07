"""맞춤 찾기(web/match.py) 검증.

여기서 막는 것
  ① 예산을 넘는 집, 고르지 않은 평형, 시세가 사라진 단지가 Top5 에 끼는 것
  ② 한 동네가 Top5 를 통째로 차지하는 것
  ③ 통근 추정이 거꾸로 가는 것 (멀수록 짧아지는 식의 버그)
  ④ 이유 문구가 투자 권유로 읽히는 것 — 화면 문구도 발행물이다
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web import match as M  # noqa: E402
from content.validator import check_banned  # noqa: E402

TODAY = date(2026, 10, 8)


# ── 픽스처 ────────────────────────────────────────────────────────────
def _stations() -> M.Stations:
    # 강남(2호선) · 역삼(2호선) · 판교(신분당선) · 멀리 떨어진 역(5호선)
    return M.Stations(pd.DataFrame({
        "station_name": ["강남", "역삼", "판교", "먼역"],
        "line": ["2호선", "2호선", "신분당선(연장)", "5호선"],
        "lat": [37.4980, 37.5007, 37.3948, 37.7000],
        "lng": [127.0279, 127.0366, 127.1112, 126.8000],
    }))


def _row(i: int, **kw) -> dict:
    base = dict(
        apt_id=f"A{i}", apt_name=f"단지{i}", sigungu_code="11680",
        sigungu_name="강남구", legal_dong_name=f"동{i}", lat=37.50, lng=127.03,
        build_year=2010, walk_min=5.0, elem_school_cnt_1km=4, green_score=50.0,
        nearest_station="강남", nearest_line="2호선", infra_score=70.0,
        pyeong_bucket="30P", area_m2=84.0, last_price=90000,
        last_date=pd.Timestamp("2026-08-01"), last_ppy=3500.0, ppy_1y=3500.0,
        trade_total=20, trade_1y=5, chg_1y=0.05, vs_peak=0.95,
    )
    base.update(kw)
    return base


def _frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    return M.add_rel_price(df)


def _ans(**kw) -> M.Answers:
    base = dict(household="couple", budget=100000, pyeongs=["30P"],
                work=None, commute_max=45, sgg=[], priorities=["station"])
    base.update(kw)
    return M.Answers(**base)


# ── ③ 통근 추정 ───────────────────────────────────────────────────────
def test_haversine_known_distance():
    # 강남역 ↔ 판교역 직선 약 13km
    d = M.haversine_km(37.4980, 127.0279, 37.3948, 127.1112)
    assert 12.5 < float(d) < 14.5


def test_commute_grows_with_distance():
    st = _stations()
    work = (37.4985, 127.0285)                       # 강남역 앞
    lat = np.array([37.5000, 37.3950, 37.6990])      # 역삼 근처 · 판교 · 먼역
    lng = np.array([127.0360, 127.1110, 126.8010])
    t = st.commute(lat, lng, *work)
    assert t[0] < t[1] < t[2]


def test_same_line_beats_transfer_at_equal_distance():
    st = _stations()
    # 같은 노선(2호선) 1정거장 vs 비교: 환승 벌점이 붙는 경로는 같은 거리에서 더 길어야 한다
    ride_same = M.ride_minutes(1.0, "2호선", "2호선")
    ride_xfer = M.ride_minutes(1.0, "2호선", "신분당선")
    assert ride_xfer - ride_same == pytest.approx(M.TRANSFER_MIN)
    assert M.ride_minutes(1.0, "신분당선(연장)", "신분당선") == M.ride_minutes(1.0, "신분당선", "신분당선")


def test_through_running_lines_are_not_transfers():
    # 부평(경인선) → 서울역(경부선) 은 같은 1호선 열차다
    assert M.ride_minutes(24.0, "경인선", "경부선") == M.ride_minutes(24.0, "1호선", "1호선")
    assert M.norm_line("중앙선") == M.norm_line("경의중앙선")


def test_ride_speed_grows_with_distance():
    per_km_short = M.ride_minutes(3.0, "2호선", "2호선") / 3
    per_km_long = M.ride_minutes(25.0, "2호선", "2호선") / 25
    assert per_km_long < per_km_short


def test_short_distance_uses_walking():
    st = _stations()
    # 회사와 800m 떨어진 집 — 지하철 경로(대기 4분 포함)보다 도보가 짧다
    t = st.commute(np.array([37.5050]), np.array([127.0279]), 37.4980, 127.0279)
    assert t[0] <= M.walk_minutes(0.8 * 1.0) + 1


# ── 점수 곡선 ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("ratio,expected", [
    (1.0, 100), (0.75, 100), (0.875, 100), (0.40, 0), (0.30, 0), (0.575, 50),
])
def test_budget_use_score(ratio, expected):
    assert M.budget_use_score(np.array([ratio]))[0] == pytest.approx(expected)


def test_commute_score_bounds():
    s = M.commute_score(np.array([15, 20, 55, 70]), limit=55)
    assert s[0] == 100 and s[1] == 100
    assert s[2] == pytest.approx(0)
    assert s[3] == 0


def test_rel_price_lower_ppy_scores_higher():
    df = _frame([_row(1, ppy_1y=2000.0), _row(2, ppy_1y=3000.0), _row(3, ppy_1y=4000.0)])
    by = df.set_index("apt_id")["rel_price_pct"]
    assert by["A1"] < by["A2"] < by["A3"]


# ── ① 하드 필터 ───────────────────────────────────────────────────────
def test_hard_filter_excludes_over_budget_wrong_pyeong_stale():
    df = _frame([
        _row(1),
        _row(2, last_price=120000),                              # 예산 초과
        _row(3, pyeong_bucket="20P"),                            # 평형 불일치
        _row(4, last_date=pd.Timestamp("2022-01-01")),           # 3년 넘게 거래 없음
        _row(5, trade_total=2),                                  # 표본 부족
        _row(6, lat=None, lng=None),                             # 좌표 없음
    ])
    keep = df[M.hard_filter(df, _ans(), TODAY)]
    assert list(keep["apt_id"]) == ["A1"]


def test_hard_filter_region_and_commute():
    df = _frame([_row(1), _row(2, sigungu_code="41135")])
    df["commute_min"] = [30.0, 80.0]
    keep = df[M.hard_filter(df, _ans(sgg=["11680"]), TODAY)]
    assert list(keep["apt_id"]) == ["A1"]
    keep = df[M.hard_filter(df, _ans(work=(37.5, 127.0)), TODAY)]
    assert list(keep["apt_id"]) == ["A1"]                       # 80분 > 45+10


# ── ② 정리 ────────────────────────────────────────────────────────────
def test_one_row_per_apt_and_dong_cap():
    rows = [_row(i, legal_dong_name="역삼동", walk_min=float(i)) for i in range(1, 5)]
    rows += [_row(10, legal_dong_name="대치동", walk_min=20.0)]
    rows += [_row(1, pyeong_bucket="35P", walk_min=1.0)]      # 같은 단지 다른 평형
    df = _frame(rows)
    scored = M.score(df[M.hard_filter(df, _ans(pyeongs=["30P", "35P"]), TODAY)],
                     _ans(pyeongs=["30P", "35P"]))
    top = M.pick_top(scored, n=5, dong_cap=2)
    assert top["apt_id"].is_unique
    assert (top["legal_dong_name"] == "역삼동").sum() == 2
    assert "A10" in set(top["apt_id"])


def test_priority_changes_order():
    df = _frame([
        _row(1, walk_min=2.0, build_year=1990),
        _row(2, walk_min=25.0, build_year=2022),
    ])
    a = M.pick_top(M.score(df, _ans(priorities=["station"])))
    b = M.pick_top(M.score(df, _ans(priorities=["new"])))
    assert a.iloc[0]["apt_id"] == "A1"
    assert b.iloc[0]["apt_id"] == "A2"


def test_weights_sum_to_one_without_work():
    w = M.weights(_ans(priorities=["station", "school"]))
    assert sum(w.values()) == pytest.approx(1.0)
    assert "commute" not in w
    w = M.weights(_ans(work=(37.5, 127.0), priorities=["station"]))
    assert w["commute"] == pytest.approx(0.25)
    assert sum(w.values()) == pytest.approx(1.0)


def test_relaxation_widens_budget_when_short():
    rows = [_row(i, legal_dong_name=f"동{i}", last_price=105000) for i in range(1, 7)]
    df = _frame(rows)
    res = M.run_match(df, _ans(budget=100000), TODAY, stations=None)
    assert len(res["items"]) == 5
    assert "budget" in res["relaxed"]


def test_no_relaxation_when_enough():
    df = _frame([_row(i, legal_dong_name=f"동{i}") for i in range(1, 8)])
    res = M.run_match(df, _ans(), TODAY, stations=None)
    assert len(res["items"]) == 5 and res["relaxed"] == []
    assert res["count"] == 7
    for it in res["items"]:
        assert 0 <= it["score"] <= 100
        assert it["reasons"]


# ── ④ 문구 ────────────────────────────────────────────────────────────
def test_reasons_pass_validator():
    df = _frame([_row(i, legal_dong_name=f"동{i}", ppy_1y=2000.0 + i * 300)
                 for i in range(1, 8)])
    for prio in M.PRIORITIES:
        res = M.run_match(df, _ans(priorities=[prio]), TODAY, stations=None)
        for it in res["items"]:
            text = " ".join(it["reasons"])
            assert check_banned(text) == [], text


def test_ui_copy_passes_validator():
    static = ROOT / "web" / "static"
    files = [static / "index.html", *sorted((static / "js" / "match").glob("*.js"))]
    files = [f for f in files if f.exists()]
    if not files:
        pytest.skip("프론트 미작성")
    for f in files:
        assert check_banned(f.read_text(encoding="utf-8")) == [], f.name


def test_small_complex_excluded_new_build_exempt():
    df = _frame([
        _row(1, apt_trade_total=200),
        _row(2, apt_trade_total=30),                         # 오래된 소규모
        _row(3, apt_trade_total=30, build_year=2023),        # 신축이라 기준 15
    ])
    keep = df[M.hard_filter(df, _ans(), TODAY)]
    assert list(keep["apt_id"]) == ["A1", "A3"]


def test_commute_options_strict_and_unlimited():
    df = _frame([_row(1), _row(2), _row(3)])
    df["commute_min"] = [28.0, 35.0, 130.0]
    work = (37.5, 127.0)
    strict = df[M.hard_filter(df, _ans(work=work, commute_max=30, commute_strict=True), TODAY)]
    loose = df[M.hard_filter(df, _ans(work=work, commute_max=30), TODAY)]
    open_ = df[M.hard_filter(df, _ans(work=work, commute_max=None), TODAY)]
    assert list(strict["apt_id"]) == ["A1"]            # 30분 미만: 여유 없음
    assert list(loose["apt_id"]) == ["A1", "A2"]       # 30분: +10분 여유
    assert list(open_["apt_id"]) == ["A1", "A2", "A3"]  # 2시간 이상: 거르지 않음
    s = M.score(open_, _ans(work=work, commute_max=None))
    assert s.set_index("apt_id")["s_commute"]["A1"] > s.set_index("apt_id")["s_commute"]["A3"]


def test_payload_commute_none_means_unlimited():
    assert M.Answers.from_payload({"commute_max": None}).commute_max is None
    assert M.Answers.from_payload({}).commute_max == 60
    a = M.Answers.from_payload({"commute_max": 30, "commute_strict": True})
    assert a.commute_max == 30 and a.commute_strict



def test_new_priority_is_absolute_not_relative():
    # 후보가 전부 구축이면 '신축' 점수도 낮아야 한다 (상대 순위면 2006년이 100점이 된다)
    df = _frame([_row(1, build_year=2005), _row(2, build_year=2006)])
    sc = M.score(df, _ans(priorities=["new"]), TODAY)
    assert sc["s_new"].max() < 30
    df = _frame([_row(1, build_year=2022)])
    assert M.score(df, _ans(priorities=["new"]), TODAY)["s_new"].iloc[0] == 100


def test_thin_trades_lower_the_score():
    df = _frame([_row(1, trade_1y=0), _row(2, trade_1y=5)])
    sc = M.score(df, _ans(), TODAY).set_index("apt_id")
    assert sc.loc["A1", "score"] < sc.loc["A2", "score"]


def test_stale_two_years_excluded():
    df = _frame([_row(1, last_date=pd.Timestamp("2024-06-01")), _row(2)])
    assert list(df[M.hard_filter(df, _ans(), TODAY)]["apt_id"]) == ["A2"]


def test_second_workplace_filters_and_scores():
    df = _frame([_row(1), _row(2)])
    df["commute_min"] = [30.0, 30.0]
    df["commute2_min"] = [40.0, 90.0]
    a = _ans(work=(37.5, 127.0), work2=(37.4, 127.1), commute_max=60)
    keep = df[M.hard_filter(df, a, TODAY)]
    assert list(keep["apt_id"]) == ["A1"]                     # 배우자 90분 > 70
    row = M.score(keep, a, TODAY).iloc[0]
    assert "함께 사는 분 40분" in M.reason_text("commute", row, a)


def test_park_zero_distance_copy():
    row = pd.Series({"park_dist": 0.0, "s_green": 90})
    assert M.reason_text("green", row, _ans()) == "단지 바로 옆 공원"


def test_weak_point_names_the_unmet_condition():
    items = [{"score": 45, "breakdown": {"price": 90, "new": 20}} for _ in range(5)]
    wk = M.weak_point(items, {"price": 0.4, "new": 0.6})
    assert wk == {"key": "new", "label": "신축", "avg": 20}
    good = [{"score": 85, "breakdown": {"price": 90, "new": 80}}]
    assert M.weak_point(good, {"price": 0.4, "new": 0.6}) is None
