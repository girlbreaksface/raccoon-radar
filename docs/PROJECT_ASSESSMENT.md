# Project assessment
Assessment date: 2026-10-26 (America/New_York). Scope: source review and offline checks, with documentation-only proposals.

## Evidence and limits
Reviewed the supplied flat workspace's 28 Python files at varying depth, especially v1.5.14, Market Intelligence, the calculation/persistence/validation modules, the five existing tests, historical README text, ignore rules, and GitHub Actions workflow. Key dashboard/research/test sources were also checked through the connected private GitHub repository. The workspace is a source snapshot without Git metadata; a separate GitHub branch was created from main for this proposal.

No research databases or saved provider diagnostic JSON/ZIP evidence were present in the supplied root inventory. They are ignored by Git. No user database was opened or changed, GUI launched, broker contacted, SEC request made, or trading path enabled. Provider timestamp semantics and real-history quality have therefore not been independently validated. This is a source assessment, not an audit of the user's complete historical research collection.

## Architecture and implemented features
The application is a flat collection of modules with a large Tkinter controller rather than an installable package. v1.5.14 contains about 1,280 lines and coordinates UI construction, threaded I/O, CSV polling, a separately launched scanner process, analysis, SQLite persistence and exports. Background workers and queues are already used in several paths; other workers call Tk's after method directly.

Data paths:
1. Local Moomoo OpenD quote/history or user CSV -> in-memory candle dictionaries -> candle labels and Setup Detective.
2. Fetch success -> automatic candle persistence through strategy_validation -> local history and journal-driven validation.
3. In-memory candles plus read-only SQLite history -> Market Intelligence, with loaded memory winning duplicate keys.
4. Daily OpenD discovery -> volume ratios/current discoveries/snapshots -> manually promoted swing research cases.
5. SEC HTTP JSON -> fundamentals snapshots and source-linked notes.
6. Diagnostic CLI tools -> JSON/CSV ZIP reports; research exports and archive backups are exposed in UI.

Implemented functionality includes session/prior levels, raw-stamp opening ranges, provisional shifted ranges, OHLC4 proxy, candle burst/breakout/rejection/continuation hypotheses, short-horizon event studies, cooldown filters, chronological and rolling evaluation summaries, daily/weekday consistency, unusual underlying-volume metrics, manual cases/journaling, SEC research, CSV imports, diagnostics and archives. News, economic calendar, macro feeds, breadth and options flow are explicitly unavailable in Market Intelligence. The original external scanner and its bias definitions are not supplied here, so their calculations are not verified.

Persistence is spread across history, discovery, swing and fundamentals SQLite files. Research operations are not uniformly read-only: history candles are upserted, discovery current rows are updated while snapshots append, and list/load helpers in several modules initialize schemas. Existing behavior must not be exercised against research stores during onboarding.

## Dependencies and reproducibility
Most offline code uses Python's standard library: Tkinter, SQLite, CSV/JSON/ZIP, datetime/zoneinfo, urllib, threading/queues and unittest. OpenD features lazily require the moomoo SDK and a local quote context at 127.0.0.1:11111 with suitable historical permissions; the recent-kline comparison may require a KL_1Min subscription, as the existing README notes. SDK transitive dependencies are not pinned or inventoried. SEC fetch requires internet and a user-supplied contact User-Agent. Windows requires Tk and usable IANA timezone data, potentially supplied by tzdata.

No requirements/lock file or pyproject was found. CI uses Python 3.11 on Ubuntu with compileall and unittest discovery and no optional SDK installation. This checks offline source/tests, not desktop UI or broker interoperability. Local assessment used bundled Python 3.12.14 on Windows.

## 09:30 versus 09:31 research
Existing README.txt states that v1.5.14 adds a reversible interval-start candidate layer: raw provider timestamps are never shifted in storage. market_intelligence.calculate requires every exact minute starting 09:30 for raw-stamp 5/15/30-minute ranges. It separately derives raw minus one minute in memory and labels resulting ranges PROVISIONAL / NOT VERIFIED FOR TRADING.

The full-session predicate checks exactly 390 unique consecutive minute stamps from 09:31 to 16:00. This is consistent with, but does not prove, end-of-minute labeling. It is not an exchange-calendar-aware completeness test and does not handle early closes.

The dashboard has two investigation tools:
- _inspect_opening_feed_worker records raw first/last timestamps, counts at 09:30/09:31 and duplicates before app filtering. It records but does not follow a pagination key.
- _verify_provider_worker compares history for hardcoded 2026-10-23 and the current ET date against recent candles, capturing opening OHLCV and up to six history pages, errors, duplicate counts and pagination indicators.

Evidence limitations: endpoint comparison uses partly implicit request defaults, records only selected OHLCV rather than full returned candles, does not establish a global cross-page deduplication/completeness result, and does not record SDK/OpenD versions or subscriptions. The UI says “Saved full OHLCV and pagination evidence,” which overstates the saved payload. Reports use second-resolution filenames and ordinary write_text, permitting same-second overwrites. Repeated pagination keys can end collection with unresolved pages. Provider tools alone do not independently establish interval semantics.

Next experiment: select completed regular and early-close sessions for SPY/QQQ; archive complete raw responses with explicit flags, versions, entitlement state, pagination and hashes; compare opening/closing OHLCV to independently documented chart intervals or obtain written vendor confirmation. Keep all derived candidates separate. No timestamp change is justified by this assessment.

