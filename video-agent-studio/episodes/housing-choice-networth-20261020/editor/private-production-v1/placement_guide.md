# 배치 가이드 · 실측 편집 v1

대본 기준: `outputs/script-final-v5/script_v5.md` / SHA `babeb15213477f3f6dcb8e8ab958e1a4ccc691c53c1fca6ca9ceae99cc5f269b`. 진실의 기준은 `director/two-episode-production-v1/locked_script.json`이다. 본문은 정식 final_timing.json의 실측 341큐에 연결되어 있습니다. 음성 속도와 발화 내용은 유지합니다. 현재 프로젝트 합계 1508.90초, 브랜드 5초·10초 포함 EDL 1523.90초.

실제 검증 프로젝트는 `outputs/private-production-v1/ch01/index.html` … `ch10/index.html`이다. 소스 프리뷰 18컷과 변경 6컷의 독립 검수가 통과했다. 현재 실제 출력은 `outputs/private-production-v1/renders/measured-v5/ch01.mp4`, `ch02.mp4`, `ch03.mp4`까지이며 합계 460.60초다. 각 파일은 1920×1080, 30fps, H.264/AAC 48kHz 스테레오이고 장별 전체 decode 검사가 통과했다. ch04 진입 전에 종료했으며 최종 본편 합본은 아직 없다. 인코딩 대표 6컷은 `renders/measured-v5/encoded-preview/`, 검사 기록은 `editor/private-production-v1/encoded_batch_review.json`에 있다.

| 장/장면 | 전체시각(measured_audio_units) | 길이 | 실제 장별 프로젝트 | 자료 유형 |
|---|---|---|---|---|
| 2/s2g | 02:26.14 | 49.26초 | ch02/index.html | data_chart |
| 2/s2p | 03:15.40 | 38.37초 | ch02/index.html | data_chart |
| 8/s8h | 16:41.30 | 48.53초 | ch08/index.html | data_chart |
| 8/s8l | 17:29.83 | 43.26초 | ch08/index.html | data_chart |
| 9/s9d | 22:07.65 | 33.12초 | ch09/index.html | editorial_diagram |
| 10/s10invest | 23:05.54 | 31.88초 | ch10/index.html | editorial_diagram |
| 10/s10stable | 23:37.43 | 25.82초 | ch10/index.html | editorial_diagram |
| 10/s10life | 24:03.25 | 32.58초 | ch10/index.html | ai_concept_living_space |
| 10/s10hold | 24:35.83 | 17.42초 | ch10/index.html | editorial_diagram |
| 10/s10next | 24:53.24 | 20.66초 | ch10/index.html | editorial_diagram |

각 장면의 제목·자료·출처·자막은 서로 분리된 레이어다. 그림과 그래프는 GSAP paused timeline의 opacity/transform/stroke로 표시하고 컷 경계는 clip 수명으로 처리한다. 본문 흰 자막 박스는 큐 사이에도 유지하며, 장 표지·클린 브랜드·마지막 발화 뒤 3초 CTA에는 숨긴다. 새 지도 줌이나 보행 캐릭터는 넣지 않았다.

`s2g`는 2006Q1부터 2026Q2까지의 실거래 연결지수 전체 경로와 2016Q2–2026Q2 가이드·양끝점을 표시한다. 세종은 2015Q1 시작이다. 연평균 수치는 facts.json의 해당 기간과 연결했다. `s8h`는 집값만 0/2/4/6%로 바꾸고 투자·대출·계약 조건은 고정한다. `s8l`의 5%는 첫해 비용 반영 전 자기자금 대비 평가액 변화다.

`s10life`의 `ch10/assets/housing-stability-v1.png`는 RGBA 생활 공간 그림으로 이 장면에서 한 번만 사용한다. 실제 단지·면적·가격을 뒷받침하는 자료로 쓰지 않는다. 생성/권리/SHA 기록은 `assets_manifest.json`에 있다. 장 표지는 각 장 자체 도식 조각을 사용하며 공통 price 사진을 반복하지 않는다.

클린 인트로는 첫 문단 발화 뒤 프레임 경계에 넣는다. `assembly_edl.json`의 분할·offset_map을 영상·음성·자막에 공통 적용한다. 실제 브랜드 영상은 150/300프레임이며 AAC 컨테이너 끝 길이로 본문을 밀지 않는다. 현재 자막은 실측 `captions_measured.srt`이며 전역 오프셋 EDL/SRT 독립 검수가 통과했다. 장별 MP4에는 브랜드가 아직 삽입되지 않았고 최종 조립에서 적용한다.

BGM은 고정된 Thinking Music을 쓰며 설명란 credit은 `editor/private-production-v1/music_credit.txt`를 그대로 전달한다. 고정 BGM에 canonical carve를 적용했다. ch01~03의 실제 믹스 인코딩과 decode는 통과했고 실제 청취·연속 재생은 후속 검수다. canonical voiceover carve 설계는 `audio_design.json`에 있다. 기존 Remotion FFmpeg 제약은 총괄이 제공한 media-bin/ffmpeg.exe로 해결했다. 프로세스 PATH에 full FFmpeg와 Remotion ffprobe 경로를 연결하며 전역 설치는 하지 않는다.

실측 빌드는 `build.py --require-measured --timing narration/free-tts-v1/final_timing.json --narration-handoff narration/free-tts-v1/handoff.full-v5.json`으로 생성했다. 변경 없는 현재 HTML을 다시 빌드할 필요는 없다. 체크는 `run_cli_checks.py`, 글자/패널 경계·역방향 seek는 `node .../validate_preview.cjs`, 대표 시간은 `snapshot_times.json`이다. 실행한 렌더 명령은 `render_pipeline.py --execute --qa-receipt qa/private-production-v1/preview_pass_receipt.json --stop-after-chapter 3`이다. 실제 argv·코드 SHA는 `render_commands.json`, 입력 HTML·출력 SHA와 장별 probe는 `renders/measured-v5/chNN.receipt.json`에 있다. CLI 0.8.181, delivery, 4 workers, 장별 `frames-cache/chNN`을 사용했다.

검수 범위: 현재 10장 소스의 headless Chrome 표본 DOM·글자 Range BBox·SVG stroke 경계·큐 사이 박스 연속성·역방향 seek 픽셀 동일성, CLI lint/runtime/layout/contrast, 실측 자막·T 앵커 연결, 독립 소스 프리뷰 검수. 실제 인코딩 결과는 ch01~03의 전체 decode와 대표 6컷 직접 확인까지 완료했다. 청취·연속 재생을 수행했다고 판정하지 않는다. ch04~07의 발화 값 ASR 재확인 결과를 총괄·narration·QA에서 전달받은 뒤 렌더 확장을 진행한다. 최종 조립과 업로드는 실행하지 않았다.
