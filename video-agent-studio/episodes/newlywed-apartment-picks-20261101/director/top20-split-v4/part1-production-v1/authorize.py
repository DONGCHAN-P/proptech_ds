"""Apply the direct user request to part 1 only; preserve the other four gates."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, sys

D = Path(__file__).resolve().parent
E = D.parents[2]
R = E.parents[2]
sys.path.insert(0, str(R))
from notify.video_decisions import create, write

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(R).as_posix()

def main():
    receipt = D/'production_authorization.json'
    if receipt.exists():
        print(json.dumps({'status':'already_applied','receipt':rel(receipt)})); return
    source = E/'writer/top20-split-v4/scene_proposals_v2.json'
    script = R/'영상/신혼부부_지역별아파트/2부작_수정안/1편_20-11위_대본_v2.md'
    assert sha(source)=='5a2a098c23137d64fbc23fd861ca1eeff5a76554d397d22171dac54b091b8b3b'
    assert sha(script)=='9d62f607c352dfbd0dbe7306ff82290607bc10477723ab92ca7851e0379420c2'
    data=read(source); selected=copy.deepcopy([s for s in data['scenes'] if s['part']==1])
    assert len(selected)==12 and sum(len(s['sentences']) for s in selected)==85
    cursor=0; body=script.read_text(encoding='utf-8')
    for s in selected:
        for v in s['sentences']:
            pos=body.find(v['text'],cursor); assert pos>=cursor; cursor=pos+len(v['text'])
        s['approval_status']='approved_part1_only'
    gate=create(E.name,'script','1편 20~11위 대본 v2의 무료 InJoon 음성 및 로컬 영상 제작. 사용자의 직접 제작 요청으로 승인. 2편·유료 생성·외부 파일 전송·업로드 제외.')
    at=datetime.now(timezone.utc).isoformat()
    scope={'part':1,'scene_ids':[s['scene_id'] for s in selected], 'cash_cap_krw':0,
           'voice':'ko-KR-InJoonNeural','paid_generation_authorized':False,
           'part2_authorized':False,'external_file_export_authorized':False,'upload_authorized':False}
    gate.update(status='approved',approved_at=at,artifact_revision='top20-split-v4/part1-script-v2',
                source='direct_user_request',user_request='1편 대본부터 제작 시작해줘',
                artifacts=[{'path':rel(script),'sha256':sha(script)}],scope=scope,
                source_scene_json_sha256=sha(source))
    write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate)
    write(D/'script_approval.json',gate)
    derivative=copy.deepcopy(data)
    derivative.update(revision='top20-split-v4/part1-production-v1',scenes=selected,
                      source_scene_json=rel(source),source_scene_json_sha256=sha(source),
                      approval={'status':'approved','decision_id':gate['id'],'scope':scope},
                      narration_handoff={'part':1,'source':'approved_part1_scene_proposals.json','sentence_count':85,'free_voice_only':True})
    out=D/'approved_part1_scene_proposals.json';write(out,derivative)
    auth={'status':'approved','applied_at':at,'user_request':'1편 대본부터 제작 시작해줘',
          'decision_id':gate['id'],'scope':scope,'script_md':rel(script),'script_md_sha256':sha(script),
          'scene_json':rel(out),'scene_json_sha256':sha(out),
          'approval_gates_preserved':['topic','script','budget','completed','pre_upload']}
    write(receipt,auth)
    part2=create(E.name,'script','2편 10~1위 대본 v2 검토 대기. 1편 제작 요청은 2편 승인에 적용하지 않습니다.')
    p2=R/'영상/신혼부부_지역별아파트/2부작_수정안/2편_10-1위_대본_v2.md'
    part2.update(artifact_revision='top20-split-v4/part2-script-v2',part=2,
                 artifacts=[{'path':rel(p2),'sha256':sha(p2)}],cash_cap_krw=0,
                 paid_generation_authorized=False,upload_authorized=False)
    write(R/'output/video_decisions/decisions'/f"{part2['id']}.json",part2)
    write(D.parent/'part2_script_decision.json',part2)
    for p in [R/'output/video_decisions/decisions/80ac87b7f114.json',D.parent/'script_decision.json']:
        old=read(p); old.update(status='superseded_by_scoped_part_decisions',resolved_at=at,
                               scoped_part1_approved=gate['id'],scoped_part2_pending=part2['id'])
        write(p,old)
    state=read(E/'state.json')
    state.update(phase='part1_production',active_revision='top20-split-v4',active_part=1,
                 active_production_revision='part1-production-v1',
                 active_script=out.relative_to(E).as_posix(),active_script_sha256=sha(out),
                 script_approval_receipt=(D/'script_approval.json').relative_to(E).as_posix(),
                 production_authorization=receipt.relative_to(E).as_posix(),
                 active_timing_status='unlocked_pending_actual_part1_audio',
                 active_voice_choice='free_InJoon',active_upload_authorized=False,
                 pending_decision_id=None,part2_pending_decision_id=part2['id'],
                 active_parts=[{'part':1,'ranks':list(range(20,10,-1)),'status':'in_production','script_decision_id':gate['id']},
                               {'part':2,'ranks':list(range(10,0,-1)),'status':'script_approval_pending','script_decision_id':part2['id']}],
                 updated_at=at)
    state.setdefault('active_approval_status',{}).update(script='approved_part1:'+gate['id'],budget='free_only_cash_0',completed='not_reached_part1',pre_upload='not_reached_part1')
    pre=read(D.parent/'episode_preflight.json');pre.update(status='part1_script_approved_production_started',part=1)
    pre['approvals']['script'].update(status='approved',decision_id=gate['id'])
    pre['approvals']['budget'].update(status='free_only',cash_cap=0)
    write(D/'episode_preflight.json',pre);state['active_preflight']=(D/'episode_preflight.json').relative_to(E).as_posix()
    write(E/'state.json',state)
    print(json.dumps({'part1_approved':gate['id'],'part2_pending':part2['id'],'scenes':12,'sentences':85,'cash_cap_krw':0,'source':rel(out)},ensure_ascii=False))

if __name__=='__main__': main()
