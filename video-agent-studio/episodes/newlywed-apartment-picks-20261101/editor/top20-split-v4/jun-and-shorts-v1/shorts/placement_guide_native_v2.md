# Jun 쇼츠 3편 배치·재현 안내

작업 `3-native-vertical-shorts-Jun-v1`. 원생 1080×1920 / 30fps. 본편 영상 크롭 없이 별도로 배치한 HyperFrames 프로젝트다. 아래 이름은 실제 배포 예정 파일명이며, 생성·기술 확인 결과는 각 프로젝트의 `render_receipt.json`, `technical_check.json`과 최종 `handoff.json`에서 확인한다.

| 배포 파일명 | 권장 배치·사용 | 실제 lock 길이 | 자료 유형 |
|---|---|---:|---|
| `short01_promo_Jun_native_v2.mp4` | 홍보 쇼츠로 단독 사용, 00:00부터 전체 재생 | 39.800초 | 실제 지역 사진, 거주 순위 범위, 연수동·송도동 실거래 비교 |
| `short02_ranks20_16_Jun_native_v2.mp4` | 20~16위 내용 쇼츠로 단독 사용, 00:00부터 전체 재생 | 75.700초 | 실제 지역 사진 5곳, 5행 순위 목록, 거래 중위값·남동구 가격대 분포 |
| `short03_ranks15_11_Jun_native_v2.mp4` | 15~11위 내용 쇼츠로 단독 사용, 00:00부터 전체 재생 | 73.133333초 | 실제 지역 사진 5곳, 5행 순위 목록, 동별 거래 중위값 |

배포 폴더는 해당 episode의 `outputs/top20-split-v4/jun-and-shorts-v1/shorts/`다. 업로드·외부 전송은 이 작업에서 수행하지 않는다. 마지막 화면은 다른 순위 영상과 **20~11위 전체 본편**으로 안내한다. 10~1위가 공개되었다고 표현하거나 미확인 URL을 넣지 않았다. 실제 영상 연결은 총괄이 게시 상태를 확인한 뒤 처리한다.

레이어는 원생 세로 사진 배경(0번 graphics 트랙의 장면별 sub-composition), 순위·가격·조건, 상시 흰 자막 받침과 단일 captions 트랙(1번), 승인된 Jun·음악 master(2번) 순서다. 사진에만 미세한 정지사진 확대를 적용하며 인물·물·차량이 움직이는 생성 영상으로 소개하지 않는다. 표·자막·출처는 확대하지 않는다. 장면 전환은 실제 lock 경계에서 하드 컷한다.

내용편은 5행 순위·지역명·쌍 수를 첫 화면부터 CTA 끝까지 유지한다. 현재 지역의 정식 소속은 제목 위 별도 줄에 표시한다. 두 가격 숫자는 각 native character anchor 전까지 숨기고 정확한 값으로 공개하며, 막대만 약 0.42초 동안 늘어난다. 숫자 카운트업이나 임의 중간 가격은 없다. 남동구는 지도 연결 **77단지 중 5억 미만 61단지 / 5~7억 16단지** 분포이며 거래 중위값 두 개로 표시하지 않는다. 원미구 첫 집단은 **2000년까지 준공**으로 2000년을 포함한다.

프로필은 `youtube_portrait_full_frame_v2`: 중요 글자 경계 x140~840 / y260~1360. 제목 56px 이상, 본문 자막 54px, 핵심 수치 52px 이상, 조건·출처 26px 이상이다. 사진과 도형은 화면 끝까지 이어진다. 상단 헤더 y0~240, 우측 레일 x900~1080, 하단 메타데이터 y1400~1920은 자체 UI 모형으로 따로 검사한다. 실제 모든 기기·앱 화면에서의 재생 검증을 뜻하지 않는다.

가격 조건: 전용 83~85㎡, 2026년 5~10월 계약, 2026년 11월 3일 조회·취소 제외. 10월은 조회일까지의 신고분이다. 순위는 2024년 11월 1일 신혼부부 거주 수 기준이다. 거래값을 현재 매물·구매 가능 가격으로 해석하지 않는다. 사진의 저자·라이선스·촬영 연도는 읽기 영역에, 원문 URL·이용조건·자세한 장소·크롭 설명은 각 `credits_manifest.json`에 보존한다.

음성·음악은 총괄이 제공한 master를 레벨·속도·문구 변경 없이 사용한다. 제공된 최종 여운 약 1.05초와 CTA 화면을 보존한다. 5초/10초 브랜드 범퍼는 없다. 실제 청취 및 연속 시청은 별도 QA 항목이다.

재현 명령(프로젝트 루트에서 실행):

```powershell
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-split-v4/jun-and-shorts-v1/shorts/build.py --version native-v2
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-split-v4/jun-and-shorts-v1/shorts/measure.py --version native-v2
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-split-v4/jun-and-shorts-v1/shorts/pipeline.py check --version native-v2
tools/python311/python.exe -X utf8 video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-split-v4/jun-and-shorts-v1/shorts/pipeline.py deliver --version native-v2
```

이미 렌더된 버전은 빌더·렌더러가 덮어쓰지 않는다. 재제작은 새 프로젝트 버전과 새 배포 파일명을 사용해야 한다. Studio가 편집용 `data-hf-id`를 추가한 경우에는 속성 추가 외 변경이 없음을 바이트 단위로 확인한 뒤 입력 manifest를 다시 동결한다. 기술 결과는 실제 출력 파일의 probe·전체 A/V decode·AAC와 동결 master의 PCM 상관·인코딩된 대표/경계 프레임으로 남긴다.
