"""Record only images actually opened by QA in this run; no automatic image-quality scoring."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
Q=Path(__file__).resolve().parent;E=Q.parent.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
t=read(Q/'final_technical_checks.json');D=Q/'encoded-136a20c43ba3';B=E/'outputs/jun-production-v1/renders/measured-jun-v1/encoded-evidence'
opened=[D/(category+'-'+str(i).zfill(2)+'.jpg') for category,count in [('representatives',7),('scene_boundaries',13),('joins',5),('longest_captions',3),('end_tail',1),('maximum_scales',1)] for i in range(1,count+1)]
assert {str(p) for p in opened}=={x['file']['path'] for x in t['contact_sheets']}
native=[D/n for n in ['maxscale-01.png','maxscale-04.png','maxscale-05.png']]+[B/n for n in ['00014.png','00067.png','00107.png','00120.png','00147.png','00169.png','00178.png']]
times={r['absolute_file']:r for r in t['all_encoded_samples']+t['maximum_scale_frames']}
frames={r['global_frame'] for r in t['all_encoded_samples']+t['maximum_scale_frames']}
result=dict(role='video_qa',actually_viewed=True,checked_at=datetime.now(timezone.utc).isoformat(),video_sha256=t['video']['sha256'],all50_scene_representatives=True,all50_scene_boundaries=True,all12_assembly_joins=True,all5_maximum_scale_samples=True,all20_longest_caption_samples=True,burned_in_captions_verified=True,viewed_sheet_paths=[str(p) for p in opened],opened_sheet_evidence=[pin(p) for p in opened],full_resolution_images_actually_opened=[dict(**pin(p),global_frame=times[str(p)]['global_frame'],global_time_s=times[str(p)]['global_time_s']) for p in native],required_issues=[],critical_issues=[],observations=['50장면 대표·직후·직전 표본에서 배치/장소 오인/필수 숫자 불일치/자막 잘림 발견 없음. 경계 직후의 미완성 차트와 투명도 변화는 소스 애니메이션 상태와 맞고, 정지 표본으로 연속 움직임의 체감까지 평가하지 않음.','인트로19.5~24.5초에 하단자막 없음. 복귀24.5초에 이전 훅 자막 재등장 없음.12접합의 전/시점/후 프레임을 구분해 실제 열람.','5곳 최대확대 표본 중 지역범례1.05배/원금강조1.4배/계속거주평가1.03배에 화면밖 잘림이나 필요한 문자 충돌 발견 없음.','20개 최장 자막 표본과 원본해상도10개 프레임에서 명시한 줄바꿈·한글·금액·하단박스 여백 확인. 전체206큐는 소스/SRT 정렬 검증이며 실제206개 자막을 연속 재생한 것은 아님.','지역그래프2006Q1~2026Q2/강조2016Q2~2026Q2,단지수범위/세종2015Q1시작 표기가 보존됨. 승인된 financial fact SHA와 대본을 재사용하고 원거래를 다시 조사하지 않음.','마지막 발화 후0.05/1.5/2.95초 CTA 표본은 안정적이고 자막 없음. 아웃트로1182.433초 시작으로 마지막 발화에서3.03초 확보.'],coverage=dict(producer_packet_unique_actual_final_frames_viewed=199,new_independent_maximum_scale_frames_viewed=5,unique_actual_final_frame_timepoints_viewed=len(frames),actual_contact_sheets_opened=30,contact_tile_resolution=[640,360],full_resolution_actual_final_frames_opened=10,scene_representative_samples=50,scene_boundary_samples=100,assembly_join_samples=36,longest_caption_samples=20,maximum_scale_samples=5,post_speech_CTA_samples=3),continuous_playback=False,actual_listening=False,all_frames_continuously_watched=False)
(Q/'visual_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='visual_sample_review_complete',video_sha256=result['video_sha256'],coverage=result['coverage']),ensure_ascii=False))