## Findings, ordered by reliability impact
| Priority | Evidence location | Finding and consequence | Proposed regression/next action |
|---|---|---|---|
| P0 | dashboard _fetch_candles_worker and _fetch_range_worker | Both exclude 16:00 while Market Intelligence accepts it and needs it for the 390-bar end-label predicate. An end-labeled normal session can lose its final interval. | Fake provider with 09:31–16:00; assert raw retention and explicit convention-aware derived filtering before changing boundaries. |
| P0 | dashboard _fetch_range_worker | Unlike the single-day fetch, range fetching has no current/incomplete-bar cutoff. Selecting today can persist a still-forming bar. | Freeze the clock; test range/single-day parity under each unresolved stamp convention. |
| P0 | market_intelligence.calculate timestamp_convention | Evidence wording is unconditional: a single 09:31 candle reports end labeling “STRONGLY SUGGESTED by 390-bar session” although its evidence flag is false. | Verified by pure in-memory probe; make wording conditional after adding a failing test. |
| P0 | strategy_validation.store_candles; persistence helpers | Candle conflicts overwrite values without revision provenance; several apparent read helpers initialize/migrate schemas. | Design explicit read-only access and separate revision history; no migrations against existing research stores in this assignment. |
| P1 | dashboard _verify_provider_worker exception handler, line 278 | Deferred lambda closes over exception variable exc, which Python clears after except. Error reporting can fail with NameError. | Capture message as callback argument; fake provider error and run deferred callback. |
| P1 | test_volume_discovery.test_migration | sqlite3 connection context does not close connection; retained db handle blocks Windows temporary-file cleanup. | Observed WinError 32; use explicit connection closure in a separate small fix PR. |
| P1 | setup_detective.detect | Future outcomes require the endpoint candle but not intervening minutes, despite “missing minutes are never bridged” docstring. A 09:35 event receives a 3m outcome at 09:38 with 09:36/09:37 absent. | In-memory probe confirmed 8.3333% synthetic outcome; decide/document endpoint-only versus continuous coverage, then test. |
| P1 | setup_detective.detect, price_action_engine.analyze, strategy_validation.store_candles | Validation differs from Market Intelligence: finite/strictly positive prices are not consistently enforced. Zero event close can cause division by zero; infinite volume can contaminate baselines. | Synthetic zero/NaN/infinity/invalid-OHLC fixtures; reject with observable exclusion counts. |
| P1 | price_action_engine.analyze | Rolling history follows input order across dates, without sorting, deduplication or session/gap isolation. Labels can differ by row order and bridge sessions. | Characterize first; define intended semantics before changing labels. |
| P1 | setup_outcome_validation.validate | Recomputes outcomes using entry_close rounded to three decimals, while original detector uses full precision; raw future close map also bypasses detector validation. Apparent discrepancies can be numeric/input-policy artifacts. | Fractional-price and invalid future-row fixtures; preserve precision and consistent validation only after tests. |
| P1 | normal fetch paths and volume_discovery.scan_moomoo | Returned pagination key is discarded. Missing pages may silently produce partial research inputs. | Fake multi-page, repeated-key, error-on-later-page responses; report completeness. |
| P1 | market_intelligence.calculate prior session | Current-session bars are deduplicated but previous-session rows are not; prior levels may include superseded duplicate extremes. “Prior” is the previous observed date, possibly partial/stale. | Duplicate correction and partial/missing previous-session fixtures. |
| P1 | dashboard refresh_intelligence | Global maximum session determines stale warning; fresh SPY can mask stale QQQ, and current-session age is not quantified. | Mixed-date symbols and intraday stale snapshots. |
| P1 | strategy_validation.validate; validation_intelligence.rolling_holdout | Chronological splits are useful but do not track prior inspection; “untouched holdout” cannot be established from chronology. Nonpositive split sizes lack validation. | Freeze/register splits; test zero/negative sizes, missing outcomes and stable fold assignments. |
| P2 | provider reports/exports | Second-resolution filenames can collide; provenance/settings and full raw evidence are incomplete. | Exclusive unique output plus reproducible manifest and tests. |
| P2 | dashboards / diagnostics | Versioned copies create drift; v1.5.13 and v1.5.14 are byte-identical locally and window title says v1.5.12. Diagnostics MODULES omits market_intelligence. | Establish canonical entry point/release metadata; include all active modules in diagnostics. |
| P2 | GUI/SQLite/I/O | Dense one-line functions, broad exception handling, direct worker after calls, repeated full-history synchronous reads and incomplete shutdown coordination complicate failures and responsiveness. | Characterize UI, then incrementally extract adapters/services and enforce queue-only results. |

## Verification performed
- All 28 top-level Python files passed AST parsing, without importing/launching dashboards.
- Five existing volume tests were attempted. Sandbox temp-file access first prevented two tests; rerun outside the sandbox produced four passes and one migration-test cleanup error (WinError 32, open SQLite handle). This is not a clean test-suite pass.
- Existing tests cover 20/50-session ratios, insufficient 50-session history, an invalid latest candle, snapshot retention and additive migration row retention. They do not check retained legacy values/IDs comprehensively.
- Pure in-memory synthetic probes confirmed unconditional timestamp evidence wording and the endpoint-only outcome across missing intermediate bars.
- No GUI, live OpenD, SEC, existing SQLite data, options execution or predictive-performance validation was performed. No production source or trading calculation was changed.

The roadmap proposes tests and evidence collection before behavior changes or major refactoring.
