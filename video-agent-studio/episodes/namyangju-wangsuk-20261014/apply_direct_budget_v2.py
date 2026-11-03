from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
e=Path(__file__).resolve().parent;repo=e.parents[2];digest=hashlib.sha256((e/'outputs/story-review-v4/script_v4.md').read_bytes()).hexdigest()
assert digest=='d816c5ba4341ddaafd4f3f3db6585873a519e1577d865dbf332d183925d4c2da'
receipt={'source':'direct_user_async_question_reply','question_call':'call_e4a41e8e6a7e452ca6d4e6c230ee5b16','answers':{'script':'대본 v4 확정','budget':'음성 제작 예산 승인'},'source_script_sha256':digest,'scope':{'credit_cap':8255,'initial_characters':6879,'correction_reserve':1376,'additional_cash_usd_cap':0,'automatic_retry':False,'overage_topup_paid_images':False},'recorded_at':datetime.now(timezone.utc).isoformat()}
(e/'outputs/story-review-v4/direct_approval_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
for ident,gate in [('553d76e214f6','script'),('f86d1138e110','budget')]:
 p=repo/f'output/video_decisions/decisions/{ident}.json';d=json.loads(p.read_text(encoding='utf-8'));assert d['episode']==e.name and d['gate']==gate and digest in d['summary'];assert d['status'] in ('pending','approved')
 d['status']='approved';d['direct_user_confirmation']=receipt;p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');(e/f'outputs/story-review-v4/{gate}_decision.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'narration/budget_proposal_v2.json';b=json.loads(p.read_text(encoding='utf-8'));assert b['source_script_sha256']==digest and b['actual_credit_hard_cap']==8255;b['generation_authorized']=True;b['approval_basis']='outputs/story-review-v4/direct_approval_receipt.json';p.write_text(json.dumps(b,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='approved_new_voice_generation',script_approved=True,budget_approved=True,new_paid_generation_authorized=True,pending_gate=None,pending_decision_ids={},active_tasks=['narration_audio_v2','editor_map_led_v6'],budget_approval_decision='f86d1138e110',script_approval_decision='553d76e214f6');p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'decisions.json';s=json.loads(p.read_text(encoding='utf-8'))
for d in s['decisions']:
 if d.get('id',d.get('decision_id')) in ('553d76e214f6','f86d1138e110'):d['status']='approved';d['direct_user_confirmation']=receipt
p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'script_approved':True,'budget_approved':True,'credit_cap':8255,'additional_cash_usd_cap':0,'publication_authorized':False}))
