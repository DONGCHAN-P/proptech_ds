"""Publish local research aliases and keep the production decision boundary explicit."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
OUT=EP/"outputs/top20-research-v2"
VISUAL=EP/"visual/top20-8min-v2"
DIR=Path(__file__).resolve().parent


def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()


def main():
    pack=read(OUT/"delivery_manifest.json")
    writer=EP/"writer/top20-8min-v2"
    v3=(writer/"scene_proposals_v3.json").exists()
    proposals=writer/("scene_proposals_v3.json" if v3 else "scene_proposals.json")
    script=writer/("script_v3.md" if v3 else "script_v2.md")
    proposal=read(proposals)
    assert proposal["target_duration_s"]==480
    assert abs(sum(s["duration_s"] for s in proposal["scenes"])-480)<0.01
    common=[]
    photos=read(EP/pack["photo_manifest"])["assets"]
    photos_by_id={p["region_id"]:p for p in photos}
    map_index={a["region_id"]:a for a in read(VISUAL/"maps/map_assets.json")["assets"]}
    scene_assets=[]
    for scene in proposal["scenes"]:
        row=dict(scene)
        row["status"]="research_draft_not_approved"
        row["timing_basis"]="estimated_before_voice_recording"
        row["actual_start_s"]=None;row["actual_end_s"]=None
        row["audio_revision"]=None
        rid=row.get("region_id")
        if rid and rid in photos_by_id:
            p=photos_by_id[rid];m=map_index[rid]
            bound_ids=[p["asset_id"] if a==f"PHOTO_{rid}" else a for a in row.get("asset_ids",[])]
            row["asset_ids"]=list(dict.fromkeys(bound_ids+[m["asset_id"],p["asset_id"]]))
            row["asset_status"]="research_materials_prepared_final_composition_pending"
            scene_assets.append({"scene_id":scene["scene_id"],"region_id":rid,"rank":scene.get("rank"),
              "actual_photo_place":p["actual_place"],"photo_asset_id":p["asset_id"],
              "canonical_photo_asset_id":f"PHOTO_{rid}",
              "photo_file":str((VISUAL/p["actual_file"]).relative_to(EP)).replace("\\","/"),
              "map_asset_id":m["asset_id"],"map_vector":m["vector_file"],
              "use_rule":"Photo names the actual depicted place; a different facility's narration uses its own verified source layer. Exact facility pins require verified coordinates.",
              "photo_capture_year":p.get("photo_capture_year"),"statistical_reference_date":"2024-11-01"})
        common.append(row)
    write(EP/"scenes.json",{"episode_id":EP.name,"revision":"top20-8min-v2","script_revision":"draft-v3" if v3 else "draft-v2",
      "target_duration_s":480,"timing_locked":False,"audio_confirmed":False,"scenes":common})
    write(DIR/"scene_asset_plan.json",{"revision":"top20-8min-v2","script_source":rel(script),"photo_manifest":pack["photo_manifest"],
      "scene_assets":scene_assets,"source_content_verified_as_place_examples":True,"voice_sync_and_final_frames":"pending"})

    brief=read(EP/"brief.json")
    if "superseded_planning_assumptions" not in brief:
        brief["superseded_planning_assumptions"]=brief.get("planning_assumptions",{})
    brief["planning_assumptions"]={"initial_scope":"2024 수도권53개구 TOP20","format_proposal":"16:9 본편·20위→1위",
       "duration_proposal":"480초 목표; 실제 음성 생성·정렬 후 타이밍 확정","voice":"미선택·새 유료 생성 미실행"}
    brief["current_stage"]="research_media_prepared_and_top20_script_drafted"
    brief["script_draft"]=rel(script)
    write(EP/"brief.json",brief)
    state=read(EP/"state.json")
    state.update({"revision":"top20-8min-v2","phase":"research_media_prepared_script_review_pending",
      "script":str(script.relative_to(EP)).replace("\\","/"),"script_sha256":sha(script),
      "scene_proposals":str(proposals.relative_to(EP)).replace("\\","/"),"duration_target_s":480,
      "actual_video_duration_s":None,"script_approval":"pending_for_new_top20_version","voice":"not_selected",
      "paid_budget":"not_requested_not_authorized","upload":"not_requested","render_created":False,
      "research_summary":pack["research_summary"],"primary_photos":20,"map_png":20,"map_svg":20,"data_cards":9,
      "asset_pack":rel(OUT),"photo_manifest":pack["photo_manifest"],"open_rights_context_flags":pack["rights_context_review_required"],
      "actual_listening_performed":False,"continuous_playback_performed":False,
      "open_research_items":["5 qualified supplementary feature claims remain outside definitive narration", "photo dates/individual credit conditions retained for final framing"],
      "updated_at":datetime.now().astimezone().isoformat()})
    # Avoid carrying a prior live-listing task into the TOP20 ranking film.
    state["previous_apartment_listing_research"]={"candidate_complexes":state.get("candidate_complexes"),"current_listing_evidence":state.get("current_listing_evidence")}
    write(EP/"state.json",state)
    preflight=read(EP/"episode_preflight.json")
    preflight["status"]="top20_research_and_media_filled_production_checks_pending"
    preflight["input_contract"].update({"narration_mode":"not_selected","proposed_script_changes":state["script"],
      "episode_specific_choices":["TOP20·8분 requested by user", "2024 53-gu scope", "20 authentic regional photos and period-matched geometry"]})
    preflight["approvals"]["topic"]={"status":"authorized_by_current_direct_user","decision_id":"direct-user-20261101-top20-eight-minutes","artifact_hashes":{}}
    preflight["approvals"]["script"]={"status":"draft_delivered_not_approved","decision_id":None,"artifact_hashes":{state["script"]:sha(script)}}
    preflight["qa"]["evidence_paths"]=["qa/top20-8min-v2/findings.json"]
    if (EP/"qa/top20-8min-v2/media_followup.json").exists():preflight["qa"]["evidence_paths"].append("qa/top20-8min-v2/media_followup.json")
    write(EP/"episode_preflight.json",preflight)
    decisions=read(EP/"decisions.json")
    known={d["id"] for d in decisions["decisions"]}
    for decision in [
      {"id":"D006","choice":"TOP20 ranking film, target480seconds","basis":"latest direct user revision","status":"authorized","supersedes":"D003 three-neighborhood first-film proposal"},
      {"id":"D007","choice":"official research and real-place photo/map materials for all20 regions","basis":"latest direct user research/image request","status":"prepared"},
      {"id":"D008","choice":"new TOP20 script is a review draft; audio timing/render follow later","basis":"AGENTS.md script stage and no current voice/budget selection","status":"pending_script_review"}
    ]:
        if decision["id"] not in known:decisions["decisions"].append(decision)
    write(EP/"decisions.json",decisions)
    write(DIR/"script_review_request.json",{"gate":"script","status":"pending","decision_id":"top20-eight-minutes-script-"+("v3" if v3 else "v2"),
      "script":state["script"],"sha256":sha(script),"not_included":["paid voice/image API","external Claude transfer","upload or publication"],
      "basis":"AGENTS.md script(대본 전달) decision stage","request_delivery":"local draft and research package; no unsolicited Telegram send"})

    shelf_path=ROOT/"config/video_shelf.json";shelf=read(shelf_path)
    entry=next(e for e in shelf["entries"] if e["name"]=="신혼부부_지역별아파트")
    entry["status"]="TOP20·8분 본편 자료조사·이미지49장 준비, TOP20 새 대본 검토 초안. 음성·영상 렌더 전"
    files=entry["files"]
    # Keep earlier three-neighborhood proposals explicitly accessible.
    files["이전_단지추천_기획안.md"]=files["기획안.md"]
    files["이전_단지추천_대본.md"]=files["대본초안.md"]
    files.update({"TOP20_자료조사.md":rel(OUT/"자료조사_결과.md"),"TOP20_이미지안내.md":rel(OUT/"이미지자료_안내.md"),
      "TOP20_사진미리보기.jpg":rel(OUT/"사진20장_미리보기.jpg"),"TOP20_지도미리보기.jpg":rel(VISUAL/"maps/지도20장_모아보기.jpg"),
      "TOP20_구성안.md":rel(OUT/"8분_구성안.md"),"TOP20_대본초안.md":rel(script),
      "TOP20_전년비교.csv":rel(EP/"research/top20-8min-v2/top20_comparison.csv"),"TOP20_사진출처.md":rel(OUT/"사진20장_출처.md")})
    # Existing open alias names are left intact; explicit TOP20 names prevent a
    # user's earlier draft from being silently replaced while it is open.
    write(shelf_path,shelf)
    pack.update({"script_file":rel(script),"script_sha256":sha(script),"scene_asset_plan":rel(DIR/"scene_asset_plan.json"),
      "user_facing_folder":"영상/신혼부부_지역별아파트","stage":"research_media_delivered_script_review_pending",
      "finalized_at":datetime.now().astimezone().isoformat()})
    write(OUT/"delivery_manifest.json",pack)
    print(json.dumps({"stage":pack["stage"],"photos":20,"map_png":20,"data_card_png":9,"script":state["script"],"duration_target_s":480,"rendered":False},ensure_ascii=False))


if __name__=="__main__":main()
