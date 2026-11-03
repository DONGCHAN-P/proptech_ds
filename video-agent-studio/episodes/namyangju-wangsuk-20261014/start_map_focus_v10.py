from pathlib import Path
from datetime import datetime,timezone
import json
e=Path(__file__).resolve().parent;repo=e.parents[2]
out=e/'outputs/map-focus-v10';out.mkdir(exist_ok=True)
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
now=datetime.now(timezone.utc).isoformat()
brief={'revision':'map-focus-v10','source':'direct_user_revision_request','recorded_at':now,'base_mp4':'outputs/video-review-v8/namyangju-landuse_full_v8.mp4','base_sha256':'94b6d04aa780c93509203b705ce02fa12085d57a0faef23a0629769db0549ba4','time_basis':'final v8 actual video time, not pre-hook content anchors','changed_interval_s':[165,525],'delivery_stages':[{'id':'part1','range_s':[165,273]},{'id':'part2','range_s':[273,369]},{'id':'part3','range_s':[369,525]}],'requirements':['planned station pins including Wangsuk with source-backed location and uncertainty','source-backed major road traces on native plan boards','large overview to detail navigation at all regional transitions','sequential focus motion for narrated school park station and parcel','replace right text panel with larger map and short on-map callout'],'preserve':['existing script v6','existing 11 audio sources','semantic captions and fixed white bar','original versions','all content after525s'],'paid_generation_authorized':False,'telegram_text_notification_authorized':True,'telegram_file_send_authorized':False,'notification_execution_owner':'editor; same pipeline after each actual rendered and checked stage, independent of root reply'}
save(out/'revision_brief.json',brief)
p=repo/'output/video_decisions/decisions/9143efd1e4d3.json';d=json.loads(p.read_text(encoding='utf-8'));d.update(status='revision_requested',direct_feedback_at=now,direct_feedback_scope='v10 actual165..525sec station/road pins, continuous map navigation and on-map focus/callouts')
save(p,d)
p=e/'decisions.json';c=json.loads(p.read_text(encoding='utf-8'))
for x in c['decisions']:
 if x.get('id')==d['id']:x.update(d)
if not any(x.get('decision_id')=='NYJ-MAP-FOCUS-V10' for x in c['decisions']):c['decisions'].append({'decision_id':'NYJ-MAP-FOCUS-V10','kind':'internal_edit_application','source':'direct_user_revision_request','recorded_at':now,'scope_s':[165,525],'brief':'outputs/map-focus-v10/revision_brief.json','new_paid_generation':False,'publication_authorized':False})
save(p,c)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='map_focus_v10_in_progress',pending_gate=None,pending_decision_ids={},current_review_render_status='v10_partial_revision_in_progress',revision_brief='outputs/map-focus-v10/revision_brief.json',new_paid_generation_authorized=False,completed_gate_approved_for_v8=False,publication_authorized=False,notification_execution_owner='editor-stage-pipeline',changed_interval_s=[165,525]);save(p,s)
print('v10 scoped revision recorded; v8 retained; staged text notification authorized.')
