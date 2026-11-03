# v5 무료 로컬 검토본

배포 파일은 `outputs/production-v5/gyosan_review_v5_free_tts.mp4`이며 1920×1080, 30fps, 18분37.6초다. 원본 v4r1은 보존한다. 업로드하지 않는다.

승인 대본 v5의 중립 표현 15개 원문 유닛과 짧은 소제목을 반영했다. 전체 261개 의미 구절 중 발음문이 같은 240개 WAV는 내용 SHA가 동일한 원본을 재사용하고, 변경 21구절은 무료 로컬 Heami rate2로 새 생성했다. 자막은 원문 표기를 유지하며 실제 WAV 길이로 배치한다.

본문 지도·자료·가격표·필지·모션 소스 코드는 v4와 바이트 단위로 같다. 새 제목과 변경 자막을 합성한 PNG만 렌더했다. C2/B2 실제 필지와 위치도, M009 기존 실거래 발화의 비교차트 재호출을 유지한다. 배경음악·브랜드 인트로/아웃트로와 음성 끝부터 아웃트로까지 3초 hold를 유지한다. 하단 자막과 출처는 지도와 별도 고정 레이어다.

장면별 실제 시각과 변경 구절·제목·연결 경계의 요청 시각은 `outputs/production-v5/changed_timestamps.json` 및 `rendered_project.json`을 참조한다. 단일 정지 프레임 seek는 정확 절대 프레임을 보장하지 않는다. 전편 재생·실제 청취·발음 자연스러움 검수는 수행했다고 주장하지 않는다.

재현 순서는 `bootstrap.py` → `generate.ps1` → `timeline.py` → `prepare_visual.py` → `prepare_render.py` → `node render_delta.cjs --render` → `production_job.json`이다. 모든 실행 파일은 이 폴더 안의 버전별 복제본이며 기존 파이프라인은 수정하지 않는다. SAPI는 레지스트리 접근이 가능한 로컬 실행이 필요하다.
