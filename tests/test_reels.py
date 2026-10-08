"""T13 — 릴스 영상 검증.

피드 캐러셀은 팔로워에게만 닿고 릴스는 추천으로 퍼진다. 그래서 규격이 다르고,
**틀리는 방식도 다르다**. 세로 비율이 틀리면 인스타가 잘라 버리고, 안전 영역을
벗어난 글자는 UI 에 가려 발행 후에야 알게 된다.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from content import reels as R  # noqa: E402
from content.carousel import pick, strip_html  # noqa: E402
from content.validator import check_banned  # noqa: E402


@pytest.fixture(scope="module")
def data() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def scs(data) -> list[dict]:
    t = pick(data)
    prof = (t["cover"].data or {}).get("profile") if t else None
    if not prof:
        pytest.skip("소개할 단지 없음")
    return R.scenes(t, prof)


# ── 규격 ─────────────────────────────────────────────────────────────────
def test_세로_9대16():
    """가로 영상을 올리면 인스타가 가운데를 잘라낸다."""
    assert (R.W, R.H) == (1080, 1920)
    assert abs(R.W / R.H - 9 / 16) < 0.01


def test_안전영역이_인스타_UI를_피한다():
    """위는 계정 배지, 아래는 캡션·버튼, 오른쪽은 액션 열이 덮는다.

    그 자리에 글자를 두면 **발행한 뒤에야** 가려진 걸 알게 된다.
    """
    assert R.SAFE_TOP >= 240, "위쪽 여백이 좁다"
    assert R.SAFE_BOTTOM >= 400, "아래쪽 여백이 좁다"
    assert R.SAFE_RIGHT >= 120, "오른쪽 액션 열 자리가 없다"
    # 글이 들어갈 폭이 남아 있어야 한다
    assert R.W - R.SAFE_X - R.SAFE_RIGHT >= 760


def test_자르기_영역이_가운데_1대1이다():
    """9:16 으로 올려도 피드·프로필 게시물은 가운데 1:1 만 보여 준다."""
    assert R.CROP_TOP == (R.H - R.W) // 2 == 420
    assert R.CROP_BOTTOM == R.CROP_TOP + R.W == 1500


def test_안전영역이_자르기_선에_맞는다():
    """예전 값(위 300·아래 460)으로는 브랜드와 진행 점이 통째로, 헤드라인
    첫 줄과 출처가 반쯤 잘려 나갔다. 전체 화면에서만 멀쩡해서 못 봤다."""
    assert R.SAFE_TOP == R.CROP_TOP
    assert R.H - R.SAFE_BOTTOM == R.CROP_BOTTOM


def test_머리글과_꼬리글이_자르기_안에_있다():
    """CSS 가 안전 영역 밖으로 음수 오프셋을 주면 다시 잘린다."""
    css = R.css()
    assert f"top:{R.SAFE_TOP}px" in css, "브랜드가 자르기 위로 나갔다"
    assert f"bottom:{R.SAFE_BOTTOM}px" in css, "출처가 자르기 아래로 나갔다"
    assert f"top:{R.SAFE_TOP - 92}px" not in css
    assert f"bottom:{R.SAFE_BOTTOM - 96}px" not in css


def test_유튜브_쇼츠_하단_띠도_피한다():
    """같은 파일을 쇼츠에도 올린다. 쇼츠는 아래 제목·채널 띠가 더 두껍다."""
    assert R.H - R.CROP_BOTTOM >= 400


def test_출처에_해제_문구가_없다(scs):
    """자리가 모자라 제일 먼저 잘리던 줄이다. 실제 필터링은 그대로 걸린다
    — tests/test_cancelled_filter.py 가 데이터 쪽을 지킨다."""
    for i, sc in enumerate(scs, 1):
        assert "해제" not in sc["foot"], f"{i}장 출처: {sc['foot']}"


def test_출처에_기관과_기준일은_남는다(scs):
    """문구를 줄이다 출처까지 지우면 안 된다."""
    for i, sc in enumerate(scs, 1):
        assert "국토교통부" in sc["foot"], f"{i}장"
        assert "기준" in sc["foot"], f"{i}장"


def test_길이가_릴스에_맞다(scs):
    """너무 길면 끝까지 안 본다. 완주율이 노출을 끌어올리는 지표다."""
    secs = len(scs) * (R.ANIM_S + R.HOLD_S) + (R.LAST_HOLD_S - R.HOLD_S)
    assert 12 <= secs <= 45, f"{secs:.0f}초"


def test_장면이_5에서_8개(scs):
    assert 5 <= len(scs) <= 8, len(scs)


# ── 움직임 ───────────────────────────────────────────────────────────────
def test_들어온_뒤에는_멈춘다():
    """글자가 계속 움직이면 읽을 수가 없다. 등장만 움직이고 나머지는 멈춘다."""
    assert R.ANIM_S <= 1.2, "등장이 너무 길다"
    assert R.HOLD_S >= R.ANIM_S * 2, "읽을 시간이 모자라다"


def test_등장이_끝나면_완전히_나타난다(scs):
    """t=1 에서 opacity 가 1 이 아니면 흐린 채로 멈춘 장이 생긴다."""
    for i, sc in enumerate(scs, 1):
        html = sc["body"](1.0)
        assert "opacity:1.000" in html, f"{i}장"
        assert "opacity:0.0" not in html, f"{i}장"


def test_숫자가_올라가며_멎는다():
    a, b = R.count(84000, 0.2), R.count(84000, 1.0)
    assert a != b, "카운트업이 안 된다"
    assert b == D.won(84000)


# ── 문구 (카드와 같은 기준) ──────────────────────────────────────────────
def test_영상_문구에_금지표현이_없다(scs):
    for i, sc in enumerate(scs, 1):
        t = strip_html(sc["body"](1.0))
        assert not check_banned(t), f"{i}장: {check_banned(t)}"


def test_영상에_통계용어가_없다(scs):
    for i, sc in enumerate(scs, 1):
        D.assert_no_jargon(strip_html(sc["body"](1.0)), f"scene{i}")


def test_마지막_장에_면책과_팔로우가_있다(scs):
    from templates.disclaimers import DISCLAIMER_SOCIAL
    t = strip_html(scs[-1]["body"](1.0))
    assert DISCLAIMER_SOCIAL.replace(" ", "") in t.replace(" ", "")
    assert D.HANDLE in t and "팔로우" in t


def test_모든_장에_출처가_있다(scs):
    for i, sc in enumerate(scs, 1):
        assert "국토교통부" in sc["foot"], f"{i}장"


# ── 소리 ─────────────────────────────────────────────────────────────────
def test_무음으로_내보낸다():
    """음원은 인스타 앱에서 고르는 게 저작권상 안전하고 노출에도 유리하다.

    영상에 음원을 박아 넣으면 저작권 신고 한 번에 계정이 위험해진다.
    """
    src = (ROOT / "content" / "reels.py").read_text(encoding="utf-8")
    assert "-c:a" not in src and "-i audio" not in src
    assert "무음" in src


# ── 산출물 ───────────────────────────────────────────────────────────────
def test_만들어진_영상이_규격에_맞다(data):
    mp4 = ROOT / "output" / data["asof"] / "reels.mp4"
    if not mp4.exists():
        pytest.skip("아직 렌더 안 됨")
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries",
         "format=duration", "-of", "json", str(mp4)],
        capture_output=True, text=True)
    j = json.loads(r.stdout)
    st = j["streams"][0]
    assert (st["width"], st["height"]) == (1080, 1920)
    assert 12 <= float(j["format"]["duration"]) <= 45


# ── 첫 프레임 ────────────────────────────────────────────────────────────
def test_훅은_첫_프레임부터_완성돼_있다(scs):
    """들어오는 동안은 글자가 투명해서 0초가 빈 화면이 된다.

    릴스는 첫 프레임이 전부고, 그리드 썸네일도 기본이 첫 프레임이다.
    실측: 평균 시청 2초 / 21초, 첫 프레임에 제목도 금액도 안 보였다.
    """
    assert scs[0].get("static") is True, "1장이 멈춰 서 있지 않다"


def test_올라가는_숫자는_1장에_쓰지_않는다(scs):
    """6.5억짜리 거래가 4.5억으로 먼저 보이고 그 상태로 스크린샷이 찍힌다.
    화면에 뜬 숫자는 늘 참이어야 한다."""
    body = R.strip_html(scs[0]["body"](1.0))
    first = R.strip_html(scs[0]["body"](1 / (R.ANIM_S * R.FPS)))
    assert body == first, "1장이 프레임마다 다른 숫자를 보여 준다"


def test_카운트업은_끝에서_참값에_멎는다():
    assert R.count(65000, 1.0) == D.won(65000)


def test_뒷장은_여전히_움직인다(scs):
    """이미 보고 있는 사람에게는 움직임이 시선을 끈다. 훅만 멈춘다."""
    assert not any(sc.get("static") for sc in scs[1:])
