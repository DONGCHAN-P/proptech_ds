# TOP20 편집 배치 · 제작 v1

최종 무료 음성 v3와 총괄의 실제 타임록/쇼츠 완성 WAV를 연결했다. 아래 배포명으로 렌더 중이며 최종 생성·기술검사 결과는 `render_receipt_*.json`에서 확인한다.

| 배포 파일명 | 추천 위치·길이 | 레이어·전환 | 자료 유형 |
|---|---|---|---|
| `outputs/top20-production-v1/main/top20_main_free_v1.mp4` | 本편 전체470.955초(약7분51초) | 훅0~23.47254 → clean v7 브랜드5초 → O002~C001 → 마지막 완결 발화부터 총3초 여백 → clean v7 아웃트로460.955~470.955. 고정 흰 자막/출처는 사진과 별도. 장면 경계 즉시 컷. | 실제 장소 사진20장(원본 바이트/비율 보존 contain), 실제2024 경계 SVG, 검증 통계 비례 막대/변화선 |
| `outputs/top20-production-v1/shorts/top20_promo_free_v1.mp4` | 홍보용33.886871초 | 원문7문장, 총괄 제공 완결 문장 컷/WAV. 마지막 발화+3초(기존 꼬리 포함). | native1080×1920 재배치, 미추홀/노원 실제 사진과 공통 척도 막대, 실제 TOP20 지도 |
| `outputs/top20-production-v1/shorts/top20_analysis_free_v1.mp4` | 내용용41.100363초 | 원문8문장, 총괄 제공 원음 재사용. 위와 같은 완결문/여백 계산. | native1080×1920, 옛 서구/강남 실제 사진·실제 지도·2023/2024 수치 |

모든 표시는 `scene_id`와 `sentence_id`로 연결한다. 본편 원본 v3와 총괄 편집 v4는 수정하지 않는다. `build.py --script <scene_proposals_v4.json> --timing <locked_timing.json> --shorts <shorts_clips_locked.json>`으로 재현한다. `lock_shorts.py --timing <locked_timing.json>`으로 새 음성에 맞춘 선택 문장·파형 무음 경계를 생성한다.

쇼츠는 `youtube_portrait_full_frame_v2`의 텍스트 x140~840/y260~1360을 사용한다. 사진·지도는 전체폭 배경 레이어, 제목·숫자·자막·출처는 독립 배치한다. 2024·수도권53개구·쌍 단위는 항상 표시하며 전년 비교는2023·2024를 함께 명시한다.

사진별 작가·촬영연도·개별 라이선스/원문 링크는 `credits.json`/`credits.md`, 지도 가공·좌표 원본 해시는 `input_manifest.json`에 있다. AI 개념 이미지나 생성 동영상은 사용하지 않는다. 모든 원본은 보존했다.

본문/두 쇼츠 BGM은 Thinking Music 원본에 canonical carve를 각각 적용했다(`audio_carve_receipt.json`). 기존 audio-deps의 core0.8.181을 재사용했고 새 설치/생성이 없다. 브랜드 구간은 별도 bed를 음소거하여 clean v7 내장 음악을 중복시키지 않는다. 설명란 필수 크레딧: Thinking Music by Kevin MacLeod | incompetech.com | Licensed under Creative Commons: By Attribution 4.0. 새 TTS·유료 생성·업로드는 이 편집 담당이 실행하지 않는다. 최종 비공개 업로드는 총괄 담당이다.

재현 순서: `build.py` → `apply_bgm.py` → `local_jobs.py check all` → `local_jobs.py render all --version v1`. FFmpeg는 select/psnr 필터가 있는 기존 full build를 명시한다. Remotion 번들 FFmpeg는 select가 없어 브랜드 스냅샷 주입이 실패했으며 이 경로 문제를 해결했다. Studio preview는 사용자 상태 폴더 로그 생성이 EPERM으로 차단되어 열지 못했다. 로컬 check/PNG와 실제 인코딩 파일 검수를 구별한다.

실제 MP4 기술검사/전체 decode/경계 프레임은 렌더 후 `render_receipt_*.json`, `evidence/encoded-*`에 기록한다. 표본/자동 배치 검사와 실제 청취·연속 재생을 구별한다.
