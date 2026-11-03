# Three-city history collection — 2026-10-22
1. Add isolated resumable collector for Busan, Daegu, Daejeon, 200601–202609; preserve master and existing raw.
2. Test success/error XML parsing, page completeness, and quota handling before live requests.
3. Persist every page and request counter before request; mark month complete only when stored rows equal totalCount.
4. Pilot live requests, then start hidden background process with status/log files. Stop on quota/auth error; never log request URLs or secrets.
5. Audit downloaded month totals before integration; historical Gunwi codes remain separate until identity review.
