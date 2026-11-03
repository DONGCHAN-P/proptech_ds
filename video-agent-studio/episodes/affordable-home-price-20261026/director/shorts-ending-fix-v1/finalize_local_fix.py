from datetime import datetime, timezone
from pathlib import Path
import hashlib, json

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
OUT = EP / "outputs/jun-quality-v2/shorts/v5-ending-fix"
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()

def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

technical = read(HERE / "v5_technical_report.json")
assert all(x["passed"] for x in read(HERE / "v5_cut_silence_check.json"))
assert not all(x["passed"] for x in read(HERE / "v4_cut_silence_check.json"))
assert all(x["full_decode"] and x["captions_unchanged"] and x["silent_tail_verified"] for x in technical["items"])
qa = read(EP / "qa/shorts-ending-fix-v1/handoff.json")
qa_findings = read(EP / "qa/shorts-ending-fix-v1/findings.json")
assert qa_findings["verdict"]["open_required"] == 0
assert qa_findings["verdict"]["open_critical"] == 0
assert qa["ready_for_local_delivery"] and qa["open_required"] == 0 and qa["open_critical"] == 0
stamp = datetime.now(timezone.utc).isoformat()
items = technical["items"]
for item in items:
    assert sha(ROOT / item["video"]) == item["sha256"]
    assert any(x["sha256"] == item["sha256"] for x in qa_findings["checked_media"])
assert sha(EP / "outputs/jun-quality-v2/main/affordable_home_price_jun_quality_v3.mp4") == "e0a84d5a5893193c7b50431c0c5b60adb279a7817bd4e970b0e04bfe32dcb561"
assert sha(EP / "outputs/jun-quality-v2/shorts/01_promo_jun_v4.mp4") == "215968608a3a6d5159f35195e65378de4d6b9f8ed63f19e5d00bc97059997953"
assert sha(EP / "outputs/jun-quality-v2/shorts/02_summary_jun_v4.mp4") == "cd72bb6c827b6695c2f24d6ed2474f7c6901943114443fe639c33168bcc703c9"
report = {
    "revision": "v5-ending-fix", "status": "local_corrected_private_upload_blocked",
    "created_at": stamp, "items": items, "new_uploads_performed": 0,
    "independent_qa": rel(EP / "qa/shorts-ending-fix-v1/handoff.json"),
    "cut_silence_regression": rel(HERE / "v5_cut_silence_check.json"),
    "full_local_ASR": rel(HERE / "v5_full_asr.json"),
    "actual_listening": False, "continuous_playback": False,
    "additional_paid_calls": 0, "additional_cash_krw": 0,
    "published_shorts_revision": "v4", "published_urls": ["https://youtube.com/shorts/PwqvBlxAoII", "https://youtube.com/shorts/Y9lZk9PmNUA"],
    "upload_blockers": ["CUA runtime could not start: missing path, same result after reset", "Existing YouTube API refresh requires reauthorization"],
    "existing_uploads_deleted": False, "public_release_performed": False,
}
save(OUT / "completion.json", report)
metadata = read(EP / "outputs/jun-quality-v2/release/shorts_metadata.json")
save(OUT / "publishing_metadata.json", {"requested_visibility": "private", "uploaded": False, "shorts": metadata["shorts"], "videos": [{"id": x["id"], "video": x["video"], "sha256": x["sha256"], "subtitles": str(Path(x["video"]).with_suffix(".srt"))} for x in items]})
text = """# 쇼츠 끝부분 잘림 수정본

현재 로컬 검토본은 v5입니다. 홍보 38.167초, 핵심 요약 51.467초입니다.

수정한 내용
- 홍보 쇼츠 약 35초, 요약 쇼츠 약 48초를 포함한 음성 편집 끝점 다섯 곳에서 다음 문장의 첫소리가 섞이는 현상을 제거했습니다.
- 원음의 문장 사이 무음에서 끝내고 기존 시간표의 남은 부분을 무음으로 채웠습니다. Jun 음성·재생 속도·대본·자막·러닝타임은 유지했습니다.
- 마지막 화면을 0.35초로 전환하고 기존 3초 마무리 구간을 유지했습니다.

확인 범위
- 기존본 회귀 검사 실패 → 수정본 5개 끝점 무음 검사 통과.
- 두 MP4 전체 디코드, 1080×1920·30fps, 자막 파일의 기존본과 동일한 SHA 확인.
- 전체 로컬 음성 전사에서 마지막 문장 완결 확인. 최종 파일의 전환·컷·끝 프레임 44장과 독립 QA의 별도 표본 확인.
- 실제 청취와 연속 재생은 미실시입니다. 전사·파형·표본 프레임 확인과 구분합니다.

업로드 상태
수정본은 아직 재업로드하지 못했습니다. 현재 브라우저 제어 도구가 실행 경로 오류로 시작되지 않으며 기존 YouTube API 인증도 만료 상태입니다. YouTube의 기존 비공개 쇼츠 두 편은 v4입니다. 본편과 기존 게시본은 보존했습니다. 추가 유료 생성은 없습니다.
"""
(OUT / "잘림수정_검수.md").write_text(text, encoding="utf-8")
save(EP / "outputs/jun-quality-v2/shorts/current_shorts.json", {"local_revision": "v5-ending-fix", "local_report": rel(OUT / "completion.json"), "published_revision": "v4", "upload_pending": True})
external_path = EP / "director/jun-quality-v2/external_status.json"
external = read(external_path)
external["youtube"]["shorts_correction"] = {"local_revision": "v5-ending-fix", "published_revision": "v4", "new_uploads_performed": 0, "blockers": report["upload_blockers"], "report": rel(OUT / "completion.json")}
save(external_path, external)

