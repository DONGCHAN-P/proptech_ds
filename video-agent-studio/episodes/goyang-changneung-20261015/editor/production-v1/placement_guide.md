# 창릉 편집 준비 v1

이 폴더는 본편 완성본이 아니다. script-v2는 승인 대기이며 실제 음성·문자정렬·타임록·최종 지리 소스가 없다. 본편 렌더를 하지 않았다. `render_contract.template.json`의 null을 임의 추정 시간으로 채우지 않는다.

총괄 지정 최종 검토 대본: `outputs/script-review-v2/script_v2.md`, SHA256 `74ed7a1af1146a7b0f93b6602869222026667dbb8de2ea0137ee81e66eb3bbba` (실제 해시 대조). script 결정 `81cdb3c2a358`, budget 결정 `fef620079862`는 현재 pending이며 승인으로 기록하지 않는다.

| 실제 배포 자산 | 추천 위치 | 길이 | 레이어·전환 | 자료 유형 |
|---|---|---|---|---|
| `outputs/editor-preflight-v1/brand_intro_generic_v1.mp4` | M000 훅 종료 뒤, 실제 문자정렬 경계 확정 후 | 영상 150f, 5초 | 자체 음악 포함. 내레이션·흰 자막 박스 숨김. 본문 음악 중복 금지 | 기존 AI 개념 도시 브랜드의 지역 문구만 범용화 |
| `outputs/editor-preflight-v1/brand_outro_generic_v1.mp4` | M009 마지막 발화 종료 90f 뒤 | 영상 300f, 10초 | CTA 마지막 화면 3초 유지 후 연결. 자막 박스 없음. 자체 음악 포함 | 기존 AI 개념 도시 브랜드의 지역 문구만 범용화 |
| `video/public/namyangju-map-led-v6/data_city_ambient_v1.wav` (repo 상대) | 본문 발화 구간 | 원본 64초 루프 | 48kHz stereo 믹스 변환, 진입/종료 페이드, 내레이션 덕킹. 기존 v15의 .18 gain은 참고값이며 최종 청취로 결정 | 로컬 합성, 샘플링 없음. 동명 `.license.json` 보존 |

브랜드 MP4 컨테이너 길이는 AAC 패킷 때문에 각각 5.013/10.005초다. 조립은 영상 150/300프레임과 48kHz 기준 240,000/480,000샘플을 기준으로 한다. 컨테이너 길이 누적을 사용하지 않는다. 음원·디자인·원본 파일은 보존했다. 신규 생성형 호출과 비용은 0이다.

## 실제 본편을 만드는 경로

