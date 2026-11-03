"""Offline security and approval semantics checks."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from notify.video_decisions import create, ingest

with tempfile.TemporaryDirectory() as tmp:
    store = Path(tmp)
    d = create("next-video", "budget", "USD 2 ceiling", store=store)
    def update(uid, text, user=123):
        return {"update_id": uid, "message": {"from": {"id": user},
                "chat": {"id": 123, "type": "private"}, "text": text}}
    assert not ingest(update(1, f'/approve {d["id"]}', 999), "123", "123", store)["accepted"]
    assert not ingest(update(2, "run rm -rf"), "123", "123", store)["accepted"]
    assert ingest(update(3, f'/note {d["id"]} 목소리 유지'), "123", "123", store)["accepted"]
    assert not ingest(update(3, f'/note {d["id"]} duplicate'), "123", "123", store)["accepted"]
    assert ingest(update(4, f'/approve {d["id"]}'), "123", "123", store)["accepted"]
    assert not ingest(update(5, f'/reject {d["id"]}'), "123", "123", store)["accepted"]
    assert not ingest({"update_id": 6, "edited_message": update(1, "x")["message"]}, "123", "123", store)["accepted"]
print("PASS: authorization, command allowlist, notes, deduplication, scoped approval, edited-message rejection")
