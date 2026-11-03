# 지역별 아파트 6개월 예측 연구

최종 결과 폴더는 **`results_v3/`**이다. [연구 보고서](../../reports/지역별%20집값%206개월%20예측%20연구.md), [6개월 전망](results_v3/forecast_next_6_months.csv), [모델 비교](results_v3/model_comparison.png), [코드 검수](code_review_v3.md), [실험 이력](RUN_HISTORY.md)을 함께 확인한다.

2006년 이후 유효 실거래 8,353,538건을 11개 시도·141개 지역 묶음의 월별 패널로 정리했다. 일부 개편 지역은 과거 경계를 유지한 통합 단위다. 거래가 충분한 지역에 대해 기준월 이후 1~6개월 가격 변화율을 직접 예측한다. 학습 예측 원점은 이번 실험에서 2009년 이후로 고정했다. 원본 및 기존 운영 모델은 수정하지 않았다.

## 출력 해석

- 기준: 2026-10-27에 이용 가능한 정보. 실거래 가격 피처는 신고 지연을 고려해 2026년 7월까지 사용한다.
- 기간: 2026년 10월 기준 월 가격 대비 11월~2027년 4월의 변화율. 10월 실제 가격이 아직 관측된 상태가 아니므로 원화 가격을 제시하지 않는다. `forecast_index`는 기준 100으로 환산한 예상 변화다.
- `range_low_pct`, `range_high_pct`: 같은 예측 기간·지역 수준의 과거 평가 잔차 10~90분위로 확장한 범위. 지역과 시점이 서로 의존하고 평가 원점이 5개이므로 미래 포함 확률을 보장하는 신뢰구간으로 읽지 않는다.
- 주 대상: 동일 단지·같은 면적의 전월 대비 변화. 실제 같은 호수의 반복 거래를 확인한 자료는 아니다. 층·수리·동별 차이와 매칭 표본 변화가 남아 있다.
- 시군구 결과는 `level=district`, 시도는 `level=province`. 두 수준의 관측은 독립 표본으로 합산하지 않는다.
- `excluded_series.json`: 거래 매칭·이력 부족으로 6개월 예측을 산출하지 않은 지역. `evaluation_coverage.csv`는 예측했으나 이후 거래 부족으로 평가 정답을 얻지 못한 지역 수까지 남긴다.

## 재실행

프로젝트 루트 `C:/projects/realestate_reco`의 PowerShell에서 실행한다. 현재 Python·pandas·DuckDB·scikit-learn 환경을 사용한다.

```powershell
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_20261027/prepare_panel.py
tools/python311/python.exe -B -X utf8 -m pytest analysis/regional_forecast_20261027/test_forecast.py -q -p no:cacheprovider
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_20261027/run_experiment.py --output results_reproduction
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_20261027/diagnose_features.py --output results_reproduction
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_20261027/plot_results.py --results results_reproduction
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_20261027/verify_experiment.py --results results_reproduction
```

`data/`의 공식 통계·정책 사본은 최초 실행 시 고정되며 자동 덮어쓰지 않는다. 다른 기준일·새 자료로 갱신하려면 새 실험 폴더를 만들고 수집 범위, `ASOF`, 공개 지연, 입력 해시를 함께 갱신한다. 현재 경로를 그대로 사용하면 2026-10-27 실험을 재현한다. 운영 중인 `run_step6_model.py`와 `config/regional_weights.json`은 건드리지 않는다.

## 주요 파일

| 파일 | 내용 |
|---|---|
| `prepare_panel.py` | 완료한 추가 수집 정규화, 개편·중복 점검, 월별 매칭 패널 |
| `forecast.py` | 정확한 달력 정답, 공개일 결합, 발표 시점 정책 노출, 학습·평가 표본 |
| `run_experiment.py` | 지역 패널·경제 변수, 9개 사전 후보의 시간 순서 검증, 1~6개월 직접 예측 |
| `diagnose_features.py` | 과거 가격·거래량 통제 후 탐색 상관관계, 같은 트리 모델의 사후 변수 제거 비교. 선정에는 사용하지 않음 |
| `results_v3/selection_frozen_before_holdout.json` | 개발 기간, 선택 시점, 후보 오차와 고정된 모델 |
| `results_v3/backtest_metrics.csv` | 오차 %p·편향·방향·평가 가능 표본 비율 |
| `results_v3/feature_correlations_by_region.csv` | 변수별 지역·표본 기간·표본 수·Spearman 상관 |
| `results_v3/current_feature_availability.csv` | 현재 지역별 변수 확보 상태 |
| `results_v3/models/` | 1~6개월별 학습 파이프라인. 전처리 포함 |
| `results_v3/artifact_verification.json` | 공개일·선정 경계·파일 해시·저장 모델 예측 재현 점검 |
| `input_manifest.json`, `panel_audit.json` | 원본 해시, 지역 경계, 매칭 산식과 유효 거래 수 |

## 데이터 보완 우선순위

1. 2026년 인허가·착공·준공을 업데이트하고 시군구별 입주 예정 물량·주택 재고 대비 공급을 연결한다. 현재 확보한 세 공급 계열은 2025년 12월까지여서 최신 예측에서는 9개 파생 공급 피처를 오래된 값으로 처리해 결측으로 남겼다.
2. 청장년 순이동·가구 형성, 근무지 일자리·소득, 전세 가격·전세 거래의 장기 월별 자료를 확보한다. 단일 고용 스냅샷·짧은 월 이동 계열은 학습에서 제외했다. 순이동은 6개 지역의 연간 보완 계열을 사용한다.
3. 실제 공개 빈티지·취소 및 신고 이력과 정책·철도 계획의 최초 공표 이력을 쌓는다. 현재 백테스트는 최신 수정본에 공개 지연을 가정한 재구성이며, 당시 공개본을 복원한 검증과 구분한다.
4. 이번 예측을 보관하고 2027년 정답이 충분히 공개된 뒤 전향 평가한다. 평가 기간을 반복 보며 변수를 고르는 과정을 별도의 새 검증으로 취급하지 않는다.

정책은 검증한 과거 24개와 2026년 발표 4개의 제한된 발표 신호를 같은 패키지 단위로 묶어 사용한다. 시행일·차주 예외를 모두 반영한 현행 대출 규칙 계산기는 별도 작업이다. 동탄구 `41597`은 화성 통합 묶음 `41590` 전체로 넓히지 않았으며, 해당 정책의 동탄 노출은 미해결로 기록했다.
