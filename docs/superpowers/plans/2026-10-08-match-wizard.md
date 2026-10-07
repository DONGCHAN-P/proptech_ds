# 맞춤 찾기 구현 계획

> 스펙: `docs/superpowers/specs/2026-10-08-match-wizard-design.md` · 인라인 실행

**Goal:** `web/` 첫 화면을 질문 6단계 → Top5 + 지도 하이라이트 → 단지 리포트로 바꾼다.

**Architecture:** 순위 로직은 `web/match.py` 순수 함수(pandas)로 두고 테스트한다.
`web/main.py` 는 엔드포인트 3개만 얇게 붙인다. 프론트는 `index.html` + `js/match/*.js` +
`css/match.css` 로 새로 만들고, 기존 지도는 `explore.html` 로 옮긴다.

**Tech Stack:** FastAPI · DuckDB · pandas/numpy · Leaflet 1.9 · Chart.js 4 · Pretendard

---

### Task 1: 통근 추정 (`web/match.py`)
- `haversine_km(lat1, lng1, lat2, lng2)` (numpy 브로드캐스팅)
- `nearest_stations(lat, lng, stations, k=3)` → (idx[N,k], dist_km[N,k])
- `estimate_commute(home_idx, home_d, work_idx, work_d, stations, direct_km)` → 분[N]
- 테스트: 멀수록 길다 · 같은 노선이 환승보다 짧다 · 1.5km 이내는 도보 이하

### Task 2: 점수 (`web/match.py`)
- `budget_use_score(ratio)` · `commute_score(min, limit)` · `pct_rank(series, ascending)`
- `prepare(apt, pyeong)` → 후보 프레임 + `rel_price_pct` (시군구×평형 백분위, 전체 모집단)
- `hard_filter(df, ans, today)` · `score(df, ans)` · `top_n(df, n=5, dong_cap=2)`
- `run_match(df, ans, stations, today)` → 완화 단계 포함 결과 dict
- `reasons(row, ans)` 사실 서술 문구
- 테스트: 예산 초과 제외 · 평형 · 오래된 거래 제외 · 예산 곡선 경계 · 동 2곳 제한 ·
  단지당 1행 · 완화 순서 · 문구가 validator 통과

### Task 3: API (`web/main.py`)
- `POST /api/match/count`, `POST /api/match`, `GET /api/stations`
- 후보 프레임·역·근접역은 캐시 파케이 mtime 기준으로 메모리 캐시
- `ODSAY_API_KEY` 있으면 Top5 실측 (httpx, 3초)
- 테스트: TestClient 스모크

### Task 4: 화면 이동
- `index.html` → `explore.html` (내용 그대로), README 갱신

### Task 5: 프론트 마법사
- `index.html` 골격, `css/match.css`, `js/match/{api,wizard,result,report}.js`
- 진행바 · 슬라이드 · 칩 · 카운터 · 좁혀지는 연출

### Task 6: 결과 + 리포트
- Top5 카드 + 무채색 지도 + 순위 핀 + 회사 점선
- 벤토 리포트 (기존 `/api/apt/*` 재사용)

### Task 7: 검증
- `pytest tests -q` 전체, 서버 띄워 브라우저 확인, 커밋
