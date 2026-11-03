# Data Insight v1 배치

배포 파일: `outputs/v1/data_insight_30s_v1.mp4` — 30초, 1920×1080, 30fps. 900프레임.
캡션: `outputs/v1/captions.srt`. 무대사 화면 자막의 별도 사본이다.

| 시간 | 장면 | 레이어·전환 | 자료 유형 |
|---|---|---|---|
| 00–04 | S1 | 전체 인물영상, 회색/컬러 분할, 원본 3개 인서트, 다크 자막 | AI 재현 + A02/A07/A13 원본 |
| 04–07 | S2 | 회색 원본 사진, 순차 등장 경로 | A04 원본 |
| 07–10 | S3a | 큰 제목, 시그널/프로모션 예시 역할 라벨, 원본 패널 | A01/A07 원본 |
| 10–13 | S3b | 로즈 메시지, UI 원본 패널 | A03/A09 원본 |
| 13–16 | S3c | 로즈 메시지, GIF 7프레임 3초 압축 재생 + 보조 패널, 빠르게 재생 표기 | A05 GIF/A12 원본 |
| 16–19 | S3d | 타임라인 전체 contain, 큰 별도 메시지 | A10 원본 |
| 19–23 | S4 | 전체 인물영상, 보라 그라데이션, 알림 자료 인서트 | AI 재현 + A04/A08/A01 원본 |
| 23–27 | S5 | 전체 인물영상, 성과 큰 텍스트, 원본 몽타주 | AI 재현 + A11/A06/A08/A10 원본 |
| 27–30 | S6 | 딥보라 엔딩, 원본 보조 패널 | A06 원본 |

컷은 정확한 timing lock에서 전환한다. 제목의 첫 12프레임은 위치·불투명도로 등장한다. 원본 UI에는 줌을 적용하지 않는다. 인물 영상은 1280×720 생성 소스를 1920×1080에 확대하며, 각 소스 0.5–4.5초를 사용한다. 해당 장면의 ‘AI 재현’ 표기는 화면에 유지된다.

음악: `video/public/data-insight-v1/bgm.wav`. 직접 합성한 original procedural composition. 외부 음악·타 채널 브랜드는 사용하지 않았다. 연속 재생·실제 청취 검수는 이 편집 담당의 완료 범위에 포함하지 않는다.

재현: 프로젝트 루트에서 `tools/python311/python.exe -X utf8 analysis/video_task_runner.py video-agent-studio/episodes/data-insight-20261019/editor/render_job.json`.
원본 준비 코드: `editor/prepare.py`; 렌더 job 생성: `editor/build_job.py`; 기술 검사: `editor/verify.py`; 독립 Remotion 엔트리: `video/src/data-insight-v1/entry.tsx`.
