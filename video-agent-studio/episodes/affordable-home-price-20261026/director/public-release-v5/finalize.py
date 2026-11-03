from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
def save(p, d): p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

release = read(HERE / "completion.json")
assert release["status"] == "public_verified_old_privates_removed"
live = read(HERE / "three_public_verification.json")
assert len(live) == 3 and all(v["status"]["privacyStatus"] == "public" and v["snippet"]["channelId"] == "UCr_mTC0x_Uobv6MrIsOkrXw" for v in live)
assert all(v["contentDetails"]["definition"] == "hd" for v in live)
for old_id in release["old_private_ids_removed"]:
    assert read(HERE / (old_id + "_delete_receipt.json"))["phase"] in ("deleted_verified", "already_absent")
items = []
main_id = "0495J7FMmCk"
main_video = EP / "outputs/jun-quality-v2/main/affordable_home_price_jun_quality_v3.mp4"
assert sha(main_video) == "e0a84d5a5893193c7b50431c0c5b60adb279a7817bd4e970b0e04bfe32dcb561"
main = next(v for v in live if v["id"] == main_id)
items.append({"id": "main", "video_id": main_id, "url": "https://youtu.be/" + main_id, "title": main["snippet"]["title"], "sha256": sha(main_video), "privacy": "public", "processing": "succeeded", "caption": "Korean serving", "existing_public_video_reused": True})
for name in ("promo", "summary"):
    r = read(HERE / (name + "_receipt.json"))
    assert r["public_verified"] and r["processing"] == "succeeded" and r["caption_status"] == "serving"
    job = next(x for x in read(HERE / "release_plan.json")["shorts"] if x["id"] == name)
    assert sha(ROOT / job["video"]) == r["sha256"]
    items.append({"id": name, "video_id": r["video_id"], "url": r["url"], "title": job["title"], "sha256": r["sha256"], "video": job["video"], "subtitles": job["subtitles"], "privacy": "public", "processing": "succeeded", "caption": "Korean serving"})
stamp = datetime.now(timezone.utc).isoformat()
release.update(items=items, finalized_at=stamp, verification_method="YouTube Data API: channel, status, processing, HD, serving captions, deletion absence", shorts_related_video_link="Main URL included in descriptions; native related-video control not set", local_originals_preserved=True, additional_cash_krw=0)
save(HERE / "completion.json", release)
summary = "# 공개 게시 완료\n\n" + "\n".join("- " + x["title"] + " — " + x["url"] for x in items)
summary += "\n\n본편은 이미 공개된 승인 파일을 유지했습니다. 끝부분을 수정한 쇼츠 v5 두 편을 새로 공개했고, 세 편의 고화질 처리·한국어 자막 제공 상태를 API로 확인했습니다. 기존 비공개 쇼츠 두 편과 예전 본편 비공개본, 총 세 개의 삭제 및 조회 결과 부재를 확인했습니다. 로컬 원본·이전 검수 자료는 보존했습니다.\n\n검수 범위는 기존 화면·전사·파형·기술/독립 QA 및 원격 상태 조회입니다. 실제 청취·연속 재생과 Claude 최종 검수는 미확인으로 유지합니다. 추가 유료 생성·충전은 없습니다. 쇼츠 설명에는 공개 본편 링크를 넣었습니다. YouTube의 전용 ‘관련 동영상’ 설정은 적용하지 않았습니다.\n"
(HERE / "공개_업로드.md").write_text(summary, encoding="utf-8")

state = read(EP / "state.json")
state.setdefault("historical_private_uploads", state.get("private_uploads", []))
state.update(stage="public_verified", publication_status="public", public_release_authorized=True, public_upload_url=items[0]["url"], private_upload_url=None, public_uploads=items, updated_at=stamp)
state["active_work"].update(stage="public_verified", public_upload_url=items[0]["url"], private_upload_url=None, shorts_published_revision="v5-ending-fix", public_uploads=items)
state["blocked_tasks"] = [x for x in state.get("blocked_tasks", []) if x["task"] != "Upload corrected Shorts"]
state["shorts_ending_fix"].update(status="public_uploaded_verified", new_uploads_performed=2, published_revision="v5-ending-fix", public_urls=[x["url"] for x in items[1:]])
state["old_private_uploads_removed"] = release["old_private_ids_removed"]
save(EP / "state.json", state)
decisions = read(EP / "decisions.json")
decisions["decisions"] = [d for d in decisions["decisions"] if d.get("id") != "PUBLIC-REPLACE-20261028-V5"]
decisions["decisions"].append({"id": "PUBLIC-REPLACE-20261028-V5", "status": "executed_verified", "authorization": rel(HERE / "authorization.json"), "report": rel(HERE / "completion.json"), "public_ids": [x["video_id"] for x in items], "removed_old_private_ids": release["old_private_ids_removed"], "at_utc": stamp})
save(EP / "decisions.json", decisions)

