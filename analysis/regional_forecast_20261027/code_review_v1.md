# Independent review: regional six-month forecasting prototype

Review date: 2026-10-27 (Asia/Seoul). Scope: `PLAN.md`, `forecast.py`, `prepare_panel.py`, `run_experiment.py`, `test_forecast.py`, `input_inventory.json`, `panel_audit.json`, input manifest, and the small derived panel/source metadata needed to verify behavior. No raw transaction scan, credentials, video files, external services, or holdout performance scores were inspected. No implementation files were edited. This report is the requested review deliverable.

**Finalized review handoff:** no additional experiments or exhaustive exploration are required for these findings. The supplied first-pass run covers **8,353,538 transactions, 11 province forecasts, and 119 district forecasts at six months**, with **nine current supply feature columns missing**. These run-output counts are supplied by the parent/user; the reviewer did not independently inspect the performance results.

**Required correction order:** (1) **F1 / P1:** enforce a selection-label publication cutoff before the first holdout; with the existing grid, end development at January 2023 or begin holdout in July 2024, and assert the boundary. (2) **F2 / P2:** timestamp each derived change at the maximum publication date of its two operands and add the delayed-prior-release regression test. (3) **F3 / P2:** predict every origin-eligible series first, attach outcomes afterward, and retain/report missing-label coverage. Preserve the missing supply columns and revised-vintage qualifications; do not substitute assumed future observations. Exact source locations and evidence follow below. Findings remain tied to the reviewed revision; any subsequent implementation fix needs its own focused verification.

The implementation changed during review as the parent integrated collectors and province policy exposure. References below use `run_experiment.py` SHA-256 `a89a7b5e9a45ede66ada5dcbf368af117c5274c12156820794cf3596e4bd8670`; earlier versions were also inspected. Findings describe that reviewed revision, not any later unreviewed edits. The directory is untracked at repository HEAD `58c027cc54b36e7b2f197bd50de391696c44e5f2`, so there is no committed base/head diff for this prototype.

## Strengths

- `forecast.py:40-59` builds exact calendar targets, propagates missing intervening monthly returns, and prevents training on labels before their assumed publication date.
- `run_experiment.py:69-104` constructs a complete calendar before shifting price predictors and eligibility inputs three months. An in-memory perturbation check confirmed that August/September 2026 price, volume, area, and match-count shocks do not change October predictors or eligibility; July remains the latest price-input month.
- Imputation/scaling/model fitting occur within historical training folds. The model family is selected on development metrics rather than the reported holdout scores, subject to the timing defect below.
- The integrated annual migration feature divides signed net migration by an available positive population denominator before count transformations. Negative annual migration rates survive. The short employment, monthly migration, and completed-unsold series are excluded from historical feature selection.
- Stale monthly supply observations become missing rather than being carried indefinitely. The updated code emits current feature availability. The code distinguishes revised-snapshot evaluation, an unobserved October reference price, descriptive correlations, and empirical residual spread from stronger statistical or causal claims.

## Findings

### F1 — P1 / Critical for holdout validity: model selection uses labels unpublished at the first holdout origin

**Locations:** `C:/projects/realestate_reco/analysis/regional_forecast_20261027/run_experiment.py:38-39`, `:303-318`; `C:/projects/realestate_reco/analysis/regional_forecast_20261027/forecast.py:53-55`.

The last development origin is **2023-07-27**. Its six-month label ends in **2024-01** and `add_target` sets `label_available` to **2024-04-01**. Its realized error nevertheless enters `devmetrics` and selects the winner used for the first holdout origin, **2024-01-27**. Writing `selection_frozen_before_holdout.json` before executing the holdout loop does not make those selection labels available in January. The label cutoff inside each model fit does not protect the separate model-selection step.

**Impact:** the first holdout forecast evaluates a model family selected using information unavailable at its issue date. This invalidates a strict chronological claim for the combined holdout, even though development and holdout six-month return windows do not otherwise overlap. No performance scores were needed to establish this.

