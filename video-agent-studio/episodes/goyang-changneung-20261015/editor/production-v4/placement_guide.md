# 창릉 v4 배치·재현 안내

주산출물: `outputs/production-v4/changneung_full_v4r2.mp4` (출력·최종 QA 완료 여부는 handoff.json과 QA 기록으로 확인).
자막: `outputs/production-v4/changneung_full_v4.srt`.
편집 입력: `outputs/production-v4/project_v4.json`, 실제 렌더 상태: `rendered_project_v4.json`.

기준본 v3r2 원본을 보존한 수정 버전이다. 기존 승인 음성과 전체 24,140프레임/30fps를 보존한다. 기존 AAC 믹스 스트림을 재인코딩 없이 사용한다. 표기용 숫자·약어만 정규화하며 spoken_text와 원문 문자 span을 별도 보존한다. 고립된 동산동 소개 1큐만 다음 단지 문장과 합쳤고 전체 길이는 같다.

초반 전체권역 및 교통 지도에는 실제 창릉지구 경계와 세 후보 용지, GTX-A 창릉역 예정 안내권역을 다른 형태로 표시한다. 예정역 타원은 CM1·CM2 부근 위치 안내이며 역 시설 경계·출입구 핀이 아니다. M001의 2025.12 변경고시 설명 화면은 공식 원본 전체를 유지한다. LH 공개 공간정보 지도는 2026.10.16 조회 자료로 구분한다.

약 6:30 학교·생활 구간과 말미 후보 비교에는 실제 S5/S1/S4 토지이용 형상·학교·공원·도로 및 같은 좌표의 전체지구 locator를 사용한다. 상세도는 고정하며 동적 줌을 넣지 않는다. 실제 운영역 사진은 기존 2015 원흥역 자료화면의 날짜·저자·CC 라이선스를 유지한다. 학교 용지는 개교·배정 확정과 구분한다.

인트로 5초는 훅 뒤, 아웃트로 10초는 마지막 발화 기준 3초 후에 배치한다. 본문 하단 흰 자막박스를 유지하고 브랜드·마지막 홀드는 예외다. 지도와 자막은 별도 레이어다.

재현 순서(프로젝트 루트):

1. `node .../editor/production-v4/normalize_captions.cjs`
2. `node .../editor/production-v4/prepare_plan_geometry.cjs`
3. `node .../editor/production-v4/prepare_overlays.cjs`
4. `node .../editor/production-v4/build_project_v4.cjs`
5. `node .../editor/production-v4/render_frames.cjs`
6. `tools/python311/python.exe .../editor/production-v4/assemble_full_v4.py --ffmpeg-bin <기존 FFmpeg bin 경로> --output-name changneung_full_v4r2.mp4`

`...`는 `video-agent-studio/episodes/goyang-changneung-20261015`이다. 입력 해시는 `outputs/production-v4/source_freeze_v4.json`, 치환 내역은 `subtitle_normalization_v4.json`에 있다. `editor/production-v4/cache`는 이번 번들·공개자료 staging·조립 임시 캐시다. 원천 자료와 재현 소스는 캐시와 별도로 보존한다. 유료 호출·업로드는 없다. 실제 청취와 연속 재생은 수행했다고 주장하지 않는다.
