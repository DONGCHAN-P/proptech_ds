# 지역별 6개월 가격 예측: 반복 검증 v1

기준일은 **2026-10-27**이다. [연구 보고서](../../reports/지역별%20집값%20예측%20반복%20검증.md)에 분석·출처·한계를 정리했다. 기존 연구와 운영 모델은 보존했다.

## 이번 결과

3차 실험을 수행했다. 주 실험은 26개 후보와 4개 결합 규칙, 입력 시차 실험은 2개 대안이다. 2015년부터 반기별 23개 예측 원점을 재생하고 2017년 이후 같은 19개 원점에서 성능을 비교했다. 최신 수정 자료로 이미 확인한 과거를 반복 평가한 결과다.

| 동일 평가 대상의 일반 MAE(%p) | 시도 | 시군구 |
|---|---:|---:|
| 전체 기존 HGB | 4.432 | 5.146 |
| 전체 입력 갱신·120개월 조건부 후보 | 4.317 | 5.063 |
| 최근 2024년 이후 기존 HGB | 1.772 | 3.166 |
| 최근 입력 갱신·120개월 조건부 후보 | 1.624 | 2.994 |

주 승격 지표는 원점·시도를 균등하게 반영하는 **균형 MAE**다. 시군구는 각 시도 내부에서 먼저 평균한다. 두 행정 수준의 기존 대비 오차비 평균으로 판정한다. 최소 5% 개선, 두 수준 각각 비악화, p90 절대오차 증가 10% 이내가 모두 필요하다. 조건부 후보의 전체 균형 개선은 **2.14%**여서 기존 `v3_hgb`를 기준으로 유지한다. 최근 오차 감소만으로 모델을 교체하지 않았다.

조건부 후보는 2020년 신고기한 단축을 근거로 2020년 5월부터 t−2 가격 집계를 사용하고, 목표 정답의 성숙 지연은 3개월로 유지했다. 당시 최초 공개본을 복원하지 못했으므로 이 성적은 입력 시차 가정에 따른 사후 민감도 결과다. 최신 공급자료 보완은 역사 평가 특징량을 바꾸지 않았으며 현재 입력의 결측만 해결했다.

## 지표와 결과 파일

- [성적 개요 그림](results/scores_overview.png), [국면별 오차](results/regime_errors.png), [범위 포함률](results/interval_calibration.png)
- [3차 실험 이력](results/trial_history.csv), [주 실험 전체 지표](results/scorecard.csv), [승격 판정](results/promotion_decisions.csv)
- [시차 후보 전체 지표](results_timeliness/scorecard.csv), [시군구별 진단](results_timeliness/by_region.csv)
- [검증 계획](PLAN.md), [자동 검증 결과](delivery_verification.json), [독립 검수](review3.md), [시차 수정 검수](review_timeliness_followup.md)

일반 MAE·RMSE·중앙값·p90·꼬리 MAE·편향을 함께 저장한다. 방향 평가는 ±1%를 보합으로 두고 하락·보합·상승을 구분한다. 방향 균형 정확도와 원점별 지역 순위상관도 평가한다. 80%·95% 경험적 범위는 포함률·폭·구간점수를 함께 본다. 전체 80% 포함률은 약 67~70%로 목표보다 낮아 구간 보정은 추가 과제다.

정답 없는 행도 발행 기록에 남긴다. 전체 채점 대상은 시도 203/203건, 시군구 1,938/2,019건이다. 자료가 부족한 81건을 제거해 성능을 높이지 않았다. 시차 후보 입력 품질이 부족하면 같은 지역의 기존 예측을 사용하고 실제 모델·학습 건수·최종 라벨 공개일·입력 월을 기록한다.

## 데이터 보완

[공식 수집 기록](../../research_notes/지역별%20집값%20예측%20반복%20검증/official_update.md)에 국토교통부 준공·착공·인허가 XLS 24개의 원문·해시·발표일·셀 위치를 보존했다. 2026년 1~8월 426관측 중 기존 장기 이력이 있는 6개 시도의 144관측을 결합했다. 9개 공급 파생변수의 현재 결측 54칸이 해소됐다. 나머지 지역은 비교 가능한 장기 이력을 확보한 뒤 결합한다. 장기 고용·청장년 이동 및 실제 시점별 데이터 공개본은 계속 필요한 자료다.

## 고정 발행본과 실제 결과 채점

- 주 실험: [6297866c5207816ec85c](releases/6297866c5207816ec85c/release.json), 130개 지역 × 30개 규칙
- 조건부 시차 후보: [2a61ece4c818ecf30e49](timeliness_releases/2a61ece4c818ecf30e49/release.json), 130개 지역 × 2개 대안

각 고정본은 발행 예측·입력·모델·과거 오차·설정·코드를 함께 보존하고 내용 해시로 식별한다. 이전 고정본도 보존했다. 작업용 `results`를 갱신해도 고정본은 덮어쓰지 않는다. CSV의 `region_code`는 문자열로 읽는다.

목표는 2027년 4월까지의 6개월 누적변화율이다. 기준인 2026년 10월 가격은 아직 관측되지 않아 10월 실제 원화 가격이나 실제 지수 수준을 발행한 것으로 해석하지 않는다. 실제 결과 채점은 같은 3개월 성숙 가정하에 **2027년 7월 27일 이후** 공개 상태를 확인해 진행한다. 현재 채점 상태는 `pending_mature_actuals`다.

프로젝트 루트에서 실행한다.

```powershell
# 캐시·설정·목표 식별자를 검증한 뒤 지표를 재계산한다.
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_iteration_20261027/experiment.py --mode evaluate

# 이번 기준일 설정으로 재학습하고 새 내용이면 별도 고정본을 만든다.
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_iteration_20261027/experiment.py --mode forecast

# 캐시를 활용한 전체 주 실험. 새 데이터/설정이면 별도 버전이 필요하다.
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_iteration_20261027/experiment.py --mode all

# 독립된 입력 시차 민감도 실험과 정적 그림
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_iteration_20261027/timeliness_experiment.py
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_iteration_20261027/render_report.py

# 발행 시점 기준 검증: 결과 미성숙을 확인한다.
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_iteration_20261027/score_release.py --as-of 2026-10-27

# 미래 관측을 수집한 뒤 해당 월별 패널로 고정본을 채점한다.
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_iteration_20261027/score_release.py --release analysis/regional_forecast_iteration_20261027/releases/6297866c5207816ec85c --panel NEW_MONTHLY_PANEL.parquet --as-of 2027-07-27

# 재학습 없는 모델/범위 재현과 회귀 테스트
tools/python311/python.exe -B -X utf8 analysis/regional_forecast_iteration_20261027/verify_delivery.py
tools/python311/python.exe -B -X utf8 -m pytest analysis/regional_forecast_iteration_20261027 analysis/regional_forecast_20261027/test_forecast.py -q -p no:cacheprovider
```

`--mode seal`은 검수 이전 캐시의 명시적 마이그레이션 용도다. 일반 재실행에는 사용하지 않는다. 기준일·원점·평가 규칙은 이번 버전에 고정했으며 자동 상시 실행을 설정한 상태는 아니다. 다음 단계는 공개본 이력과 수요 자료를 보완하고, 이번에 고정한 후보의 신규 관측 성능으로 교체 여부를 판단하는 것이다.
