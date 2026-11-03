# 시차 모듈 Important 2건 후속 검토 — 2026-10-27

**판정: 두 Important 모두 검토한 코드에서 해소되었습니다. 한정된 수정 범위에서 추가 Critical/Important 발견 없음.**

`timeliness_experiment.py`의 두 수정과 `test_timeliness.py`의 추가 테스트만 한 차례 정적으로 확인했습니다. 테스트·수치회귀·모델 재생·전체 실험은 실행하지 않았으며, 별도 탐색이나 산출물 검증도 하지 않았습니다. 파일 변경은 이 보고서뿐입니다.

## 1. Fallback/reuse 예측의 학습 메타데이터 — 해소

- `predict_with_fallback` (`timeliness_experiment.py:67–90`)은 실제 사용한 fallback/reuse 행을 복사하여 예측값과 학습 표본 수·최종 라벨 공개일을 기본 보존합니다. Fresh 예측을 수행한 good 행에만 예측값, 학습 메타데이터, `effective_predictor`, 입력 월을 함께 갱신합니다.
- 전부 fallback이면 학습을 호출하지 않고 기존 메타데이터를 유지합니다. 제도 적용 전 reuse도 재사용 모델의 메타데이터를 유지합니다.
- 과거 경로(`133`)와 current 경로(`159–174`)가 같은 helper를 사용합니다. Current fallback 학습의 실제 표본 수·공개일을 받아 보존하며, 최종 CSV에도 해당 필드와 effective predictor가 포함됩니다.
- 추가된 mixed/all-fallback/pre-rule 테스트의 단언이 위 동작을 확인하도록 작성되어 있습니다. 테스트는 읽기만 했습니다.

## 2. 구간 재현에 필요한 history·구현 동결 — 해소

- `freeze_outputs` (`timeliness_experiment.py:93–107`)는 정확한 과거 예측 파일을 `history.parquet`으로 보존합니다. History 해시만 남기던 이전 누락이 해결되었습니다.
- Fresh/original current features, 예측, 모델과 함께 timeliness·experiment·evaluation·artifacts 소스 및 원래 `forecast.py`를 동결합니다.
- `resolved_config.json`에 variant 설정, 적용 시점, 평가 구현 식별자, 가격/품질 열과 라벨 성숙 가정을 기록하고 `bank_manifest.json`도 함께 보존합니다.
- 추가 테스트(`test_timeliness.py:70–93`)는 작업용 history를 덮어쓴 뒤 보관된 history로 같은 구간을 재계산하여 비교하고, 필요한 소스·설정·manifest의 보관 해시를 확인하도록 작성되어 있습니다. 이 테스트나 별도 replay는 실행하지 않았습니다.

## 검토 식별자 및 한계

- `timeliness_experiment.py` SHA-256: `b5996fb84c0bbb0a08afa7c362f15797f39deddad8964e8089e858b3c0729c71`
- `test_timeliness.py` SHA-256: `3387643beb76048719a77b596869c861a4efeba7c5f9f13bfb8a63774fcebd5f`

시차 테스트 6개 통과는 사용자 전달 결과이며 이번 검토에서 독립 재실행하지 않았습니다. 실제 산출물의 수치 일치·모델 재생·전체 검증은 parent 진행 범위로 남습니다. 이 판정은 기존 두 지적의 코드 수정 확인에 한하며, 성능 개선·승격·새 블라인드 평가나 역사적 최초 빈티지 검증을 뜻하지 않습니다.
