# Independent bounded code review — 2026-10-27

Reviewed the amended plan; `diagnostics.py`, `interval_experiment.py`, `rental_experiment.py`, `capture_inputs.py`, `residual_experiment.py`; and all five corresponding test modules. Read the required evaluation, training, release-join, and timeliness producer helpers and the rental handoff's availability assumptions. This is one code-review pass with focused synthetic checks. Final artifact replay, the full suite, reports, and fitted-model validation remain with the parent. No models/campaigns, raw transaction reads, credentials, or network calls were used. Only this review file was written.

**Result: one Important issue; no verified Critical issue.**

## Important — diagnostic input join overwrites issued t−2 provenance

**Location:** `diagnostics.py:65–66`, called for all four models at `diagnostics.py:94`.

`read_sources()` combines baseline A/B records and timeliness C/D records, but returns only the baseline feature panel. `attach_inputs()` drops existing input columns, including `price_input_month`, and replaces them from that baseline panel. A C/D row actually issued using t−2 inputs is consequently labeled t−3, even though its retained `effective_predictor` and `fallback_to_t3=False` say it used the fresh predictor. Its attached returns and quality tags likewise describe baseline inputs. This false date reaches the all-model `error_ledger.parquet`, obscuring the fresh/fallback distinction required by the review contract. The baseline-only diagnostic summaries and numeric factor calculation are outside this finding's impact.

**Verified reproducer** (repository root, synthetic inputs only):

```python
import sys
sys.path.insert(0, 'analysis/regional_forecast_diagnostics_20261027')
import pandas as pd
from diagnostics import attach_inputs

rows = pd.DataFrame(dict(
    series_id=['p:11'], model=['hgb_t2_law'],
    origin=[pd.Timestamp('2022-07-27')],
    price_input_month=[pd.Timestamp('2022-05-01')],
    effective_predictor=['hgb_t2_law'], fallback_to_t3=[False]))
features = pd.DataFrame(dict(
    series_id=['p:11'], month=[pd.Timestamp('2022-07-01')],
    as_of=[pd.Timestamp('2022-07-27')],
    price_input_month=[pd.Timestamp('2022-04-01')], return_6=[.01]))
out = attach_inputs(rows, features)
print(rows.price_input_month.iloc[0], out.price_input_month.iloc[0])
print(out.effective_predictor.iloc[0], out.fallback_to_t3.iloc[0])
```

Observed: `2022-05-01 → 2022-04-01`, while the effective predictor remains `hgb_t2_law` and fallback remains `False`.

Preserve the issued input-date provenance. If baseline inputs intentionally provide common comparison context, name that context explicitly; tags presented as effective model inputs need the corresponding fresh/fallback snapshot. Add a regression assertion that a fresh t−2 row retains its issued date and agrees with its routing flag.

## Other requested checks

- **Actuals/cohorts and weights:** missing outcomes stay in the ledger with zero contribution. The common-target guard rejects dropping even an unscorable row. An uneven-region synthetic case, including an entirely unscorable origin, produced total weight `1` and contribution sum `6.25`, equal to `balanced_mae=6.25`.
- **Factor math:** both gain identities passed: base lag gain + base training gain + interaction = total gain, and the two Shapley contributions sum to total gain. Producer definitions confirm A/C's nominal cumulative start in 2009 and B/D's nominal 120-month window with a 2007 floor, measured from the latest mature training month. Before the sensitivity begins, C reuses A and D reuses B. Afterward, fresh-ineligible D rows fall back to A's cumulative predictor, not B. Thus the factors describe routed policy comparisons, including training-start and fallback effects; they do not isolate a pure lag intervention. The manifest acknowledges start-year and quality-fallback effects, subject to the provenance issue above.
- **Calibration and interval comparison:** all three methods use the same prior-mature-origin readiness rule and preserve current rows and points. Synthetic future, immature, and older-than-60-month extreme residuals left every method unchanged. All three returned the same forecast/scored/interval counts, `(2, 1, 1)`. Observed volatility is the scale input, and coverage, width, and interval score are evaluated together. Realized outcome/reversal tags are diagnostic outputs; calibration does not consume them.
- **Rental features:** multiplying every price-index observation by `1000` left returned features unchanged. The implementation uses exact-month log ratios, so a common multiplicative base cancels; it never supplies the rebased price-index level to the model. The survey supply-demand level is a separate declared feature. Perturbing observations after July 2026 did not change October 27 inputs. The July-step check confirmed availability on **October 1**, whereas the scout's `EOMONTH(reference month,3)` is **October 31**. This difference is explicitly declared in the experiment docstring/metadata and is intentional conditional timing, not verified historic publication timing. Latest-vintage historical revisions remain a stated limitation; cancellation of a common base does not undo revisions.
- **Residual extension:** the three focused synthetic tests passed. An additional check preserved identifiers, eligibility, and label-availability columns and reconstructed positive, negative, and missing original targets after residual transformation and log-space recombination. Historical cohorts are selected from the original panel; training uses the residual-target panel. Historical/future forecasts add back exactly `0.5 * observed return_6` in log space before scoring/calibration. No additional Important issue was verified in this module.
- **Capture and post-hoc bands:** reviewed capture/audit code and its placeholder test without accessing transaction data. The new outcome-band table explicitly retains an `unscored` band and is used only for report statistics; no path feeds it into calibration, rental features, or residual offsets.

The synthetic rental-date check initially used the wrong pandas month-end offset in the reviewer harness; it was corrected to `DateOffset(months=3) + MonthEnd(0)`, and the rental checks then passed. No implementation change was made.
