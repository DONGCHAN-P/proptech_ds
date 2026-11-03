"""Register scoped review gates after independent script QA. No paid API calls."""
from pathlib import Path
import hashlib,json,sys

e=Path(__file__).resolve().parent
repo=e.parents[2]
sys.path.insert(0,str(repo))
from notify.video_decisions import create

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')

folder=e/'outputs/story-review-v7'
assert not (folder/'approval_decisions.json').exists(), 'Already registered; reuse existing decisions'
sha=hashlib.sha256((folder/'script_v7.md').read_bytes()).hexdigest()
manifest=read(folder/'manifest.json')
assert manifest['source_script_sha256']==sha
assert manifest['unchanged_narration_verified']
budget=read(folder/'budget_proposal.json')
assert budget['source_script_sha256']==sha
assert budget['submitted_character_hard_cap']==budget['actual_credit_hard_cap']==1850
preflight=read(folder/'preflight.json')
assert preflight['passed'] and preflight['included_remaining']>=1850
# QA receipt is written by director from the independent review, scoped to this hash.
qa=read(folder/'qa_gate_receipt.json')
assert qa['script_sha256']==sha and qa['user_review_ready']
for ch in manifest['chapters']:
    assert hashlib.sha256((e/ch['path']).read_bytes()).hexdigest()==ch['sha256']
assert sum(ch['characters'] for ch in manifest['chapters'])==1541

script=create(e.name,'script',f'Approve script-v7-region-leaders: outputs/story-review-v7/script_v7.md SHA256 {sha}. Replace M008/M009 only; preserve preceding nine narration chapters. North Wangsuk1 B1/B2 jointly, south B17, Wangsuk2 A3 and conditional A1 competitor. Exclude newlywed-special housing; distinguish current trading from future ordinary resale after restrictions. Script approval only; no paid generation/publication.')
voice=create(e.name,'budget',f'Exact script SHA256 {sha}, M008/M009 inputs in outputs/story-review-v7/manifest.json. Jun/eleven_v4:1541 initial characters +309 correction reserve; both submitted-character and actual-credit hard caps1850. Fresh included balance31715; additional cash USD0. No automatic retries, topups, overage, new paid images, cloud rendering or upload. Requires separate matching script approval. Existing narration and brand clips reused.')
save(folder/'approval_decisions.json',{'script':script,'budget':voice,'script_sha256':sha})
budget.update(script_decision_id=script['id'],budget_decision_id=voice['id'])
save(folder/'budget_proposal.json',budget)
p=e/'decisions.json';d=read(p)
d['decisions'] += [{**script,'version':'script-v7-region-leaders'},{**voice,'version':'budget-v7-closing-only'}]
save(p,d)
p=e/'state.json';s=read(p)
s.update(stage='v14_visual_work_and_v7_closing_approval_pending',pending_gate='script_and_budget_separate',pending_decision_ids={'script':script['id'],'budget':voice['id']},script_review_path='outputs/story-review-v7/script_v7.md',script_review_sha256=sha,new_paid_generation_authorized=False,publication_authorized=False,active_tasks=['editor_locator_timeline_v14','qa_locator_timeline_v14'])
save(p,s)
print(json.dumps({'script':script['id'],'budget':voice['id'],'script_sha256':sha,'credit_cap':1850}))
