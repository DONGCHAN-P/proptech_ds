import json,hashlib,math,sys,shutil
from pathlib import Path
e=Path(__file__).resolve().parent;root=e.parents[2];sys.path.insert(0,str(root))
from notify.video_decisions import create,write
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
w=e/'writer/script-v1';o=e/'outputs/script-review-v1';o.mkdir(exist_ok=True)
assert not (o/'review_decisions.json').exists(),'Do not create duplicate review gates'
m=read(w/'manifest.json');q=read(e/'qa/script-v1/final_review.json');a=read(e/'narration/account_preflight.json')
assert q['required_open_count']==0 and q['ready_for_script_review']
assert sha(w/'script_v1.md')==m['source_script_sha256']==q['source_script_sha256']
assert sha(w/'manifest.json')==q['narration_manifest_sha256']
total=0
for c in m['chapters']:
 p=w/c['path'];t=p.read_bytes().decode('utf-8');assert sha(p)==c['sha256'];assert len(t)==c['characters'];total+=len(t)
assert total==m['total_characters']==q['narration_chars']
reserve=math.ceil(total*.2);cap=total+reserve
assert a['passed'] and a['included_remaining']>=cap and not a['overage_enabled']
for name in ['script_v1.md','narration_joined.txt','manifest.json','scene_proposals.json','pronunciation.json']:
 shutil.copy2(w/name,o/name)
budget={'revision':'budget-v1-script-v1','script_revision':'script-v1','source_script_sha256':sha(w/'script_v1.md'),'narration_manifest_sha256':sha(w/'manifest.json'),'voice':'Jun - Clear Korean Lecturer','voice_id':'4p6UA7mnodF5q7JFFrnW','model':'eleven_v4','chapter_count':len(m['chapters']),'input_characters':total,'correction_character_cap':reserve,'total_submitted_character_cap':cap,'actual_credit_hard_cap':cap,'included_balance_checked':a['included_remaining'],'estimate':'Conservative 1 included credit per submitted character; no discounts assumed','additional_cash_usd_cap':0,'automatic_retry':False,'overage_or_topup_authorized':False,'paid_image_or_music_generation_authorized':False,'local_render_only':True,'generation_authorized':False,'guard':'Require exact script+budget approval and fresh balance/rate/overage check before POST; failed or ambiguous request must be reconciled before retry','brand':'Reuse existing 5s intro,10s outro and owned BGM','timing':'Provider original-text alignment then semantic captions; final speech-end plus3s outro hold; no actual timing claim before generation'}
write(e/'narration/budget_proposal_v1.json',budget);write(o/'budget_proposal_v1.json',budget)
artifacts={str(p.relative_to(e)):sha(p) for p in [w/'script_v1.md',w/'manifest.json',w/'scene_proposals.json',e/'qa/script-v1/final_review.json']}
for c in m['chapters']:
 p=w/c['path'];artifacts[str(p.relative_to(e))]=sha(p)
script=create(e.name,'script','창릉 대본v1 확정 검토: 왕숙과 같은 지도·달력 포맷, S1/S4/S5와 기존 생활권 비교,10장·'+str(total)+'자. 독립 대본검수 필수0. 전체 예상14~16분(실측아님).')
script.update(revision='script-v1',artifacts=artifacts,source_script_sha256=sha(w/'script_v1.md'),publication_authorized=False)
paid=create(e.name,'budget',f'창릉 대본v1 Jun 음성: 최초{total}자+부분수정{reserve}자, 포함크레딧최대{cap}, 추가결제0원. 자동재시도/충전/초과결제/새유료이미지·음악 제외.')
paid.update(revision='budget-v1-script-v1',artifacts={**artifacts,'narration/budget_proposal_v1.json':sha(e/'narration/budget_proposal_v1.json')},source_script_sha256=sha(w/'script_v1.md'),credit_cap=cap,cash_cap=0)
for d in [script,paid]:write(root/'output/video_decisions/decisions'/f"{d['id']}.json",d)
write(o/'review_decisions.json',{'script':script,'budget':paid})
d=read(e/'decisions.json');d['decisions'].extend([script,paid]);write(e/'decisions.json',d)
s=read(e/'state.json');s.update(stage='script_and_budget_review_pending',active_tasks=[],script_revision='script-v1',pending_gate='script_and_budget',pending_decision_ids={'script':script['id'],'budget':paid['id']},source_script_sha256=sha(w/'script_v1.md'),narration_characters=total,budget_credit_cap=cap,paid_generation_authorized=False,publication_authorized=False,render_started=False);write(e/'state.json',s)
p=read(e/'preflight.json');p['approvals']['script'].update(decision_id=script['id'],status='pending',artifact_hashes=artifacts);p['approvals']['budget'].update(decision_id=paid['id'],status='pending',credits_cap=cap,cash_cap=0);write(e/'preflight.json',p)
sc=read(w/'scene_proposals.json');write(e/'scenes.json',{'episode_id':e.name,'revision':'script-v1-proposal','status':'script_review_pending','timing_status':'estimated_not_locked','scenes':sc['scenes']})
print(json.dumps({'script_decision':script['id'],'budget_decision':paid['id'],'characters':total,'reserve':reserve,'cap':cap,'balance':a['included_remaining']},ensure_ascii=False))
