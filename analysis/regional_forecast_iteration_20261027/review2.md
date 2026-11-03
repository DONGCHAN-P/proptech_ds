# Focused follow-up review — 2026-10-27

**Verdict: no verified Critical finding; two Important residuals in the original three findings.** No model refit is required to address these two residuals. This review does not change the failed primary promotion gate or support an accuracy-improvement claim.

One bounded pass limited to the three fixes in `review.md`: bank/dependency validation and the explicit sealing bridge, district diagnostics, and immutable releases. Inspected the relevant changes in `experiment.py`, `evaluation.py`, `artifacts.py`, and their two focused test files. No full campaign, original-data edits, credentials, raw transactions, or additional model search. The background campaign and active artifacts were not modified; additional reproductions used temporary directories.

Reviewed source snapshots:

- `experiment.py`: `b2a74b99a477ad155c7b653c10d2158142b747ae3973dacb285f64998d4e76b7`
- `evaluation.py`: `4926ab4c3182bf5c8860c655be3e2875b64d2e38304650cb709e5e2cb736b912`
- `artifacts.py`: `ec86c434cefb728bd554b5df8e7e58787010a6b4887aa284b6d4a1a329860d4e`

## Status of the original findings

1. **Cache and consumer identity: substantially addressed; sealing completeness remains open.** `digest_frame` includes schema/dtypes; dependencies include all panel target observations, original helper/baseline hashes, training-function digests, specs, origins, and sklearn version. Normal evaluate/forecast entrypoints check bank identity/content; forecast also checks evaluation identity/history. Captured round-two training digests, specs, and origin configuration matched current code in this review. The bridge still needs the completeness check below.
2. **District diagnostics: resolved in code and focused tests.** `regional_metrics` groups by `(model, level, series_id)`, retaining the name and parent province; `evaluate` writes that output to `by_region.csv` and preserves the older aggregation separately. The same-province/two-district regression passes. The background round's final report was not regenerated or independently audited here.
3. **Prospective freeze preservation: substantially addressed; manifest integrity remains open.** Content-addressed release directories preserve separate forecast/configuration/model/history/source snapshots, and the tests cover two releases plus modified archived prediction bytes. Reusing an existing release does not validate its manifest contents, as reproduced below.

## Important residuals

### 1. `--mode seal` accepts an incomplete origin/model grid

**Locations:** `experiment.py:503–516`, `experiment.py:240–243`.

The bridge checks the global set of model names, then validates only groups present in the artifact. It never requires the artifact's origin set to equal `ORIGINS`, or every declared origin to contain every model. A missing origin/model block is never visited. `seal_bank` records the resulting smaller counts without rejecting them.

**Verified reproduction:** copied only `cache/bank_201501.parquet` into an isolated results directory, together with the actual captured round-two configuration/training identities. Ran the real `main()` seal branch with `features()` returning the already-loaded panel, using the real cohort/target/dependency checks. It printed `Reviewed bank sealed` and wrote a manifest with **1 artifact origin, 26 models, but 23 declared dependency origins**. No predictions were fitted or changed. Normal identity loading does not reject these count differences.

**Impact:** a partial background result, truncated artifact, or missing candidate fold can be certified as the completed declared experiment. Subsequent metrics or adaptive selection can use an incomplete or unequal comparison history.

**Exact fix:** before sealing, require exact equality between observed `(origin, model)` pairs and `ORIGINS × SPECS` (or an explicitly recorded expected nonempty-origin set). Reject duplicate `(origin, model, series_id)` keys and retain the per-block exact cohort/actual checks. Enforce the same structural validation in the normal bank loader. Add regressions removing one entire origin and one model from only one origin. Once the background run finishes, validate and seal its unchanged complete artifact; these checks do not require rerunning model training.

### 2. Existing releases accept modified provenance manifests

**Location:** `artifacts.py:25–31`.

On reuse, `freeze_release` checks only the manifest's `release_id` and archived file bytes against the incoming files. It does not compare stored `metadata`, `files`, or `complete` with the expected manifest, or recompute the stored manifest identity.

**Verified reproduction:** created a temporary release for metadata `{'as_of':'2026-10-27'}`, edited only `release.json` to change its stored `as_of` to `2099-01-01`, then repeated the original freeze call. It returned the existing release successfully with the modified date still present. The current modified-file test does not exercise manifest changes.

**Impact:** changed provenance can be accepted as an intact frozen release. A subsequent `latest_release.json` update would record the modified manifest's hash rather than reject the modification.

**Exact fix:** on reuse, require the stored manifest to equal the canonical expected `{metadata, files, release_id, complete: true}` payload, including its exact file map. Recompute/verify the content identity from stored metadata and file hashes, then retain the archived-byte checks. Add regressions changing manifest metadata and its file map; both must fail without overwriting the release.

## Verification and limits

`tools/python311/python.exe -m pytest -q -p no:cacheprovider analysis/regional_forecast_iteration_20261027/test_evaluation.py analysis/regional_forecast_iteration_20261027/test_artifacts.py` — **16 passed in 1.56s**. Both additional temporary-directory reproductions above completed successfully and demonstrated the residuals.

No broader architecture audit, second model review, full origin-by-origin refit, final round-two score reproduction, or historical supply re-audit was performed. Previously inspected historical scores remain retrospective evidence, not a new blind evaluation.
