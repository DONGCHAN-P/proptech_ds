# 교산 대장 후보 쇼츠 v1

## 최신 수정본 v1r2

- 배포 파일: `gyosan_leader_short_v1r2.mp4` (v1 원본 보존).
- C2/B2 상세 지도의 실제 높이를 485px로 맞추고 필지 중심으로 재배치했습니다. 전체 위치지도는 좌측으로 이동했습니다.
- 음성·SRT·제목·자막·출처 위치는 v1과 같습니다.
- 실제 MP4 검토용 프레임: `encoded-r2-17.png`, `encoded-r2-33.png` 등 10장.
- 재현: `prepare_r2.py` → `raster_r2.cjs` → `measure_r2.cjs` → `render_command_r2.json`의 argv → `finalize_r2.py`.
- 최신 인수인계: `handoff_r2.json`, 검수 근거: `layout_validation_r2.json`.

- 배포 파일: gyosan_leader_short_v1.mp4 / 1080×1920·30fps·약50.43초
- 기존 Jun M008 의미 단위10개 PCM 원문 발췌. 120ms 구간 사이 쉼, 마지막 무음 본편 유도3초. 속도 변경 없음.
- 기존 공식 토지이용계획 필지 지도 재사용. C2/B2 실제 필지 채색, 상세 장면에 전체 지구 위치도. 장면간 정직한 컷, 필지 강조0.8초.
- 자막54px·핵심수치52px·출처26px, 출처는 자막 아래. 기존 영상 축소 카드 아님.
- 신규 AI 이미지/음성/유료 생성 없음. 기존 Jun 합성음성 재사용이며 청취 품질의 재심사는 미실시.
- 재현: prepare.py → optimize.py → raster.cjs → measure.cjs → render_command.json argv → finalize.py. prepare는 entry최적화를 되돌리지 않으므로 수정본 보존.
- 실제 청취·연속 재생은 실시하지 않음. root 독립QA 후 업로드.
