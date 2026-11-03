"""Bind this guide-only delivery to its source, checks and independent review."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os

PACK = Path(__file__).resolve().parent
EP = PACK.parents[1]
ROOT = PACK.parents[4]
GUIDE = ROOT / "영상/매매가격계산/영상가이드_직접녹음_v1.md"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    source = read(PACK / "source_extracted.json")
    plan = read(PACK / "scene_plan.json")
    rows = read(PACK / "calculation_check.json")
    source_checks = read(PACK / "source_checks.json")
    by_id = {p["id"]: p["text"] for p in source["paragraphs"]}
    used = []
    anchors = 0
    for scene in plan["scenes"]:
        used.extend(scene["paragraph_ids"])
        assert scene["narration_text"] == "\n\n".join(by_id[p] for p in scene["paragraph_ids"])
        assert scene["start"] is None and scene["end"] is None and scene["audio_revision"] is None
        for b in scene["beats"]:
            assert b["anchor"] in scene["narration_text"]
            assert b["start"] is None and b["end"] is None
            anchors += 1
    assert len(used) == 48 and len(set(used)) == 48 and anchors == 101
    original = Path(source["source"])
    snapshot = PACK / "source" / original.name
    assert sha(original) == sha(snapshot) == source["sha256"]
    assert rows["status"] == "passed_arithmetic_only"
    recording = PACK / "녹음용_문단표.md"
    recording_text = recording.read_text(encoding="utf-8")
    for pid in used:
        assert recording_text.count(by_id[pid]) == 1

    # Later successful article-specific endpoints supplement the initial generic
    # law URL. This does not turn the guide into full release/policy clearance.
    for item in source_checks["items"]:
        if item["id"] == "TAX":
            item.update({"status": "primary_articles_opened_conditional_example", "article_urls": ["https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=00&joNo=0011&lsiSeq=282559&urlMode=lsScJoRltInfoR", "https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=00&joNo=0151&lsiSeq=282559&urlMode=lsScJoRltInfoR"]})
            item["scope"] = "일반 법령 URL은 본문 추출이 안 됐으나, 이후 2026-01-01 시행판 제11·151조 공식 개별 조문을 열어 본문 확인. 6.6억 표준 취득세율1.4%와 지방교육세 산정 구조 대조. 원고의 면적·감면 조건을 유지하며 게시 전 대상주택·최신 개정과 재대조."
    source_checks["not_cleared"] = [x for x in source_checks["not_cleared"] if x != "full_article11_151_tax_review"]
    source_checks["not_cleared"].append("final_property_specific_tax_or_latest_amendment_clearance")
    write(PACK / "source_checks_final.json", source_checks)

    # New guide-specific short entry, preserving all existing managed aliases.
    alias = ROOT / "영상/매매가격계산/녹음용_원문_v1.md"
    if alias.exists():
        assert os.path.samefile(alias, recording), "Do not overwrite user/other managed files."
    else:
        os.link(recording, alias)

    qa = EP / "qa/user-recording-v1/review_r2.json"
    review = read(qa) if qa.exists() else None
    approved, required = None, None
    if review is not None:
        # An actual review may approve only its explicitly stated document scope.
        approved = review.get("approved") is True
        required = review.get("required_open", review.get("required_open_count"))
        if required is None:
            findings = review.get("findings", [])
            required = sum(f.get("severity") in {"required", "critical"} and f.get("status") not in {"closed", "resolved"} for f in findings)
        assert approved and required == 0, review

    expected_assets = [EP / "visual/hero-budget-v1.png", EP / "visual/rebuild-v2/transaction-costs.png", EP / "visual/rebuild-v2/bank-limits.png", ROOT / "video-agent-studio/assets/chapter-backgrounds/v1/price.png", ROOT / "video-agent-studio/assets/chapter-backgrounds/v1/comparison.png"]
    assert all(p.is_file() for p in expected_assets)
    files = [GUIDE, recording, snapshot, PACK / "source_extracted.json", PACK / "calculation_check.json", PACK / "scene_plan.json", PACK / "source_checks_final.json", PACK / "episode_preflight.json"]
    if review is not None:
        files.append(qa)
    receipt = {"status": "guide_delivered_pending_user_recording", "completed_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "DOCX extraction, arithmetic verification and text/visual planning only.", "source_sha256": source["sha256"], "source_original_unchanged": True, "counts": {"chapters": 7, "scenes": 31, "source_narration_paragraphs": 48, "literal_anchors": anchors}, "independent_guide_review": {"path": str(qa.relative_to(ROOT)) if review is not None else None, "status": "document_review_available" if review is not None else "not_completed_no_approval_claimed", "approved": approved, "required_open": required}, "parent_document_validation": {"source_and_snapshot_sha": "pass", "all_48_paragraphs_exactly_once": "pass", "all_101_literal_anchors_present": "pass", "measured_timing_not_invented": "pass", "recording_sheet_source_verbatim": "pass", "case_payment_and_cost_arithmetic": "pass"}, "media_QA_performed": False, "actual_listening_performed": False, "continuous_playback_performed": False, "audio_received": False, "measured_duration_s": None, "paid_generation_calls": 0, "render_performed": False, "new_upload_executed": False, "prior_video_alias_sha256": sha(ROOT / "영상/매매가격계산/영상.mp4"), "existing_chapter_asset_candidates": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p), "review_status": "existence_only_for_this_new_guide"} for p in expected_assets], "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in files]}
    assert receipt["prior_video_alias_sha256"] == "55d8626a5eff6ea43da064a44d9999133e09dc635a6b3f6e67a6f5025b64b761"
    write(PACK / "guide_validation.json", receipt)
    state_path = EP / "state.json"
    state = read(state_path)
    if not (PACK / "prior_state.json").exists():
        (PACK / "prior_state.json").write_bytes(state_path.read_bytes())
    state["direct_recording_v1"] = {"status": receipt["status"], "guide": str(GUIDE.relative_to(ROOT)), "source_sha256": source["sha256"], "recording_sheet": str(alias.relative_to(ROOT)), "scene_plan": str((PACK / "scene_plan.json").relative_to(ROOT)), "guide_validation": str((PACK / "guide_validation.json").relative_to(ROOT)), "audio_received": False, "timing_locked": False, "new_video_or_paid_voice_authorized_by_this_step": False, "prior_media_and_uploads_preserved": True}
    write(state_path, state)
    write(PACK / "decisions.json", {"status": "guide_only", "user_request": "다운로드 폴더의 1억부터5억까지 DOCX 기준 영상 가이드부터", "decisions": [{"id": "URV1-INPUT", "scope": "User-authored source accepted for guide drafting; no auto approval transfer from old script."}, {"id": "URV1-FORMAT", "scope": "Proposed voice-only narration with motion/data graphics; no presenter filming assumed."}, {"id": "URV1-TIMING", "scope": "No guessed seconds; literal source anchors pending actual user recording."}, {"id": "URV1-TEXT", "scope": "Source preserved; seven concise wording replacements and one optional insight sentence remain proposals."}, {"id": "URV1-PRODUCTION", "scope": "Three representative types before full expansion; this delivery contains no new audio/images/video render."}]})
    print(json.dumps({"status": receipt["status"], "independent_required_open": required, "source_unchanged": True, "guide": str(GUIDE.relative_to(ROOT)), "recording": str(alias.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
