# 구성과 재현 메모

- 확정 입력: scenes `v1.1-30s-text-locked`, script `script_v1_1.md`, inputs/manifest.json의 A01–A13, visual/office.mp4·pantry.mp4·team.mp4.
- 원본 13개 모두 실제 영상에 표시한다. 원본 사진 A02/A04/A11은 생성 참고 외에 원본 인서트로도 표시한다. 실제 표시 구간은 asset_usage.json에 기록한다.
- A05 GIF는 원본 7프레임과 각 delay(ms)를 추출한 뒤 총23.1초를 장면 3초에 압축하여 전체 프레임을 표시한다(7.7배속). `입력·요건서 정리 과정 · 빠르게 재생`을 화면에 표시한다. `data.json.gif_durations`에 원본 delay가 있다.
- 한글 글꼴은 public/data-insight-v1에 복사한 Pretendard Regular/Bold WOFF2. 코드의 font-face로 로드하며 모든 합성 글자는 브라우저 글꼴 렌더링이다. 생성모델에는 글자 작화를 요청하지 않는다.
- 음악은 prepare.py에서 deterministic sine pad, bell arpeggio, soft pulse를 직접 합성한 44.1kHz stereo PCM. Original procedural composition. 외부 음악 라이선스나 타 채널 음원·로고를 재사용하지 않았다.
- 인물 소스는 1280×720 생성 영상이다. 0.5초부터 4초씩 1080p 프레임에 확대하여 사용한다. 인물 장면에는 AI 재현을 표시한다.
- S1 중복 보조문구 삭제 전 렌더는 outputs/v1/data_insight_30s_v1_pre_qa.mp4로 보존했다. 현재 최종 파일은 data_insight_30s_v1.mp4다.
- 첫 기술검사에서 FFmpeg 기본 null encoder가 미지원되어 실패했다. explicit rawvideo/pcm_s16le encoder로 수정하고 새 검사를 수행했다. ffprobe count_frames로 전체 900프레임을 확인한다.
- 영상 트랙은 정확히 900프레임/30fps=30초. AAC 인코딩 패딩 때문에 컨테이너 duration에는 수 ms 차이가 있을 수 있다.
- 검수 범위: 원본 contact, Remotion 대표스틸, 최종 인코딩 sampled frame, ffprobe streams/count_frames, 전체 decode. 실제 연속 재생과 실제 음악 청취는 편집 담당이 완료했다고 주장하지 않는다. 독립 QA에게 해당 범위를 전달한다.
