# 🏢 집값지도 — 호갱노노 스타일 수도권 아파트 실거래 지도

`master/` 의 실거래 데이터와 `legacy/realestate.db` 의 인프라 데이터를 그대로 읽어
**전체화면 지도 + 가격 말풍선** 형태로 보여주는 FastAPI 웹앱입니다.

```
web/
  build_index.py   원본 → 서빙용 파케이 인덱스 빌더
  main.py          FastAPI + DuckDB API
  cache/           빌드 산출물 (git 제외 대상, 약 70MB)
  static/          지도 프론트엔드
  run.bat          더블클릭 실행
```

## 실행

```powershell
cd C:\projects\realestate_reco
.venv\Scripts\python.exe -m pip install -r web\requirements.txt
web\run.bat
```

`run.bat` 이 브라우저로 <http://127.0.0.1:8000> 을 엽니다.
첫 기동 때 `web/cache/` 가 없으면 `build_index.py` 를 자동으로 돌립니다(약 2초).

개발 중에는 자동 리로드로 띄우는 쪽이 편합니다.

```powershell
.venv\Scripts\python.exe -m uvicorn web.main:app --reload
```

## 화면

| 영역 | 내용 |
|---|---|
| **지도** | 줌 11 이하 시군구 → 12~13 읍면동 → 14 이상 단지. 말풍선 색은 평당가 6단계 |
| **좌측 목록** | 현재 지도 범위 안의 단지. 9가지 정렬, 스크롤 시 추가 로드 |
| **상단 필터** | 평형 · 매매가 · 준공연도 · 역세권 도보시간 · 인프라 점수 · 재개발 · GTX · 최근 거래 |
| **단지 상세** | 최근 실거래가, 1년/3년/전고점 대비, 평형별 시세, 월별 시세 추이 차트(2006~), 실거래 100건, 주변 지하철·학교·공원 |
| **랭킹 패널** | 저평가(step7) · 신고가/특이거래(step8) · 1년 상승률 TOP |

평형을 고르면 지도 말풍선과 목록 가격이 **그 평형 기준**으로 바뀝니다. 호갱노노와 같은 동작입니다.

## 데이터 갱신

일일 배치가 `master/` 를 갱신한 뒤 인덱스를 다시 만들면 됩니다.

```powershell
.venv\Scripts\python.exe web\build_index.py
```

서버는 파케이를 요청 시점에 읽으므로, 인덱스를 다시 만들면 재기동 없이 반영됩니다.

## 알아둘 점

### apt_id 두 세대가 섞여 있습니다

`master/apt_id_map.parquet` 과 `legacy/realestate.db`(좌표·인프라)는 **구버전 apt_id** 로
만들어져 있습니다. `common.py` v1.1 에서 `make_legal_dong_code()` 가 가짜 sha5 대신
실제 umdCd 를 쓰도록 바뀌면서 해시 입력이 달라졌고, 그 결과 `master/trade_events.parquet`
의 apt_id 와 **한 건도 겹치지 않습니다**.

`build_index.py` 의 `build_geo_bridge()` 가 두 세대 모두에서 안정적인
`(시군구, 정규화 단지명, 도로명주소)` 를 키로 다리를 놓아 **99.6%** 를 잇습니다
(20,340개 중 75개 미매칭 — 좌표가 없어 지도에 표시되지 않습니다).

근본 해결은 `run_geocode_apts.py` 를 신규 apt_id 기준으로 다시 돌려
`apt_id_map.parquet` 과 `realestate.db` 를 재생성하는 것입니다. 그 뒤에는
`build_geo_bridge()` 없이 apt_id 로 바로 조인할 수 있습니다.

### 배경 지도

기본은 키가 필요 없는 **OpenStreetMap** 타일입니다.
CARTO basemaps 는 등록되지 않은 도메인에 `API KEY REQUIRED` 워터마크가 찍힌 타일을
내려주므로 쓰지 않습니다.

VWorld 로 바꾸려면 환경변수만 넣으면 됩니다.

```powershell
$env:VWORLD_MAP_KEY = "발급받은키"
web\run.bat
```

VWorld 키에는 접속 도메인이 등록돼 있어야 하고, `localhost` 도 따로 등록해야 합니다.
`.env` 의 `VWORLD_API_KEY` 는 지오코딩용으로 발급받은 키라 도메인 등록 여부를
확인한 뒤 쓰세요.

### 수치 정의

- **금액** 단위는 만원, **평당가** 는 `price_per_pyeong` (만원/평)
- **1년 등락** = 최근 365일 평균 평당가 ÷ 그 직전 365일 평균 평당가
- **3년 등락** = 최근 365일 평균 평당가 ÷ 3~4년 전 구간 평균 평당가
- **전고점 대비** = 마지막 실거래가 ÷ 역대 최고 실거래가
- 해제(취소) 신고 건은 인덱스 빌드 단계에서 제외됩니다 (4,505,222 → 4,438,142건)
- 거래가 드문 단지는 평균 표본이 얇아 등락률이 크게 흔들립니다. 목록의 `1년 N건` 을 같이 보세요.

### 랭킹 패널의 한계

`exports/daily/` 의 step7·step8 산출물에는 apt_id 가 없거나 구버전이라 **단지명으로**
지도 단지와 잇습니다. 같은 동에 동명 단지가 여럿이면 거래가 많은 쪽 하나로 접고,
못 이은 항목은 클릭해도 지도가 움직이지 않습니다.

신고가 패널은 직전 평균 대비 편차만 보므로 증여성 거래나 저층 특이 거래가 섞입니다.
`deviation_pct` 가 200%를 넘는 건은 대체로 정상 시세가 아닙니다.

## API

| 엔드포인트 | 설명 |
|---|---|
| `GET /api/meta` | 시군구 목록, 평형 코드, 데이터 범위, 타일 설정 |
| `GET /api/map?zoom=&bbox=&<필터>` | 줌에 맞는 말풍선 |
| `GET /api/list?bbox=&sort=&offset=&<필터>` | 좌측 목록 |
| `GET /api/apt/{id}` | 단지 상세 + 평형별 + 주변 인프라 |
| `GET /api/apt/{id}/trades?pyeong=` | 실거래 내역 |
| `GET /api/apt/{id}/series?pyeong=` | 월별 시세 추이 |
| `GET /api/search?q=` | 단지·지역 검색 |
| `GET /api/rankings?kind=undervalue\|newhigh\|surge` | 랭킹 |
| `GET /api/health` | 캐시 상태 |

공통 필터 파라미터: `pyeong`(콤마), `price_min`, `price_max`, `built_from`, `built_to`,
`walk_max`, `infra_min`, `redv`, `gtx`, `chg_min`, `active_only`, `region`, `sgg`, `q`

## 기존 Streamlit 대시보드와의 관계

`dashboard/` 는 그대로 둡니다. 분석·탐색용 표와 차트 중심이고, `web/` 은 지도 탐색
중심이라 용도가 다릅니다. 두 앱이 같은 `master/` 를 읽으므로 동시에 띄워도 됩니다.
