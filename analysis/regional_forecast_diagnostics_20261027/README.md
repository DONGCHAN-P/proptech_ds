# 지역별 집값 예측 실패 진단

2026-10-27 기준 후속 연구다. 기존 원본·발행본과 운영 코드는 보존했다.

- [HTML 보고서](../../reports/지역별%20집값%20예측%20실패%20진단.html) · [Markdown 보고서](../../reports/지역별%20집값%20예측%20실패%20진단.md)
- [분석 산출물 검증](artifact_verification.json) · [독립 코드 검수](code_review.md) · [관련 테스트 기록](test_result.txt)
- [공식 전세 자료 조사](../../research_notes/지역별%20집값%20예측%20실패%20진단/rental_inputs.md) · [공개본 감사](../../research_notes/지역별%20집값%20예측%20실패%20진단/vintage_audit.md)

## 시행 결과

1. **실패 진단:** 2020~2023년의 균형 오차 기여는 시도66.4%, 시군구61.5%. 실제 +10% 초과 상승의 진폭을 줄여 예측하고, -10% 미만 급락에서 방향을 놓친 사례가 집중됐다. 관련 분류는 실제 결과를 본 뒤 만든 진단이며 실전 입력으로 사용하지 않는다.
2. **요인 분해:** 네 고정 조합에서 입력 시차와 학습 규칙을 분리했다. 최근 시도 감소0.14766%p 중 학습 규칙 몫0.14697%p, 시차 몫0.000694%p. 학습 규칙은 시작연도와 최대120개월 창, 시차는 최신 수정본·품질 대체 가정을 포함한다.
3. **자료 보강:** 공식 REB 전세가격2,657·수급1,876, 총4,533관측을 확보했다. 실제 역사 공표일은 공란이며 모형 실험만 기준월+3개월 **첫날** 가용을 가정한다. 조사 담당의 별도 +3개월 **말일** CSV와 구별한다. 가격 지수의 일정 재기준은 로그차분에서 상쇄되나 소급수정·표본개편은 남는다. 시도 값을 시군구에 부여한 대리 입력이다.
4. **점예측 대안 2개:** 같은 HGB에 전세 변수군을 더한 대안은 평균 균형 오차0.369% 악화, 고정 모멘텀0.5+잔차 HGB는2.365% 악화. 두 대안 모두 기존5% 교체 기준에 미달해 기존v3기준을 유지했다. 추가 탐색은 수행하지 않았다.
5. **범위 대안 2개:** 대칭 잔차는 시도 포함률67.98→75.86%, 구간점수29.04→26.47로 개선했지만 시군구 포함률70.54%로 공동기준 미달. 변동성 스케일 방식은 시군구 폭46.2% 증가·점수악화. 점예측은 변경하지 않았다.
6. **목표 측정 대조:** 큰 오차50건 중 지리·기간이 맞는41건을 같은 ZIP의 REB 매매가격 **조사 지수**와 비교했다. 측정 대상·방법이 다른 꼬리 선택 사례이며 지표 일치·목표 오류·우월한 정답을 전제하지 않는다. 다음 우선순위는 원천 매칭·월별 연결·층/단지 구성 감사다.

## 파일 안내

| 파일 | 의미 |
|---|---|
| `error_ledger.parquet` | 네 모델의 동일 대상·실제·예측. 발행 `price_input_month` 보존, 비교 문맥의 t3 특징·품질 태그는 `reference_` 접두어 |
| `regime_diagnostics.csv`, `regional_diagnostics.csv` | 국면·지역별 오차와 전체 균형 오차에 대한 기여 |
| `outcome_band_diagnostics.csv`, `worst_cases.csv` | 실제 변동폭별 사후 진단·상위 사례 |
| `factor_decomposition.csv` | 네 조합의 전체·시기별 요인 분해 |
| `rental_scorecard.csv`, `residual_scorecard.csv` | 두 점예측 추가 실험의 같은19원점 평가 |
| `interval_scorecard.csv`, `interval_decisions.csv` | 세 범위 방식의 포함률·폭·구간점수와 사전 기준 판정 |
| `target_crosscheck.csv` | 자체 실거래 추정량과 조사 지수의 사례별6개월 대조 및 원본 셀 좌표 |
| `local_tracking_audit.json`, `local_rental_audit.json` | 로컬 발견일의 한계·짧은 임대차 범위·빈 파일6개를 포함한 감사 |

## 고정본

- [전세 블록 후보](rental_releases/a7dfab3bdbb2d844a682/release.json)
- [모멘텀 잔차 후보](residual_releases/1e9054d57308baf4b2a8/release.json)
- [범위 보정 연구 후보](interval_releases/c5b85a25f0d83a4bada5/release.json)
- [현재 로컬 입력 보존본](input_snapshots/d6450624bbf5881e9b10/release.json): 약7.5MB의 기존 집계·공식입력과 감사 기록. 수집일이 역사 최초 공표일을 뜻하지 않으며 raw거래 전체를 복사하지 않았다.

새 후보는 연구 비교군으로 고정했으며 기존 발행본·생산 모델을 자동 교체하지 않았다. 신규 독립 평가·실제 역사 공개본 복원은 남아 있다. 자동 상시 수집기·스케줄러는 가동하지 않았다.

## 재현

프로젝트 루트에서 `tools/python311/python.exe -B -X utf8` 뒤에 실행 파일을 지정한다.

```powershell
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_diagnostics_20261027/diagnostics.py
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_diagnostics_20261027/interval_experiment.py
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_diagnostics_20261027/rental_experiment.py
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_diagnostics_20261027/residual_experiment.py
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_diagnostics_20261027/target_crosscheck.py
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_diagnostics_20261027/render_findings.py
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_diagnostics_20261027/verify_artifacts.py
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_diagnostics_20261027/build_html.py
```

점예측 스크립트는 입력·생성 코드 식별자가 같은 완성 캐시만 사용한다. 새로운 데이터·방법은 별도 버전에서 실행한다. 재현 전 원본 ZIP·지수·출처 노트·고정본·예측·검수 기록을 보존한다. `capture_inputs.py`는 현재 로컬 원본 상태를 새 스냅샷으로 보존하는 수동 도구다.

최종 테스트 범위는 새 연구17개와 이전 예측 연구41개의 Python 테스트58개다. 보존된 UTF-16 텍스트 실행기록이 doctest로 수집되지 않도록 각 연구 폴더의 `test_*.py` 파일과 이전 `test_forecast.py`를 명시적으로 실행했다.
