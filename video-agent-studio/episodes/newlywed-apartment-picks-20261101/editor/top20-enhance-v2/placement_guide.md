# TOP20 개선 메인 배치 가이드

배포 파일명: `top20_main_enhanced_v1.mp4`.
총괄 렌더 경로: `outputs/top20-enhance-v2/main/top20_main_enhanced_v1.mp4`.
편집 담당은 전체 MP4를 렌더하지 않았습니다. 실제 파일 생성·해상도·fps·오디오 스트림·전체 디코드는 총괄의 `render_receipt_main_v1.json`으로 확인합니다.

실제 PCM/단어 메타데이터 잠금: `director/top20-enhance-v2/locked_timing.json`.
원고: 같은 폴더의 `scene_proposals_v5.json`과 `script_v5.md`.
계획 길이는528.300091초(8분48.300초), 장면은29개입니다. 실제30fps 인코딩 길이는1프레임 이내 오차를 검사합니다.

사진은 실제 장소 자료사진이며 원본 비율 유지 contain입니다. 실제 장소명·촬영연도(미확인이면 연도 미상)·개별 작가/라이선스를 화면에 유지합니다. 전체 권리와 출처URL은 `credits.json`, `credits.md`에 있습니다. 원본 사진 바이트를 보존하고 생성 보정·색보정·크롭을 하지 않았습니다. 지도는2024 원본 SVG의 실제 좌표 경계를 정적으로 사용하고, 같은 지도 내 위치 안내를 작게 곁들입니다.

레이어는 크림 배경·사진/구 경계/차트 → 제목·통계 출처 → 하단 흰 자막 순입니다. 출처는 y885, 자막 레일은 y922~1052입니다. 사진·지도 줌 없이 장면 경계에서 컷으로 전환합니다. 정확한 최종 숫자와 행 강조를 실제 발화의 단어 앵커에 연결하며 count-up은 없습니다. 앵커가 없는 수치는 정적 근거값으로 표시하고 `anchor_audit.json`에 기록합니다.

미래 순위는 이름·값·막대를 `???`로 가립니다. 현재 지역과 이미 소개한 지역만 공개하고1위 장면에서 모두 공개합니다. N001/N002는 같은53개 구·같은2024.11.1 기준의 전체 수/초혼 수 비교입니다. 시간에 따른 상승·하락으로 표현하지 않습니다. 새 지역은 처음 등장할 때 시·구 전체 이름으로 표시합니다.

기존 clean v7 브랜드 intro/outro와 Thinking Music을 재사용합니다. BGM은 메인 새 길이에 맞춰 반복하고 브랜드 구간과 중복되지 않게 처리했습니다. canonical carve는 기존 로컬 의존성을 재사용했습니다. 실제 청취 완료를 뜻하지 않습니다. C001의 마지막 화면을 E001에서 그대로 유지하며 마지막 발화 후 총3초 뒤 브랜드 아웃트로로 이어집니다. 무음 구간에는 흰 자막 레일을 표시하지 않습니다.

