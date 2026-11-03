# Korean regional six-month forecasts: validation safeguards

2026-10-27; six primary references. Design proposals, not measured gains. Inspected: [forecast.py](../../analysis/regional_forecast_20261027/forecast.py), [run_experiment.py](../../analysis/regional_forecast_20261027/run_experiment.py). 

## 1. As-of nested validation

### Takeaway
Nest chronological selection; purge by publication date, grouping all regions at each origin.

### Cited Findings
- S1: Ordered splits support a sample-count gap, not publication-date rules. [sklearn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- S2: Tuning and evaluating on the same observations yields optimistic estimates. [sklearn nested CV](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html)
- S3: Rolling-origin evaluation uses prior observations and supports multi-step errors. [FPP3 §5.10](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation)

### Inferences
- S1–S3 application: q's label ends q+6, matures q+9 with three-month reporting delay. Require `label_available <= cutoff` for training AND selection errors. Use calendar dates, not nine panel rows; do not double-embargo after this filter.
- Inner training obeys each inner cutoff; outer T selects only from inner OOS errors published by T. Fit preprocessing within training. Use forward-only splits plus maturity purging; freeze outer predictions before scoring.
- Features/eligibility must be origin-known. No future realized policy/rate paths; label scenarios separately. Revised snapshots remain pseudo real time.
- Code guards maturity and ends DEV in January 2023; its global DEV winner is not per-origin nested selection.

### Gaps
Three-month delay is assumed; historical releases/vintages were not audited.

## 2. Comparable metrics and dependence

### Takeaway
Compare common cohorts; retain coverage counts and time-block summaries.

### Cited Findings
- S4: Stationary bootstrap resamples dependent observations in blocks, assuming weak dependence/stationarity. [Politis & Romano (1994), indexed publisher abstract](https://doi.org/10.1080/01621459.1994.10476870)
- S5: Interval score penalizes width and misses; coverage alone is insufficient. [Gneiting & Raftery (2007), §6.2, eq.43](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)

### Inferences
- Compare common origin/region/horizon keys, targets, scoring cutoffs and units. Freeze issuance eligibility; report issued/scored/missing/failed/excluded counts and full-cohort coverage. Predeclare fallbacks; failure-driven exclusions must not improve scores (S3–S4).
- Primary: equal-origin/equal-province six-month MAE. Districts separate: average within province, then provinces/dates. RMSE uses identical weights before square root. Add median/p90 absolute error, bias `mean(pred−actual)`, MAE ratios versus no-change/momentum; units: pp after `100*expm1(log_return)`.
- Direction: predeclare neutral band (e.g. ±0.5 pp) for both signs; report three-class accuracy, macro recall/counts. Rank: within-origin/same-level Spearman, averaged equally over origins; constant/too-small cohorts NA (S3 design).
- For 80% [L,U], report coverage, mean width and mean `IS=U-L+10*(L-y)*1(y<L)+10*(y-U)*1(y>U)`; lower IS is better (S5). Break out dates/regions/predeclared regimes.
- Resample paired losses in contiguous time blocks, retaining all regions together (S4 adaptation). Monthly six-month labels overlap: examine ≥6-month blocks and longer sensitivity. Jan/Jul labels need not overlap; common shocks persist. With five outer origins, show per-origin dispersion; avoid bootstrap significance claims.

### Gaps
Predeclare band/rank minimum/block length; Korean optima are unknown. Nonstationarity weakens bootstrap inference.

## 3. Bounded iteration and prospective release

### Takeaway
Use old published OOS errors for adaptation/calibration; freeze future releases.

### Cited Findings
- S6: DMA adapts model importance sequentially with forgetting; superiority is not guaranteed. [Raftery, Kárný & Ettler (2010), original-paper abstract](https://citeseerx.ist.psu.edu/document?doi=a40ab3f32b2340b0698ab22510ad7713acfb6fd6&repid=rep1&type=pdf)
- Code pools holdout/path-holdout residuals for intervals; these cannot validate coverage on their own calibration origins (code above).

### Inferences
- Cap at eight including two baselines: expanding pooled ridge; recent-window ridge (60 OR 120 months); local ridge with pooled fallback; regional shrinkage; equal/adaptive blends. No factorial search; existing inputs only (S1–S3).
- Adaptive blend: archived OOS forecasts, only errors published by cutoff; replay delays historically (q error enters q+9). No fitted/unmatured errors. Aggregate region/time-weighted loss; shrink nonnegative weights toward equal weights; tune decay/shrinkage inside inner folds. S6-inspired proposal, not DMA itself.
- Each outer origin/horizon: calibrate quantiles from older known OOS errors, freeze, then score (S2,S5). Pool sparse regions by level; disclose counts. Mature 2024+ errors can calibrate later releases, not their own OOS coverage. No coverage guarantee under dependence.
- Seen 2024+ is reused development evidence; re-nesting cannot create a “new blind” set (S2). Log trials; predeclare objective, cap, stopping/promotion and tail/bias/coverage guardrails. Prefer simplicity absent stable paired block gains.
- Freeze timestamp, hashes, predictions/intervals, cohorts and update rules prospectively. A 2026-10-27 release's April-2027 target matures around July under assumed delay; score after actual publication, preserving issued predictions.

### Gaps
Code not executed; parent owns metrics/experiments. No macro collection, paid calls/uploads. S4: abstract only. DMA full text failed; S6 uses indexed original abstract.
