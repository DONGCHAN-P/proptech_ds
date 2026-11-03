# 학교·철도역 레이어 (2026-10-18)

기존 수도권 단지 20,058개에 학교 위치 4,439개, 학교 구역 3,123개, 철도역 노선별 레코드 683개를 추가했다. 환승역은 노선별로 중복되므로 683개를 고유 역사 수로 해석하지 않는다.

## 원자료와 좌표

- 학교·학구도: https://schoolzone.emac.kr/publicData/publicDataList.do
  - 학교 CSV 실제 기준일 2026-10-01, WGS84 경위도 → EPSG:5179.
  - 구역 SHP 기준일 2026-09-20, EPSG:5186 → EPSG:5179. 초등 2,660 / 중학교 427 / 고등학교 36.
  - 학교 위치와 통학구역은 별도 레이어이며, 단지별 확정 배정학교를 계산하지 않았다.
- 철도역: https://data.kric.go.kr/rips/M_01_01/detail.do?id=32
  - 전체 도시철도역사정보 20260630 XLSX. 행별 기준일은 2022~2026 및 미기재로 서로 다르다.
  - 원자료 도로명주소가 서울특별시·경기도·인천광역시인 레코드만 사용. 경위도 → EPSG:5179.
  - 주소 미기재·수록 범위 등으로 일부 역이 빠질 수 있다. GTX 등 모든 수도권 철도의 최신 완전 목록으로 사용하면 안 된다.
  - 역 좌표는 출입구·도보 접근 위치가 아니다. 역 사이를 임의 직선으로 연결하지 않았다.

원본은 `raw/`, 가공 결과는 `processed/`, 해시·검증 기록은 각 `*_validation.json`에 보존한다.

## SHP 파일

- `processed/schools_5179/schools.*`: 초·중·고 학교 점.
- `processed/stations_5179/stations.*`: 철도역 노선별 점.
- 학구도 원본 SHP: `raw/education-20260920/`의 세 구역 ZIP.

SHP는 `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`를 함께 옮긴다. 학교 및 역 점 SHP는 생성 후 모든 좌표를 다시 읽어 비교했다. 웹에는 가공 JSON을 gzip으로 넣어 동일 좌표로 렌더링한다. 원본 SHP를 브라우저에서 매번 해석하지 않는다.

## 실제 선로 후속 자료

KTDB 공식 목록 https://www.ktdb.go.kr/www/selectPbldataChargerWebList.do?key=12&searchClStepCode=106

`철도망 세계좌표계 (TM-GR-MR-AML-00)`의 역 노드·철도 링크와 개통 상태가 필요하다. 현재 지도에는 실제 선로 및 계획역을 넣지 않았다. 공개 역 좌표와 선로 도형의 버전·노선 ID·개통 여부를 맞춘 뒤 연결한다.

## 재현·검증

프로젝트 Python으로 `layers/prepare_education.py`, `layers/prepare_transit.py`, `build.py` 순서로 실행한다. `tools/gis_vendor`의 pyproj·pyshp를 사용한다.

`qa_education.py`: 학교 로드·표시·토글·구역·상세 5항목 통과.
`qa_transit.py`: 역 로드·상세·표시·토글·노선 필터·한글 UI 6항목 통과.
`qa.py`: 기존 단지 검색·상세·지역·휠·드래그·촬영모드 통과.
실제 생성된 데스크톱 브라우저 스크린샷을 확인했다. 새 레이어의 휴대폰 실기기 검증은 하지 않았다.
