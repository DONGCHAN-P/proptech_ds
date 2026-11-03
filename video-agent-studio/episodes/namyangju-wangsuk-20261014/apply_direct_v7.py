from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
e=Path(__file__).resolve().parent;repo=e.parents[2];f=e/'outputs/story-review-v7'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
d=read(f/'approval_decisions.json');sha=hashlib.sha256((f/'script_v7.md').read_bytes()).hexdigest()
assert sha==d['script_sha256']=='6ce6fefb6cbd439b7073091a0107ec65261ba8638aeeb0f339369c0e68640737'
receipt={'source':'direct_user_async_question_reply','question_call':'call_a855c2dee0654fda8ab4f802583d1d63','answers':{'script':'대본 v7 확정','budget':'v7 음성 예산 승인'},'script_sha256':sha,'recorded_at':datetime.now(timezone.utc).isoformat(),'scope':{'scene_ids':['M008','M009'],'initial_characters':1541,'reserve':309,'submitted_character_hard_cap':1850,'actual_credit_hard_cap':1850,'additional_cash_usd_cap':0,'automatic_retry':False,'topup_overage_paid_images':False}}
save(f/'direct_approval_receipt.json',receipt)
for gate,ident in [('script','d6a6098a1cac'),('budget','a1112eba6e2c')]:
 p=repo/f'output/video_decisions/decisions/{ident}.json';x=read(p)
 assert x['episode']==e.name and x['gate']==gate and sha in x['summary'] and x['status'] in ['pending','approved']
 x.update(status='approved',direct_user_confirmation=receipt);save(p,x);d[gate]=x
save(f/'approval_decisions.json',d)
b=read(f/'budget_proposal.json');assert b['source_script_sha256']==sha
b.update(generation_authorized=True,approval_basis='outputs/story-review-v7/direct_approval_receipt.json');save(f/'budget_proposal.json',b)
p=e/'decisions.json';c=read(p)
for x in c['decisions']:
 if x.get('id') in ['d6a6098a1cac','a1112eba6e2c']:x.update(status='approved',direct_user_confirmation=receipt)
save(p,c)
p=e/'state.json';s=read(p)
s.update(stage='v14_approved_closing_voice_and_visual_production',script_revision='script-v7-region-leaders',script_path='outputs/story-review-v7/script_v7.md',script_sha256=sha,script_approved=True,budget_approved=True,script_approval_decision='d6a6098a1cac',budget_approval_decision='a1112eba6e2c',new_paid_generation_authorized=True,pending_gate=None,pending_decision_ids={},publication_authorized=False)
save(p,s)
o=e/'narration/region-leaders-v7';o.mkdir(exist_ok=True)
save(o/'authorization.json',{'root_execution_authorized':True,'script_decision_id':'d6a6098a1cac','budget_decision_id':'a1112eba6e2c','source_script_path':'outputs/story-review-v7/script_v7.md','source_script_sha256':sha,'budget_proposal_path':'outputs/story-review-v7/budget_proposal.json','submitted_character_hard_cap':1850,'actual_credit_hard_cap':1850,'additional_cash_usd_cap':0,'automatic_retry':False})
print('Exact v7 script and1850-credit/cash0 voice scope approved; completed/pre_upload remain unapproved.')
