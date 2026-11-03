# Korean apartment six-month forecasts: policy and regional features

Research cutoff: **2026-10-27 (Asia/Seoul)**. Scope: primary official policy announcements, geographic applicability, regional interactions and an empirical feature-ablation plan. No methods-paper review, macro-series download, paid generation or external upload was performed.

**Historical coverage ends with the 2025-10-15 announcement**, including its separately dated October 16 and October 29 financial measures. **The current 2026 policy regime is not verified for this handoff**: do not infer that the October 2025 rules remained unchanged, or add unverified 2026 developments to model inputs. No additional browsing was undertaken to finalize this note.

The coordinator reports 8,353,538 valid transactions, 141 district series and 11 province/metropolitan reporting scopes: `11,26,27,28,29,30,31,36,41,43,44`. These are supplied project facts, not independently audited here. The supplied Gwangju district-name crosswalk to stable reporting city `29` is accepted without re-audit.

**Frozen first-experiment artifact:** `policy_events.json`, schema 1.0.0, registry `KR_APARTMENT_POLICY_REGIONAL_PARTIAL_20261027`. SHA-256: `E458E7108B34D33D76A80EC6C3719C2493BD7CFBDEC21D5C51EC6C72F32DE016`. It contains **24 generic-eligible historical records**, **4 separately held 2026 records**, and **8 restricted-geography, schedule or infrastructure records**. The JSON was not changed after the first-deliverable freeze.

## 1. Which historical policy events can be encoded without future policy information?

### Takeaway

Use the frozen registry as a **partial collection of dated policy signals**, not a complete legal regime calculator. Separate public information dates, commencement dates, borrower/property conditions and geographic masks; a tightening/easing label never states a causal price effect.

### Cited Findings

The following are verified official event families. Dates in the “record release” column sometimes deliberately use a later detailed bulletin; earlier package dates remain in `package_announcement_date`. This avoids silently backdating information that was only checked in the later bulletin.

