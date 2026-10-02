# 🏙️ 수도권 아파트 시세 인사이트 대시보드

`master/`, `realestate.db`, `exports/daily/` 의 데이터를 바로 읽어서 화면으로 보여주는
**Streamlit 멀티페이지 대시보드**입니다. 일반 투자자/매수자(B2C) 대상.

## 페이지 구성

| 페이지 | 내용 |
|---|---|
| 🏙️ **홈** (`app.py`) | KPI, 저평가 Top 10 카드, 거래 급증 시군구, 시군구 평단가 분포 |
| 🔍 **단지 검색** | 시군구·평형·가격대·인프라 점수·역세권·재개발 필터 + 카드 그리드 + 지도 |
| 📊 **단지 상세** | 시세 추이, 거래 내역 50건, 평형별 시세, 주변 인프라, 위치 지도, ⭐ 관심 등록 |
| 📈 **지역 분석** | 시군구 평단가 비교, 모멘텀 산점도, 거래 빈도 TOP, 시계열 추이 |
| ⭐ **관심 단지** | 즐겨찾기 단지 카드 + 통합 시세 비교 차트 |

## 빠른 실행

이미 프로젝트 루트(`C:\projects\realestate_reco`)에 `.venv` 가 있다면:

```powershell
cd C:\projects\realestate_reco
.venv\Scripts\activate
pip install -r dashboard\requirements.txt
streamlit run dashboard\app.py
```

또는 그냥:

```powershell
dashboard\run.bat
```

기본 포트(8501)로 브라우저가 자동으로 열립니다.

## 데이터 의존성

대시보드는 다음 파일을 자동으로 읽습니다 (없으면 해당 영역만 비활성):

```
master/unified_apt_pyeong_daily.parquet   # step4 산출물 — 핵심
master/trade_events.parquet               # step3 산출물 — 거래 내역
master/apt_id_map.parquet                 # step3 산출물 — 좌표 fallback
realestate.db                             # external_data_collector 산출물
exports/daily/undervalue_top5_*.csv       # step7 산출물 — 추천
exports/daily/new_trades_sgg_*.csv        # step8 산출물 — 거래 급증
```

데이터가 갱신되면 페이지 우상단 **Rerun** 또는 사이드바 **Clear cache** 로 새로 고치면 됩니다.

## 커스터마이즈 포인트

- **테마**: `dashboard/.streamlit/config.toml` 에서 `primaryColor` 등 변경
- **사이드바 공통 필터**: `app.py` 의 `region_filter` 가 `st.session_state` 로 모든 페이지 공유됨
- **카드 디자인**: `_ui.py` 의 `apt-card` CSS 수정
- **캐시 TTL**: `_data.py` 상단 `CACHE_TTL`

## 배포

- **로컬 사용**: `run.bat` 만 더블클릭
- **무료 외부 공유**: [Streamlit Community Cloud](https://streamlit.io/cloud) 에 GitHub 연동 후 자동 배포
- **사내**: `streamlit run --server.port 8080 --server.address 0.0.0.0 dashboard/app.py`

## 앞으로 붙이기 좋은 기능

- 🔔 관심 단지 신고가 알림 (카카오톡 채널 + step8 watermark 활용)
- 📤 단지 PDF 리포트 다운로드 (크몽 판매용)
- 🧮 대출/세금 계산기 (DTI, 취득세, 보유세)
- 🤖 자연어 질의 (Claude API + 단지/거래 컨텍스트)
