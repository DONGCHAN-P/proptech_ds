"""콘텐츠 후보 선정 (content/briefing.py).

여기가 조용히 망가지면 "후보 5개"가 전부 같은 앵글·같은 지역이 되거나, 표본
몇 건짜리 거래가 후보로 올라온다. 숫자는 맞으니 보고도 못 알아챈다.

포맷 표시도 검사한다. "바로 제작"이라고 적혀 있는데 프로필이 없으면 작업을
시작한 다음에야 막힌다 — 브리핑이 하려는 일이 바로 그걸 막는 것이다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import briefing as B  # noqa: E402


# ── 재료 ─────────────────────────────────────────────────────────────────
def nh(apt, sgg, *, over=5.0, hist=100, code=None, apt_id=None):
    return {"apt_name": apt, "sigungu_name": sgg, "over_peak_pct": over,
            "history_count": hist, "prev_peak": 80000, "deal_amount": 84000,
            "sigungu_code": code, "apt_id": apt_id, "pyeong_bucket": "25P"}


def sa(apt, sgg, *, change=10.0, recent=20, prior=30):
    return {"apt_name": apt, "sigungu_name": sgg, "change_pct": change,
            "deals_recent": recent, "deals_prior": prior,
            "pyeong_bucket": "25P"}


def np_(apt, sgg, *, vs=-2.0, hist=100):
    return {"apt_name": apt, "sigungu_name": sgg, "vs_peak_pct": vs,
            "history_count": hist, "peak_date": "2022-08-11",
            "pyeong_bucket": "25P"}


def zs(sgg, *, deals=60, avg=30.0, weeks=52, code=None):
    return {"sigungu_name": sgg, "week_deals": deals, "deals_avg_52w": avg,
            "hist_weeks": weeks, "sigungu_code": code}


def ol(apt, sgg, *, dev=20.0, ref=30):
    return {"apt_name": apt, "sigungu_name": sgg, "deviation_pct": dev,
            "ref_count": ref, "floor_band": "저층", "ref_avg": 50000,
            "pyeong_bucket": "25P"}


def pack(**kw) -> dict:
    daily = {k: kw.pop(k, []) for k in ("new_high", "vs_peak",
                                        "near_peak", "outlier")}
    weekly = {k: kw.pop(k, []) for k in ("sgg_zscore", "surge_apt")}
    return {"asof": "2026-10-07", "daily": daily, "weekly": weekly,
            "profiles": kw.pop("profiles", {})}


def prof(apt, sgg, *, points=20, neighbors=6, deals=200, py="25P",
         aid="a1"):
    return {"apt_id": aid, "apt_name": apt, "sigungu_name": sgg,
            "pyeong_bucket": py, "deals_1y": deals,
            "series": [{"ym": "2024-01", "price": 1}] * points,
            "neighbors": [{"apt_name": f"N{i}"} for i in range(neighbors)]}


# ── 표본 문턱 ────────────────────────────────────────────────────────────
def test_표본이_모자란_신고가는_후보가_아니다():
    """거래 몇 건짜리 평형의 "신고가"는 최고가라는 말이 무의미하다."""
    d = pack(new_high=[nh("얇은단지", "마포구", hist=B.MIN_SAMPLE - 1)])
    assert B.build(d) == []


def test_표본이_되면_후보로_올라온다():
    d = pack(new_high=[nh("두꺼운단지", "마포구", hist=B.MIN_SAMPLE)])
    assert [i.subject for i in B.build(d)] == ["두꺼운단지"]


def test_비교기준이_얇은_특이거래는_버린다():
    d = pack(outlier=[ol("한건", "마포구", ref=B.OUTLIER_REF_MIN - 1)])
    assert B.build(d) == []


# ── 앵글별 조건 ──────────────────────────────────────────────────────────
def test_반전은_값이_오르고_거래가_줄어야_한다():
    ok = pack(surge_apt=[sa("반전단지", "마포구", change=10, recent=20,
                            prior=30)])
    assert [i.angle for i in B.build(ok)] == ["반전"]

    # 거래가 같이 늘면 "반전"이 아니다 — 그냥 오르는 단지다
    no = pack(surge_apt=[sa("동반단지", "마포구", change=10, recent=30,
                            prior=20)])
    assert B.build(no) == []

    # 값이 내리면 반전이 아니다
    down = pack(surge_apt=[sa("하락단지", "마포구", change=-5, recent=20,
                              prior=30)])
    assert B.build(down) == []


def test_회복은_전고점을_넘지_않은_구간만_센다():
    """0% 는 오늘의 신고가다. 그건 신고가 앵글이 이미 다룬다."""
    at = pack(near_peak=[np_("딱전고점", "마포구", vs=0.0)])
    assert B.build(at) == []

    over = pack(near_peak=[np_("넘었음", "마포구", vs=3.0)])
    assert B.build(over) == []

    near = pack(near_peak=[np_("근접", "마포구", vs=-2.0)])
    assert [i.angle for i in B.build(near)] == ["회복"]


def test_회복은_너무_멀면_버린다():
    far = pack(near_peak=[np_("멀었음", "마포구",
                              vs=B.RECOVER_NEAR - 1)])
    assert B.build(far) == []


def test_near_peak이_없는_옛_파일이면_vs_peak로_떨어진다():
    """지표 파일이 갱신되기 전에도 터지지 않아야 한다."""
    d = pack(vs_peak=[np_("구파일", "마포구", vs=-2.0)])
    assert [i.subject for i in B.build(d)] == ["구파일"]


def test_near_peak이_있으면_vs_peak은_보지_않는다():
    d = pack(near_peak=[np_("신파일", "마포구", vs=-1.0)],
             vs_peak=[np_("구파일", "강남구", vs=-2.0)])
    assert [i.subject for i in B.build(d)] == ["신파일"]


def test_평소와_비슷한_지역은_쓸_거리가_없다():
    same = pack(sgg_zscore=[zs("마포구", deals=30, avg=30.0)])
    assert B.build(same) == []

    surge = pack(sgg_zscore=[zs("마포구", deals=60, avg=30.0)])
    got = B.build(surge)
    assert [i.angle for i in got] == ["급증·급감"]
    assert "2.0배" in got[0].headline and "늘었" in got[0].headline

    drop = pack(sgg_zscore=[zs("마포구", deals=12, avg=30.0)])
    assert "줄었" in B.build(drop)[0].headline


def test_과거가_얕으면_평소를_말하지_않는다():
    d = pack(sgg_zscore=[zs("마포구", deals=60, avg=30.0,
                            weeks=B.HIST_MIN_WEEKS - 1)])
    assert B.build(d) == []


# ── 포맷 표시 ────────────────────────────────────────────────────────────
def test_프로필이_있으면_바로_제작으로_적는다():
    d = pack(new_high=[nh("있는단지", "마포구", apt_id="a1")],
             profiles={"a1:25P": prof("있는단지", "마포구")})
    i = B.build(d)[0]
    assert i.ready and i.fmt == B.FMT_READY


def test_프로필이_없으면_재생성_필요로_적는다():
    d = pack(new_high=[nh("없는단지", "마포구", apt_id="zz")])
    i = B.build(d)[0]
    assert not i.ready and i.fmt == B.FMT_REBUILD


def test_apt_id가_없어도_이름으로_프로필을_찾는다():
    """surge_apt·near_peak 행에는 apt_id 가 없다. 이름으로도 찾지 않으면
    프로필이 있는데도 "재생성 필요"로 잘못 적힌다."""
    d = pack(surge_apt=[sa("이름만", "마포구")],
             profiles={"a1:25P": prof("이름만", "마포구")})
    assert B.build(d)[0].ready


def test_다른_구의_같은_이름을_프로필로_붙이지_않는다():
    """주공·래미안처럼 같은 이름이 전국에 있다. 구까지 맞아야 한다."""
    d = pack(surge_apt=[sa("주공", "강남구")],
             profiles={"a1:25P": prof("주공", "마포구")})
    assert not B.build(d)[0].ready


def test_얕은_프로필은_덱을_끌고_가지_못한다():
    d = pack(new_high=[nh("얕음", "마포구", apt_id="a1")],
             profiles={"a1:25P": prof("얕음", "마포구", neighbors=1)})
    assert not B.build(d)[0].ready


def test_지역_단위_소재는_덱이_아니라_스레드다():
    d = pack(sgg_zscore=[zs("마포구", deals=60, avg=30.0)])
    i = B.build(d)[0]
    assert not i.apt and "스레드" in i.fmt and "지역 단위" in i.fmt


def test_특이거래는_한_건이라서_스레드다():
    """지역 단위라서가 아니다 — 이유를 틀리게 적으면 판단이 어긋난다."""
    d = pack(outlier=[ol("한건단지", "마포구")])
    i = B.build(d)[0]
    assert "스레드" in i.fmt and "한 건" in i.fmt
    assert "지역 단위" not in i.fmt


# ── 고르기 ───────────────────────────────────────────────────────────────
def test_한_앵글이_덱을_다_채우지_못한다():
    d = pack(new_high=[nh(f"단지{k}", f"구{k}") for k in range(9)])
    got = B.pick(B.build(d), 5)
    assert len(got) == B.MAX_PER_ANGLE


def test_앵글을_골고루_섞는다():
    d = pack(new_high=[nh(f"신고가{k}", f"가구{k}") for k in range(5)],
             surge_apt=[sa(f"반전{k}", f"나구{k}") for k in range(5)],
             near_peak=[np_(f"회복{k}", f"다구{k}") for k in range(5)],
             sgg_zscore=[zs(f"라구{k}", deals=60, avg=30.0)
                         for k in range(5)],
             outlier=[ol(f"특이{k}", f"마구{k}") for k in range(5)])
    got = B.pick(B.build(d), 5)
    assert len(got) == 5
    assert sorted(i.angle for i in got) == sorted(B.ANGLE_ORDER)


def test_같은_지역을_두_번_올리지_않는다():
    """같은 구 얘기를 두 번 하면 다섯 개를 고른 의미가 없다."""
    d = pack(new_high=[nh("가단지", "마포구")],
             surge_apt=[sa("나단지", "마포구")],
             outlier=[ol("다단지", "마포구")])
    got = B.pick(B.build(d), 5)
    assert len(got) == 1


def test_우선_지역을_앞세운다():
    d = pack(new_high=[nh("외곽단지", "연천군", hist=5000),
                       nh("서울단지", "마포구", hist=20)])
    got = B.pick(B.build(d), 1)
    assert got[0].subject == "서울단지"


def test_요청한_개수를_넘기지_않는다():
    d = pack(new_high=[nh(f"신고가{k}", f"가구{k}") for k in range(5)],
             surge_apt=[sa(f"반전{k}", f"나구{k}") for k in range(5)],
             near_peak=[np_(f"회복{k}", f"다구{k}") for k in range(5)])
    assert len(B.pick(B.build(d), 3)) == 3


def test_후보가_모자라면_있는_만큼만_준다():
    d = pack(new_high=[nh("하나", "마포구")])
    assert len(B.pick(B.build(d), 5)) == 1


def test_같은_후보를_두_번_담지_않는다():
    """2차 채우기에서 1차에 담은 걸 다시 집으면 중복이 나간다."""
    d = pack(new_high=[nh(f"신고가{k}", f"가구{k}") for k in range(3)],
             surge_apt=[sa(f"반전{k}", f"나구{k}") for k in range(3)])
    got = B.pick(B.build(d), 5)
    assert len(got) == len({(i.angle, i.subject) for i in got})


def test_앵글_순서대로_정렬해_준다():
    d = pack(new_high=[nh("신고가", "가구")],
             outlier=[ol("특이", "나구")],
             surge_apt=[sa("반전", "다구")])
    got = B.pick(B.build(d), 5)
    order = [B.ANGLE_ORDER.index(i.angle) for i in got]
    assert order == sorted(order)


# ── 문구 ─────────────────────────────────────────────────────────────────
def test_상승폭이_작으면_주의를_적는다():
    weak = B.build(pack(new_high=[nh("약함", "마포구", over=1.2)]))[0]
    strong = B.build(pack(new_high=[nh("강함", "마포구", over=12.0)]))[0]
    assert weak.caution and not strong.caution


def test_특이거래는_단정하지_말라고_적는다():
    i = B.build(pack(outlier=[ol("특이", "마포구")]))[0]
    assert i.caution


def test_헤드라인에_지역과_소재가_들어간다():
    for i in B.build(pack(
            new_high=[nh("가단지", "마포구")],
            surge_apt=[sa("나단지", "강남구")],
            near_peak=[np_("다단지", "송파구")],
            outlier=[ol("라단지", "강서구")],
            sgg_zscore=[zs("종로구", deals=60, avg=30.0)])):
        assert i.region in i.headline, i.headline
        assert i.subject in i.headline, i.headline


def test_모든_후보가_왜와_표본을_채운다():
    """표본 없이 올라온 후보는 검증 없이 발행으로 넘어간다."""
    for i in B.build(pack(
            new_high=[nh("가단지", "마포구")],
            surge_apt=[sa("나단지", "강남구")],
            near_peak=[np_("다단지", "송파구")],
            outlier=[ol("라단지", "강서구")],
            sgg_zscore=[zs("종로구", deals=60, avg=30.0)])):
        assert i.why.strip() and i.sample.strip(), i.angle


def test_특이거래_방향은_절댓값으로_적는다():
    """싸게 팔린 건을 "-20% 벌어진" 으로 쓰면 어색하다."""
    i = B.build(pack(outlier=[ol("싼거래", "마포구", dev=-20.0)]))[0]
    assert "20.0% 벌어진" in i.headline


def test_직렬화가_필요한_항목을_다_담는다():
    got = B.as_dicts(B.pick(B.build(pack(
        new_high=[nh("가단지", "마포구")])), 5))
    assert got and set(got[0]) >= {
        "angle", "region", "subject", "headline", "why", "sample",
        "format", "ready", "priority"}


# ── 실제 지표 파일 ───────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def real() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


def test_실제_지표로_후보가_나온다(real):
    got = B.pick(B.build(real), 5)
    assert got, "실제 지표에서 후보가 하나도 안 나오면 조건이 너무 좁다"
    assert len(got) == len({i.region for i in got})
    for i in got:
        assert i.headline and i.why and i.sample


def test_평형이_다른_프로필은_쓰지_않는다():
    """같은 단지라도 평형이 다르면 그래프와 헤드라인이 어긋난다.
    tests/test_cover.py 의 같은 이름 검사와 짝이다."""
    d = pack(new_high=[nh("가단지", "마포구", apt_id="a1")],
             profiles={"a1:30P": prof("가단지", "마포구", py="30P")})
    assert not B.build(d)[0].ready
