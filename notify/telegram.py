"""텔레그램 알림·전송.

쓰임새 둘.
  ① 실패 알림 (T24) — 수집 실패·검증기 차단·렌더 실패를 즉시 폰으로
  ② 발행 패키지 전송 (T17) — 릴스 mp4 와 캡션을 폰으로 받아 바로 업로드

**토큰은 URL 안에 들어간다.** requests 의 예외 메시지에는 요청 URL 이 그대로
붙으므로, 아무 생각 없이 `print(e)` 하면 봇 토큰이 로그와 콘솔에 남는다. 이
레포는 docstring 에 남은 API 키 때문에 git 이력을 통째로 재작성한 적이 있다
(H9). 그래서 밖으로 나가는 모든 문자열은 mask() 를 거친다.

**영상은 sendDocument 로 보낸다.** sendVideo 는 텔레그램이 재인코딩해서
화질이 깎인다. 우리가 보내는 mp4 는 인스타에 그대로 올릴 **원본**이고,
인스타가 어차피 한 번 더 인코딩한다. 중간에 한 번 더 깎을 이유가 없다.

키가 없으면 조용히 건너뛴다 — 알림이 안 되는 것 때문에 파이프라인이 멈추면
본말이 전도된다. 다만 "건너뛰었다"는 사실은 반드시 찍는다.

실행:
  .venv\\Scripts\\python.exe -m notify.telegram --test
  .venv\\Scripts\\python.exe -m notify.telegram --send "문구"
  .venv\\Scripts\\python.exe -m notify.telegram --file output/2026-10-06/reels.mp4
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

API = "https://api.telegram.org"
TIMEOUT = 30
# 봇이 보낼 수 있는 파일 상한 (Bot API). 넘으면 서버가 거절한다.
MAX_UPLOAD_MB = 50
MAX_TEXT = 4096          # sendMessage 본문 상한


def creds() -> tuple[str, str]:
    """(토큰, chat_id). 둘 중 하나라도 없으면 빈 문자열.

    .env 를 먼저 본다 (.env.example 이 선언한 자리). 없으면 secrets.json —
    Slack 훅이 거기 있어서 둘을 한곳에서 관리하는 사람도 있다.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except Exception:
        pass
    tok = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    cid = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not (tok and cid):
        p = ROOT / "config" / "secrets.json"
        if p.exists():
            try:
                s = json.loads(p.read_text(encoding="utf-8"))
                tok = tok or (s.get("telegram_bot_token") or "").strip()
                cid = cid or (s.get("telegram_chat_id") or "").strip()
            except Exception:
                pass
    return tok, cid


def mask(text: str, token: str = "") -> str:
    """토큰이 섞여 나갈 수 있는 문자열을 가린다.

    토큰 전체뿐 아니라 `숫자:영숫자` 꼴도 지운다. 예외 메시지가 토큰을 잘라
    담는 경우가 있어 전체 일치만 보면 샌다.
    """
    import re
    out = str(text)
    if token:
        out = out.replace(token, "<토큰>")
        head = token.split(":")[0]
        if head and head.isdigit():
            out = out.replace(head, "<봇ID>")
    # 앞에 \b 를 두면 안 된다. 토큰이 가장 흔히 새는 자리가 URL 의
    # ".../bot<토큰>/..." 인데, 't' 와 숫자 사이에는 경계가 없어 그냥 지나친다.
    return re.sub(r"\d{6,}:[A-Za-z0-9_\-]{20,}", "<토큰>", out)


def _post(method: str, token: str, *, data: dict,
          files: dict | None = None) -> dict:
    """Bot API 호출. 실패해도 예외를 밖으로 던지지 않는다."""
    import requests
    url = f"{API}/bot{token}/{method}"
    try:
        r = requests.post(url, data=data, files=files, timeout=TIMEOUT)
        try:
            body = r.json()
        except ValueError:
            return {"ok": False, "error": f"HTTP {r.status_code} (JSON 아님)"}
        if not body.get("ok"):
            return {"ok": False, "code": body.get("error_code"),
                    "error": body.get("description", "사유 미상")}
        return body
    except Exception as e:
        return {"ok": False, "error": mask(f"{type(e).__name__}: {e}", token)}


def explain(res: dict) -> str:
    """실패 사유를 사람이 고칠 수 있는 말로 바꾼다.

    텔레그램이 주는 원문("chat not found")만 보면 뭘 해야 할지 모른다.
    실제로 막히는 지점은 거의 둘뿐이라 그 둘을 짚어 준다.
    """
    code, err = res.get("code"), str(res.get("error", ""))
    low = err.lower()
    if code == 401 or "unauthorized" in low:
        return ("봇 토큰이 틀렸다. @BotFather 의 토큰을 "
                "TELEGRAM_BOT_TOKEN 에 그대로(공백·따옴표 없이) 넣었는지 확인")
    if "chat not found" in low or "chat_id is empty" in low:
        return ("chat_id 를 못 찾는다. ① 텔레그램에서 그 봇에게 먼저 "
                "/start 를 보내고 ② getUpdates 의 chat.id 를 다시 확인")
    if "bot was blocked" in low:
        return "사용자가 봇을 차단했다. 봇 대화방에서 차단 해제"
    if "file is too big" in low or "request entity too large" in low:
        return f"파일이 {MAX_UPLOAD_MB}MB 상한을 넘었다"
    return err