rel_dir = EP / "outputs/jun-quality-v2/release"
manifest = read(rel_dir / "upload_manifest.json")
manifest.setdefault("previous_private_upload_items", manifest.get("uploaded_items", []))
manifest.update(status="public_verified", privacy="public", uploaded_items=items, pending_shorts_updates=[], published_shorts_revision="v5-ending-fix", public_release_report=rel(HERE / "completion.json"), old_private_ids_removed=release["old_private_ids_removed"])
save(rel_dir / "upload_manifest.json", manifest)
(rel_dir / "upload_status.md").write_text(summary, encoding="utf-8")
meta = read(rel_dir / "main_metadata.json")
if not (HERE / "main_metadata.before.json").exists(): save(HERE / "main_metadata.before.json", meta)
meta.update(privacy="public", uploaded=True, youtube_url=items[0]["url"], verification=rel(HERE / "main_verification.json"))
save(rel_dir / "main_metadata.json", meta)
external_path = EP / "director/jun-quality-v2/external_status.json"
external = read(external_path)
external["youtube"].update(existing_API_probe="reauthenticated_same_existing_scopes_same_channel", error_code=None, error_description=None, requested_visibility="public", browser_fallback="not_used_for_this_release", public_release_authorized=True, public_verified_items=items, old_private_ids_removed=release["old_private_ids_removed"], existing_uploads_deleted=True, next_step="Published", verified_at=stamp)
external["youtube"]["shorts_correction"] = {"published_revision": "v5-ending-fix", "new_uploads_performed": 2, "blockers": [], "report": rel(HERE / "completion.json")}
save(external_path, external)

short_dir = EP / "outputs/jun-quality-v2/shorts/v5-ending-fix"
short_report = read(short_dir / "completion.json")
short_report.update(status="public_uploaded_verified", new_uploads_performed=2, published_shorts_revision="v5-ending-fix", published_urls=[x["url"] for x in items[1:]], upload_blockers=[], existing_uploads_deleted=True, public_release_performed=True, release_report=rel(HERE / "completion.json"))
save(short_dir / "completion.json", short_report)
save(EP / "outputs/jun-quality-v2/shorts/current_shorts.json", {"local_revision": "v5-ending-fix", "published_revision": "v5-ending-fix", "upload_pending": False, "public_urls": [x["url"] for x in items[1:]], "report": rel(HERE / "completion.json")})
publishing = read(short_dir / "publishing_metadata.json")
publishing.update(requested_visibility="public", uploaded=True, public_urls=[x["url"] for x in items[1:]])
for m in publishing["shorts"]:
    x = next(x for x in items if x["id"] == m["id"])
    m.update(video=Path(x["video"]).name, srt=Path(x["subtitles"]).name, youtube_url=x["url"], privacy="public")
save(short_dir / "publishing_metadata.json", publishing)
review = short_dir / "잘림수정_검수.md"
text = review.read_text(encoding="utf-8").split("업로드 상태")[0]
review.write_text(text + "업로드 상태\n수정 쇼츠 v5 두 편의 공개와 한국어 자막 제공 상태를 확인했습니다. 기존 비공개본 세 개를 삭제했습니다.\n\n" + summary, encoding="utf-8")
main_report_path = EP / "outputs/jun-quality-v2/main/completion.json"
main_report = read(main_report_path)
main_report.update(status="public_verified", public_uploads=items, release_report=rel(HERE / "completion.json"))
save(main_report_path, main_report)
review_path = EP / "outputs/jun-quality-v2/main/검토안내.md"
review_path.write_text(summary + "\n\n---\n\n이하 이전 제작·검수 기록\n\n" + review_path.read_text(encoding="utf-8"), encoding="utf-8")

shelf_path = ROOT / "config/video_shelf.json"
shelf = read(shelf_path)
entry = next(e for e in shelf["entries"] if e["workspace"].endswith("affordable-home-price-20261026"))
entry.update(status="본편·종료 수정 쇼츠 v5 두 편 공개 / 한국어 자막·고화질 확인 / 이전 비공개본 세 개 삭제", youtube_url=items[0]["url"], youtube_visibility="public", shorts_youtube_urls=[x["url"] for x in items[1:]], shorts_youtube_revision="v5-ending-fix")
entry["files"]["공개_업로드.md"] = rel(HERE / "공개_업로드.md")
save(shelf_path, shelf)
current_path = ROOT / "config/current_video.json"
current = read(current_path)
if not (HERE / "current_video.before.json").exists(): save(HERE / "current_video.before.json", current)
save(current_path, {"version": "affordable-jun-quality-v3-shorts-v5", "episode": EP.name, "video": rel(main_video), "subtitles": rel(main_video.parent / "subtitles.srt"), "script": rel(main_video.parent / "script_user_original.md"), "voice": "ElevenLabs Jun", "duration_seconds": 714.8, "youtube_url": items[0]["url"], "publication_status": "public", "previous_video_url": current["youtube_url"], "report": rel(HERE / "completion.json"), "sha256": sha(main_video), "shorts": items[1:], "updated_at": stamp})
print(json.dumps({"status": "public_verified", "items": [{"id": x["id"], "url": x["url"]} for x in items], "old_private_deleted": len(release["old_private_ids_removed"])}))
