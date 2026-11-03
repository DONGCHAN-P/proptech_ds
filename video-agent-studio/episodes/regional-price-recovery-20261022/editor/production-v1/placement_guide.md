# 실제 배포용 모션 시안 목록

전부 1920×1080, 30fps, 무음 8초, 임시 타이밍이다. 본편 삽입은 MP4 시간 늘리기 대신 실제 Jun timing lock으로 HTML을 다시 렌더한다. 아래 추천 시각은 body 추정 시간이며 본편 확정 타임코드가 아니다. 마지막 발화+3초 규칙은 별도 최종 조립 단계에 남겨 두었다.

| 실제 파일명 (`outputs/production-v1-jun/previews/`) | scene/beat | 추천 body 위치 (추정) | 길이 | 레이어/전환 | 자료 유형 |
|---|---|---|---|---|---|
| full2006paths_provisional_v1.mp4 | S004-P1 | 03:03.2 | 8초 | 6개 동일 축 패널·동기 분기 커서 / hard cut | 실제 매칭지수, 2006Q1=100 |
| incheon2008-2016recovery_provisional_v3.mp4 | S007-P2 | 06:42.5 | 8초 | 고점·관측 저점·최초 복귀·구간 음영·하단 낙폭·달력 / hard cut | 실제 인천 분기 경로와 에피소드 |
| rawmedianvsindex_provisional_v1.mp4 | S003-P3 | 02:39.6 | 8초 | 원가격 IQR/매칭지수 분리 패널·연결 커서·면적/건수·집 / hard cut | 실제 전체 거래 가격 통계와 자체 지수 |

공통 순서: 그래프 및 고정 제목 → 조건 문구 → 흰 본문 자막 박스 → 그 아래 출처. 전체 화면 줌 없음. 지도·실제 장소 사진·생성 영상이 아니라 실제 집계 데이터 그래픽이다. Fluent Emoji는 MIT 허용 로컬 보조 그림이며 새 생성물이 아니다. 돋보기는 본편 S010에 연결했다.

인천 v1은 사건 라벨에 선이 걸려 v2로 교체했다. 원본 v1, 총괄의 `지역별회복_모션시안_v1_무음.mp4`, 기존 검수 PNG는 보존한다. 최신 대표 시트는 `previews/representative_contactsheet.png`로 두 v1과 인천 v2를 함께 보여준다.

브랜드 인트로·아웃트로는 이 3개 시안에 없다. 후속 조립 시 `reusable_assets/manifest.json`의 승인 해시로 고정한 clean 영상만 쓰고, 브랜드 구간에는 본문 자막 박스를 넣지 않는다.

REQ-01 수정: 인천 최신은 v3이며 상단 자체 지수 기준값2006Q1=100을 명시했다. v2와 당시 검수 이미지는 보존한다. 최신 접촉시트는 previews/representative_contactsheet_v3.png. 독립 QA 재검수용 handoff_fix.json 참조.
