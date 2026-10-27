# Persistence write-path audit and safe provenance proposal
Source baseline: main 342c7389b735188ddf75867c1f62aca4f8176bb0 (PR #4 and PR #5 merged by maintainers). This is a source-only audit and design proposal. No application persistence path was executed against user data, and no schema or implementation changes are included.

## Current write inventory
| Store / output | Write entry points | UI triggers and hidden writes | Integrity risk |
|---|---|---|---|
| History: candles | strategy_validation.store_candles: CREATE TABLE; INSERT ... ON CONFLICT DO UPDATE | Dashboard persist_history called automatically from process_candle_events after single-day/range fetch | Existing symbol/time rows replaced with no revision/event lineage; provider settings and fetch IDs absent; count is processed rows, not unique inserts |
| History: research_runs / research_notes | research_journal.initialize, record_run, record_note | run_validation and add_journal_note | Rows append, but the ledger's candle hash points to mutable candle history rather than immutable original observations. Hash does not prove source authenticity or preserve old rows. Foreign-key enforcement is not explicitly enabled |
| History hidden DDL | get_runs, get_notes, export_json all call initialize | Journal refresh; export_research; export_archive | Reads/exports can create schema and files. "Read-only research" describes no orders, not absence of database writes |
| Discovery: discoveries | volume_discovery.initialize; save_results upsert | discovery_scan worker | Latest view overwritten for symbol/session |
| Discovery: discovery_snapshots | initialize CREATE; save_results INSERT | discovery_scan worker | Append-only observation history is useful; provider fetch/configuration identity is missing |
| Discovery hidden migration | list_results, list_snapshots call initialize, including ALTER TABLE for four missing metrics | discovery_refresh and export/archive consumers | Read-named functions may alter schemas; never invoke them for forensic inspection |
| Swing: swing_cases | swing_watchlist.initialize; save_case INSERT/UPDATE | discovery_save/promote workflow; swing_save | Editing a case replaces text with updated_utc, no revision history |
| Swing hidden DDL | list_cases calls initialize; export_csv calls list_cases | swing_refresh, swing_export | Export may create source schema, then overwrite destination CSV |
| Fundamentals: snapshots / evidence_notes | fundamental_intelligence.initialize; save_snapshot; add_note | fund_fetch worker; fund_save_note | Appending snapshots/notes preserves observations, but no raw response content hash/versioned normalization lineage |
| Fundamentals hidden DDL | latest and list_notes call initialize | fund_load and saved-note display | "Load saved" can create schema/files |
| Provider evidence JSON | _verify_provider_worker, _inspect_opening_feed_worker write_text | Read-only quote inspection UI | Same-second filenames may collide; selected stamps/opening OHLCV do not preserve complete responses or all request state |
| Diagnostic ZIP | raccoon_diagnostics.main, signal_validation_lab.main, setup_outcome_validation.main | Diagnostic UI subprocesses | ZIP uses write mode; microsecond names reduce collisions but do not guarantee exclusive creation |
| Research ZIP / archive / swing CSV | export_research, export_archive, swing_watchlist.export_csv | Save dialogs | Existing destinations can be overwritten. Archive initializes source stores before backing up |

strategy_validation.load_candles checks existence and SELECTs via an ordinary writable connection; unlike the read-only diagnostics, it does not enforce mode=ro. SQLite connection transaction contexts in this module and raccoon_diagnostics do not themselves close handles. No fixes to these APIs are included here.

Existing explicitly read-only paths include Market Intelligence's mode=ro history query, signal_validation_lab.audit and setup_outcome_validation.validate. The last two close their connections explicitly. raccoon_diagnostics.inspect_database uses mode=ro but should also explicitly close its handle. Read-only reports still write output artifacts, and mode=ro is not a backup/immutability guarantee for a live WAL store.

## Archive limitations found in source
export_archive backs up history, swing and discovery after calling their initializers. It omits raccoon_fundamentals.sqlite3, SEC notes/snapshots, market_intelligence.py and fundamental_intelligence.py from its explicit archive members/source list. Its completion message should not be used as evidence that every research artifact was preserved. No archive export or restore was attempted. Existing archives must remain untouched.

## Proposed provenance model (not a migration authorization)
1. Preserve the existing four stores and all diagnostic/research files. Inventory names, sizes, hashes and application versions through a separately approved read-only/copy workflow. Capture SQLite WAL-consistent snapshots with a reviewed backup plan; hashing only the main database while WAL is active is insufficient. Never call initialize from the inspection path.
2. Introduce a separate new opt-in evidence store/directory, never a silent in-place conversion. Store immutable raw provider responses with request UUID, retrieval UTC, SDK/OpenD versions, endpoint, entitlement/subscription state, symbol, interval, timezone/session/adjustment settings, pagination sequence/completeness, content hash and source provenance. Use exclusive creation and collision-resistant IDs. Retain failed/partial request metadata.
3. Keep each observation/revision append-only. Index symbol/raw timestamp/request ID; do not replace the original observation on a correction. A chosen "latest" view must have an explicit deterministic selection policy and revision links. Legacy imports, if approved, are labeled legacy/source-unknown with a snapshot hash rather than invented provider metadata.
4. Derived values live separately: raw observation IDs, transformation source/hash/version, parameter set, timestamp-convention hypothesis, validation state, exclusions and derivation time. Never overwrite raw timestamps. Promoting a hypothesis needs independent evidence and review; retain contradictory evidence.
5. Research runs reference an immutable dataset manifest and code/environment hashes, frozen train/test session IDs, hypotheses and parameters, valid/missing outcome counts, overlap policy and prior-inspection status. A chronological split alone is not untouched holdout.
6. Cases and notes append revisions linked to originals. Preserve original text, source URL, author-supplied assessment and capture time. "Archive" means retained status, not deletion. Read repositories SELECT through explicitly read-only connections and fail on unknown/missing schema, without initialization.
7. Exports include an inventory manifest covering all four stores, evidence and source versions; exclusive destination creation prevents overwrites. Restore rehearsals run only on disposable copies and compare hashes/counts/foreign-key integrity. Never restore over user stores during engineering verification.

## Required approval and tests before implementation
No production migration, schema write, source-history rewrite or legacy import is authorized by this design. A future implementation must first pass temporary synthetic-store tests proving:
- reads do not create/migrate missing or legacy schemas, connections close, and errors are explicit;
- a correction appends a revision, prior bytes/IDs remain intact, and deterministic selected views are reproducible;
- interrupted multi-page capture cannot be labeled complete, duplicate requests do not silently replace evidence;
- missing provenance is explicit, raw timestamps survive byte-for-byte, and derivations can be replayed from manifests;
- exports cannot overwrite an existing artifact and include fundamentals; recovery on disposable copies preserves all rows and notes.

## Verification and remaining risks
Commands: python -B -m unittest discover -v -p "test_*.py"; python -m compileall -q .
The verified main baseline passes all ten offline tests on local Windows/Python 3.12.14. This PR adds documentation only; existing Windows/Linux CI will also run the branch suite. Source inspection cannot prove actual database health, content retention, sidecar state or private archive completeness. Existing upserts, hidden initialization, archive omissions, report collisions and missing request provenance remain unresolved until separately tested fixes are reviewed.
