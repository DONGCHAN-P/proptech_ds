# Korean transaction input timing — 2026-10-27

## What deadline and public-data delays are verified?

### Takeaway
The 60→30-day change took effect on **2020-02-21**, by contract date. A reporting deadline is neither a completeness date nor a finality guarantee.

### Cited Findings
- MOLIT's 2020-02-20 announcement confirms the change. Its historical four-year figures were mean reporting time 23 days and 68% within 30 days; these are **pre-change evidence**, not current latency estimates. [MOLIT](https://www.korea.kr/news/policyNewsView.do?newsId=148869388)
- RTMS specifies 60 days for contracts before 2020-02-21, otherwise 30; publication is normally the next day after reporting **if disclosure procedures present no problem**. Records are grouped by contract date, not reporting date. [FAQ](https://rt.molit.go.kr/pt/bbs/faqList.do?mobileAt=&qnaProcessSttusCode=1)
- MOLIT explicitly warns that real-time changes and cancellations make counts and contents differ by extraction time. [Download guidance](https://rt.molit.go.kr/pt/xls/xls.do?mobileAt=)

### Inferences
- Contract-to-report delay, disclosure processing, and later revisions are distinct. Neither 30 days nor next-day publication proves all records were available or final.

### Gaps
- These sources provide no post-2020 reporting-lag distribution, guaranteed processing maximum, revision completion horizon, or historical snapshot archive.

## What may the fixed-cohort 11-province comparison claim?

### Takeaway
Retain t-3 as baseline; t-2 is defensible only as a **conditional pseudo-realtime sensitivity**, keeping the same three-month label maturity and fixed evaluation cohorts. Implementation remains with the parent.

### Cited Findings
- Contract-month assignment and extraction-dependent revisions mean today's older monthly values need not equal values visible at a historical forecast origin. [FAQ](https://rt.molit.go.kr/pt/bbs/faqList.do?mobileAt=&qnaProcessSttusCode=1); [revision warning](https://rt.molit.go.kr/pt/xls/xls.do?mobileAt=)

### Inferences
- At each month's 27th, t-3 is roughly 85 days after month-end and t-2 roughly 55 (2026-10-27: July 31→88 days; August 31→57 days).
- **March 2020 is the first wholly covered contract month**, so a whole-month t-2 rule first qualifies at 2020-05-27. Applying it at March 27 would instead use January, still under the 60-day rule; February is mixed.
- Task-supplied context: Oct-13 master plus October-2026 expansion contains August data. August 31→October 13 is 43 days, already ≥30. Age supports a lag approximation; it does not establish completeness, row provenance, or historical availability.
- State the assumption: latest-snapshot t-2 aggregates approximate what was observable then; late filings, corrections, and retrospective cancellation filtering can still introduce lookahead. Three-month label maturity also remains an assumption, not a finality guarantee.
- Report any 2020/2022 turning-point improvement as a controlled sensitivity, not proof of vintage-safe performance. Keep cohort IDs, label cutoff and scoring fixed; no further model search is authorized by this research.

### Gaps
- Snapshot dates above are supplied task context, not independently audited transaction files. True realtime claims require origin-dated archives or first-seen/revision histories.
- Optional REB/KB index download was not pursued further: the three-source cap was used for timing and revision evidence. No index file was downloaded.