| Event family | Record release / earlier package | Commencement | Geographic encoding and qualification | Official evidence |
|---|---|---|---|---|
| 2017 speculative-overheated designation | 2017-08-02 | 2017-08-03 | `11,41290`: Seoul and Gwacheon. Sejong's planned-city area is a partial-area designation and is excluded from the simple-prefix row. | [MOLIT designation notice](https://police.molit.go.kr/USR/I0204/m_14993/dtl.jsp?idx=15117&lcmspage=325&psize=10); [government announcement](https://m.korea.kr/news/policyNewsView.do?newsId=148840552) |
| 2017 LTV/DTI amendment | 2017-08-23 bulletin; package 08-02 | 2017-08-23 | Verified Seoul/Gwacheon subset; standard LTV and DTI 40%, with eligible end-user relief and transitional exceptions. | [FSC amendment](https://fsc.go.kr/no010101/72791) |
| 2018 mortgage eligibility restrictions | 2018-09-14 detailed release; package 09-13 | 2018-09-14 | Seoul subset of covered regulated areas. Multiple-home owners face purchase-mortgage restrictions; relocation exceptions matter for single-home owners. The separately planned jeonse-guarantee change is not assigned the same start date. | [FSC detailed release](https://www.fsc.go.kr/eng/pr010101/22189); [FSC September 14 implementation FAQ](https://www.fsc.go.kr/no010101/73313?curPage=413&srchBeginDt=&srchCtgry=&srchEndDt=&srchKey=&srchText=) |
| 2019 high-price mortgage rules | 2019-12-16 ban announcement; 12-23 implementation bulletin for tiers | Ban 12-17; tiered LTV 12-23 | Seoul subset of speculative/overheated areas. Apartment value above KRW1.5bn triggers the purchase-mortgage ban; tiered LTV uses 40% up to KRW900m and 20% on the marginal value above it. | [official December 16 Q&A](https://www.korea.kr/briefing/policyBriefingView.do?newsId=148867548); [FSC implementation](https://www.fsc.go.kr/no010101/74057?curPage=339&srchBeginDt=&srchCtgry=&srchEndDt=&srchKey=&srchText=) |
| 2020 occupancy/disposal conditions | 2020-06-30 detailed bulletin; package 06-17 | 2020-07-01 | Seoul subset of regulated areas: six-month move-in and conditional disposal requirements. The June 19 designation date is a different clock. | [FSC June 30 bulletin](https://www.fsc.go.kr/no010101/74417); [MOLIT June 17 Q&A](https://www.korea.kr/news/policyNewsView.do?newsId=148873507) |
| Gwangju adjustment-target designation | 2020-12-17 | 2020-12-18 | `29`: all five districts explicitly listed, including Gwangsan. Other cities in the package are not exhaustively encoded. | [MOLIT release](https://www.korea.kr/news/policyNewsView.do?newsId=148881292) |
| Borrower DSR phase 1 | 2021-05-17 clarification; package 04-29 | 2021-07-01 | Seoul subset: covered mortgages on homes above KRW600m. This row does not claim exhaustive mapping of all regulated districts or unsecured credit rules. | [FSC clarification](https://www.fsc.go.kr/no010102/75917?curPage=5&srchBeginDt=&srchCtgry=&srchEndDt=&srchKey=&srchText=); [official April announcement](https://www.korea.kr/briefing/policyBriefingView.do?newsId=148886836) |
| DSR acceleration / phases 2 and 3 | 2021-10-26 | 2022-01-01 and 2022-07-01 | National conditional coverage, total borrowing above KRW200m and KRW100m respectively; bank/nonbank borrower ceilings 40%/50%. Exempt loans and transitional arrangements matter. | [FSC October 26 plan](https://www.fsc.go.kr/no010101/76740); [FSC FAQ](https://www.fsc.go.kr/po020201/76750) |
| Provincial adjustment-target releases | 2022-09-21 | 2022-09-26 | Verified complete-city subset `29,30` for Gwangju/Daejeon. This is not a complete provincial release list. | [official September release](https://www.korea.kr/briefing/policyBriefingView.do?newsId=148906145) |
| Further adjustment-target releases | 2022-11-10 | 2022-11-14 | `28,36`: Incheon/Sejong release event. It does not prove that every tract had previously been designated. | [MOLIT November release](https://www.korea.kr/news/policyNewsView.do?newsId=148908107) |
| LTV/high-price normalization | 2022-11-10 dated schedule; package 10-27 | 2022-12-01 | Remaining regulated Seoul/Gyeonggi scope: eligible borrowers' standard LTV 50%, high-price apartment purchase mortgages permitted. DSR continues to constrain borrowing. | [FSC dated schedule](https://www.fsc.go.kr/no010101/78887); [official implementation summary](https://whatsnew.moef.go.kr/mec/ots/dif/view.do?comBaseCd=DIFGODEPRT&difGovDepart1=DIFGODR046&difSer=916747f4-8f97-4516-9b57-03f51d024027&temp=2023&temp2=HALF001) |
| Remaining-area designation release | 2023-01-03 | 2023-01-05 | Seoul's 21 districts excluding Gangnam/Seocho/Songpa/Yongsan, plus Gwacheon, Gwangmyeong, Hanam, Seongnam Sujeong/Bundang. Seongnam Jungwon is not inserted into this January release. | [ministerial briefing](https://www.korea.kr/briefing/policyBriefingView.do?newsId=156546653); [MOLIT notice 2023-1](https://www.molit.go.kr/USR/I0204/m_45/dtl.jsp?idx=17700&lcmspage=1&psize=10); [MOLIT notice 2023-2](https://www.molit.go.kr/USR/I0204/m_45/dtl.jsp?idx=17701&lcmspage=1&psize=10) |
| Stress DSR phase 1 | 2024-02-26 detailed bulletin; initial framework 2023-12-27 | 2024-02-26 | National eligible bank mortgages, calculation add-on 0.38 percentage points. This is not an increase charged on the mortgage interest rate. | [FSC implementation](https://www.fsc.go.kr/po010101/81777) |
| Stress DSR phase 2 and capital-region differential | 2024-08-20 | 2024-09-01 | National scope expansion; standard add-on 0.75pp, capital-region bank mortgages 1.2pp. The June 25 postponement must be honored. | [FSC August announcement](https://www.fsc.go.kr/no010101/82917); [FSC postponement](https://www.fsc.go.kr/no010101/82526?srchKey=sj&srchText=%EC%8A%A4%ED%8A%B8%EB%A0%88%EC%8A%A4+DSR) |
| Stress DSR phase 3 | 2025-05-20 | 2025-07-01 | All sectors' DSR-covered household loan types; standard 1.5pp, noncapital mortgages 0.75pp as then scheduled through December. Eligible credit-loan balances must exceed KRW100m. | [FSC phase 3 plan](https://www.fsc.go.kr/no010101/84617) |
| Capital-region mortgage bundle and jeonse guarantee | 2025-06-27 | Mortgage bundle 06-28; guarantee 07-21 | Capital subset `11,28,41`: KRW600m purchase-mortgage cap, 30-year maturity, move-in/first-buyer conditions; a separate row changes guarantee coverage from 90% to 80%. Clause-specific exceptions apply. | [FSC June package](https://www.fsc.go.kr/no010101/84824) |
| Regulated LTV tightening | 2025-09-07 | 2025-09-08 | Then-regulated Gangnam/Seocho/Songpa/Yongsan: eligible standard LTV 50% to 40%. | [FSC September package](https://www.fsc.go.kr/no010101/85253) |
| Price-tier loan caps, stress floor and jeonse DSR | 2025-10-15 | Caps/stress 10-16; jeonse DSR 10-29 | Capital subset: caps KRW600m/400m/200m by value tier; mortgage stress floor 3pp; one-home owners' covered jeonse-loan interest enters DSR. | [FSC October package](https://www.fsc.go.kr/no010101/85432?curPage=67&srchBeginDt=&srchCtgry=&srchEndDt=&srchKey=&srchText=) |

The October 2025 designation **names** are verified: retained four Seoul districts, 21 newly designated Seoul districts and 12 Gyeonggi districts. The JSON holds that announcement separately because the commencement gazette was not independently inspected in this task; a guessed date is not supplied to the generic loader. The named Gyeonggi coverage is Gwacheon, Gwangmyeong, Seongnam Bundang/Sujeong/Jungwon, Suwon Yeongtong/Jangan/Paldal, Anyang Dongan, Yongin Suji, Uiwang and Hanam. [Joint-government release](https://www.korea.kr/news/policyNewsView.do?newsId=148950973)

Transaction restrictions need finer masks than province or district prefixes. Seoul's 2021 redevelopment land-permit notice specifies project areas and an April 27 start, not entire Gangnam/Yeongdeungpo/Yangcheon/Seongdong districts. The February 13, 2025 release also retains named redevelopment complexes. Both are therefore excluded from flat-prefix input. [Seoul 2021 notice](https://news.seoul.go.kr/citybuild/archives/512421); [Seoul February 2025 gazette](https://event.seoul.go.kr/snews/data/CN_MST/seoulsibo_20250213092648_24250.pdf)

#### 2026 current-policy verification gap

The current policy state as of October 27, 2026, including subsequent amendments, legal commencement, transitional provisions and complete geographic coverage, **has not been verified as a current regime**. The immutable JSON contains a separate `current_2026_events` array from earlier source gathering; its presence does not make 2026 part of the 24-event historical experiment. Do not merge that array into the experiment or describe it as an exhaustive current rulebook.

Previously gathered primary links are retained only as separate source references: [FSC April release](https://www.fsc.go.kr/no010101/86606), [MOLIT June release](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95092167), [FSC June release](https://www.fsc.go.kr/no010101/87222?curPage=17&srchBeginDt=&srchCtgry=&srchEndDt=%0A&srchKey=&srchText=). Individual release evidence does not establish that a rule remained current at the research cutoff. This handoff makes no additional 2026 development claims.

### Inferences

**Generic-schema handoff.** Read the top-level `events` array and project each record to:

```text
announcement_date, effective_date, affected_prefixes,
direction, event_id, source_url
```

All 24 default rows have non-null dates, valid direction values and string prefixes. `00` is a special nationwide selector, not a literal geographic prefix. Other arrays must not be concatenated automatically. The six-field projection is compatible with the implemented input; retaining `type`, applicability and package metadata is preferable for interpretation.

**Direction is regulatory, not predictive.** `+1` means tightening/expanded restrictions, `-1` easing/release, and `0` neutral information. Do not impose an expected price sign or a fixed basis-point price effect. The registry is intended for an empirical ablation.

**Two clocks and an information gate.**

- For origin cutoff T, an event is usable only when its public information date is no later than T. The default rows set `information_available_from = announcement_date`.
- An announced but not yet effective policy can create a “known pending change” feature. A current-rule feature additionally requires commencement by T. These are separate variables.
- At a daily cutoff, use next-day activation when release time is unknown; a date alone cannot establish morning availability. Monthly forecasts should still record their actual run cutoff.
- A later implementation bulletin can be used conservatively from its own release. Do not reset its availability to the earlier package date merely because the two records concern the same measure.
- Do not inspect the future six-month outcome window and insert policy changes that had not been announced at T. Unknown future policy remains unknown.
- Do not infer a complete active LTV/DSR/legal regime by cumulatively summing this partial registry. Missing reversals, baseline rules and exceptions make that invalid.

The source publication dates are historical availability proxies, not authenticated crawler first-seen timestamps. Together with the coordinator's estimated first-seen histories, the resulting historical evaluation is **pseudo real time**, not a reconstructed archival real-time experiment.

**Expected infrastructure versus realization.** Keep project, stage, announcement date, originally expected timing, station/corridor mask and subsequent revisions as separate records. The 2023 briefing announced a broad GTX-A expectation; the March 29, 2024 notice provided a March 30 first-service schedule; the 2025 account later confirmed earlier operation. A 2023 model may use the expectation but cannot receive the later actual date, ridership, realized travel times or final station-access configuration. [2023 expectation](https://www.korea.kr/briefing/policyBriefingView.do?newsId=156546653); [March 2024 notice](https://www.molit.go.kr/USR/NEWS/m_72/dtl.jsp?id=95089607); [later official account](https://www.molit.go.kr/USR/BORD0201/m_37060/DTL.jsp?idx=263677&mode=view)

### Gaps

- This is not an exhaustive 2017–2025 register. Early-2017 baselines, intermediate designations/releases, tax amendments, policy mortgages, many transaction rules and detailed borrower exceptions remain incomplete.
- Sejong planned-city boundaries, Dongtan2, exempt eup/myeon and project/parcel restrictions cannot safely be represented as whole-district binaries.
- Historical source pages can be revised, and some MOLIT links redirected in the browser. Official indexed notice text and direct government releases were used where retrievable; an uninspected attachment is not represented as fully checked.
- The held October 2025 designation and land-permit records require further legal/mask validation before promotion to generic active-rule features. They do not block the frozen first experiment.
- Current 2026 policy status and completeness remain an explicit verification gap. The historical experiment ends with the October 2025 announcement family; no unverified 2026 rule or future realized policy is an input.

## 2. Which regional interactions are worth testing, and what availability rules do they require?

### Takeaway

Start with a small set of interpretable exposure interactions: credit constraints, household/young-adult movement, employment structure, supply pressure and jeonse conditions. These are candidate predictors, with no assumed causal or price-direction interpretation.

### Cited Findings

| Official evidence | Verified implication for feature design |
|---|---|
| [FSC 2019 price-tier rules](https://www.fsc.go.kr/no010101/74057?curPage=339&srchBeginDt=&srchCtgry=&srchEndDt=&srchKey=&srchText=) and [2025 loan-cap tiers](https://www.fsc.go.kr/no010101/85432?curPage=67&srchBeginDt=&srchCtgry=&srchEndDt=&srchKey=&srchText=) | Price thresholds and absolute caps differ; a single region's mean price is not the fraction of households or collateral actually constrained. |
| [FSC 2024 capital-region differential](https://www.fsc.go.kr/no010101/82917) and [2025 phase 3](https://www.fsc.go.kr/no010101/84617) | Region, lender sector, loan type and balance conditions affect policy coverage. A uniform national tightening dummy loses these distinctions. |
| [BOK Daejeon household-debt release, 2025-08-07](https://www.bok.or.kr/portal/bbs/P0000800/view.do?menuNo=201505&nttId=10092938) | BOK publishes regional debt analysis separating loan/lender categories. This supports checking sector exposure; it does not establish a public monthly borrower-level panel for all 141 districts. |
| [MOIS household-size statistics](https://jumin.mois.go.kr/etcStatHouseholds.do) and [population/household portal](https://jumin.mois.go.kr/) | The portal provides household/person measures and distinguishes its reference date from publication. Registered population excludes foreign nationals; registered households are not automatically census households. |
| [KOSIS domestic migration metadata](https://kosis.kr/serviceInfo/newContrainDataDetail.do?boardIdx=1976003&boardOrgId=101) | Monthly age-specific district net migration is a listed statistical product; reference periods and update dates are distinct. A table's current update date is not its historical first publication timestamp. |
| [Regional Employment Survey metadata](https://sri.kostat.go.kr/boardDownload.es?bid=12030&list_no=428812&seq=1) | Survey reference months are April/October, with major district employment releases later, including August/following February. It is not a contemporaneous monthly employment observation. |
| [MOLIT housing permits](https://stat.molit.go.kr/portal/cate/viewChk.do?hFormId=1948&hRsId=31), [completion statistics](https://stat.molit.go.kr/portal/cate/viewChk.do?hFormId=5373&hRsId=468), [permit API clarification](https://stat.molit.go.kr/portal/board/detailCenter.do?num=172) | Permits, starts and completions are different stages. Permit tables/API may be year-to-date totals; completion observations can be provisional and revised later. |
| [REB survey description](https://www.reb.or.kr/reb/cm/cntnts/cntntsView.do?cntntsId=1033&mi=10333&statId=S234820263), [REB release schedule](https://www.reb.or.kr/reb/ad/bs/beffatinfosport/view/selectBeffatinfoList.do?mi=9624) | REB supplies sale/jeonse price measures and publication schedules. Survey sample prices combine transaction and other market information; they are not identical to the project's transaction panel. |
| [REB ratio metadata](https://www.reb.or.kr/r-one/openapi/SttsApiTbl.do?STATBL_ID=A_2024_00073&Type=json), [REB interpretation notes](https://www.reb.or.kr/r-one/portal/stat/multiStatPage.do) | Published sample-level jeonse/sale ratios, ratios of regional medians, and ratios of indices are different objects. Sample and weighting changes also affect interpretation. |

### Inferences

The following is a proposed compact feature set, not a finding that these predictors improve forecasting.

| Channel | Candidate as-of-T feature | Candidate policy interaction | Main limitation / safe fallback |
|---|---|---|---|
| Credit exposure | Trailing share of observable apartment transactions above relevant thresholds; last-published province loan composition where available | Tightening pulse × prior high-price share; bank/nonbank stress-rule exposure × lagged sector share | Transaction-value exposure is a proxy, not borrower DSR/LTV eligibility. Do not label province exposure as observed district borrower debt. |
| Jobs | Last-published employment rate/working-age employment and broad industry composition; retain publication age | Local employment conditions × credit restrictions or planned accessibility | Resident employment and workplace jobs differ. Do not call a household-survey employment count “jobs located in the district.” Workplace job counts need their own verified source and vintage. |
| Households | Last available household growth, one-/two-person household shares and young-adult population | Household formation pressure × stock/supply; household structure × mortgage eligibility | Changes in registered households do not equal housing purchases or census household formation. |
| Young migration | Trailing 12-month net migration for predeclared age bands, such as 20–39; scale by last-known age-band population | Young net inflow × household growth, job structure and price affordability | Use one fixed age definition; a migration reason or annual age table may be released much later than the observation period. |
| Supply / stock | Trailing permits, starts and completions separately; unsold/completed-unsold inventory only after release; scale by last-published apartment stock | Supply pipeline × household growth; completed stock × jeonse pressure | Permits are not guaranteed completions. Unknown stock vintages should stay missing rather than use future census totals. |
| Jeonse | Lagged jeonse change, an explicitly defined level ratio where available, and coverage/missingness flags | Jeonse conditions × occupancy/disposal, guarantee or jeonse-DSR rules | Sales/jeonse sample definitions must align. A ratio of indices is not a deposit-to-market-value ratio. |
| Infrastructure | Latest announced project stage, uncertainty flag, announced expected opening interval and predeclared station/corridor exposure | Accessibility expectation × employment/young migration | Never substitute final realized station service, ridership or travel-time savings into earlier origins. |

**Geographic aggregation accepted for this handoff:** province policy exposure is built from district exposure using **past-volume weights**, as corrected upstream. Use only transaction volumes available by T, over a prespecified trailing window; do not use target-window trading volume or full-sample weights. If a parent prefix covers every valid constituent district, exposure should be one where the denominator is observed. Partial known masks should produce partial exposure, not a blanket province indicator. Keep unverified policy coverage distinct from verified absence.

District feature assignment and province aggregation must remain separate. A parent selector such as `11` matches canonical Seoul districts; a district selector such as `11680` identifies only Gangnam. Apply nationwide `00` once, even when multiple selectors match. Aggregate overlapping selectors by union, not by summing duplicated coverage.

The supplied Gwangju remapping is accepted: upstream raw `12210/12240/12270/12300/12330` is joined through its verified district-name crosswalk into stable reporting city `29`. Those raw statistical identifiers must not be prefix-matched to the legal-code selectors in the event registry. No additional source-crosswalk re-audit is required for this handoff.

For the feature store, retain `reference_period, publication_date, first_seen_estimate, vintage/revision_date, geography_version, source_url` and an estimated-availability flag. Forward-fill only from a value's availability date. Never interpolate semiannual jobs or annual stock using a future observation. Normalize and impute using training history only; also expose data staleness.

For cumulative permit tables, derive monthly changes within the same year's cumulative series and handle January as a reset, subject to that table's definitions and revisions. Preserve separate apartment/all-housing units and counts; no series were downloaded in this task.

### Gaps

- Public province-level lending aggregates do not establish observed credit constraints for individual buyers or every district. Exact lender/borrower residence/collateral geography and historical releases need metadata confirmation by the upstream data owner.
- Workplace employment, age-band population denominators, apartment stock vintages and district unsold inventory are feature candidates, not newly collected or comprehensively validated data here.
- No new station catchment or parcel/project map was built. Infrastructure and partial land-permit records remain excluded from the flat first experiment.
- Current portal values may incorporate revisions. Estimated historical publication/first-seen dates limit all availability-sensitive interpretations.

## 3. How should incremental prediction be tested against prices alone?

### Takeaway

Use the same time-ordered evaluation and model capacity for prices-only, regional, policy and interaction variants. Report any improvement as **incremental predictive performance in a pseudo-real-time backtest**, with policy packages and overlapping six-month labels treated as shared information.

### Cited Findings

Policy selection is endogenous. MOLIT's December 2020 release explicitly describes price increases and quantitative market conditions as reasons for designation; its September/November 2022 releases discuss declining prices and market conditions when explaining releases. Policy dummies therefore partly encode earlier market states and policy reactions. [2020 designation explanation](https://www.korea.kr/news/policyNewsView.do?newsId=148881292); [September 2022 explanation](https://www.korea.kr/briefing/policyBriefingView.do?newsId=148906145); [November 2022 explanation](https://www.korea.kr/news/policyNewsView.do?newsId=148908107)

The January 2023 ministerial briefing describes designation decisions as a broader judgment and distinguishes regulatory normalization from an immediate, simple price/transaction response. This is direct official evidence against interpreting an announcement indicator as a clean isolated treatment. [Ministerial briefing](https://www.korea.kr/briefing/policyBriefingView.do?newsId=156546653)

Contract grandfathering, different implementation clocks and lender/borrower conditions appear directly in the FSC documents. A geographic event date is not equivalent to every local loan becoming newly constrained on that date. [FSC DSR FAQ](https://www.fsc.go.kr/po020201/76750); [FSC 2024 phase 2 details](https://www.fsc.go.kr/no010101/82931); [FSC June 2025 transition provisions](https://www.fsc.go.kr/no010101/84824)

### Inferences

Recommended first-experiment protocol:

1. **Freeze inputs and target.** Use the frozen JSON hash above and one transaction-panel version for every arm. Define a six-month target consistently, for example district log-price change from origin T to T+6 months. Use the same valid origins, label construction, property composition treatment and missing-label exclusions. The large transaction count is not the number of independent policy experiments.
2. **Prices-only baseline P.** Include prespecified own-price histories/returns, simple calendar effects and the same district treatment across models. Compare against a no-change forecast as a basic reference. Fit all transformations on the training segment.
3. **Regional block R.** Add the small as-of household, migration, jobs, supply and jeonse set only where available. A price-plus-transaction-volume control arm is useful to distinguish policy contribution from trading-activity information.
4. **Policy block E.** Add separate tightening/easing announcement pulses over a small fixed set of trailing windows, such as 1/3/6 months, split by type when sample size permits. A known-pending-effective feature must use only announcements available by T. Do not infer persistent legal state from this incomplete register.
5. **Interaction block X.** Add only a few prespecified interactions: policy × trailing price-threshold exposure, policy × lagged lender-sector exposure where supported, and supply × household/jeonse pressure. Avoid a large district × event dummy expansion for a small number of packages.
6. **Ablation matrix.** Run P; P+R; P+E; P+R+E; P+R+E+X with the same estimator and tuning budget. The comparison P+R+E versus P+R tests policy beyond regional context; P+E versus P tests policy beyond price history. Report both, including failures.
7. **Rolling origins and mature labels.** No random row split. At each forecast cutoff, training labels must have fully matured and been available by that cutoff. Purge training examples whose six-month label intervals overlap the test interval. Apply the same availability logic inside tuning; do not tune on the final held-out dates.
8. **Evaluate common and broad samples separately.** Use a fixed common-row sample for the main ablation, then a separate broader prices-only coverage report. An arm must not appear better merely because expensive regions or hard months disappeared after feature joins.
9. **Report useful metrics and dependence.** Primary: six-month return MAE, equally weighted across districts and origins. Secondary: RMSE, directional accuracy and origin-available-volume-weighted results. Show province and policy-regime breakdowns. Estimate uncertainty by resampling origin-month blocks with six-month dependence in mind, rather than treating transaction rows or all districts as independent replicates.
10. **Stress the partial register.** Compare national rows only, verified city/district subsets only, and exclusion of each large policy package in turn. Same-package submeasures must be grouped. With few packages, large apparent gains concentrated in one episode are weak evidence of general predictive value.
11. **Availability sensitivity.** Compare the recorded availability proxy with additional conservative delays, and separately evaluate a recent period with observed collection timestamps if available. This measures sensitivity to uncertain historical lags; it does not convert the experiment into true archival real time.
12. **Use zero-leakage assertions.** Check every row's information date against T; reject future unannounced policies and future realizations; reject post-T household/stock/job vintages, future exposure weights and retrospective infrastructure confirmations. Confirm that restricted/pending arrays and `current_2026_events` are absent from a 2017–2025-only input.

Important confounders include national credit/interest conditions, employment/industry cycles, supply decisions, infrastructure selection, policy anticipation, neighboring-market substitution, transaction mix and reporting lags. National events also share the same calendar across districts. Control for available price histories and regional conditions; check package robustness and neighboring exposure where a defensible mask exists. Remaining associations are not causal estimates.

Any gain should be described narrowly: “these frozen, available-at-origin features improved held-out six-month prediction under this sample and pseudo-real-time availability reconstruction.” Do not translate a fitted coefficient into a causal percentage price effect, assume a tightening must lower prices, or use a historical event study as proof of out-of-sample gain.

### Gaps

- **No forecasting experiment was run by this researcher.** Predictive benefit, stability and economic usefulness are unresolved and must be established by the coordinator's ablation.
- A partial selected-event registry cannot support a definitive causal policy effect or a complete legal exposure history.
- Estimated first-seen histories, revisions, coarse regional credit proxies and few independent packages constrain interpretation even if forecast errors improve.
- Final handoff is ready: use the immutable JSON snapshot for the first experiment; this note provides interpretation and limitations. No further research or crosswalk audit is a prerequisite for that first run.
