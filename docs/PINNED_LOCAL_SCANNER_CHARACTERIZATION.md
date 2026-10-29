# Pinned local scanner characterization — 2026-10-29

Direct human coding-chat approval covered read-only runtime-path investigation and
isolated synthetic characterization, following PR19comment6497904473.
No production files changed. No scanner/dashboard launched. No provider, database,
credentials, paid feed, history acquisition or strategy evaluation accessed.

## Runtime identity evidence (not proof of active use)

At2026-10-29T13:29:38.7117424Z, read-only Win32_Process query reported **zero**
matching python.exe/pythonw.exe/py.exe/python3*.exe processes. A momentary observation,
not historical-use proof; renamed executables/custom hosts were not exhaustively inspected.
Raw unrelated process arguments were not exposed.

Local dashboard candidate:
C:/Users/louis/OneDrive/Desktop/Raccoon Radar/App/raccoon_radar_v1_5_1.2/raccoon_dashboard_v1_5_14.py
SHA256 febee960e5356a3296187e138f4691122934ab885b74cdb750ece10a704b5e0c,
Git blob3e985d591c0193a63a48d2116297796d59b598fa. README identifies it as launcher,
but active use remains UNKNOWN. Source initializes scanner_path=None, manual chooser
sets it in memory, find_scanner searches only Downloads defaults otherwise. No persisted
scanner-path configuration found in that source. start_scanner checks filename, not hash,
then would launch selected script with --watch/cwd=parent and watch adjacent CSV.
No relevant launcher shortcut/batch/config was identified in the inspected project-folder
inventory or Desktop .lnk names; this is not an exhaustive registry/taskbar/OS-history audit.
No shortcut targets, credentials, browser data or unrelated process commands inspected.

Scanner candidate:
C:/Users/louis/OneDrive/Desktop/Raccoon Radar/Retired dashboard/raccoon_radar_v3.py
**6222bytes, SHA25628bcd08df43b93f4f19818975d470cdc592c72a49d29fb71027d74e04d69eb0d**,
Git blobd906fcdce2a8e356244e6cecd49c90f01aab76bf.
Header identifies v3; installed/runtime SDK/pandas version NOT established.
Only this filename found in supplied folder tree. Its location under Retired dashboard
does not establish active use. No evidence binds it to a running dashboard. No hash/version
of an ACTIVE scanner can honestly be reported.

## Exact synthetic execution boundary

Fixture tests/runtime/fixtures/raccoon_radar_v3.py.txt preserves exact candidate bytes,
LF endings and hash; .txt prevents module discovery/import. Every function extraction
verifies the hash, parses AST and compiles only named analyze/append_new_rows/scan functions.
Full module, __main__, provider imports, watch loop and actual quote context never execute.
Only injected pandas DataFrames/mock provider/context, fixed clocks and temporary CSVs.
scan test injects fake constructor/append/clock and confirms one-symbol partial failure.
Network/process/SQLite audit hooks apply before function execution; file writes inside
the test process are limited to registered disposable directories. Installed dependencies
load before hooks, tempfile's system probe resolves first, and this is NOT a general
filesystem sandbox or adversarial-code isolation claim. Temp fixtures contain no real data.

Dependencies pinned to the tested pandas3.0.1/numpy2.3.5; local Python3.12.14 Windows.
These are test-environment versions, not the original scanner's deployed dependencies.
Existing root69guarded offline tests run separately; nested runtime21tests do not alter
the baseline discovery contract. No new dependency is required by production source.

## Observed current behavior — not endorsed policy

21 characterization methods PASS locally:
- Exact pinned hash/length and no moomoo module import.
- Pagination key ignored; one history call even with continuation.
- EMA9/EMA21 adjust=False recurrence, prior20-bar relative volume and cumulative
  HLC3 volume-weighted proxy match independent fixture arithmetic after output rounding.
  This is a candle proxy, not trade-level VWAP or predictive-performance evidence.
- A fresh synthetic breakout becomes stale with pattern=None but BULLISH bias retained.
  Existing raw-stamp age cutoff180seconds accepts exact180/rejects181; not approved policy
  and not verified completion/availability. Current/future minute excluded by raw stamp.
-16:00 excluded/15:59 retained; no raw timestamp shift. Provider convention unresolved.
- Missing minute accepted with35remaining rows; duplicate stamp retained changes EMA.
- Wrong-session rows can pass requested-date filtering and produce stale directional bias.
- Inconsistent OHLC accepted; infinite close can reach output, strict JSON rejects it.
- Zero volume anywhere rejects whole snapshot; fewer35bars/provider failure rejected.
- Out-of-order input sorted; original DataFrame unmodified. MIXED bias possible; actionWAIT.
- QQQ failure still passes SPY result to synthetic CSV append and closes fake context.
- Existing CSV symbol/bar dedup suppresses later revisions; duplicate rows inside one input
  batch are both written; empty batch creates no file. Writes are disposable synthetic only.
- Network/SQLite guards verified active.

These tests deliberately assert current defects. Green characterization is NOT approval
of those behaviors, a repair, a market study or a known-failing regression artifact.
Initial harness run had17ERROR from missing injected constants/tempdir probe restrictions;
then one fixture failed to produce a true breakout. Harness/constants/temp setup and
synthetic breakout data were corrected; pinned source/assertion intent unchanged.
No initial harness failure is claimed to establish a production defect.

## Relation to PR28/29 and next proposed patch

Earlier default-Downloads UNAVAILABLE statement remains true for those two paths; supplied
folder resolves candidate-source availability only, not ACTIVE source authority.
Candidate outputs scan_time_et/bar_time_et, biasBULLISH/BEARISH/MIXED and fresh boolean.
It lacks immutable source binding, original information-availability evidence and PR29
explicit event_at/available_at contract. scan_time_et is wall-clock scan start, not proof of
first market availability. PR29 should remain fail-closed; do not map fields by assumption.
Local market_intelligence still has old unconditional wording; local provider-verification
method also differs from GitHub main. Do not overwrite local app to reconcile versions.

Propose separate reviewed, test-first scanner patch only after source owner confirms target:
1. Explicit source/version/hash identity and visible recorded-vs-current status; no automatic
   launching or treating same filename as verification.
2. Finite/positive/consistent OHLCV, exact requested-date checks and explicit duplicate/
   pagination/partial-symbol exclusions. Preserve raw responses/revisions; never overwrite
   original CSV. Keep source/script hash, request/receipt metadata separate from availability.
3. Make stale/missing/unverified data ineligible, with independent per-symbol reasons.
   Preserve legacy raw observations visibly; do not silently change EMA/volume thresholds.
4. Review timestamp authority, completion/finality, exchange calendar/early closes and
   historical-availability contract before16:00/current-minute/calendar integration.
5. Design an append-only new evidence stream for revisions, not edits to existing CSV/DB.

Implementation, real-record use, provider connections, ingestion deployment, strategy
threshold changes, historical studies, orders and merges remain unauthorized here.
Independent review/design/source/merge gates remain distinct. Exact draft head,
Windows/Linux CI checkouts/results are returned on PR19 after verification.
