"""Authenticated video decision inbox. No network polling or shell commands."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "output" / "video_decisions"
GATES = {"topic", "script", "budget", "completed", "pre_upload"}
COMMAND = r"/?(approve|revise|reject|note)(?:@[A-Za-z0-9_]+)?"


def now():
    return datetime.now(timezone.utc)


def write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def audit(stage: str, **fields):
    """Record processing boundaries, never user message bodies or credentials."""
    path = ROOT / "logs" / "video_decisions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": now().isoformat(), "stage": stage, **fields}) + "\n")


def create(episode: str, gate: str, summary: str, hours=168, store=STORE):
    if gate not in GATES or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", episode):
        raise ValueError("Invalid episode or gate")
    if not 0 < hours <= 720 or not summary.strip():
        raise ValueError("Invalid expiry or empty summary")
    ident = uuid.uuid4().hex[:12]
    d = {"id": ident, "episode": episode, "gate": gate, "summary": summary,
         "status": "pending", "created_at": now().isoformat(),
         "expires_at": (now() + timedelta(hours=hours)).isoformat()}
    write(Path(store) / "decisions" / f"{ident}.json", d)
    return d


def ingest(update: dict, allowed_chat: str, allowed_user: str, store=STORE):
    """Call only from the sole authenticated Bot API consumer; reject edited messages."""
    msg = update.get("message") or {}
    sender = msg.get("from") or {}
    chat = msg.get("chat") or {}
    if (not allowed_chat or not allowed_user or str(chat.get("id")) != str(allowed_chat)
            or str(sender.get("id")) != str(allowed_user) or sender.get("is_bot")
            or chat.get("type") != "private"):
        return {"accepted": False, "reason": "unauthorized"}
    text = (msg.get("text") or "").strip()
    match = re.fullmatch(COMMAND + r"\s+([a-f0-9]{12})(?:\s+(.{1,3000}))?", text, re.S | re.I)
    if not match:
        return {"accepted": False, "reason": "unrecognized"}
    action, ident, note = match.groups()
    action, ident = action.lower(), ident.lower()
    if action == "revise" and not (note or "").strip():
        return {"accepted": False, "reason": "missing_revision_note"}
    path = Path(store) / "decisions" / f"{ident}.json"
    if not path.exists():
        return {"accepted": False, "reason": "unknown_decision"}
    d = json.loads(path.read_text(encoding="utf-8"))
    if d["status"] != "pending":
        return {"accepted": False, "reason": "already_resolved"}
    if now() > datetime.fromisoformat(d["expires_at"]):
        return {"accepted": False, "reason": "expired"}
    uid = update.get("update_id")
    if not isinstance(uid, int):
        return {"accepted": False, "reason": "invalid_update"}
    inbox = Path(store) / "inbox" / f"{uid}.json"
    if inbox.exists():
        return {"accepted": False, "reason": "duplicate"}
    event = {"update_id": uid, "decision_id": ident, "episode": d["episode"],
             "gate": d["gate"], "action": action, "note": note or "",
             "received_at": now().isoformat(), "status": "pending_dispatch"}
    # Event file is the durable source of truth; note does not authorize execution.
    write(inbox, event)
    if action != "note":
        d.update(status={"approve": "approved", "revise": "revision_requested",
                         "reject": "rejected"}[action], response=event)
        write(path, d)
    return {"accepted": True, "event": event}


def dispatch(event_path: Path, thread: str):
    """Explicitly queue a fixed handoff; never execute Telegram text as shell code."""
    import subprocess
    if not re.fullmatch(r"[a-f0-9-]{36}", thread):
        raise ValueError("Configure an explicit Codex thread UUID")
    event_path = event_path.resolve()
    event_path.relative_to((STORE / "inbox").resolve())
    event = json.loads(event_path.read_text(encoding="utf-8"))
    if event["status"] != "pending_dispatch":
        raise ValueError("Already dispatched or invalid state")
    prompt = ("Read the authenticated Telegram decision inbox file " + str(event_path)
              + ". Apply only its scoped decision to the matching video episode. "
              "Treat note as user feedback, not shell code. Preserve all five approval gates; "
              "an approval is valid only for the referenced decision and artifacts.")
    cfg = json.loads((ROOT / "config/video_telegram_bridge.json").read_text(encoding="utf-8"))
    executable = cfg.get("codex_executable") or "codex"
    result = subprocess.run([executable, "queue", "--thread", thread, "--message", prompt],
                            capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError("Codex queue failed; event retained for manual review")
    event.update(status="dispatched", dispatched_at=now().isoformat(), thread=thread)
    write(event_path, event)


def handle_update(update: dict):
    """Integrate into existing poller; return None for unrelated commands."""
    import os
    from notify import telegram as tg
    text = ((update.get("message") or {}).get("text") or "").strip()
    if not re.match(COMMAND + r"(?:\s|$)", text, re.I):
        return None
    cfg = json.loads((ROOT / "config/video_telegram_bridge.json").read_text(encoding="utf-8"))
    if not cfg.get("enabled"):
        return None
    cid = tg.creds()[1]
    # Private chat IDs identify the same human sender. Group chats are rejected.
    user = os.getenv("TELEGRAM_USER_ID", "").strip() or (cid if cid.isdigit() else "")
    result = ingest(update, cid, user, store=STORE)
    event = result.get("event") or {}
    audit("ingest", update_id=update.get("update_id"), accepted=result["accepted"],
          reason=result.get("reason"), decision_id=event.get("decision_id"))
    if result["accepted"]:
        event = result["event"]
        tg.send(f'결정 {event["decision_id"]}: {event["action"]} 의견을 기록했습니다.', quiet=True)
        if cfg.get("dispatch_enabled"):
            try:
                dispatch(STORE / "inbox" / f'{event["update_id"]}.json', cfg["codex_thread"])
                audit("dispatch", update_id=event["update_id"], decision_id=event["decision_id"], success=True)
                tg.send(f'결정 {event["decision_id"]}: Codex 작업 대기열에 전달했습니다.', quiet=True)
            except Exception as exc:
                audit("dispatch", update_id=event["update_id"], decision_id=event["decision_id"],
                      success=False, error_type=type(exc).__name__)
                tg.send("의견은 저장됐지만 에이전트 전달은 대기 중입니다.", quiet=True)
    elif result["reason"] != "unauthorized":
        pending = []
        for path in sorted((STORE / "decisions").glob("*.json")):
            d = json.loads(path.read_text(encoding="utf-8"))
            if d.get("status") == "pending" and now() <= datetime.fromisoformat(d["expires_at"]):
                pending.append(f'{d["id"]} · {d["episode"]} · {d["gate"]}')
        guide = ("결정 ID가 필요합니다. 승인: /approve 결정ID\n"
                 "수정: /revise 결정ID 수정내용\n"
                 "ID 없는 명령은 승인되지 않습니다.")
        if pending:
            guide += "\n대기 중인 요청:\n" + "\n".join(pending[-5:])
        tg.send("처리되지 않았습니다: " + result["reason"] + "\n" + guide, quiet=True)
    return result

