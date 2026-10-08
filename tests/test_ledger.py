"""발행 원장 (content/ledger.py).

여기가 비면 "2주 연속 같은 지역 금지"가 조용히 아무 일도 안 한다. 수동
업로드라서 **올렸다는 사실은 사람만 안다** — 봇의 /done 이 유일한 통로다.

고른 기록(cover_log)과 가르는 게 요점이다. 봇으로 하루에 영상을 셋 만들어도
올리는 건 하나인데, 고른 기록으로 판단하면 만들기만 하고 버린 지역이 다음
주를 막는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import ledger as LD  # noqa: E402


@pytest.fixture
def log(monkeypatch, tmp_path):
    monkeypatch.setattr(LD, "LOG", tmp_path / "publish_log.json")
    return LD.LOG


def info(name="가단지", region="마포구", key="a1:20P") -> dict:
    return {"key": key, "apt_name": name, "region": region, "pyeong": "20평대"}


# ── 기록 ─────────────────────────────────────────────────────────────────
def test_올린_것을_남긴다(log):
    LD.record("2026-10-06", info())
    rows = LD.rows()
    assert len(rows) == 1
    assert rows[0]["region"] == "마포구"
    assert rows[0]["status"] == LD.PUBLISHED
    assert rows[0]["at"]


def test_같은_회차_같은_단지는_덮어쓴다(log):
    """/done 을 두 번 눌렀다고 두 줄이 되면 '몇 번 올렸나'가 틀어진다."""
    LD.record("2026-10-06", info(), LD.SKIPPED)
    LD.record("2026-10-06", info(), LD.PUBLISHED)
    rows = LD.rows()
    assert len(rows) == 1
    assert rows[0]["status"] == LD.PUBLISHED


def test_같은_회차_다른_단지는_따로_쌓인다(log):
    LD.record("2026-10-06", info("가단지", key="a1:20P"))
    LD.record("2026-10-06", info("나단지", key="a2:25P"))
    assert len(LD.rows()) == 2


def test_같은_단지_다른_평형을_가른다(log):
    """한 단지가 평형 둘로 올라오는 날이 있다."""
    LD.record("2026-10-06", info(key="a1:20P"))
    LD.record("2026-10-06", info(key="a1:30P"))
    assert len(LD.rows()) == 2


# ── 중복 방지 ────────────────────────────────────────────────────────────
def test_안_올린_것은_막지_않는다(log):
    """만들기만 하고 버린 지역이 다음 주를 막으면 안 된다."""
    LD.record("2026-10-06", info(region="양천구"), LD.SKIPPED)
    assert LD.regions(1, exclude_asof="2026-10-07") == set()


def test_올린_지역은_다음_회차에서_막는다(log):
    LD.record("2026-10-06", info(region="양천구"), LD.PUBLISHED)
    assert LD.regions(1, exclude_asof="2026-10-07") == {"양천구"}


def test_이번_회차는_스스로를_막지_않는다(log):
    """안 빼면 기록한 뒤 다시 고를 때 자기 자신이 걸린다 — 같은 발행물
    안에서 캐러셀과 캡션이 다른 지역을 말하게 된다."""
    LD.record("2026-10-06", info(region="양천구"))
    assert LD.regions(1, exclude_asof="2026-10-06") == set()


def test_회차_수로_센다_줄_수가_아니라(log):
    """한 회차에 둘을 올려도 '직전 1회차'는 그 회차 전체다."""
    LD.record("2026-10-05", info("가", region="강북구", key="a:20P"))
    LD.record("2026-10-06", info("나", region="양천구", key="b:20P"))
    LD.record("2026-10-06", info("다", region="구로구", key="c:20P"))
    assert LD.regions(1, exclude_asof="2026-10-07") == {"양천구", "구로구"}
    assert LD.regions(2, exclude_asof="2026-10-07") == {
        "강북구", "양천구", "구로구"}


# ── 견고함 ───────────────────────────────────────────────────────────────
def test_파일이_없어도_안_터진다(log):
    assert LD.rows() == []
    assert LD.regions(1) == set()
    assert LD.has_any() is False


def test_깨진_파일이어도_발행을_막지_않는다(log):
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("{망가짐", encoding="utf-8")
    assert LD.rows() == []
    assert LD.regions(1) == set()


def test_리스트가_아닌_파일도_넘긴다(log):
    log.write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert LD.rows() == []


def test_쓰이기_시작했는지_안다(log):
    assert not LD.has_any()
    LD.record("2026-10-06", info())
    assert LD.has_any()


def test_최근_몇_줄을_준다(log):
    for i in range(12):
        LD.record(f"2026-10-{i + 1:02d}", info(key=f"a{i}:20P"))
    assert len(LD.recent(5)) == 5


# ── cover 와의 연결 ──────────────────────────────────────────────────────
def test_원장이_비면_옛_기록으로_돌아간다(log, monkeypatch, tmp_path):
    """원장을 막 도입한 주에도 직전 회차를 알아야 한다."""
    from content import cover as CV
    old = tmp_path / "cover_log.json"
    old.write_text(json.dumps(
        [{"asof": "2026-10-05", "picked": {"region": "강북구"}}]),
        encoding="utf-8")
    monkeypatch.setattr(CV, "LOG", old)
    assert CV.recent_regions("2026-10-06") == {"강북구"}


def test_원장이_있으면_원장이_이긴다(log, monkeypatch, tmp_path):
    """cover_log 는 **고른** 기록이라, 만들기만 한 지역까지 막는다."""
    from content import cover as CV
    old = tmp_path / "cover_log.json"
    old.write_text(json.dumps(
        [{"asof": "2026-10-05", "picked": {"region": "만들기만한구"}}]),
        encoding="utf-8")
    monkeypatch.setattr(CV, "LOG", old)
    LD.record("2026-10-05", info(region="실제올린구"), LD.PUBLISHED)
    assert CV.recent_regions("2026-10-06") == {"실제올린구"}
