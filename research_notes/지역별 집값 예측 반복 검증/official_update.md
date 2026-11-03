# Bounded official housing-supply supplement — as of 2026-10-27

## 1. Was the missing 2026 regional supply data actually acquired?

### Takeaway

**Yes. `data/supplement.csv` is FINAL/FROZEN: 426 rows, 2026-01 through 2026-08, three supply variables.** The existing six model regions have a complete additional **144 observations** (6 regions × 8 months × 3 variables). CSV SHA-256: **`24b6bc067466c0ba67b73746ef902d38ff495ed1df4c2dc96d10bca87c5d2bcb`**. The original frozen research CSV remains unchanged.

### Cited Findings

- Downloaded **24 actual official XLS workbooks**, eight monthly workbooks each for `housing_completions_all`, `housing_starts_all`, and `housing_permits_all`. The original attachments, three source-page HTML snapshots, two official release-index snapshots, sizes, full download URLs, and SHA-256 values are retained in [`data/raw_manifest.json`](data/raw_manifest.json). Sources: [MOLIT completions](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468), [MOLIT starts](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=471), [MOLIT permits](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=31).
- Each variable has **142 observations**: national `00` plus 17 provincial units for January–June, national plus 16 units for July–August. Existing model codes `11,26,27,28,30,41` each have all eight months. Exact variable/region endpoints are in [`data/coverage.json`](data/coverage.json). The source workbooks themselves supply the regional labels and monthly cells. [Completions attachments](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468), [starts attachments](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=471), [permits attachments](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=31).
- These are **total housing, public plus private, not apartment-only**. The monthly sector-total table uses the standard total with multi-family houses counted by buildings; the alternate total by households is not substituted. August national monthly values are **15,151 completions**, **18,013 starts**, **21,607 permits**. Each was independently matched to its workbook's housing-type monthly-total block. Source workbook and exact cell for every normalized record are included in the CSV and [`data/validation.json`](data/validation.json). [Official total-housing tables](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=31).
- Each month's own reference-month workbook supplies only its corresponding month. Future blank/zero columns, YTD totals, public/private subrows, and duplicated housing-type totals are excluded. All **24** national totals equal sums of their regional rows; all **426** source rows pass monthly-sum-to-YTD checks; all **24** national totals match the independent housing-type monthly-total block. These checks use the saved official workbooks and are recorded with cell locators in [`data/validation.json`](data/validation.json). [Official workbook collection](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468).

### Inferences

- Append the supplement by string key `(region_code, month, variable)`. Preserve `00` as national rather than dropping its leading zero. The first seven columns are the requested machine schema: `region_code,month,variable,value,available_date,availability_basis,source_url`; additional columns provide units, scope, source cells, raw SHA-256 and vintage cautions.
- The six modeled regions' supply endpoint advances from December 2025 to August 2026 without replacing any historical research observation. Filter to those six codes when the parent model requires the previous geographic scope; other provincial observations and the national total are additional coverage.
- Legacy model codes `42` for Gangwon and `45` for Jeonbuk are retained for consistency. They are a model join convention, not a claim about current government administrative code numbers. `29`/`46` end June and combined `12` begins July; do not copy the combined observation back onto both old regions.

### Gaps

- September and October 2026 supply workbooks were not listed on any of the three observed official metadata pages. No missing month was estimated, zero-filled, or extrapolated. This is an as-of collection observation, not a prediction of their eventual release dates.

## 2. What availability dates and vintage limits should the model use?

### Takeaway

All **426 observations use verified official release-index dates**. No 45-day assumption was needed. The dates verify the monthly statistical release; the downloaded files are current attachment vintages, not authenticated archived first-release files.

### Cited Findings

The two saved official release-index pages provide all eight monthly release dates. Exact titles, linked MOLIT release pages, and saved evidence locations are in [`data/release_dates.json`](data/release_dates.json). [Official index, page 1](https://stat.molit.go.kr/portal/notice/colmnList.do?hNum=1394&page_no=1), [official index, page 2](https://stat.molit.go.kr/portal/notice/colmnList.do?hNum=1394&page_no=2).

| Observation month | `available_date` | Evidence |
|---|---|---|
| 2026-01 | 2026-02-27 | [MOLIT January release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95091744) |
| 2026-02 | 2026-03-31 | [MOLIT February release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95091843) |
| 2026-03 | 2026-04-30 | [MOLIT March release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95091958) |
| 2026-04 | 2026-05-29 | [MOLIT April release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95092059) |
| 2026-05 | 2026-06-30 | [MOLIT May release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95092164) |
| 2026-06 | 2026-07-31 | [MOLIT June release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95092274) |
| 2026-07 | 2026-08-31 | [MOLIT July release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95092360) |
| 2026-08 | 2026-09-30 | [MOLIT August release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95092469) |

MOLIT labels the routine schedule as next-month-end provisional figures and next-year-September final figures. The source attachment snapshots therefore remain identified as provisional current-year data. [MOLIT statistical metadata](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468).

### Inferences

- Every acquired observation is usable with respect to publication timing for the requested **2026-10-27 current-information snapshot**. Join on `available_date <= forecast_origin`, not merely the observation month.
- `availability_basis=verified_official_release_index_date_not_archived_workbook_vintage` explicitly distinguishes release evidence from vintage authentication. Do not treat it as proof of the exact value an analyst saw at each earlier 2026 forecast origin.

### Gaps

- The exact first-publication timestamp and revision history of each XLS attachment were not separately established. No claim of a fully point-in-time historical archive is made. The helper supports an explicit month-end-plus-45-calendar-days fallback if a future bounded collection has no verified release date, but this frozen CSV uses none.

## 3. What is frozen, reproducible, and still deferred?

### Takeaway

The supplement, raw inputs, helper, coverage, checks and provenance are saved entirely within the assigned paths. No employment-history or younger-age migration expansion was attempted after the supply gap was closed.

### Cited Findings

- The new frozen hash and collector/raw-manifest hashes are in [`data/FROZEN.json`](data/FROZEN.json); final machine status is [`data/status.json`](data/status.json). Re-run [`data/collect_official_supplement.py`](data/collect_official_supplement.py) with `--verify` to check the CSV, every source input, the helper and the old frozen input. All write modes refuse after freezing. Source evidence remains the public [MOLIT metadata and attachments](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468).
- The previous `../지역별 집값 6개월 예측 연구/collected/monthly_exogenous.csv` still hashes to **`cbccdf22841a4d93c0233696e182c693fd05801929ba94522dc941e96646b576`**, matching its existing freeze declaration. It was read for verification only. The previous supply collection's official sources were [completions](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468), [starts](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=471), and [permits](https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=31).
- Existing employment normalization in the previous research reads a September 2026 regional snapshot. This supplement does not relabel that snapshot as historical monthly coverage. Its underlying official source is the [September employment release](https://mods.go.kr/board.es?act=view&bid=210&list_no=447479&mid=a10301030100).

### Inferences

- `data/supplement.csv` is ready for the parent's code/model work. This assignment collected and validated inputs; it did not retrain models or claim an out-of-sample accuracy improvement.
- The local `data/_vendor` contains only the necessary `xlrd==2.0.2` XLS reader installed for this task. The pre-existing Python environment was used with host execution because its Windows Python installation was inaccessible inside the sandbox. No global package installation or existing-venv package change was made.

### Gaps

- Long monthly regional employment/job history and younger-age migration remain deferred to preserve the bounded scope. No exhaustive KOSIS loop was run.
- No paid API calls, credential reads, transaction parsing, raw-transaction uploads, or changes to previous frozen research were performed. No raw transaction data was needed for these official aggregate supplements.
