"""Record the current user's production/private-upload scope against exact inputs."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

script=EP/"writer/top20-8min-v2/script_v3.md"
digest=sha(script)
assert digest=="4cc70ef2ae3cabda13b560104dd96ef0df0fe1f815a5f1372ac680e729d3be17"
now=datetime.now(timezone(timedelta(hours=9))).isoformat()
authorization={"source":"latest direct user requests","created_at":now,
 "requests":["Top 20으로 영상 제작해줘","영상은 기존 가이드라인 확인해서 그 기준에 맞게 만들어서 비공개 업로드해주고, 홍보용 쇼츠와 내용이 담긴 쇼츠 영상도 만들어서 비공개 업로드해줘"],
 "episode_id":EP.name,"script":"writer/top20-8min-v2/script_v3.md","script_sha256":digest,
 "main_count":1,"shorts_count":2,"private_upload_authorized":True,"public_publication_authorized":False,
 "delete_existing_videos":False,"new_paid_generation_authorized":False,
 "external_review_new_packet":"not_yet_prepared","target_channel_id":"UCr_mTC0x_Uobv6MrIsOkrXw"}
save(HERE/"authorization.json",authorization)
state=read(EP/"state.json")
save(HERE/"state.before.json",state)
state.update(revision="top20-production-v1",phase="production_audio_and_visuals",script_approval="accepted_by_latest_production_request",
 upload="three_private_uploads_authorized_after_quality_checks",shorts=["promo","analysis"],
 private_upload_authorization="director/top20-production-v1/authorization.json",updated_at=now)
save(EP/"state.json",state)
pre=read(EP/"episode_preflight.json")
pre["approvals"]["script"]={"status":"authorized_by_latest_production_request","decision_id":"D009","artifact_hashes":{authorization["script"]:digest}}
pre["approvals"]["pre_upload"]={"status":"authorized_private_after_quality_checks","decision_id":"D010","visibility":"private","artifact_hashes":{},"scope":["main","promo_short","analysis_short"]}
pre["story"]={"opening_question":"신혼부부가 많이 사는 수도권 지역은 어디일까?","order":["scope_2024_53_gu","countdown_20_to_1","stock_vs_change","composition","next_apartment_comparisons"],"price_recommendation":"future_episode"}
pre["representative_previews"]=["regional_photo_map_count","stock_and_year_over_year_change","first_and_remarriage_composition"]
pre["facts_required"]=["newlywed_scope_and_old_boundary","ranking_and_comparison_counts","photo_place_and_capture_date","source_rights"]
save(EP/"episode_preflight.json",pre)
dec=read(EP/"decisions.json")
for row in [{"id":"D009","choice":"produce latest TOP20 script v3","script_sha256":digest,"basis":"latest direct production request","status":"authorized"},
 {"id":"D010","choice":"main and two Shorts private upload after QA","basis":"latest direct user scope","status":"authorized","visibility":"private","delete_existing_videos":False}]:
    if not any(d["id"]==row["id"] for d in dec["decisions"]):dec["decisions"].append(row)
save(EP/"decisions.json",dec)
print(json.dumps({"stage":state["phase"],"script_sha256":digest,"private_uploads":3,"new_paid_generation":False},ensure_ascii=False))
