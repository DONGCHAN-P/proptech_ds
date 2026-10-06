"""표지 선정 규칙 (5-1항) · 사진 라이선스 (5-0항).

여기가 "통계적으로 가장 튄 곳"과 "사람들이 아는 곳"을 가른다. 규칙이 조용히
풀리면 매주 표지가 거래 몇십 건짜리 외곽 군으로 돌아가는데, 수치는 맞아서
아무도 못 알아챈다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import cover as CV  # noqa: E402
from content import photos  # noqa: E402


@pytest.fixture(scope="module")
def data() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


# ── 우선 후보 ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name,code", [
    ("마포구", "11440"), ("강남구", "11680"), ("송파구", "11710"),
    ("성남분당구", "41135"), ("고양일산동구", "41285"),
    ("안양동안구", "41173"), ("군포시", "41410"), ("부천원미구", "41192"),
])
def test_우선_후보로_인식한다(name, code):
    assert CV.is_priority(name, code), name


@pytest.mark.parametrize("name", ["연천군", "가평군", "양평군", "포천시"])
def test_외곽은_우선_후보가_아니다(name):
    assert not CV.is_priority(name, CV.NAME_TO_CODE.get(name))


def test_코드가_없어도_이름으로_되짚는다():
    """지표 행에 sigungu_code 가 빠지면 서울 25개 구가 통째로 밀려난다.

    실제로 daily.new_high 에 코드가 없어서 마포·송파·성북이 전부 "기타"로
    분류됐다. 지표 쪽도 고쳤지만 조용히 틀리는 자리라 안전망을 둔다.
    """
    assert CV.is_priority("마포구", None)
    assert CV.resolve("성남분당구", None) == "41135"


# ── 규칙 ─────────────────────────────────────────────────────────────────
def test_표본이_적으면_표지에_오르지_못한다(data):
    for c in CV.build(data):
        assert c.sample >= CV.MIN_SAMPLE, (c.region, c.sample)


def test_앵글_우선순위를_따른다(data):
    """① 신고가 ② 반전 ③ 급증. 세기가 더 커도 순위가 앞서지 않는다."""
    picked, top3, _ = CV.choose(data)
    assert picked is not None
    best = min(CV.ANGLE_RANK[c.angle] for c in CV.build(data))
    assert CV.ANGLE_RANK[picked.angle] == best


def test_비우선_지역은_확실히_클_때만_표지(data):
    """1.5배 미만 차이면 2장 순위표에서만 다룬다."""
    picked, _, _ = CV.choose(data)
    if picked.priority:
        return
    peers = [c.strength for c in CV.build(data)
             if c.priority and c.angle == picked.angle]
    if peers:
        assert picked.strength >= max(peers) * CV.OUTSIDER_EDGE


def test_같은_데이터면_항상_같은_표지(data):
    """캐러셀·캡션·스레드가 각자 부른다. 호출마다 답이 달라지면 말이 갈린다."""
    picks = {CV.choose(data)[0].region for _ in range(3)}
    assert len(picks) == 1, picks


def test_이번_회차는_반복금지에_걸리지_않는다(data, tmp_path, monkeypatch):
    """로그를 쓴 뒤 다시 고를 때 자기 자신이 걸리면 안 된다."""
    monkeypatch.setattr(CV, "LOG", tmp_path / "log.json")
    first, top3, notes = CV.choose(data)
    CV.log(data["asof"], first, top3, notes)
    again, _, _ = CV.choose(data)
    assert again.region == first.region


def test_직전_회차_지역은_연속으로_오르지_않는다(data, tmp_path, monkeypatch):
    monkeypatch.setattr(CV, "LOG", tmp_path / "log.json")
    first, top3, notes = CV.choose(data)
    CV.log("2000-01-01", first, top3, notes)     # 다른 회차로 기록
    again, _, _ = CV.choose(data)
    if len({c.region for c in CV.build(data)}) > 1:
        assert again.region != first.region


def test_선정_이유를_로그로_남긴다(data, tmp_path, monkeypatch):
    """10항 성과 측정의 입력. 후보 3개와 사유가 있어야 규칙을 고칠 수 있다."""
    monkeypatch.setattr(CV, "LOG", tmp_path / "log.json")
    picked, top3, notes = CV.choose(data)
    CV.log(data["asof"], picked, top3, notes)
    rows = json.loads((tmp_path / "log.json").read_text(encoding="utf-8"))
    r = rows[-1]
    assert r["picked"]["angle_label"] and r["picked"]["headline"]
    assert 1 <= len(r["candidates"]) <= 3
    for c in r["candidates"]:
        assert {"angle", "region", "priority", "headline", "sample"} <= set(c)


# ── 사진 라이선스 (5-0항) ────────────────────────────────────────────────
def test_라이선스_파일이_없으면_쓰지_않는다(tmp_path, monkeypatch):
    monkeypatch.setattr(photos, "PHOTO_DIR", tmp_path)
    d = tmp_path / "11440"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\xff\xd8\xff")
    got, problems = photos.find("11440")
    assert got is None
    assert problems and "license.json 없음" in problems[0]


def test_허용되지_않는_라이선스를_막는다(tmp_path, monkeypatch):
    monkeypatch.setattr(photos, "PHOTO_DIR", tmp_path)
    d = tmp_path / "11440"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\xff\xd8\xff")
    (d / "a.jpg.license.json").write_text(json.dumps({
        "source": "어디선가", "type": "unknown",
        "acquired": "2026-10-06", "credit": "출처 미상"}), encoding="utf-8")
    got, problems = photos.find("11440")
    assert got is None and problems


def test_제대로_된_사진은_통과한다(tmp_path, monkeypatch):
    monkeypatch.setattr(photos, "PHOTO_DIR", tmp_path)
    d = tmp_path / "11440"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\xff\xd8\xff")
    (d / "a.jpg.license.json").write_text(json.dumps({
        "source": "직접 촬영", "type": "own", "acquired": "2026-10-06",
        "credit": "사진: 직접 촬영", "scene": "region"}), encoding="utf-8")
    got, problems = photos.find("11440")
    assert got and not problems
    assert got.is_region          # 지역 풍경 → "이미지는 지역 참고용" 표기 대상
    assert got.data_uri().startswith("data:image/jpeg;base64,")


def test_사진이_없는_건_실패가_아니다(tmp_path, monkeypatch):
    """폴백 신호다 — 사진을 못 구하면 오프화이트 표지로 간다 (5항)."""
    monkeypatch.setattr(photos, "PHOTO_DIR", tmp_path)
    got, problems = photos.find("99999")
    assert got is None and not problems


def test_보유_사진이_전부_라이선스를_갖췄다():
    assert not photos.audit()
