# Final focused follow-up — 2026-10-27

**Verdict: both residuals from `review2.md` are resolved. No verified Critical or Important findings remain within this two-fix scope.** No further change or model refit is required for these fixes.

One bounded pass covered grid completeness at the seal/load entrypoints and integrity validation when reusing a frozen release. Freshness sensitivity, model changes, promotion scores, and the in-progress campaign's final outputs were outside scope. No implementation edits, full campaign, credentials, raw transactions, or additional model search. Additional probes used temporary directories and left active campaign artifacts untouched.

## 1. Incomplete bank sealing/loading — resolved

`artifacts.py:45–49` requires the exact declared origin/model Cartesian product and rejects duplicate `(origin, model, series_id)` keys. The check is called by `experiment.py:241` (`seal_bank`), `experiment.py:252` (`load_bank`), and `experiment.py:517` (explicit seal bridge), before accepting the artifact. Existing per-block cohort/actual checks remain in the bridge.

Reproduced the previous failure case using the real 26-model, single-origin cache block in an isolated directory. The real seal entrypoint, direct seal writer, and bank loader now each reject it with `Incomplete or duplicate origin/model/cohort grid`. The rejected seal entrypoint creates no bank manifest. A separate duplicate-key probe also rejects, while a complete small grid accepts. The regression suite covers missing origins and a missing candidate block.

## 2. Modified release manifest reuse — resolved

`artifacts.py:25–32` compares the entire stored manifest against the canonical expected payload, including metadata, file map, completion flag, and computed release ID, before checking archived file bytes.

Temporary-directory probes separately changed metadata, the file map, `complete`, and `release_id`: all four now reject with `Frozen release manifest was modified`, without replacing the edited manifest or prediction bytes. Reusing an unchanged release accepts and preserves the original manifest bytes. Existing regressions also cover separate immutable releases and tampered archived prediction bytes.

## Verification

`tools/python311/python.exe -m pytest -q -p no:cacheprovider analysis/regional_forecast_iteration_20261027/test_evaluation.py analysis/regional_forecast_iteration_20261027/test_artifacts.py` — **18 passed in 1.59s**. The isolated entrypoint and manifest probes described above also passed.

Inspected source SHA-256 identities:

- `experiment.py`: `f2cdbdf40f74066730245612a92e28d5e9e83cbc21c720a421b87e70b28be5ee`
- `artifacts.py`: `2d49d352b38846b6b8bc0330dcbebd3ca7b1639dacabe4621ad3e68468a07fca`
- `test_artifacts.py`: `8aa79be117c83313732b6f40e5e082d73e7220dc8ef6f904b9fee1a195ac3379`

This closes only the two reviewed residuals. It does not independently certify the completed 26-candidate bank, reproduce final scores, change the promotion decision, or establish improved accuracy or a new blind evaluation.
