import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=read(ep/'state.json')
for gate,ident in s.get('pending_decision_ids',{}).items():
    p=root/'output/video_decisions/decisions'/f'{ident}.json'
    d=read(p)
    if d['status']=='pending':
        d.update(status='revision_requested',revision_source='direct_user_message_2026-10-16',
                 revision_scope='commute times, transport facts/hubs, price subscription stage and conditional comparison; script-v2 required')
        write(p,d)
s.update(stage='script_v2_research_and_revision',active_tasks=['commute_research_v3','price_stage_research_v3','script_v2'],
         pending_gate='script_and_budget_revised_artifacts',paid_generation_authorized=False,render_started=False)
s['production_request']='User requests revised script then video; prepare exact revised script and bounded budget before paid generation. Five gates preserved.'
write(ep/'state.json',s)
p=read(ep/'preflight.json')
for gate in ('script','budget'):p['approvals'][gate]['status']='revision_requested'
write(ep/'preflight.json',p)
print('Recorded revision scope; old pending script/budget no longer actionable.')
