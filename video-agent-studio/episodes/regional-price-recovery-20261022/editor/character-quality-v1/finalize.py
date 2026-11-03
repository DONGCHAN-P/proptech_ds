from pathlib import Path
import json,datetime,shutil
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/character-quality-v1'
receipt=json.loads((OUT/'checks/verification-v3.json').read_text('utf-8'))
note=OUT/'검토안내.md'
note.write_text('''# 인물·움직임 교체 방향 시안

현재 파일: `character_quality_sample_v3.mp4` — 20초, 1920×1080, 30fps, 무음. 전체 본편을 교체한 결과가 아니다.

기존 화면은 원·선으로 인물을 그리고 같은 자세를 통째로 평행 이동했다. 캐릭터 원화·행동·장면 연결이 부족했는데 기술 검사 통과를 완성도의 근거처럼 사용했다. 기존 두 장면의 미감 감사에서도 교체가 필요하다는 판단이 나왔다.

시안은 원화에 머리·의복·얼굴·신발을 넣고, 관절 걷기·정지와 두 공간의 관계를 연결했다. v2는 초반 그림자 위치를 수정했고 v3는 대기/도착 자세를 정돈하고 중복된 작은 결론 문구를 제거했다. 기존 대본의 가구 분리 예시 네 문장은 그대로 사용한다. 인구·가구 값은 실제 통계가 아닌 설명용 가정이다.

## 설치 판단

- HyperFrames·GSAP·FFmpeg와 RTX 4060 Ti 렌더는 실제 작동했다. 새 대형 프로그램의 필수 설치 근거는 발견되지 않았다.
- 무료 오픈소스 [Lottie Web](https://github.com/airbnb/lottie-web) 5.12.2 재생 파일을 시안 프로젝트에 추가했다. 전역 설치는 하지 않았다. 런타임은 MIT, 바탕으로 삼은 [공식 캐릭터 예제](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/lottie-character-walk)는 Apache-2.0이다. 원화·시간표·대기/도착 동작을 변경했으며 출처와 라이선스를 프로젝트에 보관했다.
- [After Effects](https://www.adobe.com/products/aftereffects.html)는 캐릭터·합성·키프레임을 직접 다듬을 때 선택할 수 있는 유료 제작 도구다. 이번 수정의 선행 구매 조건으로 보지 않는다. 원화와 연출을 설계해야 결과가 바뀐다.
- 부동산 분석 영상의 기본 화면은 실제 지도·자료·차트의 관계로 설계하고, 사람의 이동·가구 변화가 필요한 장면에 인물을 제한한다.

## 검수 범위

최신 v3 MP4의 13개 실제 인코딩 프레임을 추출하고 전체 파일 디코드를 검사했다. 기존 본편과 승인 대본의 SHA256은 유지됐다. 정상 속도 연속 재생은 미검수이며 무음 시안이므로 음성 동기를 판정하지 않았다. 본편 미감 합격·업로드 승인으로 취급하지 않는다. 새 유료 미디어 생성·음성 생성·외부 전송은 수행하지 않았다.

기존 본편 미감 진단 및 최초 시안의 독립 검토는 `qa/character-quality-v1/`에 있다. 최신 확인 기록은 `checks/verification-v3.json`에 있다.
''','utf-8')
state_file=EP/'state.json';state=json.loads(state_file.read_text('utf-8'))
backup=OUT/'checks/state_before_quality_revision.json'
if not backup.exists():shutil.copy2(state_file,backup)
state['visual_quality_feedback']={'date':'2026-10-23','user_request':'막대 인물 교체, 낮은 모션 품질의 원인과 설치 필요성 확인','previous_stage':state['stage'],'status':'replacement_direction_sample_ready_full_film_revision_pending','sample_revision':'character-quality-v1/sample-v3','sample':str(Path(receipt['video']).relative_to(ROOT).as_posix()),'review_note':str(note.relative_to(ROOT).as_posix()),'full_film_visual_acceptance':'not_accepted_current_user_feedback','latest_sample_checks':str((OUT/'checks/verification-v3.json').relative_to(ROOT).as_posix()),'narration':'still_on_hold','external_send':False}
state['stage']='literature_visual_quality_revision_sample_ready_narration_on_hold';state['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
state_file.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
cfgfile=ROOT/'config/video_shelf.json';cfg=json.loads(cfgfile.read_text('utf-8'));entry=next(x for x in cfg['entries'] if x['name']=='지역별가격회복')
entry['status']='논문 본편의 인물·모션 품질 수정 중 · 20초 무음 교체 시안 v3 · 음성 생성 보류'
for alias,source in [('인물교체_20초_v3.mp4',OUT/'character_quality_sample_v3.mp4'),('인물교체_미리보기_v3.png',OUT/'checks/encoded-v3/12-19.9s.png'),('인물교체_검토안내.md',note)]:
    entry['files'][alias]=source.relative_to(ROOT).as_posix()
cfgfile.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'stage':state['stage'],'sample':receipt['alias'],'original_video_and_script_preserved':True},ensure_ascii=False))
