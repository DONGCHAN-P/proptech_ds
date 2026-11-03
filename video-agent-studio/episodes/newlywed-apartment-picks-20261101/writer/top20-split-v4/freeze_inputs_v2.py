"""대본 원문을 유지하고 최종 지도 입력과 QA 인계 메타데이터만 고정합니다."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT)).replace("\\","/")


def dump(p,obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


handoff=read(HERE/"handoff_v2.json")
script_hashes={x["path"]:x["sha256"] for x in handoff["outputs"] if x["path"] in {"part1_script_v2.md","part2_script_v2.md"}}
assert len(script_hashes)==2
assert all(sha(HERE/name)==value for name,value in script_hashes.items())
assert all(sha(HERE/x["path"])==x["sha256"] for x in read(HERE/"v1_preservation_manifest.json")["files"])

map_path=EP/"visual/top20-split-v4/map_assets.json"
map_hash=sha(map_path)
maps=read(map_path)
price_assets={a["region_id"]:(i,a) for i,a in enumerate(maps["assets"]) if a["mode"]=="prices"}
targets={"R19":"신내역","R18":"구성역","R15":"신도림역","R10":"주안역","R07":"고덕역","R03":"삼송역"}
norm=lambda s:s.removesuffix("역")
overview_evidence=[]
for rid,name in targets.items():
    for i,a in enumerate(maps["assets"]):
        if a["region_id"]==rid:
            labels=a.get("displayed_overview_labels",[])
            assert any(norm(n)==norm(name) for n in labels),(rid,a["mode"],name)
            overview_evidence.append({"region_id":rid,"mode":a["mode"],"name":name,"field":f"/assets/{i}/displayed_overview_labels","value":labels})

proposal_path=HERE/"scene_proposals_v2.json"
proposal=read(proposal_path)
prior_map_hash=next(x["sha256"] for x in proposal["input_revisions"] if x["key"]=="maps")
for x in proposal["input_revisions"]:
    if x["key"]=="maps":x["sha256"]=map_hash
if not any(x["key"]=="final_input_freezer" for x in proposal["input_revisions"]):
    proposal["input_revisions"].append({"key":"final_input_freezer","path":rel(Path(__file__).resolve()),"sha256":sha(Path(__file__).resolve())})

matched=[]
for scene in proposal["scenes"]:
    if scene["scene_kind"]!="region":continue
    rid=scene["region_id"]
    i,asset=price_assets[rid]
    ctx=scene["context_selection"]
    for facility in ctx["selected_facilities"]:
        assert facility["displayed_label"] in asset["displayed_detail_labels"],(rid,facility)
        matched.append({"region_id":rid,"label":facility["displayed_label"]})
    ctx["displayed_detail_labels"]=deepcopy(asset["displayed_detail_labels"])
    ctx["map_manifest_field"]=f"/assets/{i}"
    ctx["source_manifest_sha256"]=map_hash
    cid=f"W4V2-{rid}-CONTEXT-MATCHED"
    for f in proposal["claim_registry"][cid]["source_fields"]:
        if f["path"]==rel(map_path):
            f["field"]=f"/assets/{i}/displayed_detail_labels"
            f["value"]=deepcopy(asset["displayed_detail_labels"])
    if rid in targets:
        scene["feature_station_overview_followup"]={
            "name":targets[rid],"status":"manifest_label_confirmed_QA_in_progress",
            "source_path":rel(map_path),"source_sha256":map_hash,
            "source_field":f"/assets/{i}/displayed_overview_labels",
            "displayed_overview_labels":asset["displayed_overview_labels"],
            "scope":"전체지도 왼쪽 표시명 메타데이터 확인; 공공좌표·파란색 실제 픽셀·가독성은 QA 확인 중",
        }
for scene in proposal["scenes"]:
    for sentence in scene["sentences"]:
        sentence["source_fields"]=[{"claim_id":cid,"path":f["path"],"field":f["field"]} for cid in sentence["claim_ids"] for f in proposal["claim_registry"][cid]["source_fields"]]
proposal["map_status"]["final_manifest_sha256"]=map_hash
proposal["map_status"]["feature_station_overview_labels"]="6지역·context/prices12판에서 명칭 확인; 실제 지도/공공좌표 QA 확인 중"
proposal["final_freeze"]={"script_md_sha256":script_hashes,"narration_changed":False,"facility_selection_changed":False,"source_manifest_updated":True,"script_gate":"pending_parent_preparation_not_approval"}
dump(proposal_path,proposal)

issue_path=HERE/"issue_W4V2-FEATURE-STATION-LABELS.json"
issue=read(issue_path)
issue["status"]="visual_fix_manifest_confirmed_QA_in_progress"
issue["to"]=["director","qa"]
for item in issue["items"]:
    rid=item["region_id"]
    i,a=price_assets[rid]
    if "problem" in item:item["original_problem"]=item.pop("problem")
    if "proposal" in item:item["original_proposal"]=item.pop("proposal")
    item["status"]="visual_fix_manifest_confirmed_QA_in_progress"
    item["resolution"]={"source_path":rel(map_path),"source_sha256":map_hash,"source_field":f"/assets/{i}/displayed_overview_labels","confirmed_name":targets[rid],"modes_checked":["context","prices"]}
    item["impact"]="writer의 지도 추가 표시 요청은 메타데이터에서 반영 확인. 좌표·실제 파란 라벨·가독성은 QA 확인 중으로 인계"
issue["current_handoff"]="v2 원문과 대표 상세58시설은 유지. 시각 후속 수정은 전체지도 표시명 목록으로 확인했으며 독립 QA 완료로 기록하지 않음"
dump(issue_path,issue)

preflight_path=HERE/"preflight_writer_v2.json"
preflight=read(preflight_path)
preflight["visual"]["feature_stations"]="6곳 전체지도 표시명 목록 반영 확인; 독립QA 확인 중"
preflight["visual"]["final_map_manifest_sha256"]=map_hash
preflight["original_preservation"]="v1 13파일과 v2 MD2개 원문 SHA256 유지"
dump(preflight_path,preflight)

check={"task_id":"two-part-v4-script-v2-final-input-freeze","status":"pass","script_md_sha256":script_hashes,
       "prior_map_manifest_sha256":prior_map_hash,"final_map_manifest_sha256":map_hash,
       "counts":{"feature_stations":6,"overview_plates_checked":len(overview_evidence),"selected_detail_facilities_unchanged":len(matched),"v1_files_preserved":13},
       "overview_label_evidence":overview_evidence,"selected_detail_label_matches":matched,
       "scope":"입력 메타데이터·원문 해시 대조만. 지도 픽셀/공공좌표/독립QA/새 본편/TTS 검수 아님",
       "next":"특성역 이슈는 QA 확인 중; 총괄이 새 script 게이트 준비"}
assert len(matched)==58 and len(overview_evidence)==12
assert all(sha(HERE/name)==value for name,value in script_hashes.items())
assert sha(map_path)==map_hash
dump(HERE/"input_freeze_validation_v2.json",check)
print(json.dumps({"status":"pass","scripts_unchanged":2,"overview_labels":6,"overview_plates":12,"detail_facilities_unchanged":58,"map_manifest_sha256":map_hash},ensure_ascii=False))
