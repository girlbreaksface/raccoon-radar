# Prioritized development roadmap
Baseline: 2026-10-26 assessment. This is proposed work, not implemented fixes. Each stage should be a small separately reviewed PR; no merges without approval and no existing research DB modifications. Calculation changes require evidence and regression tests.

| Order | Deliverable | Exit criteria / tests | Dependencies |
|---|---|---|---|
| P0.1 | Establish trustworthy offline baseline | Fix Windows migration-test connection cleanup; all five existing tests pass on Windows and Linux. Add a no-network/default-database guard for tests. Add explicit supported Python/Tk/SDK/timezone setup documentation with verified versions, not guessed pins. | Documentation review |
| P0.2 | Timestamp evidence and ingestion characterization | Add immutable synthetic 09:30–15:59 and 09:31–16:00 fixtures, partial sessions, early close, gaps and duplicates. Fake both fetch paths, pagination and current clock. Reproduce excluded 16:00 and unfinished range candles. Collect provider evidence separately with explicit read-only quote requests, complete responses and independent confirmation. | P0.1; provider access for empirical portion |
| P0.3 | Correct misleading research output | Conditional timestamp evidence wording; per-symbol freshness; explicit coverage/missing-data status. Regression tests cover one-bar, full/partial, mixed-date and no-data cases. Keep candidates provisional regardless of fixture success. | P0.2 characterization |
| P0.4 | Protect research provenance | Design explicit read-only repositories and raw/derived/revision separation without applying migrations to user stores. Inventory all writes and hidden initialization. Tests prove read-only calls cannot create/migrate files, preserve source bytes, and fail clearly on missing/unknown schemas. Approve future append-only revision plan separately. | P0.1–2 |
| P1.1 | Reliable provider adapter | Shared explicit request policy, pagination/error reporting, calendar/session handling, completed-bar policy and reproducible metadata. Test repeated keys, page failures, empty/holiday sessions, early closes, DST, shutdown and resource closure. Change ingestion boundaries only after policy evidence. | P0.2 and P0.4 |
| P1.2 | Calculation regression coverage | Golden outputs for Market Intelligence, candle labels, every setup and horizons. Test input order, symbol normalization, duplicate corrections, finite positive inputs, zero volume, session boundaries and missing-minute policy. Prefix-invariance tests prove event features do not depend on later candles; outcomes attach separately. Resolve rounded-price recomputation discrepancies. | P0 baseline; documented calculation contracts |
| P1.3 | Reproducible evaluation | Validate split arguments and cooldown semantics. Save dataset/code hashes, parameters, exclusions and frozen session splits. Explicitly label previously inspected history. Report valid outcomes per horizon, unique sessions, correlation/overlap limitations and uncertainty; evaluate all setups. Test stable reruns and disjoint chronological folds. | P1.2 |
| P1.4 | GUI and error resilience | Fix deferred exception callback; isolate workers from widget operations, coordinate cancellation/shutdown, and expose partial failures. Fake workers/queues plus Windows Tk smoke checklist for load, inspect, validate, export and close. No user-store writes during smoke checks. | P0 baseline; adapter contracts |
| P2.1 | Package incrementally and reduce version drift | Establish one canonical launch command and release version while keeping legacy launchers compatible. Extract UI, provider and persistence services one boundary at a time, with golden output parity. Document scanner provenance and any missing bias formulas. | P1 characterization |
| P2.2 | Provenance-complete export and recovery design | Exclusive collision-resistant reports with complete settings, hashes and schema versions. Verify archive inventories, manifest reproducibility and restore on disposable copies only. Review fundamentals inclusion and every research store. | P0.4 and P1.3 |
| P2.3 | Broader CI and operational checks | Windows/Linux supported-Python matrix; offline regression suite, optional import/Tk checks, formatting/static checks and full active-module diagnostics. Network/provider checks remain opt-in and quote-only. Publish an evidence-based release checklist. | Incremental throughout P1–P2 |

## Suggested next PR
Fix only the open connection in test_migration and add Windows CI coverage, then establish failing regression tests for timestamp evidence wording and fetch boundaries. This restores a credible baseline without changing any market calculation.

## Review gates
- Every PR states observed problem, intended contract, evidence, validation and limitations.
- No claim of verified timestamps until independent evidence is archived and reviewed.
- No claim of trading edge or executable profitability from candle-close studies.
- No production migration, data rewrite, order API, or major architecture replacement is authorized by this roadmap.
- Record unresolved questions rather than filling gaps with assumed candle semantics or fabricated feeds.
