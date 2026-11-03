"""Close the director-owned delivery-document issue without rewriting independent QA."""
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))

def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(4194304), b""):
            h.update(block)
    return h.hexdigest()

def pin(p):
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size}

def write(name, obj):
    p = HERE / name
    assert not p.exists(), f"Preserve prior record: {p}"
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

qa_path = EP / "qa/jun-production-v1/final_review.json"
qa = read(qa_path)
assert qa["status"] == "exact_final_media_samples_pass_delivery_guide_pending"
assert qa["required_issues"] == ["JQA-DELIVERY-001"] and qa["critical_issues"] == []
video = EP / "outputs/jun-production-v1/renders/measured-jun-v1/housing_choice_jun_v1.mp4"
assert sha(video) == qa["video_sha256"]
for field, rel in {
    "script": "outputs/script-final-v6/script_v6.md",
    "subtitles": "outputs/jun-production-v1/captions_measured.srt",
    "metadata": "outputs/jun-release-v1/metadata_measured.json",
    "description": "outputs/jun-release-v1/description_measured.md",
    "thumbnail": "outputs/jun-release-v1/thumbnail.png",
}.items():
    assert sha(EP / rel) == qa[field + "_sha256"]

guide = EP / "editor/jun-production-v1/placement_guide.md"
assert guide.is_file()
refs = []
for name in re.findall(r"`([^`]+\.(?:json|txt|mp4|srt))`", guide.read_text(encoding="utf-8")):
    candidates = [EP / name, EP / "outputs/jun-production-v1" / name, ROOT / name]
    path = next((p for p in candidates if p.is_file()), None)
    assert path is not None, f"Missing delivery reference: {name}"
    refs.append({"reference": name, "file": pin(path)})
assert refs
for number in range(1, 11):
    assert (EP / f"outputs/jun-production-v1/ch{number:02}/index.html").is_file()

now = datetime.now(timezone.utc).isoformat()
closure = {
    "issue_id": "JQA-DELIVERY-001", "status": "closed_document_references_verified",
    "owner": "video_director", "at_utc": now,
    "basis": "Independent QA assigned this document-only correction to the director; no media re-review or worker resumption is asserted.",
    "independent_review_preserved": pin(qa_path), "guide": pin(guide),
    "references": refs, "all_10_composition_files_exist": True,
    "video_unchanged": True, "video_sha256": sha(video),
}
write("delivery_issue_closure.json", closure)
final = copy.deepcopy(qa)
final.update({
    "approved": True, "status": "independent_media_samples_pass_director_delivery_issue_closed",
    "required_issues": [], "pending_inputs": [],
    "scope": "독립 QA의 실제 MP4 204시점·ASR·기술 검사와 총괄의 납품 문서 참조 확인을 통합했습니다. 연속 재생·실제 청취·전체 206개 자막의 영상 확인은 미실시입니다.",
    "scope_ko": "독립 QA의 실제 MP4 204시점·ASR·기술 검사에 총괄의 납품 문서 참조 확인을 합친 승인입니다. 연속 재생·실제 청취·전체 206개 자막의 영상 확인은 미실시입니다.",
    "independent_media_review": pin(qa_path),
    "delivery_issue_closure": pin(HERE / "delivery_issue_closure.json"),
    "media_rechecked_by_director": False,
    "completed_at_utc": now,
})
final["coverage"]["final_MP4_sampled_frames_viewed"] = True
final["coverage"]["delivery_guide_references_verified"] = len(refs)
write("codex_final_review.json", final)
write("claude_egress_block.json", {
    "status": "required_user_payload_approval_pending", "at_utc": now,
    "automatic_approval_review_rejected": True, "process_started": False,
    "action": "Send final private-video review packet to logged-in Claude Anthropic Opus/max",
    "reason_ko": "비공개 영상 프레임·자막·대본의 구체적 외부 전송 자료 묶음에 대한 명시적 승인을 자동 승인 검토가 확인하지 못했습니다.",
    "payload": "director/launch-and-jun-v1/claude_media_input_v1/image_paths.json",
    "payload_image_count": 19, "video_sha256": qa["video_sha256"],
    "audio_files_included": False, "credentials_included": False,
    "user_question_already_pending": True, "retry_allowed_before_new_reply": False,
    "main_upload_executed": False, "old_video_delete_executed": False,
})
print(json.dumps({"codex_approved": True, "document_refs": len(refs), "independent_qa_preserved": True, "claude": "pending_payload_approval"}))