**Concrete fix:** declare a selection cutoff no later than `min(TEST)`, and filter every development score used for selection to labels published by that cutoff. On the present six-month grid, end development at **2023-01-27**, or retain July 2023 development and start holdout at **2024-07-27**. Save the selection cutoff and latest selection-label availability in the frozen manifest; assert `max(selection_label_available) <= min(TEST)`. Add a regression test for the July-2023 / January-2024 boundary. Recompute selection and evaluation after changing the schedule; do not choose which schedule to report from observed holdout performance.

**Status:** open in the reviewed revision; alerted during review before any reviewer inspection of scores. Experimental dry runs can continue as diagnostics, but their combined holdout must not be presented as clean chronological evidence until corrected.

### F2 — P2 / Important: derived exogenous changes can reveal a delayed prior observation

**Location:** `C:/projects/realestate_reco/analysis/regional_forecast_20261027/run_experiment.py:127-141` (the loop deriving 3/12-month changes).

`prior` is looked up by observation month. Each derived row is copied from the newer observation and therefore keeps only that row's `available_date`, even though computing the change requires both observations. A delayed older release can consequently become visible through a derived change before its own release.

**Concrete reproduction:** January 2020 rate = 999, available August 1; April 2020 rate = 4, available May 1. The April three-month change is -995 and, with the current transformation plus `join_released`, is visible at a May 27 origin, despite the January operand being unavailable until August. This was reproduced in memory. The frozen current monthly source has monotone release dates within each source series, so this edge case was **not observed to contaminate the present data**.

**Concrete fix:** carry each lagged operand's availability alongside its value and use the maximum availability date of both operands for the derived row. For vintage-aware inputs, also require both operand vintages to be available at the origin. Test an out-of-order release and a missing exact lag month. Do not replace unknown lagged values with zero or an assumed later realization.

**Status:** latent point-in-time correctness defect, not an allegation that current monotone releases already leaked through this path.

### F3 — P2 / Important: evaluation silently conditions the forecast cohort on future label availability

**Locations:** `C:/projects/realestate_reco/analysis/regional_forecast_20261027/run_experiment.py:234-236` (the `test = ... target_log_return.notna()` filter); `:249-258` (prediction records).

An origin-eligible region is removed before prediction if any of its next six matched monthly returns is missing. That removal depends on the future market/sample path, whereas live prediction uses origin eligibility alone. The resulting metrics describe only subsequently measurable outcomes; no record or coverage count explains which otherwise forecastable regions disappeared.

**Observed on the derived panel, without fitting models or reading scores:** at 2025-01-27 there are 126 origin-eligible series with sufficient training history but only 125 scored series; `d:27200` disappears. At 2025-07-27, 127 are forecastable and 126 scored; `d:11215` disappears. Thus this currently affects district evaluation; it was not observed to remove a province in the five checked holdout cohorts. Missing labels must remain missing.

**Concrete fix:** construct and predict the origin cohort using only known eligibility and training-history requirements. Attach realized labels afterward. Preserve rows with unknown outcomes, report forecastable/scored/unscored counts and reasons per origin and geography, and compute errors only on observed labels with the coverage qualification beside the metrics. Do not fill future returns merely to retain these rows. Add a test in which an otherwise eligible region loses one future matched month and still receives a prediction.

**Status:** current reporting/selection limitation; not leakage into model fitting and not evidence that the omitted outcomes had larger errors.

## Concurrent changes and policy proposals

The original province-prefix omission is addressed in the reviewed `run_experiment.py:165-177`: province policy features aggregate district pulses using `observed_recent_volume`, which was already shifted three months with the other price inputs. I do **not** leave the original province-prefix bug open as though this integration had not occurred. A regression test should cover partial district exposure, a whole-province event, a national event, missing weights, and invariance to future volume changes.

Stable forecast geographies can still combine distinct legal districts: `prepare_panel.py:22-27` maps, for example, `41597` to `41590`. A later policy specific to `41597` cannot be recovered from a single `41590` policy match. The currently reviewed frozen generic policy input does not contain that event. Before admitting such events, retain fine-geography membership and published past-volume weights separately from the stable forecast series; leave unresolvable exposure missing rather than applying a subdistrict event to an entire predecessor city.

