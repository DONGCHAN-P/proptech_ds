# Focused independent review — 2026-10-27

**Verdict: no verified Critical finding; three Important fixes before relying on repeated-round artifacts and regional diagnostics.** These findings do not establish that the completed campaign's scores are wrong or justify promoting another model. The recorded primary `online_ensemble` failed its gate; retain `v3_hgb` as recorded.

Reviewed `PLAN.md`, `evaluation.py`, `experiment.py`, and `test_evaluation.py` in one bounded pass, including the supply update received during review. Final inspected `experiment.py` SHA-256: `1938dd60002052f42ae40624e58ccf707974881bb45bebdf4101f246ab7d12d4`. Line references below refer to that snapshot. Read only the required original target/training helpers and derived feature/prediction artifacts for verification. No implementation edits, campaign run, credentials, raw transactions, external services, or new model search.

## Verified safeguards and evidence

- Focused command: `tools/python311/python.exe -m pytest -q -p no:cacheprovider analysis/regional_forecast_iteration_20261027/test_evaluation.py` — **10 passed in 1.49s**.
- Existing bank: 47,952 rows, 23 origins, 18 candidates. Exact `series_id` sets agree across every candidate at each origin; missing-actual masks also agree. Maximum numeric actual disagreement is only CSV roundoff, `3.56e-15` percentage points. No recorded `train_latest_label_available > origin` violations.
- Training uses mature labels; adaptive weights, bias correction, and intervals filter through `known_errors`, with three-mature-origin gates. Candidate selection excludes strategy names, and strategy output retains `series_id`. Cohort selection does not require the forecast's future actual to exist. This is source/artifact verification, not an independent refit of every model.
- Neutral classification includes both boundaries of ±1%; balanced MAE averages within province, then across provinces and origins. Geography levels are compared separately in the promotion gate.
- Independently compared 36,460 frozen historical feature rows to the updated feature panel by `(series_id, month)`, through January 2026: passed at the declared `1e-12` tolerances. This agrees with `results/historical_feature_invariance.json`. The supply update cannot be credited for historical improvement on these unchanged features. The 144-row collection/release provenance was not independently re-audited.
- Results are retrospective, previously seen 2017–2026 evidence. No new blind or improved-accuracy claim is supported by this review.

## Important findings

### 1. Cache and consumer identities do not cover the full scoring dependency chain

**Locations:** `experiment.py:203–217`, `experiment.py:411–416`.

The bank fingerprint includes feature rows only through January 2026, but cached rows also contain actuals whose six-month targets depend on later `log_change` observations. Verified in memory: adding `0.01` to `d:11110`'s July 2026 `log_change` preserves that fingerprint while changing its January 2026 target log return from `0.04112862872508244` to `0.05112862872508245`. Column renaming also leaves `hash_pandas_object`'s value hash unchanged. The imported target/training helper and reused v3 predictions are not separately identified. In addition, `--mode evaluate` and `--mode forecast` load stored prediction artifacts without checking any producer manifest against the current specs/configuration; those paths bypass even the existing bank fingerprint check.

**Impact:** repeated rounds can silently combine stale labels, predictions, or selection history with a newly written configuration. This is an identity/validation defect, not evidence that prices changed in this completed frozen-data campaign.

**Exact fix:** retain the historical predictor hash, but add a separate digest for the frozen target observations through the latest six-month target, ordered column names/dtypes, original v3 baseline CSV, and imported target/training implementation. Write these with specs, origins, and artifact content hashes into a bank manifest. Require matching manifests before both evaluate-only and forecast-only loads; mismatch must stop or explicitly rebuild the affected artifact. Supply-only changes after January must not invalidate historical fitted predictions. Add small regression checks for a changed July target, renamed column, and stale/mismatched producer specs.

### 2. District error diagnostics collapse different districts into their province

**Location:** `experiment.py:343–346`.

`by_region.csv` groups by `region_code`, which is the two-digit parent province even for district rows. Verified on this bank: **119 distinct district series become only 11 district diagnostic rows** for `v3_hgb`; 22 evaluated Seoul district series share code `11`. Keeping district IDs in predictions does not repair this aggregation.

**Impact:** the promised per-region error view cannot identify which district deteriorated or produced a worst regional outcome. Aggregate district metrics remain usable, but they do not provide the promised individual-district diagnostics.

**Exact fix:** group the detailed regional report by `(model, level, series_id)` and retain `name` plus parent `region_code` as metadata. Keep the existing province-balanced summary separately. Omit cross-sectional ranking from a single-region time-series report, or label any temporal correlation explicitly. Assert that the district report contains one row per evaluated district series/model.

### 3. A repeated forecast overwrites the prospective freeze

**Locations:** `experiment.py:78–80`, `experiment.py:383–401`.

Every forecast call writes to the same model paths, `future_forecasts_6m.csv`, selection trace, and `forecast_freeze.json`; the writers overwrite existing files. The checksum records the replacement CSV and does not preserve the prior release.

**Impact:** a later limited round replaces the original prospective prediction and its identity, preventing evaluation of that original frozen release unless it was archived separately. No claim is made that a prior release has already been lost.

**Exact fix:** write each forecast release into a new immutable run/release directory, with its configuration, code/input/history digests, models, selection trace, predictions, and manifest. Refuse overwriting a completed release. A `latest` pointer may identify the current release, while prospective scoring references an explicit release ID. Verify that two releases preserve both earlier bytes and checksums.

## Deliberately outside this review

- Full refits, independent score reproduction, model-quality improvements, and another campaign: excluded by the requested time and compute bound.
- Raw transaction construction, source revision vintages, exhaustive supply provenance, and original v3 internals beyond the required helpers: outside the four-file review.
- Report rendering and downstream publication: outside scope. No additional search or holdout tuning was performed.
