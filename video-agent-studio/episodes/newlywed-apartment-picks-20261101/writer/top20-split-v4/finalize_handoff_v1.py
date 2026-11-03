"""검증된 writer 산출물의 경로와 입력 버전을 총괄에게 인계합니다."""
import hashlib
import json
from pathlib import Path

p = Path(__file__).resolve().parent
read = lambda f: json.loads((p/f).read_text(encoding="utf-8"))
sha = lambda f: hashlib.sha256((p/f).read_bytes()).hexdigest()
v = read("validation_v1.json")
assert v["status"] == "pass"
assert v["checked_artifact_sha256"] == sha("scene_proposals_v1.json")
assert all(row["sha256"] == sha(f"part{row['part']}_script_v1.md") for row in v["parts"])
outputs = ["part1_script_v1.md", "part2_script_v1.md", "scene_proposals_v1.json", "validation_v1.json", "preflight_writer_v1.json"]
h = {
    "task_id":"two-part-v4-script",
    "role":"writer",
    "status":"writer_verified_pending_director_review_and_new_script_gate",
    "base_path":"writer/top20-split-v4/",
    "input_revisions":{"manifest":"scene_proposals_v1.json#/input_revisions","hashes":"각 입력 SHA256 기록","context":"최신 context_notes.json 반영"},
    "outputs":[{"path":f,"sha256":sha(f)} for f in outputs],
    "counts":{"parts":2,"regions":20,"scenes":24,"sentences":227,"sentences_per_region":10,"verified_claims_reused":51,"director_supplement":1,"selected_facilities":58},
    "affected_scene_ids":["P01-INTRO","P01-R20~R11","P01-OUTRO","P02-INTRO","P02-R10~R01","P02-OUTRO"],
    "checks":[{"check":"수치·출처 필드·분모·시설명·원고 동일성","result":"pass","evidence":"validation_v1.json; 자체176항목"}],
    "estimate":{"part1_s":784.9,"part2_s":821.8,"region_s":[65,73],"basis":"기존 v6 계획용 읽기속도 참고; 새 음성 실측 아님"},
    "open_issue_ids":["W4-CONTEXT-MATCH","W4-INDEPENDENT-SCRIPT-QA"],
    "next_role":"director→독립qa/visual; 새script승인 후 narration",
    "limits":"독립QA·지도시설매칭·OSM완전성·새음성청취 미실시. 기존v6승인 승계없음. TTS/유료/미디어/업로드/외부내보내기 없음. 공통파일 수정없음."
}
(p/"handoff.json").write_text(json.dumps(h,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert read("handoff.json")["counts"] == h["counts"]
assert all(sha(f)==row["sha256"] for f,row in zip(outputs,read("handoff.json")["outputs"]))
print(json.dumps({"handoff":"writer/top20-split-v4/handoff.json","verified_outputs":len(outputs),"pending_issues":h["open_issue_ids"]},ensure_ascii=False))
