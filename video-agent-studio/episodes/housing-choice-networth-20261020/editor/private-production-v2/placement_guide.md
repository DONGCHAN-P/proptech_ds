# 실측 v6 배치 가이드

배포 대상: `outputs/private-production-v2/renders/measured-v6/housing_choice_private_v2_injoon_v6.mp4`. 1920×1080·30fps·H.264/AAC 48kHz stereo, 1525.266667초. 전체 decode 통과. v1 원본과 렌더는 보존했다.

클린 브랜드는 훅 뒤 5초와 마지막 10초다. `assembly_edl.json`의 같은 분할·전역 오프셋을 영상·음성·342큐 SRT에 적용했다. 각 접합에는 길이를 바꾸지 않는 예방적 8ms in/out fade를 적용했다.

| 장 | 본편 기준 시작 | 장 길이 | 파일/추천 구간 |
|---|---|---|---|
| 1 | 00:00:00.000 | 107.266667초 | `renders/measured-v6/ch01.mp4` 전체 |
| 2 | 00:01:52.267 | 194.233333초 | `renders/measured-v6/ch02.mp4` 전체 |
| 3 | 00:05:06.500 | 159.100000초 | `renders/measured-v6/ch03.mp4` 전체 |
| 4 | 00:07:45.600 | 128.000000초 | `renders/measured-v6/ch04.mp4` 전체 |
| 5 | 00:09:53.600 | 125.433333초 | `renders/measured-v6/ch05.mp4` 전체 |
| 6 | 00:11:59.033 | 144.866667초 | `renders/measured-v6/ch06.mp4` 전체 |
| 7 | 00:14:23.900 | 135.766667초 | `renders/measured-v6/ch07.mp4` 전체 |
| 8 | 00:16:39.667 | 252.233333초 | `renders/measured-v6/ch08.mp4` 전체 |
| 9 | 00:20:51.900 | 110.233333초 | `renders/measured-v6/ch09.mp4` 전체 |
| 10 | 00:22:42.133 | 153.133333초 | `renders/measured-v6/ch10.mp4` 전체 |

제목·본문 도식·출처·흰 자막 박스는 분리 레이어다. 장면 수명은 컷으로 전환하며 GSAP paused/seek-safe 연출을 유지했다. 그래프는 data_chart, 나머지 설명은 editorial_diagram이며 ch10/s10life는 생활 계획용 그림이다. 해당 RGBA 그림은 그 한 장면에서 한 번만 사용하고 실제 단지·면적·가격 증거로 표시하지 않았다.

`encoded_frame_plan.json`에 50장면의 추천 대표 시점·경계 전후·실제 전역 프레임 번호·175 PNG SHA가 있다. 원본 해상도 PNG와 contact sheet 5장은 `renders/measured-v6/encoded-evidence/`에 있다.

재현은 `render_commands.json`과 `render_pipeline.py`를 따른다. 완성본을 덮어쓰지 않는다. `prefix_reuse_receipt.json`은 ch01~03 입력 및 MP4 불변 증거다. 기술 검사와 표본 프레임 확인 범위는 `render_receipt.json`, `producer_frame_review.json`에 분리했다. 청취·연속 재생·최종 미디어 승인은 main/QA 후속이며 업로드는 수행하지 않았다.
