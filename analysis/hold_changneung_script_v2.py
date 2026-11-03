import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import write,now
from notify.telegram import send
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
updates={}
for ident,status,answer in [('81cdb3c2a358','revision_requested','대본 추가 수정'),('fef620079862','rejected','유료 음성 보류')]:
    p=root/'output/video_decisions/decisions'/f'{ident}.json';d=read(p)
    assert d['episode']==ep.name
    d.update(status=status,response_source='direct_async_user_reply',response_text=answer,response_at=now().isoformat())
    if d['gate']=='budget':d['hold_scope']='No paid generation; no authorization inferred for subsequent revisions.'
    write(p,d);updates[ident]=d
dec=read(ep/'decisions.json')
for index,d in enumerate(dec['decisions']):
    if d.get('id') in updates:dec['decisions'][index]=updates[d['id']]
write(ep/'decisions.json',dec)
s=read(ep/'state.json');s.update(stage='script_v2_revision_requested_voice_on_hold',paid_generation_authorized=False,pending_gate='script_revision_feedback',active_tasks=[],render_started=False)
s['pending_decision_ids']={};s['voice_generation_hold']=True
write(ep/'state.json',s)
p=read(ep/'preflight.json');p['approvals']['script']['status']='revision_requested';p['approvals']['budget']['status']='on_hold_not_authorized';write(ep/'preflight.json',p)
sent=send('창릉 대본 v2 추가 수정·유료 음성 보류를 반영했습니다. 음성 생성/유료 호출/본편 렌더는 시작하지 않았습니다. 추가로 바꾸실 문단이나 방향을 이 대화에서 알려주시면 다음 대본에 반영하겠습니다. 무상으로 만든 지도·브랜드 소스는 보존합니다.')
write(ep/'outputs/script-review-v2/hold_receipt.json',{'script_status':'revision_requested','voice_on_hold':True,'generation_started':False,'telegram_notice_sent':sent})
print(json.dumps({'voice_on_hold':True,'telegram_notice_sent':sent}))
