from pathlib import Path
import json,datetime,hashlib
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/relocation-space-v1'
v=json.loads((OUT/'checks/verification.json').read_text('utf-8'))
qa=EP/'qa/relocation-space-v1/review.md';assert qa.exists(),qa
assert hashlib.sha256((ROOT/v['video']).read_bytes()).hexdigest()==v['sha256']
note=OUT/'검토안내.md'
note.write_text('''# 재건축 이주 장 — 집과 시간표

현재 검토본은 `relocation_space_chapter_v1.mp4` — **1분 26.567초, 1920×1080, 30fps, 무음**입니다. L004 장 전체의 화면 교체본이며, 영상 전체의 최종본은 아닙니다.

## 반영한 내용

사용자가 수락한 `household-space-v1`의 인물 없는 집 단면 구도·생활 소품·절제된 움직임을 계승했습니다. 기존 집→공사 중인 사업지, 다른 집에서의 거주, 새집 입주를 시간 순서로 연결합니다. 캐릭터·보행·실제 장소 사진은 사용하지 않았습니다. 건물과 실내는 자체 제작 개념 그림입니다.

- 00:00–00:24.2: 집을 비운 뒤 새집에 입주하기 전까지의 대체 거주. 위치·기간의 비례가 없는 개념도입니다.
- 00:24.2–00:38.667: 가락시영 연구 사례와 주요 이주 기간 2012.8–2013.5. 분석 기간 2011Q1–2014Q4는 따로 표시합니다.
- 00:38.667–00:56.533: 과거 목적지 분포를 활용한 도구변수 추정, 59㎡ 매매가격·환산 임대료의 양의 추정 방향. 과거 목적지 분포의 외생성 가정을 명시하며 효과 크기는 제시하지 않습니다.
- 00:56.533–01:12.567: 사업지의 거주 가능 주택 일시 감소와 대체 거주지의 수요 증가 가능성을 구분합니다.
- 01:12.567–01:26.567: 실제 이주 목적지·시점·이동량을 함께 살필 후속 질문입니다.

논문 출처: [서문규·정재엽·이효중(2026), 재건축사업으로 인한 이주가 주택가격에 미치는 영향: 서울 가락시영아파트 사례](https://www.kpaj.or.kr/_PR/view/?aidx=50743&bidx=4543). 기존 승인 대본과 검증된 R3/C04 기록을 사용했습니다. 실제 목적지별 유입량 지도·원인 기여율·상승률 수치는 만들지 않았습니다.

## 검수 범위

실제 인코딩 MP4에서 26개 표본을 추출해 모든 화면과 전환 전후를 확인했습니다. 2,597프레임 전체 디코드와 미디어 규격을 검사했고, 15개 자막을 합쳐 기존 대본의 6단락 표시 문장과 일치하는지 검증했습니다. 기존 본편·승인 대본·사용자 수락 시안의 SHA256은 유지됐습니다.

독립 검토는 episode의 `qa/relocation-space-v1/review.md`에 기록했습니다. 표본 검토와 실제 연속 재생은 구분합니다. 정상 속도 연속 재생은 미검수이며, 음성 생성 보류로 발음·음성 동기·최종 발화 길이는 검수하지 않았습니다. 시간표와 SRT는 기존 텍스트 기준의 잠정본입니다.

CLI에는 5개 박자 구간을 한 파일에 둔 트랙 구성, 3개 건물 상태를 담은 SVG의 패널 자르기, 다른 구간의 연구 카드로 잘못 연결한 선 검출 경고가 남았습니다. 기술 검사의 오류는 없었으며, 실제 표본에서의 잘림·의미·가독성은 별도 검토했습니다.

새 유료 미디어 생성·음성 생성·외부 전송·업로드는 수행하지 않았습니다. HyperFrames 호스팅 사용량은 조회 실패로 미확인이며 이번 렌더는 로컬에서 수행했습니다. 전체 본편 통합은 아직 진행하지 않았습니다.
''','utf-8')
state_path=EP/'state.json';state=json.loads(state_path.read_text('utf-8'))
state['active_visual_task']={'revision':'relocation-space-v1','scene_ids':['L004'],'scope':'complete chapter visual revision','status':'local_chapter_review_ready','video':v['video'],'sha256':v['sha256'],'qa_report':qa.relative_to(ROOT).as_posix(),'full_film_replaced':False,'voice':'still_on_hold'}
state['stage']='literature_relocation_chapter_local_review_ready_narration_on_hold';state['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();state['updated_client_date']='2026-10-25'
state.setdefault('visual_scene_revisions',{})['L002-P2']={'revision':'household-space-v1','status':'user_accepted','acceptance_record':'director/household-space-v1/user_acceptance.json'}
state['visual_scene_revisions']['L004']={'revision':'relocation-space-v1','status':'local_review_ready','full_film_integration':'pending'}
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
cfgpath=ROOT/'config/video_shelf.json';cfg=json.loads(cfgpath.read_text('utf-8'));entry=next(e for e in cfg['entries'] if e['name']=='지역별가격회복')
entry['status']='집 공간 방식 수락 · 재건축 이주 장 1분 27초 화면 교체본 · 전체 통합 전 · 음성 보류'
for alias,path in [('재건축이주_검토본_v1.mp4',OUT/'relocation_space_chapter_v1.mp4'),('재건축이주_미리보기_v1.png',OUT/'checks/encoded/frame-06-22s.png'),('재건축이주_임시자막_v1.srt',OUT/'relocation_space_v1_provisional.srt'),('재건축이주_검토안내.md',note)]:entry['files'][alias]=path.relative_to(ROOT).as_posix()
cfgpath.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n','utf-8')
decision={'client_date':'2026-10-25','request':'맘에들어 다음','accepted_direction':'household-space-v1','new_visual_revision':'relocation-space-v1','changed_scene_ids':['L004'],'scope':'complete L004 chapter only','input_script_sha256':'5f40c29d4a3e0ef5255ade11eaa63cb04c8093e2c3d1d0296873126707a26d9b','actual_roles_executed':['main director/editor','video_visual building asset','video_qa'],'visual_agent':'01a1726e-bd69-7bc0-829a-a92b90a80259','qa_agent':'01a16930-85f5-7de0-a0dc-cde61cb4b3cc','video_sha256':v['sha256'],'qa_report':qa.relative_to(ROOT).as_posix(),'continuous_playback':'unchecked','voice_generation':'still_on_hold','full_film_integrated':False,'external_send':False}
(EP/'director/relocation-space-v1/decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'sample':v['alias'],'duration':v['duration'],'full_film_integrated':False,'voice_still_on_hold':True},ensure_ascii=False))
