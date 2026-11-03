from pathlib import Path
from datetime import datetime,timezone
import json
e=Path(__file__).resolve().parent;repo=e.parents[2];now=datetime.now(timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
o=e/'outputs/locator-timeline-v14';o.mkdir(exist_ok=True)
brief={'revision':'locator-timeline-v14','source':'direct_user_revision_request','recorded_at':now,'base_full':'outputs/caption-station-v13/caption-station_v13_full.mp4','base_sha256':'a567476f33043b87092bff363f8a1f37d0aa3229aa42630cdc0b3b5186d98f9b','visual_work_authorized':['from273s single relevant district whole-landuse plan on left with current area locator','horizontal date timeline for narrated transport/school/commerce/move-in/sale time references; unknown dates stay unknown','526..622s actual Dasan and Byeollae station-area maps with major apartment positions and comparable83<=area<85 prices'],'script_work_authorized':'Rewrite M008 and M009 from approx12:02: summarize five conditions, select ordinary resale-market leaders by region, explain reasons; exclude newlywed-special housing from leader shortlist','preserve':['v13 fixes for transient frames and caption gaps','no zoom in/out or temporary locator inserts','caption bar through speech, no empty boxes over brand intro/outro','existing narration until revised script and budget approval','original versions'],'approval_status':{'new_script':'not_approved','new_voice_budget':'not_approved','paid_generation_authorized':False,'publication_authorized':False},'telegram_text_updates_authorized':True}
save(o/'revision_brief.json',brief)
p=repo/'output/video_decisions/decisions/2bc84e492326.json';d=json.loads(p.read_text(encoding='utf-8'));d.update(status='revision_requested',direct_feedback_at=now,direct_feedback_scope='v14 whole-plan locator, timelines, Dasan/Byeollae price maps, and rewrite regional leaders closing');save(p,d)
p=e/'decisions.json';c=json.loads(p.read_text(encoding='utf-8'))
for x in c['decisions']:
 if x.get('id')==d['id']:x.update(d)
c['decisions'].append({'decision_id':'NYJ-LOCATOR-LEADERS-V14','source':'direct_user_revision_request','recorded_at':now,'brief':'outputs/locator-timeline-v14/revision_brief.json','new_paid_generation_authorized':False});save(p,c)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='v14_visual_and_closing_script_revision_in_progress',active_tasks=['research_region_leaders_v14','writer_closing_script_v7','editor_locator_timeline_v14'],pending_gate=None,pending_decision_ids={},current_review_render_status='v14_visual_revision_in_progress',revision_brief='outputs/locator-timeline-v14/revision_brief.json',script_revision_target='script-v7-region-leaders',new_paid_generation_authorized=False,publication_authorized=False);save(p,s)
print('v14 visual work and new closing script scope recorded; new paid voice remains unauthorized.')
