# Official supply supplement — 2026-10-27

`supplement.csv` is the machine-ready append-only supplement, UTF-8 BOM. Read `region_code` as string. Keys are `(region_code, month, variable)`. Month format is `YYYY-MM`.

- 426 observations: 2026-01 through 2026-08, three variables, national + available provincial units.
- Existing six model codes `11,26,27,28,30,41`: 144 observations, complete 8 months × 6 regions × 3 variables.
- Standard official total housing units, not apartment-only. Multi-family houses use building-count total, not the alternate household-count total.
- `29` and `46` end June; combined `12` begins July. Never duplicate `12` across its old constituent units. Legacy code `42`/`45` matches the existing model geography.
- `available_date` is the verified official release-index date. A downloaded current workbook is not a proven archived first-release vintage. For current 2026-10-27 inference all rows were published; historical real-time backtests still need a vintage caveat.
- No September/October observations were invented or copied from future zero placeholders.

Use `coverage.json`, `release_dates.json`, `validation.json`, `raw_manifest.json`, and `FROZEN.json` for machine-readable coverage, release evidence, cell-level checks, original input SHA-256, and the frozen output hash. Parent-folder `official_update.md` and `provenance.json` explain limitations.

The collector uses existing Python/requests plus xlrd 2.0.2 in the local `_vendor` folder. No system-wide installation was made. A normal host process is necessary in this environment because the sandbox cannot execute the Windows installation underneath the existing venv.

```powershell
& '.venv/Scripts/python.exe' 'research_notes/지역별 집값 예측 반복 검증/data/collect_official_supplement.py' --verify
```

All write modes refuse to run once `FROZEN.json` exists. Do not delete the marker to update this snapshot; create a separate version folder. Existing previous research is read-only and its expected frozen hash is checked.

No new employment or younger-age migration history was collected in this bounded supplement. Existing September employment is a snapshot, not a historical monthly panel.
