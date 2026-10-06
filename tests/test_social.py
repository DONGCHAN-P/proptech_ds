"""스레드 · 인스타 텍스트 포맷 검증.

두 플랫폼은 읽기 방식이 달라서 같은 글을 올리면 양쪽 다 안 읽힌다
(`docs/02_CLI_디자인지시사항.md` 8항).

                  스레드                 인스타 캡션
    길이          500자                  2,200자
    면책          1줄 축약 + 프로필      전문 그대로
    해시태그      쓰지 않는다            마지막 블록
    첫 줄         훅 (여기서 접힌다)     훅 + 넘김 유도 (2줄이 미리보기)

포맷이 무너지는 건 눈으로 잘 안 보인다 — 500자를 3자 넘겨도 멀쩡해 보이고,
잘리는 건 발행 후다. 그래서 기계가 센다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import caption as CAP  # noqa: E402
from content import thread as T  # noqa: E402
from content import design as D  # noqa: E402
from templates.disclaimers import (  # noqa: E402
    DISCLAIMER_SOCIAL, DISCLAIMER_THREADS,
)


@pytest.fixture(scope="module")
def data() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def posts(data) -> list[dict]:
    out = []
    for kind in T.DRAFTERS:
        out += T.generate(kind, data, n=1)
    if not out:
        pytest.skip("재료 부족")
    return out


def lines(text: str) -> list[str]:
    return [ln for ln in text.split("\n") if ln.strip()]


# ── 스레드 ───────────────────────────────────────────────────────────────
def test_스레드_초안이_검증을_통과한다(posts):
    for p in posts:
        assert p["ok"], f"{p['kind']}: {p['reasons']}"


def test_스레드는_500자_안에_든다(posts):
    """넘으면 뒤가 잘린다. 잘리는 건 보통 면책과 CTA 다."""
    for p in posts:
        assert p["length"] <= T.MAX_LEN, f"{p['kind']} {p['length']}자"


def test_첫줄이_훅이다(posts):
    """타임라인에서 접히기 전에 보이는 건 첫 줄까지다."""
    for p in posts:
        first = lines(p["text"])[0]
        assert T.hook_ok(first), f"{p['kind']}: {len(first)}자 — {first}"
        assert not first.startswith("·"), f"{p['kind']}: 훅이 불릿이다"


def test_훅_다음이_근거_3에서_5줄(posts):
    for p in posts:
        body = [ln for ln in lines(p["text"]) if ln.startswith("·")]
        lo, hi = T.BODY_LINES
        assert lo <= len(body) <= hi, f"{p['kind']}: 근거 {len(body)}줄"


def test_마지막_본문줄이_질문형(posts):
    """댓글이 붙어야 노출이 는다. 평서문으로 끝나면 대화가 안 열린다.

    본문과 고정 꼬리(면책 + CTA)는 `split_fixed` 가 가른다. 꼬리 문구를
    테스트가 직접 열거하면 CTA 가 바뀔 때마다 같이 고쳐야 한다 — 실제로
    자리표시자를 팔로우 유도로 바꾸자 이 검사가 깨졌다.
    """
    from content.thread import split_fixed
    for p in posts:
        body = lines(split_fixed(p["text"])[0])
        assert body[-1].endswith("?"), f"{p['kind']}: {body[-1]}"


def test_스레드_면책은_1줄_축약(posts):
    """전문 4줄을 붙이면 본문보다 면책이 길어져 아무도 안 읽는다."""
    for p in posts:
        assert DISCLAIMER_THREADS in p["text"], p["kind"]
        assert DISCLAIMER_SOCIAL not in p["text"], f"{p['kind']}: 전문이 들어갔다"


def test_축약_면책이_전문의_자리를_가리킨다():
    """줄이는 대신 전문이 어디 있는지는 반드시 말한다."""
    assert "프로필" in DISCLAIMER_THREADS
    assert "책임은 본인" in DISCLAIMER_THREADS


def test_스레드에_해시태그를_쓰지_않는다(posts):
    """스레드는 해시태그 문화가 아니다. 붙이면 스팸으로 읽힌다."""
    for p in posts:
        assert "#" not in p["text"], p["kind"]


def test_스레드가_구어체다(posts):
    """보고서 문체는 타임라인에서 넘겨진다."""
    for p in posts:
        body = [ln for ln in lines(p["text"]) if ln.startswith("·")]
        assert any(ln.rstrip(".").endswith(("요", "고요", "어요"))
                   for ln in body), f"{p['kind']}: 구어체가 아니다"


def test_스레드에_통계용어가_없다(posts):
    for p in posts:
        D.assert_no_jargon(p["text"], p["kind"])


def test_CTA가_모든_글에_있다(posts):
    """Phase 7 M0 — Day 1부터 동선을 넣는다.

    뉴스레터 링크가 아직 없으면 팔로우 유도로 대신한다. 자리표시자
    "(링크 준비 중)" 을 그대로 올리지는 않는다.
    """
    import os
    want = "받아보기" if os.environ.get("NEWSLETTER_URL", "").strip() else "팔로우"
    for p in posts:
        assert want in p["text"], p["kind"]
        assert "준비 중" not in p["text"], f"{p['kind']}: 자리표시자가 올라간다"


# ── 인스타 캡션 ──────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def cap(data) -> dict:
    c = CAP.build(data)
    if c is None:
        pytest.skip("재료 부족")
    return c


def test_캡션이_검증을_통과한다(cap):
    assert cap["ok"], cap["reasons"]


def test_캡션이_2200자_안에_든다(cap):
    assert cap["length"] <= CAP.MAX_LEN, cap["length"]


def test_캡션_앞_2줄이_미리보기로_선다(cap):
    """'더 보기' 앞에서 넘길지 말지가 결정된다."""
    pre = cap["preview"].split("\n")
    assert len(pre) == CAP.PREVIEW_LINES
    assert all(0 < len(ln) <= 80 for ln in pre), pre
    assert not pre[0].startswith("·"), "미리보기 첫 줄이 불릿이다"


def test_캡션_면책은_전문이다(cap):
    """캡션은 2,200자가 있다. 줄일 이유가 없다."""
    assert DISCLAIMER_SOCIAL in cap["text"]


def test_해시태그가_30개_이하(cap):
    assert cap["text"].count("#") <= CAP.MAX_TAGS


def test_해시태그가_맨_끝에_몰려있다(cap):
    """본문 사이에 끼우면 읽기가 끊긴다."""
    tag_block = cap["text"].split("\n")[-1]
    assert tag_block.startswith("#")
    assert cap["text"].count("#") == tag_block.count("#")


def test_해시태그에_금지어가_없다(cap):
    """#저평가아파트 같은 태그가 섞이는 사고를 막는다."""
    from content.validator import check_banned
    assert not check_banned(cap["text"].split("\n")[-1])


def test_캡션에_질문이_있다(cap):
    assert "?" in cap["text"], "댓글을 유도하는 질문이 없다"


# ── 두 포맷이 같은 소재를 쓴다 ───────────────────────────────────────────
def test_캡션과_캐러셀이_같은_단지를_가리킨다(data, cap):
    """캡션이 가리키는 단지와 이미지에 그려진 단지가 어긋나면 사람 눈에 잘
    안 띄는데, 보는 사람은 바로 알아챈다."""
    from content.carousel import build_cards
    cards = build_cards(data, ROOT / "output" / data["asof"])
    if not cards:
        pytest.skip("재료 부족")
    # 캡션 첫 줄은 **표지 소재**를 말한다. 전에는 거래량 1위 단지(top)를
    # 봤는데, 표지는 5-1항 규칙으로 따로 고르므로 둘이 달라질 수 있다.
    cov = cap["facts"]["cover"]
    key = cov.get("apt_name") or cov.get("sigungu_name")
    assert any(key in c["html"] for c in cards), key
