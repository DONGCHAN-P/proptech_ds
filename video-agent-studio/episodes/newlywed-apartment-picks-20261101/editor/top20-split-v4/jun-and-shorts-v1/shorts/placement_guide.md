# Jun 쇼츠 native-v4 배치·재현 안내

배포 폴더는 해당 episode의 `outputs/top20-split-v4/jun-and-shorts-v1/shorts/`다. 원생 세로 1080×1920, 30fps, 48kHz 스테레오. 실제 파일·해시는 각 `render_receipt.json` 및 배포 manifest를 따른다. v2와 기존 v3 산출물·소스·로그를 보존한다.

| 배포 파일명 | 추천 사용 시간 | lock 길이 | 자료 유형 |
|---|---|---:|---|
| `short01_promo_Jun_native_v4.mp4` | 00:00부터 전체 재생, 본편 홍보 | 39.800초 | 실제 지역 사진, 53개 구와 20~11위 범위, 연수동·송도동 거래 중위값 |
| `short02_ranks20_16_Jun_native_v4.mp4` | 00:00부터 전체 재생, 20~16위 내용편 | 75.700초 | 실제 지역 사진 5곳, 5행 목록, 거래 중위값·남동구 단지별 분포 |
| `short03_ranks15_11_Jun_native_v4.mp4` | 00:00부터 전체 재생, 15~11위 내용편 | 73.133333초 | 실제 지역 사진 5곳, 5행 목록, 동별 거래 중위값 |

프로젝트는 `editor/top20-split-v4/jun-and-shorts-v1/shorts/native-v4/<short_id>/`에 있다. 장면별 sub-composition은 graphics 트랙 0, 전체 자막은 captions 트랙 1, 승인된 Jun·음악 master는 audio 트랙 2다. 실제 lock 경계에서 하드 컷한다. 사진만 미세하게 확대하며 글자·자막·출처는 고정한다. 자료 유형은 실제 사진에 적용한 정지사진 배경 모션이다.

각 자막 큐가 배경과 본문을 한 그룹으로 소유한다. native cue의 `[start,end)` 동안만 그룹 전체를 표시한다. 첫 발화 전·문장 사이·장면 사이·마지막 CTA의 무자막 구간에는 배경과 본문이 함께 사라진다. 원문·줄바꿈·폰트·큐 시간·음성·전체 길이는 유지한다.

v4 화면의 `price-note`는 **“10월은 조회일까지 신고분”** 또는 **“10월 계약은 조회일까지 신고분”**이다. 전용 83~85㎡, 2026년 5~10월 계약, 2026년 11월 3일 조회·취소 제외 조건을 유지한다. 순위는 2024년 11월 1일 신혼부부 거주 수다. 가격·중위 집단·표본수는 승인값을 그대로 쓴다. 원미구는 “2000년까지 준공”으로 2000년을 포함하며, 남동구는 지도 연결 77단지 중 5억 미만 61단지 / 5~7억 16단지의 분포다. 숫자는 native anchor에서 정확한 값으로 공개하고 막대만 약 0.42초 동안 늘어난다.

안전영역은 `youtube_portrait_full_frame_v2`, x140~840 / y260~1360. 제목 56px 이상, 자막 54px, 핵심값 52px 이상, 조건·출처 26px 이상이다. 배경은 화면 전체를 채운다. 사진 저자·라이선스·촬영 연도는 읽기 영역에, 상세 URL·장소·이용조건은 `credits_manifest.json`에 보존한다. 음악 출처 표기는 배포 파일명과 같은 `.description.txt`에 제공한다.

CTA는 다른 순위 영상과 **20~11위 전체 본편**으로 연결한다. 실제 URL은 총괄이 게시 상태를 확인한 뒤 연결한다. 이 편집 작업의 외부 전송·업로드·새 TTS/API 호출은 0회다.

저장소 루트에서 재현한다. 출력된 버전은 덮어쓰기 가드가 보호하므로 재작업은 새 버전·새 파일명을 쓴다.

```powershell
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-split-v4/jun-and-shorts-v1/shorts/build_native_v4.py --version native-v4
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-split-v4/jun-and-shorts-v1/shorts/check_native_v4.py
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-split-v4/jun-and-shorts-v1/shorts/run_native_v4.py
```

PROMO+SH03을 각각 2워커로 병렬 출력하고 SH02를 2워커로 잇는다. 프로젝트·출력·로그·상태·캐시는 분리하며 동시 렌더 워커는 최대 4개다. 실제 포트 관측은 `native-v4/runtime_port_check.json`에 있다. MP4 probe·전체 A/V decode·AAC와 동결 master PCM 상관·인코딩 증거 프레임을 각 프로젝트에 남긴다. 실제 청취·연속 시청과 최종 독립 QA 범위는 해당 검수 기록을 따른다.
