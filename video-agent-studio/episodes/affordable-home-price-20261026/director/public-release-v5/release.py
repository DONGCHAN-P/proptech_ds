"""Publish the two exact corrected Shorts; retain public main; retire old privates."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, sys, time, warnings
warnings.filterwarnings("ignore", category=FutureWarning)

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
from upload_changneung_scheduled_v8 import service, CHANNEL

MAIN = "0495J7FMmCk"
OLD_PRIVATE = ["PwqvBlxAoII", "Y9lZk9PmNUA", "szSvG_2IehY"]
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.now(timezone.utc).isoformat()
rel = lambda p: p.relative_to(ROOT).as_posix()

def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def prepare():
    main = EP / "outputs/jun-quality-v2/main/affordable_home_price_jun_quality_v3.mp4"
    assert sha(main) == "e0a84d5a5893193c7b50431c0c5b60adb279a7817bd4e970b0e04bfe32dcb561"
    assert read(EP / "qa/shorts-ending-fix-v1/findings.json")["verdict"]["open_required"] == 0
    checked = read(EP / "qa/shorts-ending-fix-v1/findings.json")["checked_media"]
    completion = read(EP / "outputs/jun-quality-v2/shorts/v5-ending-fix/completion.json")
    meta = read(EP / "outputs/jun-quality-v2/release/shorts_metadata.json")["shorts"]
    items = []
    for item in completion["items"]:
        path = ROOT / item["video"]
        assert sha(path) == item["sha256"]
        assert any(c["sha256"] == item["sha256"] for c in checked)
        m = next(m for m in meta if m["id"] == item["id"])
        description = m["description"] + "\n\n본편: https://youtu.be/" + MAIN
        assert len(m["title"]) <= 100 and len(description.encode("utf-8")) <= 5000
        items.append({"id": item["id"], "video": rel(path), "sha256": item["sha256"], "subtitles": rel(path.with_suffix(".srt")), "subtitles_sha256": sha(path.with_suffix(".srt")), "title": m["title"], "description": description, "privacy": "public", "notify_subscribers": False})
    auth = {"decision_id": "PUBLIC-REPLACE-20261028-V5", "user_instructions": ["기존에 비공개로 올렸던 영상들 삭제하고 지금 작업한 내용으로 업로드해줘", "공개로 바로 올려줘"], "channel_id": CHANNEL, "reuse_already_public_main": MAIN, "upload": items, "delete_only_if_still_private": OLD_PRIVATE, "scope": "This episode only", "new_paid_generation": False, "actual_listening": False, "continuous_playback": False, "claude_final_approval_claimed": False, "created_at": now()}
    save(HERE / "authorization.json", auth)
    save(HERE / "release_plan.json", {"main_video_id": MAIN, "main_sha256": sha(main), "shorts": items, "old_private_ids": OLD_PRIVATE, "private_staging_then_immediate_public_on_processing_and_caption_verification": True})
    print(json.dumps({"preflight": "passed", "reuse_public_main": MAIN, "corrected_shorts": len(items), "old_private_candidates": OLD_PRIVATE}), flush=True)

def get_videos(y, ids):
    return y.videos().list(part="snippet,status,contentDetails,processingDetails", id=",".join(ids)).execute(num_retries=0).get("items", [])

def verify_owned(v):
    assert v["snippet"]["channelId"] == CHANNEL
    assert not v["status"].get("publishAt")
    assert v["status"].get("uploadStatus") not in ("failed", "rejected", "deleted")

def caption(y, item, record, rp):
    from googleapiclient.http import MediaFileUpload
    deadline = time.monotonic() + 90
    while True:
        try:
            tracks = y.captions().list(part="snippet", videoId=record["video_id"]).execute(num_retries=0).get("items", [])
            break
        except Exception as exc:
            try: transient = json.loads(exc.content)["error"]["errors"][0]["reason"] == "videoNotFound"
            except Exception: transient = False
            if not transient or time.monotonic() >= deadline: raise
            # Read-only propagation check; never repeat an insert or upload.
            time.sleep(3)
    expected = [c for c in tracks if c["snippet"].get("language") == "ko" and c["snippet"].get("name") == "한국어"]
    assert len(expected) <= 1
    if expected:
        result = expected[0]
    else:
        assert not record.get("caption_insert_started"), "Uncertain caption insertion: verify rather than repeat"
        record["caption_insert_started"] = True
        save(rp, record)
        result = y.captions().insert(part="snippet", body={"snippet": {"videoId": record["video_id"], "language": "ko", "name": "한국어", "isDraft": False}}, media_body=MediaFileUpload(str(ROOT / item["subtitles"]), mimetype="application/octet-stream")).execute(num_retries=0)
    record.update(caption_id=result["id"], caption_status=result["snippet"].get("status"))
    save(rp, record)

def upload(y, item):
    from googleapiclient.http import MediaFileUpload
    rp = HERE / (item["id"] + "_receipt.json")
    video = ROOT / item["video"]
    assert sha(video) == item["sha256"] and sha(ROOT / item["subtitles"]) == item["subtitles_sha256"]
    if rp.exists():
        record = read(rp)
        assert record.get("video_id") and record["sha256"] == item["sha256"], "Prior upload outcome uncertain; no duplicate insertion"
    else:
        record = {"phase": "upload_started", "sha256": item["sha256"], "created_at": now(), "privacy_requested": "public"}
        save(rp, record)
        body = {"snippet": {"title": item["title"], "description": item["description"], "tags": ["내집마련", "집값예산", "Shorts"], "categoryId": "27", "defaultLanguage": "ko", "defaultAudioLanguage": "ko"}, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
        request = y.videos().insert(part="snippet,status", body=body, notifySubscribers=False, media_body=MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8*1024*1024, resumable=True))
        response = None
        while response is None:
            _, response = request.next_chunk(num_retries=0)
        record.update(phase="uploaded_staging", video_id=response["id"], url="https://youtube.com/shorts/" + response["id"])
        save(rp, record)
        print(json.dumps({"id": item["id"], "uploaded": record["video_id"]}), flush=True)
    caption(y, item, record, rp)
    return record

def ready(y, items):
    deadline = time.monotonic() + 1200
    while time.monotonic() < deadline:
        complete = True
        for item in items:
            rp = HERE / (item["id"] + "_receipt.json")
            record = read(rp)
            v = get_videos(y, [record["video_id"]])[0]
            verify_owned(v)
            assert v["snippet"]["title"] == item["title"] and v["snippet"]["description"] == item["description"]
            processing = v.get("processingDetails", {}).get("processingStatus")
            assert processing not in ("failed", "terminated")
            tracks = y.captions().list(part="snippet", videoId=record["video_id"]).execute(num_retries=0).get("items", [])
            c = next((c for c in tracks if c["id"] == record["caption_id"]), None)
            assert c is not None and c["snippet"].get("status") != "failed"
            record.update(processing=processing, caption_status=c["snippet"].get("status"), verification=v)
            record["ready_to_publish"] = processing == "succeeded" and record["caption_status"] == "serving"
            save(rp, record)
            complete = complete and record["ready_to_publish"]
        if complete: return
        time.sleep(5)
    raise TimeoutError("Processing or captions not ready; preserve previous videos")

def run():
    plan = read(HERE / "release_plan.json")
    auth = read(HERE / "authorization.json")
    assert auth["channel_id"] == CHANNEL and auth["delete_only_if_still_private"] == OLD_PRIVATE
    y = service()
    main = get_videos(y, [MAIN])[0]
    verify_owned(main)
    assert main["status"]["privacyStatus"] == "public"
    save(HERE / "main_verification.json", main)
    old = get_videos(y, OLD_PRIVATE)
    for v in old:
        verify_owned(v)
        assert v["status"]["privacyStatus"] == "private", "Old candidate changed visibility; do not delete"
    save(HERE / "old_private_before_delete.json", old)
    for item in plan["shorts"]: upload(y, item)
    ready(y, plan["shorts"])
    for item in plan["shorts"]:
        rp = HERE / (item["id"] + "_receipt.json")
        r = read(rp)
        v = get_videos(y, [r["video_id"]])[0]
        verify_owned(v)
        if v["status"]["privacyStatus"] != "public" or not v["status"].get("embeddable") or not v["status"].get("publicStatsViewable"):
            assert v["status"]["privacyStatus"] in ("private", "public")
            r["public_update_started"] = True
            save(rp, r)
            result = y.videos().update(part="status", body={"id": r["video_id"], "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True, "license": "youtube", "embeddable": True, "publicStatsViewable": True}}).execute(num_retries=0)
            r["public_update_response"] = result
            save(rp, r)
        deadline = time.monotonic() + 60
        while True:
            v = get_videos(y, [r["video_id"]])[0]
            verify_owned(v)
            if v["status"]["privacyStatus"] == "public" and v["status"].get("embeddable") and v["status"].get("publicStatsViewable"): break
            assert time.monotonic() < deadline, "Public status propagation not confirmed; no repeat mutation"
            time.sleep(2)
        r.update(phase="public_verified", public_verified=True, verification=v, verified_at=now())
        save(rp, r)
        print(json.dumps({"id": item["id"], "public_url": r["url"]}), flush=True)
    active = get_videos(y, [MAIN] + [read(HERE / (p["id"] + "_receipt.json"))["video_id"] for p in plan["shorts"]])
    assert len(active) == 3 and all(v["status"]["privacyStatus"] == "public" for v in active)
    save(HERE / "three_public_verification.json", active)
    main_tracks = y.captions().list(part="snippet", videoId=MAIN).execute(num_retries=0).get("items", [])
    save(HERE / "main_captions.json", main_tracks)
    assert any(c["snippet"].get("language") == "ko" and c["snippet"].get("status") == "serving" for c in main_tracks)
    for old_id in OLD_PRIVATE:
        dp = HERE / (old_id + "_delete_receipt.json")
        current = get_videos(y, [old_id])
        if not current:
            if not dp.exists(): save(dp, {"video_id": old_id, "phase": "already_absent", "verified_at": now()})
            continue
        v = current[0]
        verify_owned(v)
        assert v["status"]["privacyStatus"] == "private" and old_id not in [x["id"] for x in active]
        save(dp, {"video_id": old_id, "phase": "delete_started", "old_metadata": v, "authorization": rel(HERE / "authorization.json"), "started_at": now()})
        y.videos().delete(id=old_id).execute(num_retries=0)
        save(dp, {"video_id": old_id, "phase": "delete_response_received", "old_metadata": v, "at": now()})
        deadline = time.monotonic() + 60
        while get_videos(y, [old_id]):
            assert time.monotonic() < deadline, "Deletion propagation not confirmed; do not repeat deletion"
            time.sleep(2)
        save(dp, {"video_id": old_id, "phase": "deleted_verified", "old_metadata": v, "verified_at": now(), "local_sources_preserved": True})
        print(json.dumps({"deleted_old_private": old_id}), flush=True)
    save(HERE / "completion.json", {"status": "public_verified_old_privates_removed", "main": "https://youtu.be/" + MAIN, "main_reused_already_public": True, "shorts": [read(HERE / (p["id"] + "_receipt.json")) for p in plan["shorts"]], "old_private_ids_removed": OLD_PRIVATE, "verified_at": now(), "new_paid_calls": 0, "actual_listening": False, "continuous_playback": False, "claude_final_approval_claimed": False})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "run"])
    args = parser.parse_args()
    try:
        prepare() if args.action == "prepare" else run()
    except Exception as exc:
        reason = None
        try: reason = json.loads(exc.content)["error"]["errors"][0]["reason"]
        except Exception: pass
        save(HERE / "error.json", {"type": type(exc).__name__, "api_reason": reason, "at": now()})
        print(json.dumps({"status": "needs_attention", "error_type": type(exc).__name__, "api_reason": reason}), flush=True)
        raise SystemExit(2)
