# Raccoon Radar contributor instructions

## Scope and architecture
Raccoon Radar is a Python/Tkinter market research application, primarily for SPY/QQQ. The current requested entry point is `raccoon_dashboard_v1_5_14.py`; it orchestrates UI, queues, worker threads, CSV input, local OpenD quote requests, research exports, and persistence. Older versioned dashboards remain compatibility artifacts. Do not remove them or assume their behavior is identical.

- `market_intelligence.py`: pure candle-derived session levels, strict raw-stamp 5/15/30-minute ranges, provisional end-labeled candidates, and an explicitly labeled OHLC4 volume-weighted proxy.
- `price_action_engine.py`: exploratory candle labels and CSV loader.
- `setup_detective.py`: per-symbol/session event detection and 1/3/5-minute directional close outcomes.
- `strategy_validation.py`: candle storage, chronological split, strict symbol cooldown, weekday summaries.
- `performance_intelligence.py` and `validation_intelligence.py`: descriptive daily/consistency and expanding-window summaries.
- `volume_discovery.py`: daily underlying-volume discovery, current results and append-only snapshots.
- `fundamental_intelligence.py`: SEC submissions/companyfacts snapshots and source-linked evidence notes.
- `research_journal.py` and `swing_watchlist.py`: research runs/notes and manual cases.
- `raccoon_diagnostics.py`, `signal_validation_lab.py`, `setup_outcome_validation.py`: offline diagnostic/report tools.

Four local stores are normally named `raccoon_history.sqlite3`, `raccoon_discovery.sqlite3`, `raccoon_swing.sqlite3`, and `raccoon_fundamentals.sqlite3`. They contain user research, not disposable build output. Some functions described as read-only research still initialize or update these stores.

## Non-negotiable boundaries
- Never delete, overwrite, replace, normalize in place, or silently revise existing research data or diagnostic evidence.
- Do not modify existing SQLite databases, run migrations against them, or launch UI paths that initialize/write stores during inspection. Audit through explicit `mode=ro` connections and close connections explicitly.
- Persistence tests may create disposable databases under temporary test directories with explicit paths; never use default project DB paths. Label fixtures synthetic.
- Do not enable live trading, trade contexts, account unlock, order placement, or execution. Quote research must remain separate from order APIs.
- Preserve existing functionality. No trading/research calculation or threshold changes without supporting evidence and meaningful regression tests.
- Work on a separate Git branch; submit reviewable changes in a PR. Never merge into main without explicit user approval.
- Explain findings and proposed scope before major refactoring. Prefer small changes with a clear rollback.

## Research integrity
- Preserve provider timestamps and source OHLCV exactly. A derived timestamp belongs in a separate, versioned, reversible layer, never in raw history.
- 09:31–16:00 coverage with 390 unique consecutive bars supports an end-label hypothesis; it does not establish provider semantics. Missing 09:30 alone proves neither a missing interval nor end labeling.
- Keep raw-stamp ranges, provisional shifted candidates, and independently verified ranges visibly distinct. Never fabricate missing candles.
- Record provider endpoint, SDK/OpenD version, entitlement/subscription state, session, timezone, interval, adjustment/session flags, pagination completeness, fetch time, and evidence hash for timestamp claims.
- Require independent opening/closing OHLCV comparison or explicit provider confirmation before promoting a timestamp convention. Record contrary evidence and unresolved assumptions.
- Verify session calendars, early closes, DST, completed-bar status, chronology, gaps, duplicates, and finite positive price inputs before making completeness claims.
- OHLC4 volume-weighted candles are a proxy, not trade-level VWAP. Candle-close directional outcomes are not executable returns, options P/L, or proof of predictive edge.
- Separate event-time features from future outcomes. Freeze hypotheses, parameters, datasets, and train/test boundaries before evaluation. Previously inspected data cannot be called untouched holdout solely because it is chronologically later.
- Report missing outcomes, exclusions, event/session counts, overlapping observations, SPY/QQQ correlation, uncertainty, and all evaluated setups. Unsupported feeds remain UNAVAILABLE.
- New exports should use collision-resistant names and exclusive creation. Include source/code hashes, parameters, software versions, exclusions, and provenance; never overwrite earlier evidence.

## Development and validation
Use Python 3.11 as the existing CI baseline; verify Windows as well as Linux. Offline modules mostly use the standard library. GUI needs Tk; OpenD quote paths lazily import the `moomoo` SDK and use localhost:11111. `zoneinfo` needs system IANA data or `tzdata`, especially on Windows. No dependency lock or supported SDK version is currently established.

Verified baseline: main `0d9015cc3cba0977cafcb952cbb33a11870e2754` includes PR #4 (temporary SQLite fixture closure and Windows/Linux CI) PR #5 (conditional timestamp-evidence wording), PR #8 (deferred error capture), and PR #10 (diagnostic handle closure). Main has 17 offline tests. Draft PR #1 adds five complementary opening-range tests; it is not merged. PRs #6/#7/#9 and ingestion characterization PR #11 remain separate proposals until approved.

Default offline checks:
```text
python -B -m unittest discover -v -p "test_*.py"
python -m compileall -q .
```
Compilation creates only bytecode; AST parsing is an alternative when inspection must avoid generated files. Existing tests use temporary synthetic stores. Do not claim GUI, OpenD, SEC, or real-history validation from compilation/unit tests.

For fixes, add tests that reproduce observable failures before changing behavior. Cover timestamp boundaries, nonfinite/zero inputs, duplicates, missing minutes, no future leakage, session isolation, provider errors/pagination, and persistence resource lifetime as relevant. Test network adapters with fakes; normal CI must not require OpenD, SEC access, credentials, or user databases.

Keep pure calculations outside GUI callbacks. Route worker results through queues; update Tk widgets from the main thread. Capture exception messages before deferred callbacks and handle shutdown/cancellation. Close SQLite connections explicitly; a SQLite connection context manager handles transactions but does not close the handle. Avoid broad swallowed exceptions; report partial failures and exclusions.

The public `fetch_range` handler permits only completed past dates; the range worker itself lacks that defensive restriction. Do not describe normal UI requests as accepting today. Characterize callers and timestamp assumptions before changing either layer.

The guarded runner in PR #9 and standalone candle-quality diagnostics in PR #6 are proposals, not tools available on current main. Once approved, use their documented contracts without treating synthetic coverage as provider verification.

PRs should state problem, behavior impact, evidence, validation results and limitations, and any data/schema implications. Keep test counts scoped to a verified commit/branch; do not count unmerged tests as part of main. See `docs/PROJECT_ASSESSMENT.md` and `docs/DEVELOPMENT_ROADMAP.md`.
