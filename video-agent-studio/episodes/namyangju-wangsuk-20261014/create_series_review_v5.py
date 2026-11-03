from pathlib import Path
import json,hashlib,sys
e=Path(__file__).resolve().parent;repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
out=e/'outputs/story-review-v5';m=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
h=hashlib.sha256((out/'script_v5.md').read_bytes()).hexdigest();assert h==m['script_sha256']
old=(e/'writer/map-led-v4/script_v4.md').read_text(encoding='utf-8')
new=(out/'script_v5.md').read_text(encoding='utf-8')
assert old.split('## M001 —',1)[1].rstrip()==new.split('## M001 —',1)[1].split('## v5 공통 편집 변경',1)[0].rstrip()
receipt=out/'approval_decisions.json'
if receipt.exists():d=json.loads(receipt.read_text(encoding='utf-8'));assert d['script_sha256']==h
else:
 script=create(e.name,'script',f'대본 v5 전편 연결·현재 왕숙→다음 창릉→그다음 교산 시리즈 예고. M000234자 교체, M001이후 원문·기존음성10개 동일. 전편5초인트로/10초아웃트로 재사용. Exactscript SHA256 {h}. 예산·완성본·업로드 승인 아님.')
 budget=create(e.name,'budget',f'Only new M000234chars SHA941013e3ea0f467a7aaed1d25aeea5de4a5c811ffb30488bb84c319be323ae58 for script SHA256 {h}: Jun/eleven_v4 initial234+correctionreserve47, submittedcharANDactualcredits hardcap281, includedbalance31809 checked, additionalcashUSD0. Noautomaticretry/overage/topup/newpaidimages/cloudrender. Existing10audiochapters/brandclips reused. Priorbudgetreservenottransferred. Requiresmatchingnewscriptapproval.')
 d={'script_sha256':h,'script_decision_id':script['id'],'budget_decision_id':budget['id']}
 for obj in [script,budget]:
  obj.update(version='script-v5-series-brand',source_script_sha256=h)
  write(repo/'output/video_decisions/decisions'/f"{obj['id']}.json",obj)
 common=json.loads((e/'decisions.json').read_text(encoding='utf-8'));common['decisions'] += [script,budget];write(e/'decisions.json',common)
 write(receipt,d)
s=json.loads((e/'state.json').read_text(encoding='utf-8'))
s.update(stage='v8_visual_ready_hook_v5_review',script_revision_target='script-v5-series-brand',
 pending_gate='script_and_budget',pending_decision_ids={'script':d['script_decision_id'],'budget':d['budget_decision_id']},
 new_paid_generation_authorized=False,full_render_waiting_for='new_hook_audio_and_brand_timing_lock')
write(e/'state.json',s)
print(json.dumps(d))
