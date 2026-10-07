"""텔레그램 봇 (notify/bot.py).

여기서 가장 중요한 건 **아무나 /숫자 를 못 보내게 하는 것**이다. 봇 이름만
알면 누구나 말을 걸 수 있는데, 번호 하나가 이 PC 에서 파이썬을 돌린다.

둘째는 **막혔을 때 이유가 폰까지 가는 것**이다. "실패"만 가면 PC 앞에
앉기 전까지 뭘 고쳐야 할지 모른다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from notify import bot as B  # noqa: E402
from notify import telegram as TG  # noqa: E402

MINE, OTHER = "8716873514", "9999999999"


@pytest.fixture
def sent(monkeypatch, tmp_path):
    """보낸 문구를 모은다. 네트워크는 타지 않는다."""
    box: list[str] = []
    monkeypatch.setattr(TG, "creds", lambda: ("1:tok", MINE))
    monkeypatch.setattr(B.TG, "creds", lambda: ("1:tok", MINE))
    monkeypatch.setattr(B.TG, "send",
                        lambda t, **k: box.append(t) or True)
    monkeypatch.setattr(B.TG, "send_file",
                        lambda p, c="", **k: box.append(f"[파일] {p}") or True)
    monkeypatch.setattr(B, "STATE", tmp_path / "state.json")
    return box


def state(n: int = 5) -> dict:
    return {
        "asof": "2026-10-06",
        "rows": [{"apt_id": f"a{i}", "pyeong_bucket": "20P"}
                 for i in range(1, n + 1)],
        "candidates": [{"apt_name": f"단지{i}", "region": f"구{i}",
                        "dong": "동", "pyeong": "20평대", "amount": "9.7억",
                        "over": 2.1, "hist": 100} for i in range(1, n + 1)],
    }


# ── 접근 제어 ────────────────────────────────────────────────────────────
def test_내_chat_id만_받는다(sent):
    assert B.allowed(MINE)
    assert B.allowed(int(MINE))


def test_남의_chat_id는_막는다(sent):
    """번호 하나가 이 PC 에서 파이썬을 돌린다."""
    assert not B.allowed(OTHER)
    assert not B.allowed(None)


def test_chat_id가_설정되지_않으면_아무도_못_들어온다(monkeypatch):
    monkeypatch.setattr(B.TG, "creds", lambda: ("1:tok", ""))
    assert not B.allowed(MINE)
    assert not B.allowed("")


# ── 번호 받기 ────────────────────────────────────────────────────────────
def test_후보가_없으면_먼저_받으라고_한다(sent):
    B.save({})
    B.handle("2")
    assert any("/today" in s for s in sent)


def test_범위_밖_번호를_막는다(sent):
    B.save(state(5))
    B.handle("9")
    assert any("1~5" in s for s in sent)


def test_영번도_막는다(sent):
    B.save(state(5))
    B.handle("0")
    assert any("1~5" in s for s in sent)


def test_지표가_바뀌면_다시_받으라고_한다(sent, monkeypatch):
    """후보 목록은 그때의 지표에 묶여 있다. 그 사이 지표가 갱신되면
    번호와 단지가 어긋난다 — 엉뚱한 단지로 영상이 나간다."""
    B.save(state(5))
    monkeypatch.setattr(B, "metrics", lambda: {"asof": "2026-10-07"})
    B.handle("1")
    assert any("다시" in s for s in sent)


def test_지표가_아예_없으면_알린다(sent, monkeypatch):
    B.save(state(5))
    monkeypatch.setattr(B, "metrics", lambda: None)
    B.handle("1")
    assert sent


def test_재료가_모자라면_이유를_보낸다(sent, monkeypatch):
    """프로필을 못 만드는 단지가 있다. 그냥 실패하면 왜인지 모른다."""
    B.save(state(5))
    monkeypatch.setattr(B, "metrics", lambda: {"asof": "2026-10-06"})
    monkeypatch.setattr("metrics.build_metrics.profile_for",
                        lambda d, r: None)
    B.handle("1")
    assert any("재료" in s for s in sent)


def test_터져도_폰으로_이유가_간다(sent, monkeypatch):
    B.save(state(5))

    def boom():
        raise RuntimeError("검증 실패: 2장 숫자 불일치")

    monkeypatch.setattr(B, "metrics", boom)
    B.handle("1")
    assert any("막혔" in s for s in sent)


def test_예외에_토큰이_섞여도_가린다(sent, monkeypatch):
    """예외 메시지에 요청 URL 이 붙는 경로가 있다."""
    tok = "8621196066:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    B.save(state(5))

    def boom():
        raise RuntimeError(f"fail https://api.telegram.org/bot{tok}/x")

    monkeypatch.setattr(B, "metrics", boom)
    B.handle("1")
    assert not any(tok in s for s in sent)


# ── 명령 ─────────────────────────────────────────────────────────────────
def test_도움말을_준다(sent):
    B.handle("/help")
    assert any("/today" in s for s in sent)


def test_모르는_말에는_도움말을_붙인다(sent):
    B.handle("안녕하세요")
    assert any("/today" in s for s in sent)


def test_again은_마지막_영상을_다시_보낸다(sent, tmp_path):
    f = tmp_path / "reels.mp4"
    f.write_bytes(b"0")
    B.save({"last": str(f), "last_label": "신트리4 (양천구)"})
    B.handle("/again")
    assert any(s.startswith("[파일]") for s in sent)


def test_만든_게_없으면_again이_알려준다(sent):
    B.save({})
    B.handle("/again")
    assert any("없습니다" in s for s in sent)


def test_사라진_파일을_보내려_하지_않는다(sent):
    B.save({"last": str(ROOT / "output" / "없는파일.mp4")})
    B.handle("/again")
    assert not any(s.startswith("[파일]") for s in sent)


# ── 아침 전송 ────────────────────────────────────────────────────────────
def test_후보가_없으면_없다고_보낸다(sent, monkeypatch):
    monkeypatch.setattr(B, "metrics", lambda: {"asof": "2026-10-06"})
    monkeypatch.setattr(B, "candidates", lambda d: [])
    assert B.morning() is False
    assert any("없습니다" in s for s in sent)


def test_아침_전송이_번호와_단지를_묶어_남긴다(sent, monkeypatch):
    """남겨 두지 않으면 사용자가 보낸 '3' 이 무엇인지 알 수 없다."""
    cands = [dict(c, row={"apt_id": f"a{i}", "pyeong_bucket": "20P"})
             for i, c in enumerate(state(3)["candidates"], 1)]
    monkeypatch.setattr(B, "metrics", lambda: {"asof": "2026-10-06"})
    monkeypatch.setattr(B, "candidates", lambda d: cands)
    assert B.morning() is True
    st = B.load()
    assert len(st["rows"]) == 3 and len(st["candidates"]) == 3
    assert st["asof"] == "2026-10-06"
    # row 는 따로 담는다 — 카드 문구에 섞이면 안 된다
    assert "row" not in st["candidates"][0]


def test_아침_문구에_단지와_금액이_들어간다(sent, monkeypatch):
    cands = [dict(c, row={"apt_id": "a1", "pyeong_bucket": "20P"})
             for c in state(2)["candidates"]]
    monkeypatch.setattr(B, "metrics", lambda: {"asof": "2026-10-06"})
    monkeypatch.setattr(B, "candidates", lambda d: cands)
    B.morning()
    body = sent[-1]
    assert "단지1" in body and "9.7억" in body and "구1" in body


def test_카드에_표본이_들어간다():
    """표본 없이 고르면 거래 몇 건짜리 '신고가'를 고르게 된다."""
    c = dict(state(1)["candidates"][0], deals_1y=70)
    out = B.card(1, c)
    assert "100건" in out and "70건" in out


def test_카드는_1년_거래가_없어도_만들어진다():
    out = B.card(1, state(1)["candidates"][0])
    assert "단지1" in out and "누적" in out


# ── 상태 파일 ────────────────────────────────────────────────────────────
def test_깨진_상태파일을_읽어도_안_터진다(sent):
    B.STATE.parent.mkdir(parents=True, exist_ok=True)
    B.STATE.write_text("{망가짐", encoding="utf-8")
    assert B.load() == {}


def test_상태를_저장하고_다시_읽는다(sent):
    B.save({"offset": 42})
    assert B.load()["offset"] == 42
