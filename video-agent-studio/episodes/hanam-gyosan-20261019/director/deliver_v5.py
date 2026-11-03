from pathlib import Path
import json,hashlib,datetime
E=Path(__file__).resolve().parents[1];R=E.parents[2];O=E/'outputs/production-v5'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
q=read(E/'qa/review-v5-independent/report.json');assert q['required_unresolved']==0
t=read(O/'technical.json');v=O/'gyosan_review_v5_free_tts.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest();assert sha==t['sha256']==q['sha256']
(O/'개선검토.md').write_text('''# 교산 무료 TTS 검토본 v5

소제목은 ‘1. 일자리’, ‘2. 교통’, ‘3. 가격’, ‘4. 생활시설’, ‘5. 공급’, ‘6. 주변 시세’, ‘7. 대장 후보’처럼 번호와 주제만 표시했습니다. 도입·전체 계획·정리 제목도 짧게 바꿨습니다.

‘제가·저는’으로 시작하던 15개 문장을 채널이 주거·투자 가치의 비교 기준을 설명하는 중립적 표현으로 수정했습니다. 숫자·사실·후보 구성은 그대로입니다. 기존 지도·자료화면·모션·M009 실거래 차트 수정도 계승했습니다.

무료 음성은 기존 240구절을 재사용하고 21구절만 새로 생성했습니다. 전체 261구절, 18분 37.6초, 1920×1080, 30fps입니다.

독립 검수 보고서의 필수 미해결 0건을 확인했습니다. 검수는 대본 대조·기술 검사·변경 대상의 실제 MP4 표본 확인이며, 실제 청취와 전체 연속 재생은 미실시입니다. 상세 범위는 작업폴더/qa/review-v5-independent/report.md를 참조하세요.

기존 버전·승인 기록은 보존했습니다. 추가 유료 생성·업로드는 없습니다. 유튜브 비공개본은 이전 v1r3입니다.
''',encoding='utf8')
s=read(E/'state.json');s.update(stage='review_v5_ready',current_render=str(v.resolve()),current_render_sha256=sha,current_render_revision='v5-free-tts',video_path=v.relative_to(E).as_posix(),rendered_video_sha256=sha,actual_video_duration_seconds=1117.6,qa_review='qa/review-v5-independent/report.json',qa_sha256=hashlib.sha256((E/'qa/review-v5-independent/report.json').read_bytes()).hexdigest(),required_unresolved=0)
s['production_v5']={'status':'delivered_local_review','script_revision':'v5','video':v.relative_to(E).as_posix(),'video_sha256':sha,'required_unresolved':0,'paid_calls':0,'upload_performed':False,'actual_listening':False,'continuous_playback':False,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()};s['script_language_revision'].update(audio_reflected=True,video_reflected=True,render_revision='v5-free-tts');write(E/'state.json',s)
shelf=read(R/'config/video_shelf.json')
for e in shelf['entries']:
 if e['name']=='교산':
  e['status']='무료 TTS 검토본 v5 · 소제목 간결화·중립적 서술 반영 · 로컬 미게시 · YouTube는 v1r3'
  for k,x in {'영상.mp4':'outputs/production-v5/gyosan_review_v5_free_tts.mp4','자막.srt':'outputs/production-v5/gyosan_v5.srt','대본.md':'outputs/script-review-v5/script_v5.md','개선검토.md':'outputs/production-v5/개선검토.md','검토안내.md':'outputs/production-v5/개선검토.md'}.items():e['files'][k]=(E/x).relative_to(R).as_posix()
write(R/'config/video_shelf.json',shelf);print(json.dumps({'sha256':sha,'required_unresolved':0,'duration_s':1117.6,'paid_calls':0,'uploaded':False}))
