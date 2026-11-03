from pathlib import Path
import json,shutil,datetime
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/household-space-v1'
v=json.loads((OUT/'checks/verification.json').read_text('utf-8'))
note=OUT/'검토안내.md'
note.write_text('''# 집 공간 중심 교체 시안

2026-10-25 사용자 피드백: 집을 보여주는 구도는 좋지만 교체 인물과 걷기는 마음에 들지 않는다.

현재 결과는 `household_space_sample_v1.mp4` — 20초, 1920×1080, 30fps, 무음이다. 전체 본편 교체 결과가 아니다.

집을 보여주는 단면 구도와 기존 대본의 네 문장을 유지했다. 보행 캐릭터는 제거했다. 가족의 거실과 자녀의 별도 원룸을 서로 다른 생활 공간으로 그렸으며, 카메라가 4.6–7.8초에 천천히 물러나 두 공간을 보여준다. 기존 집의 자녀 컵이 사라지고 같은 색 컵이 별도 집에 나타난다. 인구는 3명으로 유지하고 가구 수는 두 번째 집이 드러난 뒤 8.2초에 1에서 2로 바뀐다. 집을 물리적으로 쪼개거나 인물·상자를 미끄러뜨리는 표현은 없다.

장면은 설명용 가상 예시다. 실제 아파트·평면도·지역 통계로 제시하지 않는다. 대본·인용·기존 본편·이전 시안은 보존했고, 음성 생성 보류도 유지한다. 새 유료 미디어 생성과 외부 전송은 없다. HyperFrames 호스팅 사용량 조회는 `unknown/usage_request_failed`였으며 호스팅 렌더를 사용하지 않았다.

## 확인 범위

- 최신 시안의 17개 실제 인코딩 프레임을 추출했다. 카메라 전환과 1→2가구 변경 전후를 포함한다.
- 600프레임 전체 디코드 및 해상도·프레임레이트를 확인했다.
- 자막 네 문장을 승인 원문과 비교했다. 기존 본편·대본·인물 교체 v3의 SHA256 보존을 확인했다.
- 기술 검사에서 오류·경고는 없었다. 이것은 사용자의 미감 승인이나 영상 전체의 완성을 뜻하지 않는다.
- 정상 속도 연속 재생은 미검수다. 무음 시안이므로 내레이션 발음·음성 동기·최종 길이를 판정하지 않았다.

독립 검토는 episode의 `qa/household-space-v1/review.md`, 인코딩 검증은 `checks/verification.json`에 기록한다. 본편 전체 반영은 아직 수행하지 않았다.
''','utf-8')
path=EP/'state.json';state=json.loads(path.read_text('utf-8'))
backup=OUT/'checks/state_before.json'
if not backup.exists():shutil.copy2(path,backup)
previous=state.get('visual_quality_feedback',{})
history=state.setdefault('visual_quality_feedback_history',[])
if previous and previous not in history:history.append(previous)
state['visual_quality_feedback']={'date':'2026-10-25','user_request':'집 단면 구도는 좋으나 인물/걷기가 부자연스러움. 더 자연스러운 방식 요청','previous_sample_status':'character_sample_v3_rejected_by_user','status':'space_based_local_direction_sample_ready_not_yet_user_accepted','sample_revision':'household-space-v1','sample':v['video'],'sample_sha256':v['sha256'],'review_note':note.relative_to(ROOT).as_posix(),'full_film_visual_acceptance':'revision_pending','full_film_replaced':False,'narration':'still_on_hold','external_send':False}
state['stage']='literature_visual_space_direction_sample_ready_narration_on_hold'
state['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();state['updated_client_date']='2026-10-25'
path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
cfgpath=ROOT/'config/video_shelf.json';cfg=json.loads(cfgpath.read_text('utf-8'));entry=next(x for x in cfg['entries'] if x['name']=='지역별가격회복')
entry['status']='집 단면 유지·보행 제거한 20초 공간 중심 시안 · 본편 전체 반영 전 · 음성 생성 보류'
for alias,src in [('집공간_교체시안_v1.mp4',OUT/'household_space_sample_v1.mp4'),('집공간_미리보기_v1.png',OUT/'checks/encoded/frame-16-19.9s.png'),('집공간_검토안내.md',note)]:entry['files'][alias]=src.relative_to(ROOT).as_posix()
cfgpath.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'stage':state['stage'],'sample':v['alias'],'voice_still_on_hold':True,'full_film_replaced':False},ensure_ascii=False))
