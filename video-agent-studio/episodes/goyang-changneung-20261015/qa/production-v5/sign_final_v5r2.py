from pathlib import Path
import json,hashlib,datetime
Q=Path(__file__).resolve().parent; EP=Q.parents[1]; O=EP/'outputs/production-v5'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
t=read(Q/'final_input_technical_r2.json');m=read(Q/'encoded_frame_manifest_r2.json');p=read(O/'project_v5.json');base=read(O.parent/'production-v4/project_v4.json')
assert t['source_mismatches']==[] and t['aac_identical'] and t['aac_exit_code']==0
assert m['exit_code']==0 and m['decoded_output_frames']==24140
assert m['sha256_before']==m['sha256_after']==t['primary_files'][0]['sha256']
assert all(p[k]==base[k] for k in ['captions','chapters','segments','duration_frames','fps'])
assert len(p['captions'])==183
assert t['primary_files'][1]['sha256']=='2f43c5f9a1f7857635224ee073d013a42234eeb7abdd95af6a5611ab88b2a3a1'
video,srt,project=t['primary_files']
assert sha(Path(video['file']))==video['sha256']
f=read(Q/'findings.json')
for x in f['findings']:
 if x['issue_id']=='QA-V5-015':
  x['status']='closed_encoded_verified'
  x['checked_revision']='v5r2 '+video['sha256']
  x['evidence']+=['encoded_frames_r2/frame_000762.jpg','encoded_frames_r2/frame_000763.jpg','encoded_frames_r2/frame_000764.jpg','encoded_frame_manifest_r2.json']
f.update(revision='v5r2-final-encoded-reviewed',required_open_count=0,critical_open_count=0,local_review_ready=True)
(Q/'findings.json').write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf-8')
r={
 'revision':'production-v5r2','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'required_open_count':0,'critical_open_count':0,'local_review_ready':True,
 'video_file':video['file'],'sha256':video['sha256'],'video_sha256':video['sha256'],
 'frame_count':24140,'duration_s':804.666667,'fps':30,'width':1920,'height':1080,'bytes':video['bytes'],
 'srt_file':srt['file'],'srt_sha256':srt['sha256'],'project_file':project['file'],'project_sha256':project['sha256'],
 'primary_files':t['primary_files'],'source_freeze_file':str(O/'source_freeze_v5.json'),'source_freeze_sha256':t['source_freeze_sha256'],'source_count':t['source_count'],'source_mismatches':[],
 'script_sha256':p['script_sha256'],'timing_lock_sha256':p['timing_lock_sha256'],
 'caption_count':183,'caption_chapter_segment_timing_identical_to_v4':True,
 'aac_identical':True,'aac_adts_sha256':t['aac_sha256'],'aac_adts_bytes':t['aac_bytes'],
 'full_video_decode':{'exit_code':0,'output_frames':24140,'method':'全 MJPEG 출력 전역 순번 직접 계수. 필터 내부 n 미사용.'},
 'coverage':{
  'v5_original':{'sha256':'affcc8b60a6e1f45419ff0a4e46a462b1b99be23765e3c0fe7935c83394fb0f2','actual_sample_frames_viewed':706,'contact_sheets_viewed':40,'scope':'47개 장면 경계와 중간, 183개 자막 중간, 152개 발화 대상 이벤트 전후, 제한 모션, 학교 3종·가격 3종·대안 6개·호반 최종 패치·브랜드·발화 후 유지·종료 경계'},
  'v5r2':{'sha256':video['sha256'],'actual_sample_frames_viewed':15,'frames':m['frames'],'scope':'변경된 763프레임과 앞뒤 연결, 브랜드 613~762, 자막 숨김 23748, 마지막 발화 뒤 유지, 종료 23840~24139 직접 열람. 동일 소스 나머지는 v5 검수 승계.'},
  'schedule':'183개 의미 자막·38개 의미 상태·694개 구간·152개 발화 대상 이벤트의 실제 캐시 분할과 225개 모션 프레임 배치를 대조. 초기 캐시 688개와 호반 18개 교체 상태 해시 확인.',
  'message_visual_focus':'1:38 일자리 전환, 외부 5개 업무지, 열차 사례, 접근·대기·마지막 이동, 실제 단지·학교·시설·노선·대안 대상의 순차 강조를 표본 실제 인코딩에서 확인.'
 },
 'actual_listening':False,'continuous_playback':False,
 'limits':['표본 프레임 검사이며 전체 24140프레임 육안 열람 또는 실제 연속 재생을 의미하지 않음.','AAC 동일성은 신호·바이트 검사이며 실제 청취를 의미하지 않음.','화면 강조 시점은 provider 문자 정렬과 실제 전역 프레임을 대조했으며 새 음성 인식 또는 청취 검증은 하지 않음.','썸네일 및 외부 게시 상태는 이번 본편 수정 검수 범위 밖임.'],
 'delivery_scope':'v5r2 직접 MP4·기존 해제 소스 폴더·SRT·프로젝트. ZIP 추가 생성 없음. 게시·업로드 승인 아님.',
 'evidence':['final_input_technical_r2.json','encoded_frame_manifest.json','encoded_review_v5.json','encoded_frame_manifest_r2.json','rendered_cache_audit_final.json','schedule_precheck.json','findings.json']
}
(Q/'final_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
h={'revision':'production-v5r2','status':'독립 본편 검수 완료','next_owner':'director','outputs':[str(Q/'final_review.json'),str(Q/'findings.json')],'video_file':video['file'],'sha256':video['sha256'],'required_open_count':0,'critical_open_count':0,'local_review_ready':True,'input_versions':{'project_sha256':project['sha256'],'srt_sha256':srt['sha256'],'source_freeze_sha256':t['source_freeze_sha256']},'verification':'v5 706개 실제 표본 및 v5r2 변경 경계 15개 실제 표본, 전체 디코드·103개 입력·AAC 동일성·183개 자막/타이밍 보존 확인. QA015 763프레임 지도 회귀 해소.','unresolved':[],'actual_listening':False,'continuous_playback':False,'next_action':'총괄이 정확한 v5r2 파일과 새 완료 결정으로 납품. 미디어 변경 시 서명 갱신.'}
(Q/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'video_sha256':video['sha256'],'srt_sha256':srt['sha256'],'project_sha256':project['sha256'],'ready':True}))
