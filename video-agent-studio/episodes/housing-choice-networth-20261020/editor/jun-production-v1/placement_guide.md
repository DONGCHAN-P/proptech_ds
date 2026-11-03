# 매매 전세 월세 Jun 최종 영상 배치 가이드

대본 v6와 기존 화면을 유지하고 ElevenLabs Jun 실제 음성에 맞춰 자막·장면·강조 시점을 연결한 렌더본입니다. 비공개 업로드는 별도 검수·게시 절차에서 기록합니다.

- 본편: `video-agent-studio/episodes/housing-choice-networth-20261020/outputs/jun-production-v1/renders/measured-jun-v1/housing_choice_jun_v1.mp4`
- 본편 SHA256: `136a20c43ba3a99a138ba7282c1fb1a8532fc3aa92695c57ca2f904d011b1079`
- 자막: `video-agent-studio/episodes/housing-choice-networth-20261020/outputs/jun-production-v1/captions_measured.srt`
- 자막 SHA256: `8aae8aa974108c22ff297f9a0619baecf56cd7264ec29a8cdf557cc2b88038ce`
- 편집 소스: `outputs/jun-production-v1/ch01`부터 `ch10`의 index.html
- 시간표: `narration/jun-production-v1/final_timing.json`
- 조립 시간표: `outputs/jun-production-v1/assembly_edl.json`
- 실제 프레임: `outputs/jun-production-v1/encoded_frame_plan.json`
- 제목·설명·선택 썸네일: `outputs/jun-release-v1`

출력은1920×1080·30fps·H.264/AAC이며 실제 길이는1192.433333초입니다. 자막206개는 영상에 포함했고 동일한 SRT를 별도로 제공합니다.

첫 문단의 실제 발화가 끝난19.5초에5초 브랜드 인트로를 삽입합니다. 본문은 장별 PCM·공급자 문자 정렬을 기준으로 재배치했습니다. 마지막 실제 발화 끝1179.403333초 이후3.03초 유지하고1182.433333초에10초 아웃트로를 시작합니다.

| 장 | 시작 | 주제 |
|---|---|---|
| 1 | 00:00 | 선택 |
| 2 | 01:28 | 기준 |
| 3 | 03:57 | 출발 자금 |
| 4 | 05:59 | 매달 나가는 돈 |
| 5 | 07:40 | 원금과 보증금 |
| 6 | 09:16 | 투자수익 |
| 7 | 11:07 | 10년 후 |
| 8 | 12:52 | 조건의 변화 |
| 9 | 16:06 | 실행 |
| 10 | 17:36 | 다음 선택 |

새 음성은 원래의 Jun 속도로 사용하며 이전 InJoon 길이에 맞추지 않았습니다. BGM은 기존 Thinking Music을 새 Jun 음성 기준으로 carve·덕킹해 섞었습니다. 음량 측정은통합-17.2LUFS·true peak-2.0dBFS입니다.

전체 AV 디코드·실제 인코딩 표본 프레임·전체 자막과 원문 정렬·선택34문단 음성인식·신호 검수 기록을 제공합니다. 실제 청취·연속 재생·Studio Content ID 확인은 수행하지 않았습니다. 독립 검수 범위와 미해결 권고는 `qa/jun-production-v1/final_review.json` 및 `qa/jun-production-v1/findings.json`에 기록합니다.

기존 본편·음성·원본·승인 기록은 보존합니다. 새 비공개 업로드의 처리·한국어 자막 제공을 확인한 뒤 기존 비공개 exEGpjcqdF0 한 편만 교체 삭제합니다. 다른 비공개 영상과 공개 기준본은 유지합니다.
