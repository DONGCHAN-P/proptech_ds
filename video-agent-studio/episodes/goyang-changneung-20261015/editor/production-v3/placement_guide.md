# 창릉 production-v3 실제 편집

승인 script-v3 SHA256 `9b5d93523e0d50154d976beee0cccc57a4cddf38245838f77741faa6444a5311`과 총괄 `timing_lock_v3.json`이 기준이다. 예상 시간 배분은 사용하지 않았다. 1920×1080/30fps, 총 24,140프레임(13분24.667초).

## 실제 배포 파일과 레이어

| 파일(episode 상대) | 추천 위치·길이 | 자료·레이어/전환 |
|---|---|---|
| `outputs/production-v3/changneung_full_v3r2.mp4` | 전체 본편 0~804.667초 | 실제 Jun 음성+원문 문자정렬 의미자막+고정 지리/선택 강조/표·사진/브랜드/BGM. 기술 확인과 최종 독립 QA 기록은 별도 |
| `outputs/production-v3/changneung_full_v3.srt` | 위 MP4와 동일 | 원문 span을 보존한 184개 의미 큐. 하드자막과 같은 text/프레임 시간 |
| `outputs/editor-preflight-v1/brand_intro_generic_v1.mp4` | f613~763, 20.433~25.433초, 5초 | 첫 문단 훅 뒤. 기존 디자인·음원, 지역 문구만 범용화. 내레이션/자막 없음 |
| `outputs/editor-preflight-v1/brand_outro_generic_v1.mp4` | f23840~24140, 794.667~804.667초, 10초 | 마지막 제공자 문자 끝 f23750에서 정확90f 뒤. 자체 음원, 본문 BGM 중복 없음 |
| `outputs/production-v3/cta_motion_v3.mp4` | 최종 CTA 발화~아웃트로 전, 227f | 기존 채널의 벨·좋아요 16px 짧은 진입. 최종 무발화 유지 구간에서 흰 자막 박스 숨김 |
| `video/public/changneung-v3/map_*.svg` (repo 상대) | 실측 shot/cue 구간, `project_v3.json` 참조 | OSM 실제 좌표로 미리 투영한 고정 지도. 설명 운영역·노선·도로·시설만 별도 강조. 지도 줌/패닝 없음 |
| `video/public/changneung-v3/wonheung_1.jpg`, `wonheung_2.jpg` | M002 원흥역 출발 설명, M003 기존 교통 진입의 짧은 구간 | 2015.03.04 안우석 자료사진, CC BY-SA3.0. 전체 비례contain. 현재 출입구/2026현장 증거·사진GPS 위치 자료로 사용하지 않음. 사진 밖 저자·날짜·라이선스·Commons URL |

본문 흰 자막 박스 x96~1824/y922~1052를 큐 공백에도 유지한다. 제목 x80/y103 43px 굵게, Pretendard regular/bold, 크림 `#f6f4ef`, 잉크 `#173348`, 파랑 `#286cda`. 출처는 자막과 분리한 y873 이후 두 줄이다. 지도·사진·원문 전체도는 y190~850 안에서 사용한다.

47개 발화 트리거 화면 구간을 184개 의미 큐/365개 실제 상태 구간과 결합했다. 고정 배경을 매프레임 재투영하지 않고 현재 유효 231개 상태 이미지를 재사용한 뒤 FFmpeg로 프레임 수를 정확히 조립한다. 대표3장 PNG만 이어붙인 것이 아니다. 운영역/도로 선택, 공고가격 해당 행, 6개 대안 표의 강조, 학교별 방위관계, 사진, 전편 카드, CTA가 원문 트리거에 따라 바뀐다. 정적 지도 소스를 생성형 움직임 영상이라고 소개하지 않는다.

## 소스와 권리 경계

공식 국토교통부 2025.12.24 본단지 전체 계획도는 공공누리3유형 원본 전체 fit이다. 표제·범례를 포함해 보존하고 도면 안에 새 경계·핀·locator·테두리를 그리지 않았다. 공식 계획도와 독립 OSM 도형을 정합/트레이싱하지 않는다. OSM 파생 데이터는 `video/public/changneung-v3/osm_subset.geojson` 및 ODbL 고지를 보존한다. 해당 지도는 계획블록의 정밀 경계나 출입구 도면이 아니다.

S1/S4/S5 학교 장면은 공고의 텍스트 방위 사실을 독립 패널에 배치했다. `research/block-locator-v3/facts.json`의 S4 서측6유6초·북상업주차·남공원, S1 남측학교공원·동측녹지하천, S5 남측공원5초5유·북업무주차보행로를 사용했다. 거리·면적·경계를 표현하지 않는 관계도임을 명시했다. 실제 생활시설 장면은 별도의 OSM 지리판이다. 공식 정밀 블록 지도/통학거리/횡단 경로까지 검증됐다는 뜻은 아니다.

가격은 공고 기본가+확장 합계와 2026Q3 기존 매매 중위값을 분리했다. 대안 6개 표는 전용83≤㎡<85, 5층 이상, 해제 제외, 중개·직거래 포함, 원거래 분기 중위값, n을 함께 표시한다. 소수 표본3건은 해당 행에 표시한다. 사진 두 장은 원흥역의 역사 자료이며 AI 개념 도시 이미지는 기존 브랜드에만 사용한다. 기사 사진·상업시설 CI·새 AI 이미지·유료 지도는 사용하지 않았다.

## 재현 명령

workspace 루트, 기존 설치 도구만 사용한다.

```powershell
node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v3/prepare_assets.cjs
node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v3/build_timeline.cjs
node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v3/render_frames.cjs
& tools/python311/python.exe video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v3/assemble_full_v3.py --output-name changneung_full_v3r2.mp4 --ffmpeg-bin '<기존 검증 ffmpeg bin>'
node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v3/finalize_delivery.cjs
```

사진 원본/전편 추출 프레임은 해당 `video/public/changneung-v3/`에 이미 연결돼 있다. 독립 Remotion 엔트리 `video/src/changneung-v3/frame_entry.tsx`이며 공통 Root/index를 수정하지 않았다. 필요한 자산만 `editor/production-v3/cache/public`에 1회 준비하고 동일 bundle/browser를 재사용한다.

`cache/assembly`의 PCM·중간H264·ffconcat, `cache/public`, `cache/bundle`, 이전 school 수정 전 상태 이미지는 중간 재현/검수 파일이다. 현재 의존 파일과는 manifest로 구분하며 원본을 삭제하지 않았다. 최종 해시와 검수 대상은 `technical_full_v3.json`, 입력은 `source_manifest_v3.json`, 현재 프레임은 `render_frames_receipt.json`을 기준으로 한다.

전체 디코드·기술 스트림 확인·표본 실제 프레임 검수는 실제 청취·연속 재생과 별개다. 실제 청취/연속 재생을 수행하지 않았으며 이를 통과로 기록하지 않는다. 업로드·공개는 수행하지 않는다.
