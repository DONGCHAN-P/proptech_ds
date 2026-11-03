"""Record accepted local edit and a new pending ElevenLabs credit cap."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,sys
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2];N=E/'narration/top20-split-v4/jun-and-shorts-v1'
sys.path.insert(0,str(R))
from notify.video_decisions import create,write
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    m=read(N/'narration_manifest.json');a=read(N/'account_readonly.json');assert a['status']=='read_only_queries_succeeded'
    f=a['model']['model_rates'];rate=f['character_cost_multiplier']*f['cost_discount_multiplier']*a['voice']['sharing']['rate'];assert rate==1
    sub=a['subscription'];assert sub['included_remaining']>=6500
    assert sub.get('can_extend_character_limit')is False and sub.get('allowed_to_extend_character_limit')is False
    assert sub.get('max_credit_limit_extension',sub.get('max_character_limit_extension'))==0
    expected=math.ceil(m['input_characters_to_send']*rate)
    assert expected==5520
    budget={'revision':'jun-and-shorts-v1','status':'pending_credit_cap_approval','provider':'ElevenLabs','voice_name':'Jun - Clear Korean Lecturer',
            'model':a['model']['model_id'],'input_characters':m['input_characters_to_send'],'planned_requests':len(m['chunks']),
            'estimated_first_pass_credits':expected,'included_credit_cap_proposed':6500,'correction_headroom':6500-expected,
            'included_remaining':sub['included_remaining'],'account_snapshot_sha256':sha(N/'account_readonly.json'),
            'manifest_sha256':sha(N/'narration_manifest.json'),'main_sentences':90,'shared_shorts_CTA_sentences':2,
            'shorts_count':3,'shorts_body_voice_reused':True,'additional_cash_cap_krw':0,'top_up_authorized':False,
            'overage_disabled':True,'automatic_retry':False,'generation_authorized':False,'tts_post_calls':0}
    write(D/'budget_proposal.json',budget)
    gatepath=D/'budget_decision.json'
    if gatepath.exists():gate=read(gatepath)
    else:
        gate=create(E.name,'budget','1편 Jun 본편90문장+3개쇼츠공통CTA2문장:5520자/예상5520크레딧,수정여유포함상한6500.잔여16664.추가결제·충전0원,자동재시도없음.쇼츠본문은본편음성재사용.')
        gate.update(part=1,artifact_revision='top20-split-v4/jun-and-shorts-v1',
                    artifacts=[{'path':str(p.relative_to(R)).replace('\\','/'),'sha256':sha(p)}for p in [D/'budget_proposal.json',N/'narration_manifest.json']],
                    proposed_credit_cap=6500,additional_cash_cap_krw=0,top_up_authorized=False,upload_authorized=False,part2_production_authorized=False)
        write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate);write(gatepath,gate)
    state=read(E/'state.json');oldid='3136b4ba6c9d';path=R/'output/video_decisions/decisions'/f'{oldid}.json';old=read(path)
    assert old['video_sha256']==m['source_video_sha256']
    old.update(status='approved',approval_basis='direct_user_오케이_이걸로_일레븐랩스_적용',accepted_at=datetime.now(timezone.utc).isoformat(),
               scope_note='Accepts map-clean-v1 local completed artifact and requests Jun replacement. New generation cap and uploads remain separately scoped.')
    write(path,old);write(E/'director/top20-split-v4/part1-map-clean-v1/completed_decision_v1.json',old)
    state.update(phase='part1_jun_credit_cap_pending_shorts_preparation',pending_decision_id=gate['id'],
                 active_requested_voice='ElevenLabs Jun',active_requested_shorts_count=3,
                 active_requested_short_groups=[[20,19,18,17,16],[15,14,13,12,11]],
                 jun_budget_proposal=str((D/'budget_proposal.json').relative_to(E)).replace('\\','/'),
                 updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(budget='pending:'+gate['id'],completed='map_clean_v1_approved:'+oldid,pre_upload='not_reached_jun_v1')
    write(E/'state.json',state)
    scope=read(D/'request_scope.json');scope['user_request']='현재 수정본에 ElevenLabs Jun 적용. 홍보용1편과 내용20~16위/15~11위2편, 끝에다른순위영상유도.';write(D/'request_scope.json',scope)
    print(json.dumps({'status':'budget_pending','decision_id':gate['id'],'expected_credits':expected,'cap':6500,'remaining':sub['included_remaining'],'tts_post_calls':0},ensure_ascii=False))
if __name__=='__main__':main()
