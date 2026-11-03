"""Finish a verified local revision. Never uploads, publishes, or deletes media."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
H=E/'editor/top20-enhance-v2';O=E/'outputs/top20-enhance-v2';Q=E/'qa/top20-enhance-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.resolve().relative_to(R)).replace('\\','/')

rec=read(H/'render_receipt_main_v1.json');video=Path(rec['output']);t=read(D/'locked_timing.json')
assert rec['full_decode_passed'] and sha(video)==rec['output_sha256']
assert 480<float(rec['probe']['format']['duration'])<550
qa=read(Q/'main_final.json')
assert qa['video_sha256']==sha(video) and qa['critical_open']==qa['required_open']==0
subs=read(O/'subtitle_verification.json');assert subs['sentences']==113 and subs['sha256']==sha(O/'자막.srt')
old=read(D/'previous_state.json');duration=float(rec['probe']['format']['duration'])
md=f'''# TOP20 본편 수정본 · 8분 48초

새 본편: `{rel(video)}`

- 기존 7분 51초에서 {duration:.2f}초로 확장했습니다. 추가 분석 음성은 57.345초입니다.
- 지역 장면을 사진 중심·옆 순위 비교·상위 5곳 중심의 세 구도로 나눴습니다. 실제 지역 경계와 작은 위치 안내를 함께 제시합니다.
- 순위 사다리의 같은 척도로 규모 차이를 보여주고, 현재 설명하는 지역·값을 강조합니다. 뒤에 소개할 지역의 순위 결과는 미리 노출하지 않습니다.
- 같은 수도권 53개 구를 초혼 부부 수로 재정렬한 두 분석 장면을 추가했습니다. 동안구·마포구의 TOP20 진입과 남동구·원미구의 기준별 차이를 비교합니다.
- 기존 내레이션·브랜드 음성은 PCM 바이트를 보존했고, 추가 부분만 같은 무료 Edge InJoon으로 생성했습니다. 새 유료 생성은 0원입니다.

원고: `director/top20-enhance-v2/script_v5.md` · 자막: `outputs/top20-enhance-v2/자막.srt`

## 검수 범위

검수 근거: `qa/top20-enhance-v2/main_final.json`, 편집 폴더의 check·실제 MP4 디코드/프레임 색인, 원자료 재계산·무료 음성 단어 매핑·113문장 자막 연결 검사.

실제 청취·연속 재생·Claude Opus/max 검수는 미실시입니다. Claude CLI 연결은 loggedIn=false로 확인했습니다. 프레임·신호·ASR 검사를 청취 승인으로 표시하지 않은 로컬 수정 검토본입니다.

## 버전과 업로드

이전 비공개 본편은 https://youtu.be/{old['youtube_video_id']} 이며 이전 MP4·대본·음성·검수 기록과 쇼츠 두 편을 보존했습니다. 이번 수정본은 로컬 제작 결과입니다. 업로드 결과 문서는 기존 비공개 영상 세 편의 기록을 가리킵니다.
'''
(O/'개선내용.md').write_text(md,encoding='utf-8')
comp={'revision':'top20-enhance-v2','status':'local_enhanced_review_delivered','video':rel(video),'video_sha256':sha(video),'duration_s':duration,'additional_information_s':t['added_duration_s'],'script':rel(D/'script_v5.md'),'script_sha256':sha(D/'script_v5.md'),'subtitles':rel(O/'자막.srt'),'qa':rel(Q/'main_final.json'),'qa_sha256':sha(Q/'main_final.json'),'actual_listening':False,'continuous_playback':False,'Claude_review':'unavailable_cli_logged_out','paid_generation_cost_krw':0,'new_upload':False,'previous_private_main_id':old['youtube_video_id'],'previous_short_ids':[s['video_id']for s in old['shorts']]}
save(O/'completion.json',comp)
save(O/'release_manifest.json',comp)
state=read(E/'state.json');state.update(active_revision='top20-enhance-v2',revision='top20-enhance-v2',phase='enhanced_main_local_review_delivered',script=rel(D/'script_v5.md'),script_sha256=sha(D/'script_v5.md'),timing=rel(D/'locked_timing.json'),video=rel(video),video_sha256=sha(video),actual_video_duration_s=duration,publication_status='local_review_not_uploaded',youtube_video_id=None,youtube_url=None,previous_private_main={'video':old['video'],'sha256':old['video_sha256'],'video_id':old['youtube_video_id'],'url':old['youtube_url'],'privacy':'private'},completion=rel(O/'completion.json'),updated_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat())
state.update(active_preflight=rel(D/'episode_preflight.json'),audio_revision=t['audio_revision'],render_revision='top20-enhanced-v1',script_approval='latest user authorized informational expansion; producer v5 with verified facts; no separate exact-script user approval claimed',previous_release_manifest=old.get('release_manifest'),release_manifest=rel(O/'release_manifest.json'),duration_target_s=510,artifact_quality_scope='independent representative and final encoded scene/boundary/caption/technical review; actual listening and continuous playback unperformed',Claude_review='unavailable_cli_logged_out_2026-11-02')
save(E/'state.json',state)
if not(D/'previous_scenes.json').exists():save(D/'previous_scenes.json',read(E/'scenes.json'))
save(E/'scenes.json',read(D/'scene_proposals_v5.json'))
pre=read(D/'episode_preflight.json');pre.update(status='local_enhancement_delivered_with_disclosed_limits',video_sha256=sha(video),qa=rel(Q/'main_final.json'),actual_duration_s=duration)
save(D/'episode_preflight.json',pre)
d=read(E/'decisions.json')
if not any(x.get('id')=='D021'for x in d['decisions']):d['decisions'].append({'id':'D021','revision':'top20-enhance-v2','choice':'deliver8m48enhancedlocalmain with57.345s new firstmarriage comparison; keep three prior private uploads','evidence':rel(O/'completion.json'),'status':'delivered_local_review','owner':'director'})
save(E/'decisions.json',d)
cfg=R/'config/video_shelf.json';shelf=read(cfg);entry=next(x for x in shelf['entries']if x['name']=='신혼부부_지역별아파트')
entry['status']='본편 비주얼·정보 보강 로컬 수정본 8분48초. 기존 비공개 본편·쇼츠 보존. 실제 청취/Claude 미실시.'
entry['files'].update({'영상.mp4':rel(video),'자막.srt':rel(O/'자막.srt'),'대본.md':rel(D/'script_v5.md'),'개선내용.md':rel(O/'개선내용.md'),'추가분석.md':rel(O/'추가분석.md'),'이전_비공개업로드본.mp4':old['video']})
if(O/'비주얼_전후비교.jpg').exists():entry['files']['비주얼_전후비교.jpg']=rel(O/'비주얼_전후비교.jpg')
save(cfg,shelf)
cp=subprocess.run([str(R/'tools/python311/python.exe'),'-X','utf8',str(R/'tools/refresh_video_shelf.py')],cwd=R,capture_output=True,text=True,encoding='utf-8');assert cp.returncode==0,cp.stderr
(D/'shelf_refresh.log').write_text(cp.stdout,encoding='utf-8')
for name,source in [('영상.mp4',video),('자막.srt',O/'자막.srt'),('대본.md',D/'script_v5.md'),('이전_비공개업로드본.mp4',R/old['video'])]:assert os.path.samefile(R/'영상/신혼부부_지역별아파트'/name,source)
print(json.dumps({'status':comp['status'],'video':rel(video),'sha256':sha(video),'duration_s':duration,'qa_critical_open':qa['critical_open'],'qa_required_open':qa['required_open'],'shelf_aliases_verified':4,'new_upload':False},ensure_ascii=False))