state = read(EP / "state.json")
state["shorts_ending_fix"] = {"revision": "v5-ending-fix", "status": report["status"], "outputs": [x["video"] for x in items], "report": rel(OUT / "completion.json"), "new_uploads_performed": 0, "published_revision": "v4"}
state["active_work"]["shorts"] = [x["video"] for x in items]
state["active_work"]["shorts_local_revision"] = "v5-ending-fix"
state["active_work"]["shorts_published_revision"] = "v4"
state["blocked_tasks"] = [x for x in state.get("blocked_tasks", []) if x["task"] != "Upload corrected Shorts"]
state["blocked_tasks"].append({"task": "Upload corrected Shorts", "reason": "; ".join(report["upload_blockers"]), "revision": "v5-ending-fix"})
state["updated_at"] = stamp
save(EP / "state.json", state)
decisions = read(EP / "decisions.json")
decisions["decisions"] = [d for d in decisions["decisions"] if d.get("id") != "shorts-ending-fix-20261028-v5"]
decisions["decisions"].append({"id": "shorts-ending-fix-20261028-v5", "gate": "internal_correction", "status": report["status"], "user_feedback": "쇼츠 영상 봤는데 뒷부분에 갑자기 영상 잘리는데?", "changed_scope": "Two Shorts outgoing audio cuts and 0.35s closing transition", "report": rel(OUT / "completion.json"), "new_paid_calls": 0, "new_uploads": 0, "at_utc": stamp})
save(EP / "decisions.json", decisions)

release = EP / "outputs/jun-quality-v2/release"
manifest = read(release / "upload_manifest.json")
manifest.update(local_shorts_revision="v5-ending-fix", published_shorts_revision="v4", pending_shorts_updates=[{"id": x["id"], "video": x["video"], "sha256": x["sha256"], "privacy": "private"} for x in items])
save(release / "upload_manifest.json", manifest)
up = release / "upload_status.md"
old = up.read_text(encoding="utf-8")
marker = "\n\n## 쇼츠 끝부분 수정 v5"
old = old.split(marker)[0]
up.write_text(old + marker + "\n\n수정본 두 편은 로컬에서 완료했습니다. 브라우저 제어 실행 오류와 API 인증 만료로 v5 재업로드는 0건입니다. 위 YouTube 링크는 v4이며, 현재 로컬 수정본·검수 기록은 영상/매매가격계산/쇼츠_홍보.mp4, 쇼츠_핵심요약.mp4, 쇼츠_잘림수정_검수.md에서 확인할 수 있습니다.\n", encoding="utf-8")
shelf_path = ROOT / "config/video_shelf.json"
shelf = read(shelf_path)
entry = next(e for e in shelf["entries"] if e["workspace"].endswith("affordable-home-price-20261026"))
for item, label in zip(items, ["쇼츠_홍보", "쇼츠_핵심요약"]):
    entry["files"][label + ".mp4"] = item["video"]
    entry["files"][label + ".srt"] = str(Path(item["video"]).with_suffix(".srt")).replace("\\", "/")
entry["files"]["쇼츠_잘림수정_검수.md"] = rel(OUT / "잘림수정_검수.md")
entry.update(status="본편 비공개 업로드 완료 / 로컬 쇼츠 v5 끝부분 수정·검수 완료 / 유튜브 쇼츠 v4 유지·v5 업로드 연결 복구 대기", shorts_local_revision="v5-ending-fix", shorts_youtube_revision="v4")
save(shelf_path, shelf)
print(json.dumps({"status": report["status"], "items": [{"id": x["id"], "sha256": x["sha256"]} for x in items], "uploads": 0}, ensure_ascii=False))
