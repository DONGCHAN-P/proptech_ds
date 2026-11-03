# Investment King local alpha Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. User explicitly selected direct implementation from the supplied documents.

**Goal:** Deliver a playable local MOCK alpha of 나는야 투자왕 with an independently tested 80-quarter TypeScript simulator.

**Architecture:** Pure TypeScript engine, Node HTTP API authoritative over file saves, browser UI. No external accounts, paid APIs, publication, or changes to the existing property service. This first alpha prioritizes the README Day-1 scope; broader production PRD remains tracked as pending.

**Tech Stack:** Node 24 native TypeScript, node:test, bigint KRW and fixed-point quantities, HTML/CSS/JS. Next.js and PostgreSQL remain production integration work; native Node removes installation dependencies for this local alpha.

**Spec:** investment-king/docs/{README_START_HERE.md,PRD_v1.0.md,GAME_SYSTEM_SPEC_v1.0.md,BALANCE_CONFIG_v1.0.json}

## Global Constraints

- 2006Q4 through 2026Q3, exactly 80 commits, ending 2026-10-01.
- Starting cash 1,000,000 KRW, age 20, AP 3, initial stats and action values from supplied config.
- Fixture prices must carry MOCK labels. BTC remains RESEARCH_REQUIRED, no inferred first trading date.
- Integer currency, balanced ledger, arrears instead of negative cash, deterministic personal RNG independent of market.
- Public projections exclude future executions and future news; duplicate commits cannot settle twice.

## Review Focus

- Reused idempotency keys with a different payload must conflict, including after restart.
- Multiple orders and action costs must share cash reservations, without overspending.
- Missing prices or volume must not fill; unavailable holding valuations must not silently become zero.
- Malformed quantities, unknown actions, stale hashes and turns must fail without state mutation.
- API writes require same-origin requests and local-only binding; serialized concurrent requests cannot lose updates.

### Task 1: Pure simulator

**Files:** investment-king/src/core/{engine,market}.ts, investment-king/tests/engine.test.ts

**Interfaces:** createRun(seed, runId), simulate(state, request, dataset), project(state, dataset), hashState(state), QUARTERS.

- [ ] Write behavioral tests for exact quarter boundaries, AP/costs, ledger, orders/fees, availability, no future data, same-seed hashes, arrears and scoring.
- [ ] Run node --test tests/engine.test.ts; observe missing implementation failure.
- [ ] Implement deterministic state transitions using original config; label supplemental salaries, fees, market and event content as alpha hypotheses.
- [ ] Re-run the engine tests and complete an 80-turn replay.

### Task 2: Durable local API

**Files:** investment-king/src/{store,server}.ts, investment-king/tests/server.test.ts

**Interfaces:** createApp(saveDirectory) returns http.Server; run creation/read/preview/commit/history endpoints.

- [ ] Write integration tests using real HTTP and temporary saves: creation, stale state, duplicate/reused keys, restart, concurrent commits, future projection, rejected request rollback.
- [ ] Run tests; observe missing implementation failure.
- [ ] Implement bounded JSON input, validation, atomic save replacement and per-run serialization; keep hidden dataset server-side.
- [ ] Re-run full test suite.

### Task 3: Playable UI and simulation report

**Files:** investment-king/public/{index.html,style.css,app.js}, scripts/bots.ts, README.md, docs/IMPLEMENTATION_STATUS.md

**Interfaces:** UI uses API only; never calculates authoritative balances or stores server state in localStorage. Browser persists only opaque run identifiers.

- [ ] Connect onboarding, actions, order reservation, ledger/quarter results, charts, memories, ending and previous-run comparison.
- [ ] Preserve pending commit identity for safe retry after ambiguous network failure.
- [ ] Test full API suite and 1,000 fixed-seed balanced-policy runs; record explicit limits (not 7-policy production balancing).
- [ ] Review the whole implementation and test user-facing flow. Record any visual QA limits accurately.

## Rulings and progress

- User approved separate investment-king directory and immediate implementation of the documents with MOCK data and local web play.
- Files in the existing repository are heavily modified by other work. All implementation is confined to a new project directory; no existing service edits or automatic commits.
- Actual historical ETL, market licensing, property purchase/mortgages, deposit contracts, 40-event production content, official rankings, authentication, and cloud publication are follow-up production work, not claims for this alpha.

## Completion record

- Task 1 complete: engine tests first failed for missing engine, then passed; expanded coverage also caught pre-listing metadata visibility and now passes.
- Task 2 complete: HTTP tests first failed for missing server, then passed; independently reproduced prototype-key receipt loss, regression failed then passed after own-property persistence.
- Task 3 complete: responsive playable UI, same-request retry preservation, shareable SVG, ending comparison, 1,000 fixed-seed policy report, and implementation status delivered. Browser race regression failed on both viewports before lock/snapshot correction, then passed.
- Final evidence: 15 engine/API tests, strict TypeScript check, JS syntax check, 4 actual Chrome desktop/mobile browser tests. 1,000/1,000 balanced-policy bots completed with zero ending arrears. Independent whole-project review and follow-up found no remaining important regression in the scoped alpha.
- UI screenshots directly inspected on desktop/mobile. Actual historical datasets and broader P0 features remain pending as documented; no beta/public-MVP completion claim.
- Local server runs at http://127.0.0.1:3210; source docs SHA256 checked against original downloads.
