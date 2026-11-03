# Focused review: policy clustering and 2026 projection

Date: 2026-10-27. Scope is limited to the package clustering in `policy_features`, appending the separate frozen four-event 2026 projection, its snapshot/hash integration, and the related regression test. No broad research, score inspection, experiment-output review, full experiment, or implementation edit was performed. The DEV/selection/training/cohort/metrics logic was not reopened; the v2 review remains the reference for F1/F2/F3.

**Assessment: no critical or important defect found in this policy patch. The v3 rerun and report may proceed within the existing statistical and policy-coverage qualifications. This does not verify the in-progress v3 experiment outputs or forecast accuracy.**

## Verified behavior

- **One pulse per package/direction and regional row.** `C:/projects/realestate_reco/analysis/regional_forecast_20261027/forecast.py:100-114` groups by explicit package ID, otherwise package announcement date, otherwise record announcement date, plus direction. It unions eligible regional masks before adding the package once. The June 30 designation and LTV projection records therefore yield one tightening pulse and one announcement count for a matching district, rather than two.
- **No early disclosure from clustering.** `forecast.py:106-112` still applies each submeasure's own announcement date, six-month window, and geographic mask before unioning within a package. Synthetic checks for a shared package date and a shared package ID confirmed that a later submeasure's geographic scope remains invisible before that submeasure is announced. Appending the actual four projected 2026 records did not change pre-April-2026 features in the checked historical fixtures.
- **Projection append and frozen input.** `C:/projects/realestate_reco/analysis/regional_forecast_20261027/run_experiment.py:63-70` loads the original frozen registry and appends the separate 2026 snapshot. The inspected combined input contains exactly four additional unique event IDs, with the required fields and announcement dates on or before October 27, 2026. `run_experiment.py:290-294` freezes that projection separately; the frozen file was byte-identical to its local projection source. `run_experiment.py:199-203` records the extra snapshot hash, clustering rule, and unresolved geography.
- **Geography remains narrow.** In `C:/projects/realestate_reco/analysis/regional_forecast_20261027/data/policy_2026_verified_snapshot.json:19-32`, June coverage remains `41597`, `41463`, and `41310`. An October 27 fixture showed one June-package pulse for the matching districts and none for canonical `41590` or an unrelated district. April's six-month pulses have expired by that October origin. The test inclusion of `41597` checks prefix matching only: the actual stable forecast panel does not thereby acquire a resolved Dongtan exposure. Its omission from canonical Hwaseong remains an explicit coverage gap, not evidence that Hwaseong was unaffected.
- **Regression test.** `C:/projects/realestate_reco/analysis/regional_forecast_20261027/test_forecast.py:133-141` verifies that same-package designation/lending submeasures count as one signal.

The fallback date/direction cluster is an operational definition of a registered policy-package signal. Its announcement count is not a count of independently identified legal actions. The code correctly gates information by announcement rather than retroactively using an effective date; this review does not certify continuing legal force or reconstruct a complete policy regime.

## Verification

Executed:

```text
tools/python311/python.exe -B -X utf8 -m pytest analysis/regional_forecast_20261027/test_forecast.py -q -p no:cacheprovider
14 passed in 1.36s
```

Additional checks were read-only and in memory: loading the actual frozen registries, checking their append/schema/unique IDs, comparing the projection bytes with the local source, confirming no pre-announcement feature change, exercising same-package date/ID geography gates, and checking duplicate June pulses and the unresolved `41597`/`41590` boundary. The parent reports observing the new test fail then pass; this reviewer verified its current passing state, not the earlier red/green sequence.

Reviewed SHA-256 fingerprints:

```text
forecast.py                             a23fc229c9145eb34aa2e02725b38530b7bc54eab41fab6bc503529fa19b8ade
run_experiment.py                       45cc0c6d26df368c4b7bd0d97be4b1c5f82e53b705308737b063ce8f2f5f7710
test_forecast.py                        458e5c760695690cce14aac56f5177e4d80996d194b536fc748eac00a1ed67ac
data/policy_2026_verified_snapshot.json  42ace953b180e822a061041c551c56a1dee18f6a095b8c12e3902ce37bdeaa4d
```

**Declined to judge:** the substantive FSC source verification performed by the separate researcher (not independently repeated here); completeness or legal/regime interpretation of the four-event projection; v3 scores/artifacts (run in progress and outside the requested inspection); unrelated features and previously reviewed model logic. Revised-vintage limitations, missing supply inputs, dependence, unknown current reference price, and the lack of causal identification remain as documented in v1/v2. No additional experiment or implementation change is requested by this review. Later source revisions are outside these fingerprints.
