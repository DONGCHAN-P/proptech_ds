# Focused timeliness-module review — 2026-10-27

**Verdict: no verified Critical finding; two Important provenance/replay findings.** Neither establishes a numerical score error or supports promotion. Treat this module only as the stated conditional sensitivity using revised historical observations, with no verified historical first vintages or new blind evaluation.

One bounded pass reviewed `timeliness_experiment.py` and `test_timeliness.py`, plus the required target/training/calibration helpers and timing notes found at `research_notes/지역별 집값 예측 반복 검증/timeliness.md`. No full experiment, model fit, score inspection, raw transactions, or implementation changes. Read only series/month keys from the allowed 37,676-row monthly panel to check calendar continuity. Additional synthetic probes ran in a separate process with temporary outputs.

Reviewed SHA-256 identities:

- `timeliness_experiment.py`: `41945ce15fac11482f9f30f137c5405ca0ffe5f2b70111aa5cabc67f0c4bef7a`
- `test_timeliness.py`: `49bfd7aaf40f4641ac8702bf9a68b4308b28db8d06478134d8027fd8e750e073`

## Checks that passed

- The rule starts at May 2020 origins and looks up March 2020 inputs first, consistent with the notes' whole-contract-month assumption. This review did not independently verify the legal sources or historical publication vintages.
- Price rolling windows use past/current raw rows, then exact `(series_id, origin minus two months)` lookup. The inspected monthly panel has no duplicate keys or internal calendar gaps, so row-based rolling windows do not cross missing calendar months on this input. The t−1 perturbation regression passes.
- The original `log_change` target series remains unchanged. Both six-month target construction and three-month label maturity use the existing helpers; training filters mature labels. Cohorts come from the original panel, and fresh-input quality rejection retains the v3 prediction rather than removing the row.
- Interval calibration uses earlier same-rule forecasts, the existing label-availability filter, and three mature origins. No own-outcome calibration or shortened maturity was found in the inspected path.
- Current point-prediction replay inputs include fresh and original feature rows plus the two fitted models and fallback model. The interval-history preservation gap below is separate.

## Important findings

### 1. Fallback rows receive training provenance from a model that did not predict them

**Locations:** `timeliness_experiment.py:86–100`; current-output omission at `133`, `142–144`.

Historical rows start as copies of the v3 fallback, but `train_n` and `train_latest_label_available` are then overwritten for every row with the fresh fit's metadata. This includes rows whose predictions remain the cached v3 fallback. If every row falls back, the loop skips fitting and instead overwrites valid fallback metadata with `0` and `NaT`. The current forecast path also discards the returned fit count/cutoff and does not export those fields.

**Verified synthetic reproduction:** executed only the unchanged historical-loop prefix, using two synthetic cohort rows and an instrumented fit, without fitting a model or running the experiment. The fallback bank had `train_n=999`, cutoff `2026-07-01`; the fresh fit returned `train_n=7`, cutoff `2026-10-01`. In the mixed case, the fallback district correctly kept prediction `3.0` but incorrectly received `7 / 2026-10-01`. With all rows rejected by fresh quality, both unchanged fallback predictions received `0 / NaT`.

**Impact:** the per-prediction audit ledger attributes fallback predictions to the wrong training sample/cutoff, undermining provenance and model replay checks. This does not show that the predictions or maturity filtering themselves are wrong.

**Exact fix:** preserve fallback metadata by default; overwrite it only for rows actually predicted by the fresh model. Record an explicit effective predictor/model source. For pre-rule reuse of the 120-month model, use that cached model's metadata. In current forecasting, capture count/cutoff for both the fallback fit and each fresh fit, assign them according to the effective predictor, and retain them in the published ledger. Add mixed-fallback and all-fallback metadata regressions.

### 2. Frozen releases omit the residual history and implementation needed to replay intervals

**Locations:** `timeliness_experiment.py:109–114`, `148–157`.

The immutable file list includes future predictions, fresh/original current features, the assumption manifest, scorecard, and models. It omits `predictions.parquet`, which supplies the historical residuals used for future calibration. Its SHA is recorded in release metadata, but the history bytes remain only in the mutable results directory. The release also records only a hash of `timeliness_experiment.py`, without preserving that source or identifying/preserving the imported training/calibration implementation and variant configuration.

**Impact:** fitted point predictions can be replayed from the saved features/models with routing, but a later rerun can overwrite the only local residual history needed to reconstruct the originally published intervals. A hash detects mismatch; it does not recover the missing history or implementation.

**Exact fix:** add the exact historical prediction parquet to the immutable release, together with the timeliness source and an immutable snapshot/reference for the imported target/training/calibration helpers and relevant configuration. Preserve resolved variant specs and the associated bank/dependency identity. Add a small release-content/replay regression that reconstructs intervals from archived history after mutable working files change. Archiving these existing artifacts requires no model refit.

## Verification and limits

`tools/python311/python.exe -m pytest -q -p no:cacheprovider analysis/regional_forecast_iteration_20261027/test_timeliness.py` — **2 passed in 1.99s**. The additional bounded historical-loop probe verified both mixed and all-fallback metadata failures. No scores were read or recomputed.

Excluded: final campaign verification, accuracy comparisons, true historical availability/vintage verification, legal-source revalidation, other modules beyond the required helpers, and further model/spec search. No broader approval or performance claim is implied.
