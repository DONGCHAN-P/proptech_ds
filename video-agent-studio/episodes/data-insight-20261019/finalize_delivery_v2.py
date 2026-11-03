"""Publish local short paths for reviewed v2, while preserving v1 outputs."""
from pathlib import Path
import json,hashlib,subprocess,os
EP=Path(__file__).resolve().parent;ROOT=EP.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
movie=EP/'outputs/v2/data_insight_30s_v2.mp4'
sha=hashlib.sha256(movie.read_bytes()).hexdigest()
technical=read(EP/'editor-v2/technical_verification.json')
assert technical['sha256']==sha
assert technical['status']=='technical_pass' and technical['frames']==900 and technical['decode_errors']==0
issues=read(EP/'qa-v2/findings.json')
assert isinstance(issues,list)
assert not [x for x in issues if x.get('severity') in ['critical','required'] and not x.get('status','').startswith('closed')]
qa_handoff=read(EP/'qa-v2/handoff.json')
assert sha in json.dumps(qa_handoff),'Independent QA has not recorded the final media hash'
assert 'waiting_final' not in qa_handoff.get('status',''),'Independent final QA still pending'
cost=read(EP/'visual-v2/cost_report.json');assert cost['new_generation_cost_usd']<=3
note='''# Data Insight 30초 수정본 v2

이번 수정: 사람이 모니터·노트북·휴대폰을 실제로 확인하는 구도로 변경했습니다. 원본 UI는 기기의 물리적 디스플레이 안에 원근·움직임을 맞춰 합성했습니다. 화면 밖 캡처 카드와 원본 사진 인서트를 제거했습니다.

사무실 사진 3개는 생성 장면의 공간 참조로 활용했고, 나머지 UI·도식·GIF 10개는 기기 화면 안에서 활용했습니다. UI 한글은 원본 픽셀 또는 로컬 한글 합성으로 처리합니다. 인물·사무실 동작은 AI 재현이며 실제 직원 촬영은 아닙니다. 모바일 UI는 제공 메시지와 차트 부분을 디바이스 화면에 맞춰 구성한 예시입니다.

30초·1920×1080·30fps·900프레임·무대사·배경음악. API 촬영 소스는 1280×720 생성본을 1080p로 확대했습니다. 원본 한글 텍스트·UI 자료, v1의 음악·글꼴은 재사용했습니다. GIF는 빠르게 재생한다는 표기를 포함합니다.

추가 API 사용량 180크레딧($1.80), v1 포함 누적 360크레딧($3.60), 세금 제외. v2 별도 승인 상한 $3.00 이내입니다. 추가 충전·유료 재생성 없음.

검수: 인코딩된 최종 MP4의 기기 화면 합성·원근·가림·한글·샘플 장면과 경계 프레임, 스트림, 전체 프레임 디코드를 확인했습니다. 연속 재생과 실제 음악 청취는 수행하지 않았습니다. 세부 범위는 qa-v2/report.md에 기록합니다.

팀 인원·Weekly7회·시간 단축 수치는 사용자 제공 구성안 기준입니다. v1·원본 ZIP·원본13개와 생성소스를 보존했습니다. 제작 재현·화면 추적·자산별 활용 기록은 editor-v2에 있습니다.

사용자 요청에 따라 최종 MP4 원본을 설정된 텔레그램 개인 대화로 전달합니다. 실제 송신 성공 여부는 outputs/v2/telegram_receipt.json에서 확인합니다. 외부 공개 게시 승인을 뜻하지 않습니다.
'''
(EP/'outputs/v2/검토안내.md').write_text(note,encoding='utf8')
cfgp=ROOT/'config/video_shelf.json';cfg=read(cfgp)
entry=next(e for e in cfg['entries'] if e['name']=='Data Insight')
assert entry['workspace']==EP.relative_to(ROOT).as_posix()
entry.update(status='30초 기기 확인 장면 수정본 v2 / 사용자 검토용 / 외부 미게시',files={
 '영상.mp4':movie.relative_to(ROOT).as_posix(),
 '자막.srt':(EP/'outputs/v2/captions.srt').relative_to(ROOT).as_posix(),
 '대본.md':(EP/'script_v2.md').relative_to(ROOT).as_posix(),
 '화면문구.md':(EP/'editor-v2/on_screen_text_v2.md').relative_to(ROOT).as_posix(),
 '검토안내.md':(EP/'outputs/v2/검토안내.md').relative_to(ROOT).as_posix(),
 '검수.md':(EP/'qa-v2/report.md').relative_to(ROOT).as_posix()})
write(cfgp,cfg)
subprocess.run([str(ROOT/'tools/python311/python.exe'),'-X','utf8',str(ROOT/'tools/refresh_video_shelf.py')],check=True,cwd=ROOT)
alias=ROOT/'영상/Data Insight/영상.mp4';assert os.path.samefile(alias,movie)
state=read(EP/'state.json');state.update(status='v2_reviewed_pending_telegram_delivery',revision='v2',video=movie.relative_to(ROOT).as_posix(),video_sha256=sha,short_path='영상/Data Insight/영상.mp4',script_revision='v2-device-shots-text-locked',completed='awaiting_user_feedback_on_v2',publication='not_uploaded',telegram_delivery='pending',continuous_playback=False,actual_listening=False);write(EP/'state.json',state)
pre=read(EP/'episode_preflight.json');pre['status']='v2_reviewed_pending_telegram_delivery';pre['qa'].update(actual_encoded_frames='900 frames; final v2 samples independently inspected',full_decode='pass_v2',required_open_issues=0,continuous_playback_performed=False,actual_listening_performed=False,evidence_paths=['editor-v2/technical_verification.json','editor-v2/frames','qa-v2/report.md','qa-v2/findings.json']);write(EP/'episode_preflight.json',pre)
write(EP/'outputs/v2/delivery_manifest.json',dict(version='v2',video=movie.relative_to(ROOT).as_posix(),alias=alias.relative_to(ROOT).as_posix(),sha256=sha,bytes=movie.stat().st_size,technical=technical,source_roles={'office_photo_references':3,'ui_assets_inside_devices':10},new_api_cost_usd=1.8,total_api_cost_usd=3.6,qa_report='qa-v2/report.md',continuous_playback=False,actual_listening=False))
print(json.dumps({'delivered':str(alias),'sha256':sha,'bytes':movie.stat().st_size},ensure_ascii=False))
