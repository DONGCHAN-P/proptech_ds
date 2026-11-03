from pathlib import Path
import json
from datetime import datetime,timezone
e=Path(__file__).resolve().parent;repo=e.parents[2];now=datetime.now(timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
o=e/'outputs/stable-maps-v11';o.mkdir(exist_ok=True)
brief={'revision':'stable-maps-v11','recorded_at':now,'source':'direct_user_rejection_v10','review_scope_s':[0,525],'critical_times_s':[64,165,180],'supersedes':'v10 camera and spotlight animation guidance','requirements':['remove map zoom pan pulse line drawing and short transition inserts','stable high contrast operating railway map throughout railway explanation','all relevant operating stations and lines readable at once','planned station positions rechecked against official sources and independent news','correct 64s visual context','audit dense actual frames and shot lengths, not only representative stills'],'preserve':['approved narration and captions','original versions','channel opening branding','scope after525s not edited'],'paid_generation_authorized':False,'publication_authorized':False,'telegram_text_notice_authorized':True}
save(o/'revision_brief.json',brief)
p=repo/'output/video_decisions/decisions/91a40cf0a547.json';d=json.loads(p.read_text(encoding='utf-8'));d.update(status='revision_requested',direct_feedback_at=now,direct_feedback_scope='v11 remove map motion, rapid cuts, unreadable rail context; reverify planned station positions');save(p,d)
p=e/'decisions.json';c=json.loads(p.read_text(encoding='utf-8'))
for x in c['decisions']:
 if x.get('id')==d['id']:x.update(d)
if not any(x.get('decision_id')=='NYJ-STABLE-MAPS-V11' for x in c['decisions']):c['decisions'].append({'decision_id':'NYJ-STABLE-MAPS-V11','source':'direct_user_revision_request','recorded_at':now,'scope_s':[0,525],'brief':'outputs/stable-maps-v11/revision_brief.json','publication_authorized':False})
save(p,c)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='stable_maps_v11_in_progress',pending_gate=None,pending_decision_ids={},current_review_render_status='v11_motion_removed_revision_in_progress',revision_brief='outputs/stable-maps-v11/revision_brief.json',new_paid_generation_authorized=False,publication_authorized=False);save(p,s)
print('v10 rejected; v11 stable-map revision recorded. Previous assets preserved.')
