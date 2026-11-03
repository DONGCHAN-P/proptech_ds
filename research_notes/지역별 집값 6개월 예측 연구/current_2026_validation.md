# Four 2026 Korea apartment policy announcement signals

Validation date: 2026-10-27, Asia/Seoul. Scope: only the four `current_2026_events` records in `policy_events.json`. The new JSON is a four-item list with exactly the six requested projection keys; per-record justifications follow here. The historical 24-event experiment and `policy_regional.md` remain frozen.

## Which dated signals can be retained?

### Takeaway

Retain all four as dated regulatory-tightening announcement signals (`direction = +1`), representing two packages. No price-effect sign, magnitude or current-law persistence is encoded. Dates below are the publication dates and commencement dates stated in the releases, rather than proof of unchanged rules on 2026-10-27. [April FSC release](https://www.fsc.go.kr/no010101/86606); [June FSC release](https://www.fsc.go.kr/no010101/87222).

### Cited Findings

- `KR_20260401_ONLINE_INVESTMENT_LINKED_LENDING_RULES`: published **2026-04-01**, stated start **2026-04-02**. Section II(4) extends mandatory mortgage constraints to online investment-linked lenders. `00` is safe for a nationwide lender-class announcement pulse; it does not mean every borrower or loan faces the same limit. This extension supports `+1`. [FSC, section II(4) and III](https://www.fsc.go.kr/no010101/86606).
- `KR_20260401_MULTIPLE_HOME_OWNER_RENEWAL_RESTRICTION`: published **2026-04-01**, stated start **2026-04-17**. Section II(2) restricts apartment-backed mortgage renewals for multiple-home owners and rental businesses in the capital region or regulated areas. Retain the complete capital-region subset **Seoul `11`, Incheon `28`, Gyeonggi `41`**. Tenant and other exceptions prevent a universal repayment interpretation. Restricting renewal supports `+1`. [FSC, section II(2)](https://www.fsc.go.kr/no010101/86606).
- `KR_20260630_THREE_DISTRICT_DESIGNATION`: published **2026-06-30**, stated effectiveness **2026-07-01**. FSC explicitly identifies **Hwaseong Dongtan-gu `41597`, Yongin Giheung-gu `41463`, Guri-si `41310`** as newly designated speculative-overheated and adjustment-target areas. The three named district/city scopes support `+1`; do not widen them to all Gyeonggi, Hwaseong or Yongin. The projection cites the successfully read FSC corroboration. [FSC, sections I–II](https://www.fsc.go.kr/no010101/87222).
- `KR_20260630_THREE_DISTRICT_LTV40`: same publication, start date and three prefixes. The release states standard LTV tightening from 70% to 40%, supporting `+1`. First-home/policy-mortgage exceptions and pre-effective-date contracts or applications remain outside the generic pulse. This is the same designation package. [FSC, section II](https://www.fsc.go.kr/no010101/87222).
- The government confirms Dongtan-gu's **`41597`** code following the **2026-02-01** reorganization. Never substitute predecessor **`41590`**, or apply Dongtan's code retrospectively to all historical Hwaseong. [Government 110, dated 2026-03-31](https://www.110.go.kr/data/counselView.do?curPage=1&num=A01_720927).

### Inferences

- Geographic projection is deliberately a verified subset. `00` matches nationwide lender-class exposure only within the requested forecast scope: **11, 26, 27, 28, 29, 30, 31, 36, 41, 43, 44**. Other rows retain their narrower prefixes. This encoding is an analytical choice, not borrower-level eligibility evidence.
- Preserve canonical Gwangju `29`; do not extrapolate `29` to other provinces or match upstream statistical `12...` codes without a verified crosswalk. Missing regional entries mean unverified coverage, not proven absence of regulation.
- Gate by announcement availability at each forecast origin; absent a verified release time, date-only daily models should activate the following day. Do not backdate the pulse to a package rumor or treat effectiveness as a second independent announcement. Cluster the June pair as one package; the April pair also shares one package.
- Keep actual dates: for a strict six-month lookback from 2026-10-27, June announcements qualify; April 1 announcements fall outside that window. Do not refresh April dates or manufacture future six-month pulses. Keep this separate from the frozen historical training input.

### Gaps

- The referenced [MOLIT announcement](https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95092167) repeatedly returned a redirect loop; direct independent inspection of its text or designation notification was unavailable. June inclusion rests on the directly read, same-day FSC primary release, which explicitly names the designations, geography and effective date. No independent MOLIT legal-notification audit is claimed.
- **Explicitly excluded:** partial-dong/parcel overlays and land-transaction-permission boundaries; price-conditioned April lending-cap tiers and June jeonse restrictions as standalone generic rows; individual borrower exceptions and transition-rule assignments; regulated locations outside the renewal row's verified capital-region subset. No excluded condition is expanded into a whole district/province.
- Later amendments, withdrawals, continued enforcement and the exhaustive legal regime as of 2026-10-27 were not investigated. Retained rows certify dated announcements only. This bounded round ends with these two files; no paid tools or external raw-data uploads were used.
