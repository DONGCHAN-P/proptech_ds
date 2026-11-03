# Korean regional six-month apartment forecasting: official predictor inputs

As of **2026-10-27**. Collection is complete for this iteration. No paid calls, credential reads, `.env` changes, transaction parsing, or raw transaction uploads were performed. All new outputs are under this assigned research folder; existing inputs elsewhere were read without alteration.

## 1. Which concrete public inputs were acquired and normalized?

### Takeaway

**`collected/monthly_exogenous.csv` is FINAL/FROZEN:** 16,810 data rows, 18 variables, UTF-8 with BOM, 6,081,342 bytes. SHA-256: **`cbccdf22841a4d93c0233696e182c693fd05801929ba94522dc941e96646b576`**. No further edits will be made to it. The collection helper now refuses to overwrite this frozen filename. A separate annual supplement does not change this hash.

### Cited Findings

Actual acquired coverage, calculated from the saved files, is below. Ranges are endpoints, not a claim that every region has every intermediate observation. Exact region-level coverage is in [`collected/coverage_by_region.json`](collected/coverage_by_region.json); checks and the frozen hash are in [`collected/official_validation.json`](collected/official_validation.json).

| File under `collected/` | Variables / observations actually acquired | Coverage and source |
|---|---|---|
| `bok_policy_rate_monthly.csv` | `bok_policy_rate_eom_pct`; 249 rows | National `00`, 2006-01–2026-09. Derived month-end settings from the official dated rate-change table; not a monthly average. The associated event CSV retains the underlying changes. [BOK rate history](https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643) |
| `bok_mortgage_rate_monthly.csv` | `mortgage_rate_new_business_pct`; 248 rows | National `00`, 2006-01–2026-08. ECOS `121Y006`, monthly, item **`BECBLA0302` = 주택담보대출**, deposit banks, new business, percent per annum. The definition metadata says the source starts 2001-09, but this collection starts 2006-01. [Official item metadata](https://ecos.bok.or.kr/api/StatisticItemList/sample/json/kr/21/30/121Y006), [first acquired ten months](https://ecos.bok.or.kr/api/StatisticSearch/sample/json/kr/1/10/121Y006/M/200601/200610/BECBLA0302) |
| `supply_monthly_six_regions.csv` | `housing_completions_all`, `housing_starts_all`, `housing_permits_all`; 1,440 rows each, 4,320 total | Seoul `11`, Busan `26`, Daegu `27`, Incheon `28`, Daejeon `30`, Gyeonggi `41`; 2006-01–2025-12. Reused existing extraction and three official source workbooks. **All housing, not apartments only.** [Completions](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468), [starts](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=471), [permits](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=31) |
| `molit_unsold_monthly.csv` | `unsold_housing_total`: 1,968 rows; `unsold_housing_completed`: 506 rows | Total unsold: 2017-01–2026-08. Completed unsold: 2024-03–2026-08. Up to 17 legacy provincial units, with absent observations left absent. The latest workbook supplies the long total-unsold grid; 30 explicitly dated existing workbook vintages supply completed-unsold snapshots. [MOLIT unsold report and public attachments](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=32) |
| `mois_population_households_monthly.csv` | `resident_registered_population`, `resident_registered_households`; 3,993 observations each | 2008-01–2026-09, national and regional observations. Nineteen annual download requests returned official CSVs, including the 2026 partial year. Not every administrative unit exists throughout. **Gwangju `29` and Jeonnam `46` end 2026-06; combined `12` begins 2026-07.** [Official population/household CSV interface and definitions](https://jumin.mois.go.kr/statMonth.do) |
| `migration_regional_monthly.csv` | `net_migration_thousand`, `migration_inflow_thousand`, `migration_outflow_thousand`: 475 rows each; exact `net_migration_persons`, `migration_inflow_persons`, `migration_outflow_persons`: 19 rows each | Rounded series: 2024-08–2026-08. Exact-person series: **2026-08 only**. Regional + national + combined-region observations. Original HWPX, extracted table JSON and references are retained. These differently precise variables must not be counted as independent copies of the same signal. [2026-08 official release](https://mods.go.kr/board.es?act=view&bid=205&list_no=447113&mid=a10301020400), [official HWPX download](https://mods.go.kr/boardDownload.es?bid=205&list_no=447113&seq=3) |
| `employment_regional_202609.csv` | `employed_residents_thousand`, `employment_rate_15plus_pct`, `unemployment_rate_pct`; 17 observations each | **2026-09 only**. Residence-based economically active population survey; not workplace employment. Source is the regional sheet of the downloadable official XLSX. [Official release, 2026-10-16](https://mods.go.kr/board.es?act=view&bid=210&list_no=447479&mid=a10301030100), [XLSX](https://mods.go.kr/boardDownload.es?bid=210&list_no=447479&seq=4) |
| `migration_annual_net_six_regions.csv` — **separate supplement, outside frozen combined CSV** | `net_migration_annual_persons`; 126 rows, frequency explicitly annual | Six supply regions, **2005–2025**; the 2005 baseline is included deliberately. 120 observations are 2006 onward. Original annual workbook/extraction were already collected. Each calendar-year observation is stored at December, with assumed availability on March 31 of the following year. [Official 2025 annual migration release / attachment source](https://mods.go.kr/board.es?act=view&bid=205&list_no=443278&mid=a10301020100) |

The public ECOS `sample` endpoint was actually tested. It permits at most ten records per request, so the mortgage history was acquired in 25 nonoverlapping windows of no more than ten months, using the documented public demonstration token rather than a personal key. The first trial item **`BECBLA03` is household lending, not mortgages**; its ten observations are retained as a diagnostic raw response and **excluded from the normalized predictors**. A request exceeding the sample metadata limit returned an official error, retained and marked as an error payload in provenance. [Household trial](https://ecos.bok.or.kr/api/StatisticSearch/sample/json/kr/1/10/121Y006/M/200601/200610/BECBLA03), [mortgage metadata](https://ecos.bok.or.kr/api/StatisticItemList/sample/json/kr/21/30/121Y006).

The reviewed existing `analysis/housing_growth_2006/research` contains the supply workbooks, unsold workbook vintages, annual migration workbook, 2024 census snapshot and an employment report. Its older base-rate extraction started in 2008; this collection uses the official historical change **table** to cover 2006. The other requested existing folder, `research_notes/서울 경기 집값 격차의 복합 원인`, contains predominantly paper PDFs/HTML, findings and manifests; it did not supply an additional ready historical monthly demographic/job panel. See the prior [collection status](../../analysis/housing_growth_2006/research/collection_status.json), [prior manifest](../../analysis/housing_growth_2006/research/collection_manifest.json), and current [provenance](official_provenance.json). No trade inventory was duplicated.

### Inferences

- National code `00` is a common exogenous covariate to join onto modeled regional units. Keep it as a string to preserve leading zeros.
- Six regional supply series and two national rate histories are the immediately useful long historical inputs. Registered population/households add history from 2008. The annual net-migration supplement adds a long, signed demand proxy for the same six regions; it does not add Gwangju.
- Source headers such as numeric `19.1` can mean January or an October label that lost its trailing zero. For total unsold, all **116 consecutive positions** from 2017-01 to 2026-08 were anchored and checked against every adjacent label before normalization. Earlier isolated annual December columns were not relabeled as monthly history. See [header validation](collected/unsold_header_validation.json).

### Gaps

- No claim is made to have acquired monthly unsold history for 2006–2016, monthly population/households for 2006–2007, or historical monthly regional employment before 2026-09.
- The combined CSV does not contain 2026 supply observations. Public 2026 `.xls` attachments are listed at MOLIT, but were not normalized in this bounded iteration. Missing months remain missing. [Completions attachment list](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468).

## 2. When could observations have been used, and what do the vintages mean?

### Takeaway

`available_date` is accompanied by an explicit `availability_basis`. **Assumed lags are not verified release dates, and current revised observations are not a historical first-release database.** The frozen CSV is useful for lag-aware exploratory forecasting, but it is not certified as a strict point-in-time backtest input.

### Cited Findings

| Series | Official timing / definition evidence | Date used in normalized files |
|---|---|---|
| Policy setting | Official table supplies dated rate changes. The historical policy series uses the call-rate target through 2008-02 and base rate thereafter. [BOK table](https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643), [BOK financial snapshot definition](https://snapshot.bok.or.kr/dashboard/A) | Month-end date for a derived month-end setting; underlying last effective date retained. 2026-10 is omitted because the month has not ended. Same-day announcement availability of individual changes is an explicit assumption inferred from the change table, not a separately verified press-release archive. |
| Mortgage rates | Monthly new-business mortgage lending rate, rather than base rate, household-loan average or outstanding-balance rate. [ECOS official metadata](https://ecos.bok.or.kr/api/StatisticItemList/sample/json/kr/21/30/121Y006) | **Month-end +45 calendar days**, labelled assumed. No historical release-day archive was acquired. |
| Permits, starts, completions | Official metadata states next-month-end provisional publication and September of the next year final figures. Coverage includes housing subject to relevant building permits/reports and housing-project approvals. [Permits](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=31), [starts](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=471), [completions](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468) | **Month-end +45 days**, labelled assumed. This is conservative relative to the usual provisional schedule, but **does not make subsequently revised/final figures available at that old date**. |
| Unsold housing | Official metadata states next-month-end publication. Report covers unsold approved/permitted housing, including before and after completion. [MOLIT report](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=32) | **Month-end +45 days**, labelled assumed. Long total-unsold values are from a current workbook; completed-unsold values use each explicitly dated reference-month workbook. |
| Registered population / households | Month-end reference; publication after noon on the first day of the next month, moved to the next working day for weekends/public holidays. Foreigners excluded; residence-unknown persons included from 2010-10, overseas nationals from 2015-01. [MOIS definitions](https://jumin.mois.go.kr/statMonth.do) | **Month-end +10 days**, labelled assumed conservative calendar proxy. Exact historical holiday-adjusted publication dates were not verified. The resulting variable is registered households/세대, not census general households/일반가구. |
| Monthly migration | Report overview states next-month-end publication; current release gives **2026-09-23, 12:00** for 2026-08. Monthly rates are annualized; this collection primarily keeps migration **counts**, not those rates. [Official release](https://mods.go.kr/board.es?act=view&bid=205&list_no=447113&mid=a10301020400), [release HWPX](https://mods.go.kr/boardDownload.es?bid=205&list_no=447113&seq=3) | 2026-08: actual **2026-09-23**. Earlier rounded observations in the current release: assumed **month-end +45 days**. |
| Annual net migration supplement | The release overview describes annual publication at the end of the following January. [Official migration release overview/HWPX](https://mods.go.kr/boardDownload.es?bid=205&list_no=447113&seq=3) | Observation remains `YYYY-12`; assumed availability **`YYYY+1-03-31`**. Never copied to January or expanded into twelve monthly observations. A frequency-specific maximum observation age of 18 months is a parent-pipeline option, recorded in the supplement. |
| Regional employment snapshot | Posted **2026-10-16**, reference 2026-09. [Official release](https://mods.go.kr/board.es?act=view&bid=210&list_no=447479&mid=a10301030100) | Actual **2026-10-16**. No claim to historical publication dates. |

Source files retain URLs, SHA-256 hashes, response types and retrieval timestamps in [`official_provenance.json`](official_provenance.json). Reused files retain their original absolute paths and newly verified hashes. The legacy supply rows use `vintage_date=2026-10-22` as the prior collection's as-of context, explicitly labelled as such; it is **not an independently verified publication timestamp**. Current downloads use 2026-10-27 as retrieval vintage.

### Inferences

- Join with `available_date <= forecast_origin`; then apply the parent's frequency-specific age mask. For strictly defensible vintage use, an exact historical revised value cannot be presumed known before its observed snapshot. Using only the labelled lag still leaves revision leakage possible. Archive first releases/final revisions before claiming point-in-time performance.
- Policy-rate persistence between dated changes is definitional, not imputation of missing survey observations. No other missing observation has been forward-filled, interpolated or changed to zero.
- Six negative source supply observations survive with `negative_source_value_review_required`; they require review/masking, not log clipping or an interpretation of negative physical construction. Signed net migration is preserved, including negative values. Use signed changes/rates in the parent model.

### Gaps

- No exhaustive historical announcement calendar, revision archive or series-level finalization vintage was downloaded. Assumed +45/+10-day dates are modelling assumptions, not guarantees about every historical release.
- The combined CSV intentionally omits a fixed rectangular grid. An absent row means unavailable/not acquired under this extraction, not observed zero. Structural pre-existence/post-abolition demographic zero rows were excluded and logged in [geography missingness](collected/mois_geography_missing.json).

## 3. What should integration defer or exclude?

### Takeaway

The parent owns modeling and feature selection. [`official_feature_registry.json`](official_feature_registry.json) records historical-training exclusions, sparse-series deferral, the separate annual supplement and the frozen input SHA. No additional long network fetch is running.

### Cited Findings

- **Gwangju scope:** the official migration release explicitly says the integrated Jeonnam-Gwangju region began **2026-07-01**, with old Gwangju/Jeonnam migration subitems temporarily supplied through 2026-12 for comparison. The employment XLSX also has explicit Gwangju and Jeonnam subrows, which were used separately. [Migration notice and HWPX](https://mods.go.kr/board.es?act=view&bid=205&list_no=447113&mid=a10301020400), [employment XLSX](https://mods.go.kr/boardDownload.es?bid=210&list_no=447479&seq=4).
- The downloaded demographic CSVs contain old code `29` through **2026-06**, then code `12` observations from **2026-07**. They have **not been spliced**. For a Gwangju-only forecast, filter `29` and leave later population/household observations missing; never use combined `12` totals as Gwangju. Exact bounds were checked from every acquired CSV and logged in [coverage](collected/coverage_by_region.json). [MOIS source](https://jumin.mois.go.kr/statMonth.do).
- The project retains legacy regional identifiers `42` for Gangwon and `45` for Jeonbuk. MOIS original codes `51`/`52` are mapped to those identifiers, with original names/codes retained in `source_locator`. This is a province identifier crosswalk; it is not a full historical boundary adjustment. [MOIS administrative source](https://jumin.mois.go.kr/statMonth.do), [provenance mapping](official_provenance.json).

### Inferences

- **Employment:** exclude all three 2026-09-only employment variables from historical training/feature selection. Retain the raw workbook as a concrete download route for the next iteration.
- **Monthly migration:** do not select these features using a pre-2024 design or use post-2024 coverage to optimize a prior holdout. Its 25-month history is short and the historical table is rounded. The exact-person series is just one month. Longer monthly regional history remains **deferred** rather than represented as obtained.
- **Annual migration:** the separate six-region 2005–2025 supplement is available now, checked against `inflow - outflow = net` for all 126 observations. It can be evaluated with annual-frequency age handling without touching the frozen monthly file. It adds no Gwangju history and has the same current-vintage caveat as the source workbook.
- **Supply staleness:** the latest acquired observation is 2025-12. At the current October 2026 origin it is roughly nine completed months old; the parent-specified `>6 months` mask and missing flags are appropriate integration controls. No 2026 supply was silently carried forward.

### Gaps

- Next iteration: collect long monthly regional migration from KOSIS and historical regional employment tables; obtain/normalize 2026 supply `.xls` files; recover earlier monthly unsold vintages; reconcile official administrative boundaries and release vintages. These are explicit deferred tasks, not prerequisites to reading the frozen CSV.
- Monthly registered household counts are a feasible demographic proxy, not a replacement for annual census household definitions. Employment is resident-based and does not identify workplace jobs, commuting access or income. No new papers or policy chronology were researched here; other agents own those scopes.