The proposed 24-month registered-event pulses, package/date deduplication, and announced future-effective flags are reasonable **predeclared candidate features**, not solutions to F1 and not legal regime reconstruction. Fix definitions before looking at holdout scores. Deduplicate within the same announced package/type while preserving distinct geographic exposure; gate every flag by the announcement actually known at the origin. An announced effective date inside the next six months can be known; a later revision or realized implementation cannot be backfilled. The absence of verified 2026 records remains a coverage gap, and zero registry pulses must not be described as zero actual regulation. A longer window does not verify that a 2025 measure remained in force in October 2026.

## Statistical limitations checked; no additional defect asserted

- **Source vintages/reporting lag:** `input_inventory.json` records 4,921,602 estimated first-seen timestamps versus 4,067 non-estimated timestamps in the master source. `prepare_panel.py:114-127` discards those availability/cancellation timestamps and builds the current revised snapshot; three-month shifts and `forecast.py:55` are assumed buffers, not reconstructed historical first releases. The official validation metadata explicitly marks strict point-in-time readiness false and labels most release dates as proxies. Existing warnings are appropriate for a prototype. These runs cannot establish strict historical information availability or defensible live accuracy, regardless of F1's fix. A stronger claim needs archived vintages, announcement/publication evidence, and cancellation/revision timing, or an explicit revised-snapshot interpretation throughout every report.
- **Current reference month:** October 2026's full-month price is unknown on October 27. The output explicitly sets `reference_month_observed=False`, normalizes its reference to 100, and predicts relative returns. This is not an observed October price or a won-level forecast, and must not be rebased onto the observed July price without separately forecasting the intervening months and evaluating that different target.
- **Omitted/stale statistics:** all three supply levels are missing for every current province in the inspected feature build because their acquired histories end in December 2025. This masking is correct. Historical model performance where supply is observed does not validate the same contribution under today's missingness. Preserve the availability table and disclose imputations as model handling of missing inputs, not newly observed supply. Annual migration has only six-region coverage; the remaining regions stay missing.
- **Overlap/geographic dependence:** training labels overlap monthly, national covariates are shared, and province/district observations reuse transactions. Chronological cutoffs prevent direct train/test target overlap at an issue date; they do not create independent replications. The five six-month-spaced holdout origins are a short time sample. Separate level metrics and no naive correlation p-values are appropriate. Pooled residual quantiles are descriptive spreads, not calibrated 80% regional prediction intervals. Any later uncertainty comparison needs time-block/geographic dependence handling; adding the number of districts does not add independent time periods.
- **Causal interpretation:** region-level Spearman associations and predictive ablations do not identify policy/rate causal effects. No causal effect is asserted by the reviewed estimator; maintain the existing qualification, especially for hand-coded policy directions and registry coverage.

## Verification and scope boundaries

Executed `tools/python311/python.exe -B -X utf8 -m pytest analysis/regional_forecast_20261027/test_forecast.py -q -p no:cacheprovider`: initially **8 passed**, then **10 passed** after the parent added two calendar/release tests during review. The final checked test-file SHA-256 is `4740cda6742e64532ba72bf36a414c66964f825d3932eaa793cc361ac897cde1`. These tests do not cover the model-selection cutoff or the two other findings.

Additional focused checks used synthetic data or the 37,676-row derived monthly panel: selection-label date arithmetic; delayed prior-release reproduction; source release ordering; annual migration sign/missingness; stale supply masking; excluded short histories; future price-input perturbation; and origin-eligible versus scored cohort counts. No full forecasting experiment or review of its performance results was performed. The parent is running that experiment independently. Implementation/source files are concurrently owned by the parent; later revisions require rechecking the cited lines and findings.

**Declined to judge:** full eight-million-row transaction parsing/deduplication and raw source authenticity (outside requested scan); collector implementations/network collection (parallel parent ownership); paid-service/deployment/production readiness (not requested); realized prediction accuracy and superiority of any model (no experiment results inspected); the proposed new policy features' measured benefit (not implemented or evaluated by this reviewer).

## Assessment

**Ready to claim a clean chronological six-month holdout: No.** F1 must be corrected before that claim. F2 needs an availability-safe transformation and test; F3 needs explicit forecast-cohort coverage. The prototype has useful safeguards and can continue exploratory runs with its revised-vintage and missing-data qualifications, but passing the unit tests alone does not establish statistical validity or high forecast accuracy.
