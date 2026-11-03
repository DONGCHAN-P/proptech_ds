from pathlib import Path
import json,hashlib,datetime
E=Path(__file__).resolve().parents[1];R=E.parents[2];O=E/'outputs/production-v4'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
q=read(E/'qa/review-v4-independent/report.json')
assert q['required_unresolved']==0 and q['critical_unresolved']==0
v=E/q['video'];sha=hashlib.sha256(v.read_bytes()).hexdigest();assert sha==q['sha256']
t=read(O/'technical_v4r1.json');assert t['sha256']==sha
report='''# 교산 무료 TTS 검토본 v4r1

대본 v4와 장면별 자료화면 설계를 반영했습니다. 길이 18분 44.37초, 1920×1080, 30fps입니다.

- 무료 Microsoft Heami 음성을 새로 생성하고 263개 의미 단위 자막을 맞췄습니다.
- AI 클러스터 참여계획·기능·사업기간, 자족7 지정 추진, 캠프콜번 개발 계획을 반영했습니다.
- 주변 시설은 공식 주소의 VWorld 좌표와 실제 OSM 도로를 사용합니다. 주소 대표점이며 사업경계·출입구·계산된 도보경로는 아닙니다.
- 지도·노선·원문 가격표·비용 누적·일정·면적·실거래 비교 자료화면을 사용합니다. M008 대장 후보의 기존 상세 토지계획도 구성은 유지했습니다.
- 인트로·아웃트로·BGM과 마지막 발화 뒤 3초 여유를 계승했습니다.
- 독립 검수의 필수 수정 2건(줄바꿈 문자 노출, 요약 실거래 화면 불일치)을 수정하고 재검수했습니다. 현재 필수 미해결 0건입니다.

## 검수 범위

전체 디코딩·음성 PCM 유효성·대본 재결합·자막 시간과 실제 MP4 표본 프레임을 검사했습니다. 독립 QA는 v4 85개 표본과 v4r1 변경 구절·앞뒤 프레임을 직접 확인했습니다. 정확한 프레임 번호와 seek 추출의 대응에는 도구 제약이 있습니다. 실제 청취·전체 연속 재생·발음 자연스러움 검수는 미실시입니다. 모션의 추가 검사 범위는 같은 폴더의 motion_verification.json이 존재할 경우 그 기록을 참조합니다.

기존 영상·원본·승인 기록은 보존했습니다. 유료 생성과 새 유튜브 업로드는 하지 않았습니다. 유튜브 비공개본은 이전 v1r3이며 이번 로컬 검토본과 다릅니다.

상세 근거: 작업폴더/qa/review-v4-independent/report.md · 작업폴더/outputs/production-v4/technical_v4r1.json
'''
(O/'개선검토.md').write_text(report,encoding='utf8')
s=read(E/'state.json');s.update(stage='review_v4_ready',current_render=str(v.resolve()),current_render_sha256=sha,current_render_revision='v4r1-free-tts',video_path=q['video'],rendered_video_sha256=sha,actual_video_duration_seconds=q['duration_s'],qa_review='qa/review-v4-independent/report.json',qa_sha256=hashlib.sha256((E/'qa/review-v4-independent/report.json').read_bytes()).hexdigest(),required_unresolved=0)
s['production_v4'].update(status='delivered_local_review',video=q['video'],video_sha256=sha,qa='qa/review-v4-independent/report.json',required_unresolved=0,paid_calls=0,upload_performed=False,actual_listening=False,continuous_playback=False,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
s['script_language_revision'].update(audio_reflected=True,video_reflected=True,render_revision='v4r1-free-tts')
write(E/'state.json',s)
shelf=read(R/'config/video_shelf.json')
for row in shelf['entries']:
 if row['name']=='교산':
  row['status']='무료 TTS 검토본 v4r1 · 대본 v4·자료화면 반영 · 로컬 미게시 · YouTube 비공개본은 v1r3'
  files={'영상.mp4':q['video'],'자막.srt':'outputs/production-v4/gyosan_v4.srt','대본.md':'outputs/script-review-v4/script_v4.md','개선검토.md':'outputs/production-v4/개선검토.md','검토안내.md':'outputs/production-v4/개선검토.md'}
  for k,x in files.items():row['files'][k]=(E/x).relative_to(R).as_posix()
write(R/'config/video_shelf.json',shelf)
print(json.dumps({'video':q['video'],'sha256':sha,'required_unresolved':0,'paid_calls':0,'upload':False}))
