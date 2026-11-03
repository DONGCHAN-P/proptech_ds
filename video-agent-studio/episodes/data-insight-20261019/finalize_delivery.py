"""Create versioned delivery records and the existing short-path video shelf."""
from pathlib import Path
import json,hashlib,subprocess,os

EP=Path(__file__).resolve().parent
ROOT=EP.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
movie=EP/'outputs/v1/data_insight_30s_v1.mp4'
verification=read(EP/'editor/technical_verification.json')
sha=hashlib.sha256(movie.read_bytes()).hexdigest()
assert verification['sha256']==sha
assert verification['status']=='technical_pass' and verification['frames']==900
assert verification['decode_errors']==0
cost=read(EP/'visual/cost_report.json')
assert cost['observed_credit_delta']==180 and cost['generation_cost_usd']<=3
usage=read(EP/'editor/asset_usage.json')
assert {x['asset_id'] for x in usage}=={f'A{i:02}' for i in range(1,14)}
assert all(x['uses'] for x in usage)
qa=read(EP/'qa/findings.json')
assert isinstance(qa,list)
assert not [x for x in qa if x.get('severity') in ['critical','required'] and not x.get('status','').startswith('closed')], 'Open required QA issue'
note='''# Data Insight — 30초 영상 v1

무대사 · 배경음악 · 한글 자막. 1920×1080, 30fps, 영상 900프레임.

제공 ZIP의 이미지 12개와 GIF 1개를 모두 사용했습니다. 사무실 사진 3개를 Runway Gen-4.5 인물 클립의 배경으로 활용했고, 원본 사진 자체도 인서트로 배치했습니다. 인물은 AI 재현이며 실제 임직원 촬영이 아닙니다. API 소스는 1280×720 생성본을 1080p로 확대했습니다.

한글 문구는 `script_v1_2.md`와 `editor/on_screen_text_v1.md`에 먼저 작성했습니다. 한글 폰트를 로컬에 포함해 별도 합성했고, 제공 UI의 원래 글자·수치는 원본 이미지로 유지했습니다. GIF는 23.1초 원본의 7프레임을 3초에 압축하고 ‘빠르게 재생’을 표시합니다. 사용 음악은 직접 합성한 original procedural composition입니다.

비용: 승인 상한 $3.00, 관측 사용량 180크레딧($1.80, 세금 제외). API 생성 3회, 재생성·추가 충전 없음.

검수 범위: 최종 MP4 기술 검사·900프레임 카운트·전체 디코드·장면 및 컷 경계 샘플 프레임·원본 13개 무결성·한글 표시 검사. 연속 재생과 실제 음악 청취는 수행하지 않았습니다. 자세한 독립 검수는 `qa/report.md`를 확인합니다.

팀 규모·Weekly 7회·2~3시간→5분 수치는 사용자 제공 구성안 기준입니다. 외부 사실 검증을 수행했다는 의미가 아닙니다. 현재 결과는 사용자 검토용 완성본이며 게시·외부 공유 승인은 포함하지 않습니다.

재현 명령과 자산별 사용 시간은 `editor/placement_guide.md`, `editor/asset_usage.json`에 있습니다. 원본 ZIP과 기존 영상은 보존했습니다.
'''
(EP/'outputs/v1/검토안내.md').write_text(note,encoding='utf8')
entry=dict(name='Data Insight',status='30초 인물 API·한글 별도 합성 v1 / 사용자 검토용 / 미게시',workspace=EP.relative_to(ROOT).as_posix(),files={
 '영상.mp4':movie.relative_to(ROOT).as_posix(),
 '자막.srt':(EP/'outputs/v1/captions.srt').relative_to(ROOT).as_posix(),
 '대본.md':(EP/'script_v1_2.md').relative_to(ROOT).as_posix(),
 '화면문구.md':(EP/'editor/on_screen_text_v1.md').relative_to(ROOT).as_posix(),
 '검토안내.md':(EP/'outputs/v1/검토안내.md').relative_to(ROOT).as_posix(),
 '검수.md':(EP/'qa/report.md').relative_to(ROOT).as_posix()
})
cfgp=ROOT/'config/video_shelf.json';cfg=read(cfgp)
existing=next((e for e in cfg['entries'] if e['name']==entry['name']),None)
if existing is None:cfg['entries'].append(entry)
else:
 assert existing['workspace']==entry['workspace'],'Preserve another workspace entry'
 existing.update(entry)
write(cfgp,cfg)
subprocess.run([str(ROOT/'tools/python311/python.exe'),'-X','utf8',str(ROOT/'tools/refresh_video_shelf.py')],check=True,cwd=ROOT)
alias=ROOT/'영상/Data Insight/영상.mp4'
assert os.path.samefile(alias,movie)
state=read(EP/'state.json');state.update(status='delivered_for_user_review',revision='v1',script_revision='v1.2-30s-text-locked',video=str(movie.relative_to(ROOT)),video_sha256=sha,short_path='영상/Data Insight/영상.mp4',completed='awaiting_user_feedback',pre_upload='not_authorized',publication='not_uploaded',qa_coverage='technical/full-decode/sampled-scene-and-cut-frames; no continuous playback or actual listening')
write(EP/'state.json',state)
pre=read(EP/'episode_preflight.json');pre['status']='delivered_for_user_review';pre['qa'].update(full_decode='pass',actual_encoded_frames='900 frames counted; samples inspected',required_open_issues=0,continuous_playback_performed=False,actual_listening_performed=False,evidence_paths=['editor/technical_verification.json','editor/frames','qa/report.md','qa/findings.json']);pre['change_control'].update(single_timing_lock='900frames at30fps',package_frozen_before_hash=True);write(EP/'episode_preflight.json',pre)
write(EP/'outputs/v1/delivery_manifest.json',dict(video=movie.relative_to(ROOT).as_posix(),alias=alias.relative_to(ROOT).as_posix(),bytes=movie.stat().st_size,sha256=sha,credits_used=180,cost_usd=1.8,all_source_assets=13,generated_people_clips=3,technical=verification,independent_qa='qa/findings.json',continuous_playback=False,actual_listening=False))
print(json.dumps({'delivered':str(alias),'sha256':sha,'bytes':movie.stat().st_size,'cost_usd':1.8},ensure_ascii=False))
