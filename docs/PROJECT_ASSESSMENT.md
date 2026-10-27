# Project assessment
Updated against main 0d9015cc3cba0977cafcb952cbb33a11870e2754. Original assessment: 2026-10-26 (America/New_York). Scope: source review and offline synthetic verification, not an audit of private research data.

## Current verified baseline
- PR #4 is merged: explicit migration-fixture connection closure; Python 3.11 CI on Windows and Ubuntu.
- PR #5 is merged: timestamp-evidence wording depends on the existing full-session predicate; insufficient data says UNVERIFIED.
- PRs #8 and #10 were merged by a maintainer during this sprint: deferred provider error capture and explicit read-only diagnostic handle closure. CI on main after each merge passed Windows/Linux.
- Main contains 31 top-level Python files and 17 tests (five volume-discovery, five timestamp-wording, four provider-callback and three diagnostic-closure). These merged fixes pass Windows/Linux CI.
- Draft PR #1 adds five opening-range tests. Combined with current main, all 22 pass locally; refreshed PR #1 runs the combined set on Windows/Linux CI. Results and readiness are recorded in that PR.
- Draft PR #2 is documentation only. PRs #6/#7/#9 and #11 remain proposals; they are not silently treated as merged functionality.

The initial report's four-pass/one-error migration result and unconditional wording observation were valid before PRs #4/#5. They are historical findings, not current failures. No user database, real provider response, GUI or trading execution has been validated by these fixes.

## Architecture and dependencies
A flat standard-library Python project centers on the ~1,280-line Tkinter dashboard raccoon_dashboard_v1_5_14.py. It owns widgets, worker queues/threads, a separately selected scanner process, CSV imports, analysis calls, database persistence and exports. Older versioned dashboards remain compatibility artifacts, not an established single versioned package.

Data flow:
1. CSV or local OpenD quote history -> raw candle dictionaries -> price_action_engine labels and setup_detective events/outcomes.
2. Fetch success events -> persist_history -> strategy_validation candle upserts. Validation and notes use research_journal.
3. Loaded memory plus explicit mode=ro history query -> market_intelligence session levels, raw-stamp opening ranges and provisional candidates.
4. OpenD daily volume discovery -> current results and appended snapshots -> manually entered swing cases.
5. SEC urllib JSON -> fundamentals snapshots/source-linked notes.
6. Diagnostic tools and export handlers -> JSON/CSV/ZIP outputs.

Offline dependencies are primarily stdlib: Tkinter, sqlite3, datetime/zoneinfo, CSV/JSON/ZIP, urllib, threading/queue, unittest. Quote paths lazily require moomoo SDK and OpenD at localhost:11111 with suitable permissions; recent klines may require subscription. Windows needs Tk and system IANA data or tzdata for real zoneinfo use. No supported SDK version, requirements lock or pyproject is established. CI installs no broker dependencies and does not establish GUI/SDK interoperability.

Implemented research includes session/prior levels, strict raw-stamp 5/15/30-minute ranges, provisional shifted candidates, an OHLC4 volume-weighted proxy, exploratory candle/setup labels, directional close outcomes, chronological/rolling descriptive summaries, daily volume discovery, cases/journal, SEC evidence, CSV input and diagnostics. News/calendar/macro/breadth/flow feeds remain explicitly unavailable. External scanner/bias definitions are not supplied, so those calculations remain unverified.

Four local stores are history, discovery, swing and fundamentals SQLite. "No orders" is not the same as "no database writes": candles/current discovery rows/cases can be overwritten, and several read/export helpers initialize schemas.

## Timestamp and ingestion evidence
Raw timestamps remain the source record. Market Intelligence requires exact 09:30-start minute coverage for raw ranges and derives raw-minus-one-minute candidates in memory only. Its existing predicate requires 390 unique consecutive stamps from 09:31 to 16:00. This supports an end-label hypothesis; it does not prove Moomoo semantics or exchange-calendar completeness. Positive wording retains "not independently verified"; candidates remain provisional.