1. 총괄이 script-v2 및 예산의 정확한 승인 파일과 해시를 고정한다. narration이 각 M000~M009의 원본 음성·해시·실제 길이·승인 원문 문자정렬을 납품한다. M000 훅 뒤 5초 브랜드 삽입은 장 중간이므로 **장 전체 음성 시작/끝만으로는 부족하다.** 훅 마지막 문자 offset과 분할 샘플을 받아 원음 손실 없이 분할한다.
2. 총괄이 실제 `timing_lock`을 기록한다. 자막 큐는 `scene_id + 승인 원문 offset`으로 연결한다. 원문 정규화 대조, 숫자·단위·역명 보호 후 프레임으로 반올림한다. CTA 끝은 마지막 발화 문자 끝 + 90프레임이며 PCM 꼬리를 그 시간에 포함한다.
3. visual이 아래 보완 소스를 완성한다. 현 시안 PNG를 장 전체에 붙이는 방식은 금지다. `M003/M004/M005`를 각각 지리/시간축/가격 근거/실제 시설 화면으로 나누고 발화 트리거를 대응한다. 각 shot은 source_type, 실제 파일/해시, 권리 근거/해시, 지리 검수 상태, start/end, 화면 목적을 가진다.
4. 공통 `video/src`를 건드리지 않고 `editor/production-v1/`에 본편 엔트리와 장 컴포넌트를 추가한다. 기존 `video/src/namyangju-landuse-v8/PersistentCaptions.tsx`는 스타일·큐 조회 코드만 참고한다. 왕숙 project/type/좌표/자막 원문은 가져오지 않는다. `video/src/namyangju-v15/cta_entry.tsx`의 벨·좋아요 진입 모션만 창릉 M009 정렬에 맞춰 이식한다. `DateTimeline.tsx`는 레이아웃 로직만 참고하고 날짜는 창릉 `research/production-v2/calendar.json`에서 로드한다.
5. 본문 화면 영역은 y<880에 두고 출처는 자막 상단에 고정한다. 흰 자막 박스 x96~1824/y922~1052, 높이130을 유지한다. 큐 공백에도 박스를 유지하고 브랜드 및 CTA 끝 무발화 유지 구간에서만 숨긴다. 지도 카메라 고정, 원문·가격·자막·출처를 지도 변환에서 분리한다. 대상 윤곽·노선·가격 해당 행만 발화 경계에서 강조한다.
6. `render_contract.template.json`을 새 `render_contract.ready.json`으로 복사해 실측값을 채운다. `node .../validate_render_contract.cjs <ready파일>`로 입력 누락·해시·장면/shot 범위를 확인한다. 이 검사만으로 실제 승인·위치·자막 원문·소리·시각 QA를 대신하지 않는다. 대표 장과 최악 문구부터 Remotion 렌더하여 검수한 뒤 장별 H264 1920×1080/30fps 출력과 48kHz PCM 믹스를 만든다.
7. 장별 검수 후 기존 v15 `assemble_full_v15.py`의 **조립 방식만** 새 editor 스크립트로 이식한다. 프레임 수와 샘플 수를 고정해 concat하고 브랜드의 중복 음악을 피한다. 새 `changneung_full_v1.mp4`로 출력한다. 원본 왕숙 MP4·기존 음성·대본을 수정하지 않는다. 최종 ffprobe, 전체 decode, 컷 경계±2f, 가장 긴 자막, 시간축 우측 끝, 전 장 대표 프레임, 음성/음악 실제 청취를 별도 기록한다.

## 지리·자료 보완 계약