|장면|추천 시작|길이(초)|구도 / 자료 유형|
|---|---:|---:|---|
|O001|00:00.000|23.472540|실제 자료 · 정확한 통계 비교|
|O002|00:28.473|22.008413|실제 자료 · 정확한 통계 비교|
|S003|00:50.481|11.297211|사진 중심 · 실제 사진/구 경계/순위 사다리|
|S004|01:01.778|11.362018|비교 중심 · 실제 사진/인접 비교 막대/순위 사다리|
|S005|01:13.140|6.741088|사진 중심 · 실제 사진/구 경계/순위 사다리|
|S006|01:19.881|10.338639|사진 중심 · 실제 사진/구 경계/순위 사다리|
|S007|01:30.220|19.804467|비교 중심 · 실제 사진/인접 비교 막대/순위 사다리|
|I001|01:50.024|29.710363|실제 자료 · 정확한 통계 비교|
|S008|02:19.735|12.111859|비교 중심 · 실제 사진/인접 비교 막대/순위 사다리|
|S009|02:31.847|9.682268|사진 중심 · 실제 사진/구 경계/순위 사다리|
|S010|02:41.529|14.658322|비교 중심 · 실제 사진/인접 비교 막대/순위 사다리|
|S011|02:56.187|11.323333|비교 중심 · 실제 사진/인접 비교 막대/순위 사다리|
|S012|03:07.511|17.194830|사진 중심 · 실제 사진/구 경계/순위 사다리|
|I002|03:24.705|35.415147|실제 자료 · 정확한 통계 비교|
|S013|04:00.120|21.801678|비교 중심 · 실제 사진/인접 비교 막대/순위 사다리|
|S014|04:21.922|14.807778|사진 중심 · 실제 사진/구 경계/순위 사다리|
|S015|04:36.730|16.375261|비교 중심 · 실제 사진/인접 비교 막대/순위 사다리|
|S016|04:53.105|12.516327|사진 중심 · 실제 사진/구 경계/순위 사다리|
|S017|05:05.622|12.662313|비교 중심 · 실제 사진/인접 비교 막대/순위 사다리|
|I003|05:18.284|26.631134|실제 자료 · 정확한 통계 비교|
|S018|05:44.915|17.831270|상위5 · 실제 사진/구 경계/순차 공개 순위|
|S019|06:02.746|10.430658|상위5 · 실제 사진/구 경계/순차 공개 순위|
|S020|06:13.177|12.414467|상위5 · 실제 사진/구 경계/순차 공개 순위|
|S021|06:25.591|16.518481|상위5 · 실제 사진/구 경계/순차 공개 순위|
|S022|06:42.110|27.379070|상위5 · 실제 사진/구 경계/순차 공개 순위|
|N001|07:09.489|26.169683|기준 비교도 · 전체/초혼 · 같은53개 구·같은 기준일|
|N002|07:35.659|31.175351|기준 비교도 · 전체/초혼 · 같은53개 구·같은 기준일|
|C001|08:06.834|29.097982|실제 자료 · 정확한 통계 비교|
|E001|08:35.932|2.368141|마지막 화면 유지 · 무음/자막 없음|

프로젝트 루트에서 실행하는 재현 명령입니다. 현재 runner와 실제 렌더 소유자는 총괄입니다.

```powershell
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-enhance-v2/build.py --script video-agent-studio/episodes/newlywed-apartment-picks-20261101/director/top20-enhance-v2/scene_proposals_v5.json --timing video-agent-studio/episodes/newlywed-apartment-picks-20261101/director/top20-enhance-v2/locked_timing.json
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-enhance-v2/apply_bgm.py
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-enhance-v2/local_jobs.py check main
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-enhance-v2/local_jobs.py render main --version v1
```

`build.py`는 index.html을 새로 생성하므로 재빌드 뒤에는 BGM 적용과 검증을 다시 합니다. Shorts를 자동 생성하지 않습니다. 새 장면은 `extra_scenes.py`의 함수 등록 또는 `--visual-module <local.py>`의 `SCENE_RENDERERS`로 추가합니다. `--scene-data <JSON>`은 아래 형식을 받습니다. 추가 scene_id는 script와 timing 양쪽에 있어야 합니다. 장면 수27개 고정 조건은 없습니다.

```json
{"scenes":{"N003":{"type":"rank_criteria","rows":[{"name":"지역 전체 이름","total_rank":22,"first_rank":16,"first_count":6510,"anchor":"정확한 발화 구절"}],"takeaway":"검증된 비교 설명"}}}
```

편집 동결 당시 check34시점과34개 스냅샷이 통과했습니다. 이후 총괄 preview가 HTML의 data-hf-id를 정규화하고 .thumbnails를 생성하여 총괄이 runner 지문과 check를 갱신 중입니다. source_freeze.json의 SHA는 최초 동결 기록입니다. 이후 정규화된 프로젝트와 일치한다고 주장하지 않습니다. preview 포트는3049입니다.

검수 증거는 `evidence/snapshots-main-locked/`, `evidence/final-representatives/`, `evidence/before-after3/`입니다. 전후 비교는 기존 MP4 디코드 정지영상과 개선 프로젝트 스냅샷의 비교입니다. 개선 MP4의 실제 디코드 비교는 총괄/QA가 수행합니다. 연속 재생·실제 청취·발음 판정은 수행하지 않았습니다.