Both ordinary fetch workers explicitly exclude 16:00. Single-day also rejects today's stamps >= now rounded to the minute; range does not apply that per-candle cutoff. **Correction to the initial assessment:** the public fetch_range handler rejects end >= today ET before dispatch. The normal range UI already requires completed past dates. Direct/internal worker callers lack that defensive boundary; this is not evidence that the UI currently persists today's unfinished bars.

PR #11 adds fake-provider/clock characterization: exact session/time boundaries, the public date guard, missing minutes, duplicates, discarded pagination keys, partial symbol/day results and numeric-only ingestion validation. It changes no runtime logic. Tests record current behavior, including undesirable behavior; they do not endorse it or assume interval-end labeling.

Provider inspection tools compare raw historical/recent endpoints, selected opening OHLCV, timestamps, counts and bounded pagination. Their saved reports do not preserve all returned OHLCV/settings/versions, despite a "full OHLCV" UI phrase. Seconds-only filenames can collide, and repeated keys/incomplete pagination remain evidence gaps. No independently sourced chart/interval comparison or vendor confirmation was available.

## Findings and present disposition
| Area | Finding | Status / next action |
|---|---|---|
| Temporary migration fixture | SQLite transaction context did not close handle | Resolved on main by #4; Windows/Linux tests pass |
| Timestamp evidence text | One candle claimed 390-bar support | Resolved on main by #5; calculation predicate and ranges unchanged |
| 16:00 filtering | Both workers exclude it despite Market Intelligence accepting it | Characterized in #11; provider-aware raw/derived policy must precede a fix |
| Range completion | Worker lacks cutoff, public handler rejects today/future | Corrected assessment; #11 tests both layers; direct-worker defensive policy unresolved |
| Pagination/partial responses | Keys ignored; empty symbols can still yield success | Characterized in #11; needs explicit completeness metadata and bounded pagination contract |
| Ingestion validation | Float conversion permits invalid OHLC/NaN raw rows | Characterized in #11; diagnostic reporting before any calculation-policy change |
| Persistence provenance | Candle upserts and case edits replace observations; reads may initialize/migrate | Source-only audit/design in #7; no migration authorized |
| Archive completeness | Portable archive omits fundamentals and some active source modules | Unresolved; full manifest/recovery tests on disposable copies needed |
| Provider error callback | Deferred lambda captures cleared exception variable | Resolved on main by #8 with four fake-provider regression tests |
| Diagnostic handle lifetime | mode=ro connection context does not explicitly close handle | Resolved on main by #10 with three temporary-store regression tests |
| Quality visibility | Gaps, duplicates, invalid rows and partial coverage need explicit diagnostics | Pure standalone audit proposed in #6; caller bounds remain hypotheses |
| Offline safety | Tests should not reach project stores, network or child processes | Managed-connection/SQL-authorizer runner proposed in #9 after ATTACH/VACUUM escapes were reproduced; precise limits exclude pre-existing handles and malicious/native/file API behavior |
| Detector outcomes | Endpoint outcomes can bridge missing interior minutes; rounded recomputation can differ | Decide documented outcome coverage/precision contracts, then regression tests |
| Validation consistency | Finite/positive OHLCV checks, symbol normalization, ordering and session isolation vary by module | Characterize before changing calculation results |
| Prior/freshness summaries | Prior duplicates/partial observed dates and global-symbol staleness can mislead | Add regression coverage and per-symbol evidence status |
| Holdout language | Chronology cannot prove prior non-inspection; invalid split sizes unchecked | Freeze/register datasets/splits; qualify claims and test arguments |
| Structure/GUI | Version drift, broad exception handling, direct worker after calls, synchronous full-history reads | Small tested extractions and real Windows smoke tests; no broad refactor yet |

## Validation scope and remaining evidence
PR #1 covers raw-range extrema/completeness, absent 09:30, provisional coverage, an interior gap and invalid OHLC. Main's wording tests cover evidence scoping, insufficient/no data, input preservation and provisional report text. These are complementary contracts. Synthetic samples are not vendor evidence or executable return studies.

Source snapshots and disposable fixtures were used. No research store was inspected, migrated or changed, no provider/SEC service contacted, and no real Tk window or scanner launched. Existing research/diagnostic files remain untouched. See the roadmap for review gates and separate empirical work.