| 장면 | 본편에 필요한 실제 자료 | 현재 파일 기반 출발점 | 채택 전 남은 작업 |
|---|---|---|---|
| M000 | 창릉 서북권 위치 및 전편 실제 카드 | `config/current_video.json`, 전편 URL T_GBxTRgRSc | 현재 왕숙 본편 실제 프레임을 별도 추출해 카드로만 사용. 창릉 현장으로 오인시키지 않음 |
| M001 | 창릉 본단지 전체 지리 배치 | `research/map-clearance-v1/raw/eum_lots_overall_20251224.jpg` | 2025.12.24 고시·국토교통부·토지이음·공공누리3유형·원URL 도면 밖 표기. 원본 전체 fit, 범례/표제 보존. 크롭/덧칠/트레이싱/도면내 locator 금지. 상세 지리에는 별도 상업가공 허용 벡터/지도 필요 |
| M002 | 자족계획과 현재 직장 목적지의 위치 | `research/production-v2/facts.json`, `research/commute-v3/facts.json` | 자족용지 실제 위치와 운영 사업장/계획을 구분. 기업 사진·CI는 개별 권리 근거 확보 전 제외 |
| M003 | 원흥·새절·DMC·행신·대곡 실제 운영역 관계, 계획 회랑, 입주/철도 달력 | `visual/production-v2/drawing_data.json`, `research/commute-v3/report.md`, `research/production-v2/calendar.json` | 대표 개략도는 데이터 검토용. 운영역 실제 좌표와 허용 지도 확보·노선 교차검수. 계획역 정밀 핀 금지. 달력은 별도 화면으로 충분히 유지 |
| M004 | 공고 가격과 산술, 원문 해당 행 | `research/price-stage-v3/facts.json`, `visual/production-v2/M004_price.svg` | 큰 종합표 한 장 유지 대신 S5→S1→S4 해당 행, 기본+확장 합계. 원문 발췌는 공고별 재사용 조건 확인. 3개 대안만 보이는 시안 대신 최종 6개 비교를 분리 화면으로 연결 |
| M005 | S1/S4/S5 주변 학교·상업·공원·도로의 실제 지리 및 시설 사진 | 전체 원도면, `research/facts.json:CN-S34-LIFE`, `research/production-v2/facts.json:CN2-S4-SCHOOL` | **시안 관계도 그대로 장 전체 사용 금지.** 별도 허용 기초지도/벡터에 검증 위치를 연결. 이케아 고양점·롯데아울렛 고양점·원흥 상권의 직접촬영 또는 개별 영상허용 사진 확보. 건널목/입구 확인 전 실제 보행경로·시간은 그리지 않음. 미확인은 대상 옆 짧은 상태주석으로 한정 |
| M006 | 공급/입주 달력과 상품·기산 차이 | `research/production-v2/calendar.json`, script-v2 claim_basis | 시간축/짧은 조건표로 전환. S3 상품을 일반 거래 후보와 분리. 거주의무 등 미확인은 해당 칸 주석 |
| M007 | 삼송·원흥·지축 실제 생활권 지도와 6개 대안 거래 비교 | `research/prices-v2/facts.json`, `research/price-stage-v3/facts.json` | 실제 단지 위치·사진 권리 확인. 83≤전용<85㎡, 5층이상, 기간/n/중위값/취소제외를 지도와 별도 차트에서 읽히게 표시 |
| M008/M009 | 앞서 검수된 지리·사진 재사용과 조건부 후보 | 위 자료 및 `writer/script-v2/scene_proposals.json` | 새로운 장문 결론 슬라이드 대신 대상 지도/시설을 회수하고 이유 1줄만 대상 가까이 표기. CTA 모션은 실제 발화 트리거로 연결 |

현재는 창릉 상업가공 허용 상세 지리 벡터·시설 사진이 완성되지 않았다. 전체 원본 fit 및 관계도만으로 사용자가 요구한 본편 품질을 충족했다고 선언하지 않는다. LH S4 2026.07 계획도와 S1 홈페이지 그림은 사실대조 자료이며 개별 상업영상 허락 확인 전 영상에 넣지 않는다. 레퍼런스 세 영상의 프레임/음원은 재사용하지 않는다.

교통 후속 근거 `research/commute-v3/addendum_ilsan.md`를 입력에 추가했다. 원흥→경복궁24분/종로3가28분/교대49분은 코레일 공개 **평일07~09시 출발18편 계획시각표**의 같은 열차 출발~도착 차이다. 실제 지도에는 경복궁·종로3가·교대 운영역을 표시하고, 철도 구간 수치만 해당 선 가까이에 표시한다. 경복궁을 광화문으로, 교대를 강남역으로 바꾸지 않는다. 원흥 접근·대기·출구/회사보행은 별도 구성요소이며 임의 합산하지 않는다. 시각표 시행2022.08.01/등록2025.08.06/조회2026.10.16을 근거 옆 짧은 출처로 표시한다. 현행 지도 실검색/실측 통근으로 소개하지 않는다.

## 재현 명령과 검수 범위

workspace 루트에서 실행한다. 새 설치가 필요 없다.

```powershell
node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v1/render_brand.cjs
node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v1/prepare_inputs.cjs
& video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v1/probe_assets.ps1 -FFmpegBin '<검증된 기존 ffmpeg bin 경로>'
node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v1/validate_render_contract.cjs
```

마지막 명령은 현재 template 상태에서 의도적으로 실패한다. 실제 음성·타임록·최종 지리 자료가 없다는 것이 정상 결과다. 브랜드 MP4는 전체 decode와 메타데이터 확인, 실제 추출 7프레임 직접 view를 수행했다. 실제 청취·연속 재생·Studio 브라우저 확인은 수행하지 않았다. 본편은 제작 전이다.
