"""텔레그램 알림 (notify/telegram.py).

여기서 가장 중요한 건 **토큰이 밖으로 새지 않는 것**이다. 봇 토큰은 URL 에
들어가고 requests 예외에는 URL 이 그대로 붙는다. 이 레포는 소스에 남은 API
키 때문에 git 이력을 통째로 재작성한 적이 있다 — 같은 일을 로그로 반복하지
않게 마스킹을 테스트로 고정한다.

둘째는 **알림이 파이프라인을 멈추지 않는 것**이다. 키가 없거나 텔레그램이
죽어도 수집·지표는 그대로 돌아야 한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from notify import telegram as T  # noqa: E402

TOKEN = "2222222222:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


@pytest.fixture
def unset(monkeypatch):
    """키가 없는 상태. load_dotenv 는 이미 있는 환경변수를 덮지 않는다."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "")
    monkeypatch.setattr(T, "creds", lambda: ("", ""))
    return monkeypatch


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(T, "creds", lambda: (TOKEN, "1111111111"))
    return monkeypatch


# ── 토큰 유출 ────────────────────────────────────────────────────────────
def test_토큰을_그대로_내보내지_않는다():
    out = T.mask(f"HTTPError: 401 for url https://api.telegram.org/bot{TOKEN}/getMe",
                 TOKEN)
    assert TOKEN not in out
    assert "AAHxxx" not in out


def test_봇ID만_있어도_가린다():
    """토큰 앞의 숫자만으로도 어느 봇인지 특정된다."""
    assert "2222222222" not in T.mask("bot 2222222222 실패", TOKEN)


def test_토큰을_모르는_자리에서도_모양으로_가린다():
    """마스킹 대상 토큰을 넘기지 못하는 호출 경로가 있다."""
    leaked = f"url=https://api.telegram.org/bot{TOKEN}/sendMessage"
    assert TOKEN not in T.mask(leaked)


