"""Deliver only the reviewed local v6 video. No network, upload, or approval inference."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, subprocess, sys

D=Path(__file__).resolve().parent
E=D.parents[1]
R=E.parents[2]
P=E/'editor/top20-explain-v3/main/v2-bgm'
O=E/'outputs/top20-explain-v3'
Q=E/'qa/top20-explain-v3/production'
SHELF=R/'영상/신혼부부_지역별아파트'
sys.path.insert(0,str(R))
from notify.video_decisions import create,write

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def rel(p):return Path(p).relative_to(R).as_posix()
def stamp(t):
    ms=round(t*1000);hour,ms=divmod(ms,3600000);minute,ms=divmod(ms,60000);sec,ms=divmod(ms,1000)
    return f'{hour:02d}:{minute:02d}:{sec:02d},{ms:03d}'

def main():
    render=read(D/'render_receipt_v1.json')
    assert render['status']=='encoded_decode_passed_for_independent_QA' and render['full_decode_passed']
    video=Path(render['output']);assert sha(video)==render['output_sha256']
    assert read(D/'script_decision.json')['status']=='approved'
    review=read(Q/'final_media_review.json')
    assert review['status']=='passed' and review['required_open_count']==0
    assert review['checked_revision']['video_sha256']==render['output_sha256']
    assert not review['actual_listening_performed'] and not review['continuous_playback_performed']
    baseline=E/'outputs/top20-enhance-v2/main/top20_main_enhanced_v1.mp4'
    assert sha(baseline)=='12b2221c246c1a10fb6e2c92750fbb4ca4d40b2195b721bef0afa2ee56bf28f5'
    cfg_path=R/'config/video_shelf.json';cfg=read(cfg_path)
    entry=next(x for x in cfg['entries'] if x['name']=='신혼부부_지역별아파트')
    # Freeze the previous state/config before replacing only managed shelf links.
    for name,data in [('previous_episode_state.json',read(E/'state.json')),('previous_shelf_entry.json',entry.copy())]:
        if not (D/name).exists():write(D/name,data)
    O.mkdir(parents=True,exist_ok=True)
    cues=read(P/'caption_mapping.json')['cues']
    assert len(cues)==206
    previous_end=0
    rows=[]
    for i,cue in enumerate(cues,1):
        assert cue['start_s']>=previous_end-.002 and cue['end_s']>cue['start_s']
        previous_end=cue['end_s']
        rows.append(f"{i}\n{stamp(cue['start_s'])} --> {stamp(cue['end_s'])}\n{cue['text']}\n")
    captions=O/'자막_v6.srt';captions.write_text('\n'.join(rows),encoding='utf-8')
    script=SHELF/'수정안_v3/대본_v6.md';assert script.is_file()
    credits=read(P/'credits.json');music=read(P/'music_credit.json')
    lines=['# 신혼부부 TOP20 수정본 v3 출처','','통계 기준: 국가데이터처 「2024년 신혼부부통계」, 2024년 11월 1일 당시 수도권 53개 구.','- https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3','','가격 기준: 국토교통부 아파트 매매 실거래가. 2026년 5월 1일~10월 31일 계약, 11월 3일 조회, 전용 83~85㎡, 전체 층·직거래 포함, 명시적 해제 거래 제외. 10월 신고는 진행 중입니다.','- https://www.data.go.kr/data/15126468/openapi.do','','## 지역 자료사진과 지도','']
    for c in credits:
        lines.extend([f"### {c['region_id']} · {c.get('actual_place','지역 자료사진')}",'',c['full_attribution'],'',c.get('price_map_attribution',''),''])
    lines.extend(['## 음악','',music['credit'],music['url'],music['license_url'],'','편집: 반복·음량 조절·음성 대역 덕킹·브랜드 구간 페이드.'])
    sources=O/'출처_v6.md';sources.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    duration=float(render['probe']['format']['duration'])
    info=O/'완성본_안내.md'
    info.write_text('\n'.join(['# 신혼부부 TOP20 수정본 v3','','- 영상: 대본 v6 · 무료 InJoon 음성 · 1920×1080 · 30fps · 약 12분 17초.','- 지역 20곳의 특징·랜드마크, 실제 경계 지도, 지역 가격 중위값, 개별 단지 가격과 거래 건수를 연결했습니다.','- 금액은 설명하는 단어에 맞춰 나타나며, 출처 설명은 도입부에 모았습니다.','- 2024년 거주 통계와 2026년 5~10월 가격 자료의 시점을 구분했습니다.','','## 검수 범위','','- 최종 소스 124시점 검사: 글자 잘림·배치·실행 오류 0건.','- 실제 MP4 전체 디코딩 및 독립 표본 프레임·가격 전환·자막·브랜드 경계 검사. 세부 결과는 검수 JSON에 기록했습니다.','- 음성 25구간의 단어 경계·숫자·파형과 로컬 ASR을 대조했습니다. 실제 청취와 영상 전체 연속 재생은 수행하지 않았습니다.','','## 로컬 검토','','새 수정본은 로컬 확인용입니다. 기존 8분 48초 비공개본과 쇼츠는 보존했습니다.','기존 YouTube 비공개본: https://youtu.be/qu18qr0bIQw','새 버전의 제작 완료 확인과 최종 업로드 승인은 별도 단계입니다. 추가 유료 생성 0원, 외부 파일 전송 0건.','']) ,encoding='utf-8')
    timeline=read(P/'timeline_resolved.json')
    chapters=['','## 장면 목차','']
    for scene in timeline['scenes']:
        if scene['scene_id']=='E001':continue
        sec=int(scene['start_s']);chapters.append(f"- {sec//60:02d}:{sec%60:02d} {scene['title']}")
    with info.open('a',encoding='utf-8') as f:f.write('\n'.join(chapters)+'\n')
    artifact_paths=[video,captions,script,sources,Q/'final_media_review.json']
    artifacts=[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in artifact_paths]
    gate_path=D/'completed_decision.json'
    if gate_path.exists():
        gate=read(gate_path);assert gate['artifacts']==artifacts
    else:
        gate=create(E.name,'completed','신혼부부 TOP20 대본 v6 기반 약12분17초 로컬 완성본 검토. 지역20곳 특징·자료사진·지도·실거래가격, 무료 InJoon. 파일: 영상/신혼부부_지역별아파트/영상.mp4. 실제MP4 표본·기술검수 통과, 실제청취/연속재생 미실시. 제작완료 확인만이며 업로드/외부파일전송/유료생성 승인과 별개입니다.')
        gate.update(artifact_revision='top20-explain-v3/free-v1',artifacts=artifacts,scope='local completed artifact review only',cash_cap_krw=0,upload_authorized=False,file_export_authorized=False)
        write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate);write(gate_path,gate)
    entry['files'].update({'영상.mp4':rel(video),'자막.srt':rel(captions),'대본.md':rel(script),'출처.md':rel(sources),'완성본_안내.md':rel(info),'검수결과_v6.json':rel(Q/'final_media_review.json'),'이전_8분48초_비공개본.mp4':rel(baseline)})
    entry['status']='수정 v3 · 대본 v6 · 12분17초 무료 InJoon 로컬 검토본 / 기존 비공개본·쇼츠 보존'
    if entry.get('youtube_url'):entry['previous_youtube_url']=entry.pop('youtube_url')
    entry['active_local_revision']='top20-explain-v3/free-v1';entry['previous_youtube_url']='https://youtu.be/qu18qr0bIQw'
    write(cfg_path,cfg)
    result=subprocess.run([sys.executable,'-X','utf8',str(R/'tools/refresh_video_shelf.py')],cwd=R,capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0,result.stderr
    assert os.path.samefile(SHELF/'영상.mp4',video)
    state=read(E/'state.json')
    state.update(phase='awaiting_completed_v3_review',active_revision='top20-explain-v3',active_video=rel(video),active_video_sha256=render['output_sha256'],active_captions=rel(captions),active_completion=rel(O/'completion.json'),active_qa=rel(Q/'final_media_review.json'),pending_decision_id=gate['id'],active_publication_status='local_only_not_uploaded',active_upload_authorized=False,updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(completed='pending:'+gate['id'],pre_upload='not_requested_new_revision')
    write(E/'state.json',state)
    completion={'status':'local_video_delivered_awaiting_completed_review','revision':'top20-explain-v3/free-v1','duration_s':duration,'artifacts':artifacts,'completed_decision_id':gate['id'],'paid_calls':0,'cash_spent_krw':0,'external_file_transfers':0,'new_uploads':0,'baseline_preserved':True,'actual_listening_performed':False,'continuous_playback_performed':False,'shelf_video':rel(SHELF/'영상.mp4'),'qa_scope':review.get('review_scope',review.get('scope','encoded-media sampled-frame and technical checks'))}
    write(O/'completion.json',completion)
    manifest_path=SHELF/'수정안_v3/검토파일_명세.json'
    manifest=read(manifest_path)
    manifest.update(status=completion['status'],video=completion['shelf_video'],video_sha256=render['output_sha256'],duration_s=duration,completed_gate_id=gate['id'],file_delivery='local_files_only',telegram_files_sent=0)
    write(manifest_path,manifest)
    feedback_path=R/'output/telegram_conversation/inbox/718066312.json'
    feedback=read(feedback_path);assert feedback['application_status']=='applied'
    feedback.update(application_phase='feedback_implemented_local_v3_video_delivered',application_updated_at=datetime.now(timezone.utc).isoformat(),followup_completion=rel(O/'completion.json'))
    write(feedback_path,feedback)
    print(json.dumps({'status':completion['status'],'video':str(SHELF/'영상.mp4'),'duration_s':duration,'completed_decision_id':gate['id'],'baseline_preserved':True},ensure_ascii=False))

if __name__=='__main__':main()