def discover(token: str = "") -> dict[int, str]:
    """봇에게 말을 건 대화의 chat_id 를 찾는다.

    사람이 브라우저로 getUpdates 를 열어 JSON 에서 숫자를 집어내는 단계가
    가장 자주 막힌다. 여기서 대신 읽어 준다.

    주의: 텔레그램은 getUpdates 를 24시간만 보관한다. 너무 늦게 부르면
    말을 걸었어도 비어 있다 — 그때는 다시 한 줄 보내면 된다.
    """
    token = token or creds()[0]
    if not token:
        return {}
    res = _post("getUpdates", token, data={"limit": 100})
    if not res.get("ok"):
        print(f"  [텔레그램] getUpdates 실패 — {explain(res)}")
        return {}
    found: dict[int, str] = {}
    for up in res.get("result") or []:
        for key in ("message", "edited_message", "channel_post",
                    "my_chat_member"):
            chat = (up.get(key) or {}).get("chat") or {}
            if chat.get("id") is not None:
                who = (chat.get("username") or chat.get("title")
                       or chat.get("first_name") or "?")
                found[chat["id"]] = f'{chat.get("type", "?")} · {who}'
    return found


def me(token: str = "", *, quiet: bool = False) -> dict:
    """토큰이 살아 있는지 확인하고 봇 정보를 돌려준다."""
    token = token or creds()[0]
    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN 미설정"}
    res = _post("getMe", token, data={})
    if not res.get("ok") and not quiet:
        print(f"  [텔레그램] getMe 실패 — {explain(res)}")
    return res


def send(text: str, *, quiet: bool = False) -> bool:
    """문구 전송. 설정이 없으면 건너뛰고 False."""
    tok, cid = creds()
    if not (tok and cid):
        if not quiet:
            print("  [텔레그램] 미설정 — 알림 건너뜀 "
                  "(.env 의 TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID)")
        return False
    body = text if len(text) <= MAX_TEXT else text[:MAX_TEXT - 1] + "…"
    res = _post("sendMessage", tok,
                data={"chat_id": cid, "text": body,
                      "disable_web_page_preview": "true"})
    if not res.get("ok"):
        print(f"  [텔레그램] 전송 실패 — {explain(res)}")
        return False
    if not quiet:
        print("  [텔레그램] 전송 완료")
    return True


def send_file(path, caption: str = "", *, quiet: bool = False) -> bool:
    """파일 전송. 원본 보존을 위해 sendDocument 를 쓴다."""
    tok, cid = creds()
    if not (tok and cid):
        if not quiet:
            print("  [텔레그램] 미설정 — 전송 건너뜀")
        return False
    p = Path(path)
    if not p.exists():
        print(f"  [텔레그램] 파일 없음: {p}")
        return False
    mb = p.stat().st_size / 1024 / 1024
    if mb > MAX_UPLOAD_MB:
        print(f"  [텔레그램] {p.name} 가 {mb:.1f}MB — "
              f"봇 전송 상한 {MAX_UPLOAD_MB}MB 초과")
        return False
    data = {"chat_id": cid}
    if caption:
        data["caption"] = caption[:1024]
    with p.open("rb") as fh:
        res = _post("sendDocument", tok, data=data,
                    files={"document": (p.name, fh)})
    if not res.get("ok"):
        print(f"  [텔레그램] 전송 실패 — {explain(res)}")
        return False
    if not quiet:
        print(f"  [텔레그램] {p.name} ({mb:.1f}MB) 전송 완료")
    return True


def alert(title: str, lines: list[str] | None = None) -> bool:
    """실패 알림 (T24). 제목 한 줄 + 세부 몇 줄."""
    nl = chr(10)
    body = f"[실패] {title}"
    if lines:
        body += nl + nl.join(f"· {s}" for s in lines)
    return send(body)


def main() -> int:
    ap = argparse.ArgumentParser(description="텔레그램 전송")
    ap.add_argument("--test", action="store_true", help="연결 점검 후 시험 발송")
    ap.add_argument("--chat-id", action="store_true",
                    help="봇에게 말을 건 대화의 chat_id 찾기")
    ap.add_argument("--send", metavar="문구")
    ap.add_argument("--file", metavar="경로")
    ap.add_argument("--caption", default="")
    a = ap.parse_args()

    if a.chat_id:
        tok = creds()[0]
        if not tok:
            print("TELEGRAM_BOT_TOKEN 이 먼저 필요하다")
            return 1
        info = me(tok)
        if info.get("ok"):
            print(f"봇 @{info['result'].get('username')}")
        got = discover(tok)
        if not got:
            print("\n대화 기록이 없다. 텔레그램에서 위 봇을 찾아")
            print("아무 메시지나(또는 /start) 한 줄 보낸 뒤 다시 실행.")
            return 1
        print("\n찾은 chat_id:")
        for cid, who in got.items():
            print(f"  {cid}   ({who})")
        print("\n.env 에 넣기:")
        print(f"  TELEGRAM_CHAT_ID={next(iter(got))}")
        return 0

    if a.test:
        from datetime import datetime
        tok, cid = creds()
        print("텔레그램 연결 점검")
        print(f"  토큰    {'설정됨' if tok else '없음'}"
              f"{f' (봇ID {tok.split(chr(58))[0]})' if ':' in tok else ''}")
        print(f"  chat_id {'설정됨' if cid else '없음'}")
        if not (tok and cid):
            print("\n  .env 에 아래 두 줄이 필요하다:")
            print("    TELEGRAM_BOT_TOKEN=...")
            print("    TELEGRAM_CHAT_ID=...")
            return 1
        info = me(tok)
        if not info.get("ok"):
            return 1
        u = info["result"].get("username", "?")
        print(f"  봇      @{u} 확인")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        ok = send(f"proptech_ds 알림 연결 확인 ({now}){chr(10)}"
                  f"이 메시지가 보이면 설정 완료.")
        if ok:
            print("\n  폰에서 메시지를 확인하면 끝.")
        return 0 if ok else 1

    if a.send:
        return 0 if send(a.send) else 1
    if a.file:
        return 0 if send_file(a.file, a.caption) else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
