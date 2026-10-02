"""T12 — 발행 전 검증기.

여기가 뚫리면 되돌릴 수 없는 사고가 난다. 취소된 거래를 "신고가"로 소개하거나
(T8), LLM 이 지어낸 숫자를 발행하거나, 투자 권유로 읽히는 문장이 나간다.

로드맵 완료 기준: 금지어·숫자 검증 각 5케이스.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content.validator import (  # noqa: E402
    BANNED, check_banned, check_disclaimer, check_floor_exposure,
    check_numbers, validate,
)
from templates.disclaimers import (  # noqa: E402
    DISCLAIMER_SOCIAL, DISCLAIMER_YOUTUBE,
)

FACTS = {
    "apt_name": "래미안대치팰리스", "sigungu_name": "강남구",
    "deal_amount": 470000, "prev_peak": 420000, "over_peak_pct": 11.9,
    "area_m2": 93.2, "ref_count": 5, "deals_z": -0.97,
}


# ── ② 금지 표현 (5케이스 이상) ───────────────────────────────────────────
@pytest.mark.parametrize("text", [
    "지금 매수 추천합니다",
    "이 단지는 저평가 상태입니다",
    "무조건 오를 자리입니다",
    "여기는 떡상 각입니다",
    "지금 사야 합니다. 막차입니다",
    "바닥 확인됐습니다",
    "사지 마세요",
    "내년에 오를 것입니다",
    "원금 보장됩니다",
    "숨은 보석 같은 유망 단지",
])
def test_금지표현이_걸린다(text):
    hits = check_banned(text)
    assert hits, f"못 걸렀다: {text!r}"


@pytest.mark.parametrize("text", [
    "매 수 추 천 합니다",        # 띄어쓰기 우회
    "저·평가 구간입니다",         # 구두점 우회
    "매수-추천",                  # 하이픈 우회
    "ｍ저평가",                   # 전각 혼입
])
def test_띄어쓰기나_기호로_우회할_수_없다(text):
    assert check_banned(text), f"우회 통과: {text!r}"


@pytest.mark.parametrize("text", [
    "종전 최고가를 넘겼습니다",
    "직전 평균과 벌어진 거래가 신고됐습니다",
    "거래량이 평소보다 적습니다",
    "한 건의 거래로 시세를 판단하기는 어렵습니다",
    "층과 향, 수리 상태에 따라 가격이 갈립니다",
])
def test_사실_진술은_통과한다(text):
    assert not check_banned(text), f"정상 문장을 막았다: {text!r}"


def test_면책문구는_자기자신에게_걸리지_않는다():
    """면책은 '매수·매도를 추천하거나 ... 않으며' 라 부정문 안에 금지어가 있다."""
    assert not check_banned(DISCLAIMER_SOCIAL)
    assert not check_banned(DISCLAIMER_YOUTUBE)


def test_금지목록이_로드맵_항목을_덮는다():
    필수 = ["매수추천", "매도추천", "저평가", "무조건오를", "떡상",
            "강추", "바닥확인", "지금사야", "사지마세요"]
    blob = " ".join(p for p, _ in BANNED)
    for w in 필수:
        assert check_banned(w), f"로드맵 지정 금지어 누락: {w} ({blob[:0]})"


# ── ③ 숫자 검증 (5케이스 이상) ───────────────────────────────────────────
@pytest.mark.parametrize("text", [
    "거래가 47만원이 아니라 999999만원입니다",
    "전고점 대비 33.3% 입니다",
    "거래 77건이 신고됐습니다",
    "표준편차 기준 +5.5 입니다",
    "전용 123.4㎡ 입니다",
])
def test_출처_없는_숫자가_걸린다(text):
    bad, _ = check_numbers(text, FACTS)
    assert bad, f"못 걸렀다: {text!r}"


@pytest.mark.parametrize("text", [
    "이번 거래 470,000만원",
    "47.0억에 거래됐습니다",
    "종전 최고 420000만원",
    "차이 11.9%",
    "전용 93.2㎡",
    "거래 5건",
    "표준편차 기준 -0.97",
])
def test_출처_있는_숫자는_통과한다(text):
    bad, _ = check_numbers(text, FACTS)
    assert not bad, f"정상 숫자를 막았다: {text!r} -> {bad}"


def test_억_단위_환산을_인식한다():
    """470000만원을 '47억'으로 쓴 것도 같은 값이다."""
    bad, _ = check_numbers("47억에 거래", FACTS)
    assert not bad


def test_날짜는_숫자검증에서_제외된다():
    bad, _ = check_numbers("2026-09-29 계약, 2026년 9월 신고", FACTS)
    assert not bad


def test_해시태그는_숫자검증에서_제외된다():
    bad, _ = check_numbers("#강남구아파트2026 #실거래", FACTS)
    assert not bad


def test_검증한_숫자_개수를_보고한다():
    _, n = check_numbers("470,000만원 11.9% 5건", FACTS)
    assert n == 3


# ── ① 면책 ───────────────────────────────────────────────────────────────
def test_면책_누락이_걸린다():
    assert check_disclaimer("아무 말", "social")


def test_면책이_있으면_통과한다():
    assert not check_disclaimer(f"본문\n\n{DISCLAIMER_SOCIAL}", "social")


def test_면책이_변형되면_걸린다():
    """'변경 금지' 문구다. 한 글자라도 바꾸면 통과시키지 않는다."""
    broken = DISCLAIMER_SOCIAL.replace("모든 책임은 본인에게 있습니다", "참고하세요")
    assert check_disclaimer(f"본문\n\n{broken}", "social")


def test_유튜브_면책은_종류가_구분된다():
    assert check_disclaimer(f"본문\n\n{DISCLAIMER_SOCIAL}", "youtube")
    assert not check_disclaimer(f"본문\n\n{DISCLAIMER_YOUTUBE}", "youtube")


# ── 층 노출 ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("text,blocked", [
    ("15층 거래입니다", True),
    ("3 층", True),
    ("중층 거래입니다", False),
    ("저층 매물", False),
    ("고층 선호", False),
])
def test_정확한_층수는_막고_구간은_통과한다(text, blocked):
    assert bool(check_floor_exposure(text)) is blocked


# ── 통합 ─────────────────────────────────────────────────────────────────
def test_정상_글은_통과한다():
    text = (f"[강남구] 래미안대치팰리스가 종전 최고가를 넘겼습니다.\n"
            f"· 이번 거래 470,000만원 (중층)\n· 종전 최고 420,000만원\n"
            f"· 차이 11.9%\n\n{DISCLAIMER_SOCIAL}")
    r = validate(text, FACTS)
    assert r.ok, r.reasons
    assert r.numbers_checked >= 3


def test_한_군데만_틀려도_차단된다():
    base = (f"래미안대치팰리스 470,000만원\n\n{DISCLAIMER_SOCIAL}")
    for broken, why in [
        (base.replace("470,000", "999,999"), "숫자"),
        (base + "\n지금 사야 합니다", "금지어"),
        (base + "\n15층 매물", "층 노출"),
        (base.replace(DISCLAIMER_SOCIAL, ""), "면책"),
    ]:
        r = validate(broken, FACTS)
        assert not r.ok, f"{why} 가 안 걸렸다"
