"""Freeze review files and create only the scoped script gate; never send/upload."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys

D=Path(__file__).resolve().parent; E=D.parents[1]; R=E.parents[2]
sys.path.insert(0,str(R))
from notify.video_decisions import create,write
W=E/'writer/top20-explain-v3'; OUT=R/'영상/신혼부부_지역별아파트/수정안_v3'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    script_sha='4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38'
    scene_sha='8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e'
    assert sha(W/'script_v6.md')==script_sha and sha(W/'scene_proposals_v6.json')==scene_sha
    review=read(E/'qa/top20-explain-v3/independent-review/script_review.json')
    assert review['status']=='passed' and review['checked_revision']['scene_json_sha256']==scene_sha
    assert review['counts']['sentences']==133 and not review['failed_checks']
    spec_review=read(E/'qa/top20-explain-v3/independent-review/spec_final_review.json')
    assert spec_review['status']=='passed' and spec_review['checked_revision']['scene_json_sha256']==scene_sha
    assert spec_review['required_open_count']==0
    narration=[t['text'] for s in read(W/'scene_proposals_v6.json')['scenes']for t in s.get('sentences',[])]
    body=(OUT/'대본_v6.md').read_text(encoding='utf-8'); cursor=0
    for sentence in narration:
        at=body.find(sentence,cursor); assert at>=cursor,sentence; cursor=at+len(sentence)
    files=[OUT/name for name in ['대본_v6.md','지역별_가격기준표.md','대표화면.jpg','반영내역.md']]
    assert all(p.exists() and p.stat().st_size>500 for p in files)
    baseline=E/'outputs/top20-enhance-v2/main/top20_main_enhanced_v1.mp4'
    assert sha(baseline)=='12b2221c246c1a10fb6e2c92750fbb4ca4d40b2195b721bef0afa2ee56bf28f5'
    artifact_rows=[{'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in files]
    decision_path=D/'script_decision.json'
    if decision_path.exists():
        decision=read(decision_path)
        assert decision['scene_sha256']==scene_sha and decision['artifacts']==artifact_rows
    else:
        summary='신혼부부 TOP20 수정 대본 v6 승인:20지역 특징·랜드마크·지역중위값·단지사례,합니다체,출처도입1회,2024통계 한계와2026가격기간 구분. 무료 InJoon·현금0원 유지. 대본 내용 승인만 요청하며 새 유료생성/공개전환/업로드/기존본삭제를 승인하지 않습니다. 검토폴더:영상/신혼부부_지역별아파트/수정안_v3. production MD SHA='+script_sha+';scene JSON SHA='+scene_sha
        gate=create(E.name,'script',summary)
        gate.update(artifact_revision='top20-explain-v3/script-v6',script_md_sha256=script_sha,scene_json_sha256=scene_sha,
                    artifacts=artifact_rows,scope='script content v6 only; free voice preference remains; completed/pre_upload remain separate',
                    budget={'provider_choice':'free Edge InJoon','cash_cap_krw':0,'paid_generation_authorized':False})
        write(R/'output/video_decisions/decisions'/f'{gate["id"]}.json',gate)
        decision={'id':gate['id'],'gate':'script','status':'pending','scene_sha256':scene_sha,'script_sha256':script_sha,
                  'artifacts':artifact_rows,'spec_scope':'static representative prototype, provisional timings; no audio/full MP4',
                  'created_at':datetime.now(timezone.utc).isoformat()}
        write(decision_path,decision)
    state=read(E/'state.json')
    state.update(phase='awaiting_script_v6_approval',active_revision='top20-explain-v3',pending_decision_id=decision['id'],
                 active_script='writer/top20-explain-v3/script_v6.md',active_script_sha256=script_sha,
                 active_review_folder=OUT.relative_to(R).as_posix(),active_approval_status={
                     'topic':'existing_TOP20_scope_retained','script':'pending:'+decision['id'],
                     'budget':'free_only_cash_cap_0_krw','completed':'not_reached_new_revision','pre_upload':'not_reached_new_revision'},
                 updated_at=datetime.now(timezone.utc).isoformat())
    write(E/'state.json',state)
    event=R/'output/telegram_conversation/inbox/718066312.json'; inbox=read(event)
    assert inbox['application_status']=='applied'
    inbox.update(application_phase='awaiting_script_v6_approval',application_updated_at=datetime.now(timezone.utc).isoformat(),
                 application_result={'script_gate_id':decision['id'],'review_folder':OUT.relative_to(R).as_posix(),
                                     'research_and_script_prepared':True,'new_tts_generated':False,'full_video_rendered':False,'uploaded':False},
                 application_note='다섯 수정 요구를 자료·수정 대본v6·실값 지도 대표시안에 반영. 새 대본 승인 대기이며 기존 비공개본 보존. 새 음성·본편·업로드는 아직 실행하지 않음.')
    write(event,inbox)
    write(OUT/'검토파일_명세.json',{'status':'script_review_ready_approval_pending',**decision,
          'verification_scope':'133 written sentences and static representative prototype; no actual listening or MP4 playback',
          'budget_cash_cap_krw':0,'baseline_preserved_sha256':sha(baseline)})
    print(json.dumps({'script_gate_id':decision['id'],'files':len(files),'sentences':len(narration),'cash_cap_krw':0,
                      'phase':'awaiting_script_v6_approval','baseline_preserved':True},ensure_ascii=False))

if __name__=='__main__':main()
