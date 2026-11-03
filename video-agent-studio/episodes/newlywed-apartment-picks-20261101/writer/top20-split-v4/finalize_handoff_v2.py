"""v2 검증 결과와 산출물을 인계하며 v1 handoff.json도 보존합니다."""
import hashlib
import json
from pathlib import Path

p=Path(__file__).resolve().parent
read=lambda f:json.loads((p/f).read_text(encoding="utf-8"))
sha=lambda f:hashlib.sha256((p/f).read_bytes()).hexdigest()
v=read("validation_v2.json")
assert v["status"]=="pass" and v["scene_proposals_sha256"]==sha("scene_proposals_v2.json")
assert all(sha(row["path"])==row["sha256"] for row in v["parts"])
assert all(sha(row["path"])==row["sha256"] for row in read("v1_preservation_manifest.json")["files"])
outputs=["part1_script_v2.md","part2_script_v2.md","scene_proposals_v2.json","validation_v2.json","preflight_writer_v2.json"]
freeze_path=p/"input_freeze_validation_v2.json"
freeze=read("input_freeze_validation_v2.json") if freeze_path.exists() else None
if freeze:
    assert freeze["status"]=="pass"
    assert all(sha(name)==value for name,value in freeze["script_md_sha256"].items())
    proposal=read("scene_proposals_v2.json")
    for entry in proposal["input_revisions"]:
        assert hashlib.sha256((p.parents[4]/entry["path"]).read_bytes()).hexdigest()==entry["sha256"]
    lock={"revision":"top20-split-v4-writer-v2-final-input-lock","status":"frozen_for_parent_script_gate_not_approved",
          "script_md_sha256":freeze["script_md_sha256"],"input_revisions":proposal["input_revisions"],
          "artifacts":[{"path":f,"sha256":sha(f)} for f in outputs],
          "verification_code":{"path":"verify_script_v2.py","sha256":sha("verify_script_v2.py")},
          "final_input_check":{"path":"input_freeze_validation_v2.json","sha256":sha("input_freeze_validation_v2.json")},
          "feature_issue":{"path":"issue_W4V2-FEATURE-STATION-LABELS.json","sha256":sha("issue_W4V2-FEATURE-STATION-LABELS.json"),"status":"QA_in_progress"},
          "reproduction":"build_script_v2.py 후 freeze_inputs_v2.py→verify_script_v2.py→finalize_handoff_v2.py; 대본 원문 유지",
          "limits":"새 본편/TTS 생성 없음; 독립 QA·사용자 script 승인 미완료"}
    (p/"input_lock_v2.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    outputs += ["input_freeze_validation_v2.json","input_lock_v2.json"]
h={
    "task_id":"two-part-v4-script-v2","role":"writer",
    "status":"v2_deliverables_self_verified_pending_new_script_gate_and_independent_QA",
    "base_path":"writer/top20-split-v4/",
    "input_revisions":{"manifest":"scene_proposals_v2.json#/input_revisions","maps":"visual/top20-split-v4/map_assets.json displayed_detail_labels/displayed_overview_labels","final_lock":"input_lock_v2.json" if freeze else None},
    "outputs":[{"path":f,"sha256":sha(f)} for f in outputs],
    "preservation":"v1_preservation_manifest.json:13파일 보존. 기존 handoff.json도 보존.",
    "counts":{"parts":2,"regions":20,"scenes":24,"sentences":174,"selected_facility_labels_matched":58,"selected_price_comparisons":20},
    "affected_scene_ids":["P01-INTRO","P01-R20~R11","P01-OUTRO","P02-INTRO","P02-R10~R01","P02-OUTRO"],
    "estimate":{"part1_s":619.0,"part2_s":654.4,"intro_s":[41.3,41.3],"status":"estimate_only_no_new_TTS"},
    "checks":[{"check":"최신 요구·출처 필드·수치·표시명·v1 보존","result":"pass","evidence":"validation_v2.json; writer 자체207항목"}],
    "open_issue_ids":["W4V2-FEATURE-STATION-LABELS","W4V2-INDEPENDENT-QA-SCRIPT-GATE"],
    "next_role":"director의 검토용 script 게이트 준비·독립QA 확인; 승인 후 narration",
    "limits":"v2 원문 유지. 대표 상세58시설·특성역6곳 전체지도 표시명 대조. 특성역은 QA 확인 중. 픽셀/모션 재생·새TTS/본편 생성·독립QA 미실시.",
    "issue_statuses":{"W4V2-FEATURE-STATION-LABELS":"visual_fix_manifest_confirmed_QA_in_progress","W4V2-INDEPENDENT-QA-SCRIPT-GATE":"pending_independent_QA_and_new_script_gate"},
    "final_freeze":{"scripts_unchanged":True,"source_manifest_sha256":freeze["final_map_manifest_sha256"] if freeze else None,"verification_sha256":sha("validation_v2.json"),"lock_sha256":sha("input_lock_v2.json") if freeze else None}
}
(p/"handoff_v2.json").write_text(json.dumps(h,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert read("handoff_v2.json")["counts"]==h["counts"]
assert all(sha(o["path"])==o["sha256"] for o in read("handoff_v2.json")["outputs"])
print(json.dumps({"handoff":"writer/top20-split-v4/handoff_v2.json","verified_output_files":len(outputs),"v1_preserved_files":13,"pending_issues":h["open_issue_ids"]},ensure_ascii=False))
