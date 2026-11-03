# Focused review of F1/F2/F3 fixes

Date: 2026-10-27. Scope: the three corrections from `code_review_v1.md`, their integration in `forecast.py` / `run_experiment.py`, and their regression tests. No performance scores, experiment outputs, raw transactions, or unrelated implementation were inspected. No implementation was edited and no full experiment was run.

**Verdict: F1, F2, and F3 are closed for the reviewed revision. No remaining critical or important defect was found within this focused scope. The corrected v2 experiment/report can proceed with the existing revised-vintage and missing-data qualifications.** This is approval of these corrections, not verification of the in-progress `results_v2` outputs or forecast accuracy. The parent reports that older experiment results are invalid for final model selection and only v2 will inform the final report; this reviewer has not inspected those result files.

## Fix verification

| Original finding | Reviewed locations | Verification and disposition |
| --- | --- | --- |
| F1 / P1: selection labels unavailable at first holdout | `C:/projects/realestate_reco/analysis/regional_forecast_20261027/run_experiment.py:39-40`, `:305-315`; `C:/projects/realestate_reco/analysis/regional_forecast_20261027/forecast.py:62-64`; `C:/projects/realestate_reco/analysis/regional_forecast_20261027/test_forecast.py:106-110` | **Closed.** Development ends 2023-01-27. Its six-month target ends July 2023 and is available under the configured buffer on 2023-10-01, before the first holdout at 2024-01-27. `assert_selection_available` runs before scoring/selection and the manifest stores the selection cutoff and latest selection-label availability. The original April-2024-label / January-2024-holdout boundary is rejected. |
| F2 / P2: derived change uses only newer operand's release date | `C:/projects/realestate_reco/analysis/regional_forecast_20261027/forecast.py:67-80`; `C:/projects/realestate_reco/analysis/regional_forecast_20261027/run_experiment.py:128-143`; `C:/projects/realestate_reco/analysis/regional_forecast_20261027/test_forecast.py:113-120` | **Closed.** `lagged_change` finds the exact lag month and sets the information date to the maximum of both operands' release dates. Feature construction calls this helper before the release-date join. An integrated helper-plus-join check reproduces the delayed January operand: the April change remains missing on May 27 and becomes visible after the August release. Missing exact lag values stay missing and are removed before the feature join. |
| F3 / P2: forecast cohort silently excludes unavailable future outcomes | `C:/projects/realestate_reco/analysis/regional_forecast_20261027/forecast.py:83-89`; `C:/projects/realestate_reco/analysis/regional_forecast_20261027/run_experiment.py:216-257`, `:330-341`; `C:/projects/realestate_reco/analysis/regional_forecast_20261027/test_forecast.py:123-130` | **Closed.** Cohort selection uses origin eligibility and already available training history without testing the origin row's future target. `run_fold` preserves predictions whose actual outcome is missing. Metrics score observed outcomes while counting forecastable/unscored rows; the separate coverage export reports those counts by stage, origin, horizon, model, and level. A synthetic two-region fold retained both predictions, kept the unknown actual missing, and reported two forecasts, one scored outcome, and one unscored outcome. |

The additional post-2009 history check in `run_fold` still uses published training labels; it does not reintroduce the future-outcome exclusion. Holdout regional MAE/bias and empirical residual quantiles also naturally omit missing actual errors, while the prediction table and coverage export retain their existence.

## Evidence

Executed:

```text
tools/python311/python.exe -B -X utf8 -m pytest analysis/regional_forecast_20261027/test_forecast.py -q -p no:cacheprovider
13 passed in 1.36s
```

Additional read-only in-memory checks exercised the actual revised schedule, the selection assertion, `lagged_change` followed by `join_released`, and the actual `run_fold` / `metrics` definitions with a zero-prediction synthetic fixture. The same coverage aggregation used by the exporter counted the retained missing-label row correctly. No fitting of a research model or reading of actual holdout scores was necessary. The parent reports observing the three new tests fail then pass; this reviewer independently verified the current passing tests and the focused integration behavior, not that earlier red/green sequence.

Reviewed SHA-256 fingerprints:

```text
forecast.py       af57eab706aae02763162889f3e2d3748ee4c3fcb5cf41249b58c95955308e95
run_experiment.py 0ab2519e89380050cfa8eb68de6d120d54e5c6dce44561fa34d6e7ccb5c9d3f7
test_forecast.py  dc1e6962a295d9074f9c3db7751c0a7ee1c56fb0435abfe0a38897cbddb68095
```

## Remaining qualifications and review boundary

The v1 qualifications about revised historical snapshots, assumed publication buffers, the unknown October reference price, missing/stale inputs, dependence across regions/time, partial policy coverage, and absence of causal identification remain applicable. Correcting F1/F2/F3 does not reconstruct historical vintages or establish calibrated forecast intervals. Preserve the nine missing current supply feature columns and their disclosure; do not fill them with assumed future observations. No new feature changes or further full runs are requested by this review.

**Declined to judge:** actual v2 artifacts and measured performance (run in progress; no score inspection requested); unrelated policy-feature proposals, raw collectors, transaction normalization, and broader model design (outside this focused follow-up). Later source edits are not covered by the fingerprints above.