def test_예외_메시지가_마스킹을_거친다(setup, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError(f"connect fail https://api.telegram.org/bot{TOKEN}/x")

    import requests
    monkeypatch.setattr(requests, "post", boom)
    res = T._post("sendMessage", TOKEN, data={})
    assert not res["ok"]
    assert TOKEN not in res["error"]


def test_마스킹이_멀쩡한_문장은_건드리지_않는다():
    s = "수집 실패: 서울 84개 시군구 중 3곳 누락"
    assert T.mask(s, TOKEN) == s


# ── 설정이 없을 때 ───────────────────────────────────────────────────────
def test_키가_없으면_조용히_건너뛴다(unset):
    """알림이 안 되는 것 때문에 파이프라인이 죽으면 본말전도다."""
    assert T.send("아무거나") is False


def test_키가_없으면_파일도_건너뛴다(unset, tmp_path):
    f = tmp_path / "a.mp4"
    f.write_bytes(b"x")
    assert T.send_file(f) is False


def test_키가_없으면_알림도_건너뛴다(unset):
    assert T.alert("수집 실패") is False


def test_건너뛸_때_사실을_찍는다(unset, capsys):
    T.send("x")
    assert "미설정" in capsys.readouterr().out


# ── 실패 사유 안내 ───────────────────────────────────────────────────────
def test_토큰이_틀리면_토큰을_가리킨다():
    msg = T.explain({"code": 401, "error": "Unauthorized"})
    assert "토큰" in msg


def test_chat을_못찾으면_start를_가리킨다():
    """가장 흔한 막힘. "chat not found" 만 보면 뭘 할지 모른다."""
    msg = T.explain({"code": 400, "error": "Bad Request: chat not found"})
    assert "/start" in msg


def test_차단당한_경우를_구분한다():
    msg = T.explain({"code": 403, "error": "Forbidden: bot was blocked by the user"})
    assert "차단" in msg


def test_모르는_사유는_원문을_남긴다():
    assert "flood wait" in T.explain({"code": 429, "error": "flood wait"})


# ── 전송 ─────────────────────────────────────────────────────────────────
def test_문구를_보낸다(setup, monkeypatch):
    sent = {}

    def fake(method, token, *, data, files=None):
        sent.update(method=method, data=data)
        return {"ok": True, "result": {}}

    monkeypatch.setattr(T, "_post", fake)
    assert T.send("안녕") is True
    assert sent["method"] == "sendMessage"
    assert sent["data"]["text"] == "안녕"
    assert sent["data"]["chat_id"] == "1111111111"


def test_너무_긴_문구는_잘라서_보낸다(setup, monkeypatch):
    """4096자를 넘기면 텔레그램이 통째로 거절한다 — 잘려도 가는 게 낫다."""
    got = {}
    monkeypatch.setattr(T, "_post", lambda m, t, *, data, files=None: (
        got.update(data=data) or {"ok": True}))
    T.send("가" * 9000)
    assert len(got["data"]["text"]) <= T.MAX_TEXT


def test_전송_실패해도_예외를_던지지_않는다(setup, monkeypatch):
    monkeypatch.setattr(T, "_post", lambda *a, **k: {
        "ok": False, "code": 400, "error": "chat not found"})
    assert T.send("x") is False


def test_영상은_재인코딩되지_않게_document로_보낸다(setup, monkeypatch, tmp_path):
    """sendVideo 는 텔레그램이 다시 인코딩한다. 인스타에 올릴 원본이라
    중간에 화질을 깎으면 안 된다."""
    got = {}
    monkeypatch.setattr(T, "_post", lambda m, t, *, data, files=None,
                        timeout=None: (
        got.update(method=m, files=files) or {"ok": True}))
    f = tmp_path / "reels.mp4"
    f.write_bytes(b"0" * 1024)
    assert T.send_file(f, "캡션") is True
    assert got["method"] == "sendDocument"
    assert "document" in got["files"]


def test_큰_파일은_기다리는_시간을_늘린다(setup, monkeypatch, tmp_path):
    """30초는 글 몇 줄 기준이다. 상한이 50MB 인데 30초로 끊으면 큰 파일은
    영영 못 보낸다 — 12분짜리 영상이 실제로 write timeout 으로 끊겼다."""
    got = {}
    monkeypatch.setattr(T, "_post", lambda m, t, *, data, files=None,
                        timeout=None: (
        got.update(timeout=timeout) or {"ok": True}))
    f = tmp_path / "long.mp4"
    f.write_bytes(b"0" * 30 * 1024 * 1024)
    assert T.send_file(f, quiet=True) is True
    assert got["timeout"] > T.TIMEOUT * 10


def test_없는_파일은_보내지_않는다(setup):
    assert T.send_file("output/없는파일.mp4") is False


def test_상한을_넘는_파일은_보내기_전에_막는다(setup, monkeypatch, tmp_path):
    """서버가 거절할 걸 알면서 50MB 를 올리면 시간만 버린다."""
    called = []
    monkeypatch.setattr(T, "_post", lambda *a, **k: called.append(1) or {"ok": True})
    f = tmp_path / "big.mp4"
    f.write_bytes(b"0" * 1024)
    monkeypatch.setattr(T, "MAX_UPLOAD_MB", 0.0005)
    assert T.send_file(f) is False
    assert not called, "상한 초과인데 업로드를 시도했다"


# ── chat_id 찾기 ─────────────────────────────────────────────────────────
def test_메시지에서_chat_id를_찾는다(monkeypatch):
    monkeypatch.setattr(T, "_post", lambda *a, **k: {"ok": True, "result": [
        {"message": {"chat": {"id": 1111111111, "type": "private",
                              "username": "DongChan"}}}]})
    got = T.discover(TOKEN)
    assert 1111111111 in got and "private" in got[1111111111]


def test_start만_눌러도_찾는다(monkeypatch):
    """/start 는 my_chat_member 로만 올 때가 있다 — message 만 보면 놓친다."""
    monkeypatch.setattr(T, "_post", lambda *a, **k: {"ok": True, "result": [
        {"my_chat_member": {"chat": {"id": 42, "type": "private",
                                     "first_name": "D"}}}]})
    assert 42 in T.discover(TOKEN)


def test_대화가_없으면_빈_결과(monkeypatch):
    monkeypatch.setattr(T, "_post", lambda *a, **k: {"ok": True, "result": []})
    assert T.discover(TOKEN) == {}


def test_getUpdates가_실패해도_터지지_않는다(monkeypatch):
    monkeypatch.setattr(T, "_post", lambda *a, **k: {
        "ok": False, "code": 401, "error": "Unauthorized"})
    assert T.discover(TOKEN) == {}


# ── 실패 알림 ────────────────────────────────────────────────────────────
def test_알림은_제목과_세부를_함께_보낸다(setup, monkeypatch):
    got = {}
    monkeypatch.setattr(T, "_post", lambda m, t, *, data, files=None: (
        got.update(data=data) or {"ok": True}))
    T.alert("수집 실패", ["서울 3곳 누락", "재시도 2회 실패"])
    body = got["data"]["text"]
    assert "수집 실패" in body and "서울 3곳 누락" in body


def test_세부가_없어도_보낸다(setup, monkeypatch):
    monkeypatch.setattr(T, "_post", lambda *a, **k: {"ok": True})
    assert T.alert("토큰 만료") is True
