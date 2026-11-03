"""Deliver one accepted-main Jun replacement and three Shorts, locally only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2];N=E/'narration/top20-split-v4/jun-and-shorts-v1'
sys.path.insert(0,str(R))
from notify.video_decisions import create,write
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).resolve().relative_to(R).as_posix()
erel=lambda p:Path(p).resolve().relative_to(E).as_posix()
def main():
    a=read(D/'production_authorization.json');g=read(D/'budget_decision.json');assert g['status']=='approved'and a['included_credit_cap']==6500
    assert sha(N/'narration_manifest.json')==a['manifest_sha256'];usage=read(N/'generation_ledger.json');assert usage['actual_credits']==usage['observed_account_delta']==2208<=6500
    assert usage['automatic_retries']==usage['topup_calls']==usage['cash_spent_krw']==0
    release=read(D/'release_manifest.json');assert len(release['assets'])==4
    records=[]
    for item in release['assets']:
        v=R/item['video'];assert sha(v)==item['video_sha256'];q=read(R/item['qa'])
        assert q['status']in['passed','passed_for_local_review','bounded_review_passed']
        assert q['required_open_count']==q['critical_open_count']==0
        assert q['video_sha256']==item['video_sha256'],item['id']
        evidence=read(R/item['encoded_manifest']);assert evidence['video_sha256']==item['video_sha256']and evidence['status']=='passed'
        lock=read(R/item['timing']);assert sha(lock['master_audio'])==lock['master_audio_sha256']
        assert evidence['minimum_audio_correlation']>.97
        if item['id']!='main':assert evidence['probe']['streams'][0]['width']==1080
        records.append(dict(item,bytes=v.stat().st_size,qa_status=q['status'],required=0,critical=0))
    byid={x['id']:x for x in records};assert set(byid)=={'main','SHORT01-PROMO','SHORT02-R20-R16','SHORT03-R15-R11'}
    previews=read(D/'previews.json');assert previews['source_video_sha256']==byid['main']['video_sha256']
    for key in ['intro','changes']:assert sha(previews[key]['path'])==previews[key]['sha256']
    out=E/'outputs/top20-split-v4/jun-and-shorts-v1';out.mkdir(parents=True,exist_ok=True)
    credits=out/'출처와크레딧.md';previous=E/'outputs/top20-split-v4/map-clean-v1/출처_지도정리와사진전환.md'
    credits.write_text(previous.read_text(encoding='utf-8')+'\n## Jun 본편과 쇼츠 3편\n\n내레이션: ElevenLabs Jun. 본편의 동일한 발화를 쇼츠에서 재사용하고, 공통 연결 안내 2문장을 한 번 생성해 세 편에 사용했습니다. 각 쇼츠의 원문·집계·사진 출처는 writer/top20-split-v4/jun-and-shorts-v1/source_manifest.json 및 director의 shorts_visual_facts.json에 기록했습니다.\n\n쇼츠 가격 비교는 동별·준공군의 거래 중위값입니다. 남동구는 지도에 연결된 77개 단지의 단지별 중위가격 구간 분포(61/16단지)입니다.\n',encoding='utf-8')
    notes=out/'검토안내.md'
    text=['# 신혼부부가 사는 곳 · 1편 Jun 본편과 쇼츠 3편','',
          '사용자가 확인한 지도 하단 정리·지역 대표 사진 전환을 유지하고, 본편 전체에 ElevenLabs Jun을 적용했습니다. 실제 새 음성의 문장·숫자·장소 시각에 맞춰 화면과 자막을 다시 배치했습니다.','',
          '## 파일','',
          '- `영상.mp4`: 20~11위 Jun 본편 · 11분22초 · 1920×1080 · 30fps.',
          '- `홍보용_쇼츠.mp4`: 지역 선정 취지와 연수구의 가격 대비를 보여주는 홍보용 · 40초.',
          '- `순위_20-16위_쇼츠.mp4`: 원미·중랑·기흥·연수·남동 다섯 지역의 순위·쌍 수·가격 비교 · 1분16초.',
          '- `순위_15-11위_쇼츠.mp4`: 구로·은평·권선·영통·노원 다섯 지역의 순위·쌍 수·가격 비교 · 1분13초.',
          '- `이전_검토본.mp4`: 직전 10분15초 무료 음성 검토본.',
          '- `인트로_미리보기.mp4` · `수정구간_미리보기.mp4`: 현재 Jun 버전으로 갱신한 도입/지역 진입 모음.',
          '- `자막.srt` 및 각 쇼츠 자막: Jun 실제 시각으로 맞춘 의미 단위 자막.','',
          '## 제작·검수 범위','',
          '- 본편 90문장과 쇼츠 공통 안내 2문장을 생성했습니다. 쇼츠에서 쓰인 나머지 문장은 본편 음성을 재사용했습니다.',
          '- 본편 화면은 승인된 전체 구도를 유지하고 실제 발화·숫자·장소 앵커로 시간을 조정했습니다. 본편과 쇼츠 모두 실제 자막 큐에만 박스를 표시해 문장 사이의 쉼과 마지막 여백의 빈 박스를 정리했습니다.',
          '- 쇼츠는 1080×1920 세로 화면으로 별도 구성했습니다. `youtube_portrait_full_frame_v2` 프로필의 글자 경계·최소 크기·앱 UI 모사를 검수했습니다. 가격의 계약·조회 기준을 표시하고 불필요한 회피 문구는 제거했습니다.',
          '- 각 지역의 소개와 가격 설명을 완결된 문장으로 추출하고 앞뒤 실제 제공자 발화 경계와 여백을 대조했습니다. 마지막 발화 뒤 1.05초를 확보했습니다.',
          '- 네 실제 MP4의 표본 프레임·전체 디코드·프레임 수·해상도와 최종 오디오 신호를 마스터와 대조했습니다. 독립 검수에서 필수·치명 수정은 0건입니다.',
          '- 새 Jun의 숫자·지명을 로컬 ASR로 보조 검토했습니다. 실제 청취와 전 구간 연속 재생, Claude 외부 검수는 수행하지 않았습니다. 표본·ASR·신호 검사는 그 범위로 기록했습니다.','',
          '## 크레딧','',
          '- 승인 상한: 포함 크레딧 6,500. 실제 사용: 2,208. 추가 결제·충전·자동 재시도: 0.',
          '- 새 안내 멘트 2문장은 한 번만 생성해 쇼츠 세 편에 재사용했습니다.','',
          '## 확인 상태','',
          '이 결과는 본편 1편과 쇼츠 3편의 새 로컬 completed 확인 단계입니다. 유튜브 업로드·게시 전환·2편 제작은 별도 상태로 유지했습니다. 쇼츠에 안내한 다른 순위 영상은 함께 만든 20~16위/15~11위 편이며, 본편의 소개 범위는 20~11위 10개 지역입니다.','',
          '## 파일 검증','']
    for x in records:text +=[f"- {x['id']} · {x['duration_s']:.3f}초 · SHA256 `{x['video_sha256']}`"]
    notes.write_text('\n'.join(text)+'\n',encoding='utf-8')
    pack={'status':'passed_for_local_review','revision':'jun-and-shorts-v1','video_sha256':byid['main']['video_sha256'],
          'required_open_count':0,'critical_open_count':0,'media':records,'actual_listening':False,'continuous_playback':False,
          'scope':'Four exact encoded artifacts with individual independent reports, measured layout and sampled frame/signal review'}
    write(D/'bundle_review_index.json',pack)
    gatepath=D/'completed_decision.json';artifacts=[R/x['video']for x in records]+[R/x['qa']for x in records]+[notes,credits,D/'release_manifest.json',D/'captions.srt']
    if gatepath.exists():gate=read(gatepath);assert gate['main_video_sha256']==byid['main']['video_sha256']
    else:
        gate=create(E.name,'completed','Jun 본편11분22초와 홍보용40초·20→16위76초·15→11위73초 쇼츠3편의 로컬 검토본. 실제MP4표본·문장끝·안전영역·디코드·신호 및 독립 검수에서 필수·치명0건. 실제청취·연속재생은 미수행. 사용2208/상한6500크레딧,추가결제0원. 업로드는별도.')
        gate.update(part=1,artifact_revision='top20-split-v4/jun-and-shorts-v1',main_video_sha256=byid['main']['video_sha256'],
                    artifacts=[{'path':rel(p),'sha256':sha(p)}for p in artifacts],actual_credits=2208,credit_cap=6500,
                    additional_cash_cap_krw=0,upload_authorized=False,part2_production_authorized=False)
        write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate);write(gatepath,gate)
    state=read(E/'state.json');main=byid['main'];timing=read(D/'locked_timing.json')
    state.update(phase='awaiting_part1_Jun_and_three_shorts_completed_review',active_production_revision='jun-and-shorts-v1',
                 active_video=erel(R/main['video']),active_video_sha256=main['video_sha256'],active_voice_choice='ElevenLabs Jun',
                 active_audio=erel(timing['master_audio']),active_audio_sha256=timing['master_audio_sha256'],active_timing=erel(D/'locked_timing.json'),
                 active_measured_duration_s=timing['total_s'],active_captions=erel(D/'captions.srt'),active_source_project=erel(R/main['project']),
                 active_render_receipt=erel(R/main['editor_receipt']),active_qa=erel(D/'bundle_review_index.json'),active_completion=erel(gatepath),
                 active_shorts=[{**x,'video':erel(R/x['video']),'qa':erel(R/x['qa'])}for x in records if x['id']!='main'],
                 active_publication_status='local_only_not_uploaded',active_upload_authorized=False,pending_decision_id=gate['id'],
                 active_review_folder='영상/신혼부부_TOP20_1편',jun_actual_credits=2208,
                 actual_listening_performed=False,continuous_playback_performed=False,updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(completed='pending:'+gate['id'],pre_upload='not_reached_jun_v1')
    state['active_parts'][0].update(status='Jun_main_and3shorts_local_review_ready',video=state['active_video'],completed_decision_id=gate['id'])
    write(E/'state.json',state)
    cfg=read(R/'config/video_shelf.json');entry=next(x for x in cfg['entries']if x['name']=='신혼부부_TOP20_1편');reader=read(N/'narration_manifest.json')['main_reader_script']
    files={'영상.mp4':main['video'],'홍보용_쇼츠.mp4':byid['SHORT01-PROMO']['video'],'순위_20-16위_쇼츠.mp4':byid['SHORT02-R20-R16']['video'],
           '순위_15-11위_쇼츠.mp4':byid['SHORT03-R15-R11']['video'],'자막.srt':rel(D/'captions.srt'),
           '홍보용_자막.srt':rel(D/'shorts/SHORT01-PROMO/captions.srt'),'순위_20-16위_자막.srt':rel(D/'shorts/SHORT02-R20-R16/captions.srt'),
           '순위_15-11위_자막.srt':rel(D/'shorts/SHORT03-R15-R11/captions.srt'),'대본.md':reader,
           '쇼츠_구성안.md':rel(E/'writer/top20-split-v4/jun-and-shorts-v1/shorts_plan.md'),'출처.md':rel(credits),'검토안내.md':rel(notes),
           '검수결과.json':rel(D/'bundle_review_index.json'),'이전_검토본.mp4':read(D/'baseline_state.json')['active_video'],
           '인트로_미리보기.mp4':rel(previews['intro']['path']),'수정구간_미리보기.mp4':rel(previews['changes']['path'])}
    # baseline_state paths are episode-relative; all shelf targets are workspace-relative.
    files['이전_검토본.mp4']=rel(E/files['이전_검토본.mp4'])
    entry.update(status='20~11위 · Jun 본편11분22초 + 홍보·순위 쇼츠3편 · 로컬 검토용',active_local_revision='top20-split-v4/jun-and-shorts-v1',files=files)
    write(R/'config/video_shelf.json',cfg)
    delivery={'status':'local_review_ready','assets':records,'shelf':'영상/신혼부부_TOP20_1편','completed_decision_id':gate['id'],
              'actual_credits':2208,'credit_cap':6500,'cash_cost_krw':0,'uploads':0,'actual_listening':False,'continuous_playback':False}
    write(D/'delivery.json',delivery);print(json.dumps({'status':delivery['status'],'videos':len(records),'shelf':delivery['shelf'],'credits':2208,'completed_decision':gate['id']},ensure_ascii=False))
if __name__=='__main__':main()
