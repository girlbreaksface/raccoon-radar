# Prioritized development roadmap
Updated against main 342c7389b735188ddf75867c1f62aca4f8176bb0. Each implementation remains a separately reviewed PR; no merges, production migrations, timestamp rewrites or order APIs are authorized by this document.

## Status and scope
| Priority | Deliverable | Current state and next acceptance evidence |
|---|---|---|
| P0.1 | Trustworthy offline baseline | #4 merged: connection cleanup and Windows/Linux Python 3.11 CI. Main has ten passing tests after #5. #9 proposes guarded discovery and source/runtime manifests; review its native-code/filesystem limitations. |
| P0.2 | Opening-range integration | Draft #1 adds five tests complementary to main's five wording tests and five volume tests. Combined set is 15, not ten. Refresh and pass both CI platforms before approval. No provider claim is promoted. |
| P0.3 | Honest timestamp wording | #5 merged: full-session claim gated by existing evidence predicate. Raw ranges/candidates unchanged. Per-symbol freshness and other misleading-output risks remain. |
| P0.4 | Ingestion characterization | #11 tests actual worker/handler ASTs with fake provider and fixed wall clock, including 16:00, public past-date guard, direct-worker cutoff asymmetry, gaps/duplicates, pagination and partial failures. This phase changes no ingestion behavior. |
| P0.5 | Standalone quality reporting | #6 proposes a pure offline audit and standalone report path for missing/duplicate/invalid/partial data. Expected bounds are caller hypotheses, never confirmation of provider semantics. Prefer this before GUI integration. |
| P0.6 | Persistence inventory/design | #7 audits hidden initialization, upserts, report collisions and archive omissions. Review separate opt-in append-only evidence/revisions and read-only repository contracts. No schema/data writes authorized. |
| P1.1 | Define ingestion policy before repairs | Decide raw response retention, interval/session flags, pagination completeness and partial-data states. Obtain independent evidence before adopting interval-start/end rules. Public range UI already rejects today; defensive worker changes need separately justified tests. |
| P1.2 | Isolated error/resource fixes | #8 proposes deferred error-message capture; #10 proposes explicit diagnostic read-only connection closure. Review their failing-first tests independently. No claim of real GUI/SDK validation. |
| P1.3 | Calculation regression coverage | Cover finite/zero inputs, duplicate corrections, ordering, session isolation, detector labels/horizons, missing-minute outcome policy and rounding. Prefix-invariance tests must separate event-time features from later outcomes. No threshold changes without evidence. |
| P1.4 | Reproducible evaluation | Validate split/cooldown arguments and keep immutable dataset/code/parameter/exclusion manifests. Freeze hypothesis and session splits before evaluation; report overlap/correlation, missing outcomes, sample counts and uncertainty. Previously viewed history is not untouched holdout. |
| P1.5 | GUI resilience | Queue worker results, cancellation/shutdown coordination and visible partial errors. Fake-provider tests plus Windows Tk smoke tests on disposable fixtures; no user-store writes for testing. |
| P2.1 | Packaging/version consistency | Establish canonical launch/release metadata while preserving old entry points. Extract one service boundary at a time after output parity tests. Obtain external scanner/bias source before accuracy claims. |
| P2.2 | Complete archives/provenance exports | Include all four stores and active sources, exclusive destination creation and immutable manifest hashes. Restore rehearsals only on disposable copies; do not overwrite existing archives or research stores. |
| P2.3 | Release readiness | Both CI platforms, known test inventory and branch differences, optional dependency checks and separate empirical provider/GUI evidence. No version bump substitutes for evidence. |

## Recommended next decisions
1. Review #1 and refreshed #2 against verified main; CI/tests establish synthetic compatibility, not Moomoo conventions. Require explicit approval before any merge.
2. Review ingestion characterization and choose an evidence-backed raw/derived/completed-bar contract. The initial claim that the range UI accepts today was wrong; keep the handler's completed-past-date restriction documented.
3. Review #6/#7/#9 as diagnostic/provenance/testing infrastructure and #8/#10 as isolated fixes. Unmerged proposals are not current-main behavior.
4. Then write desired-behavior regression tests for a small ingestion repair, with immutable raw timestamps, pagination/coverage metadata and explicit exclusions. Independent provider evidence may block semantic changes; proceed with non-destructive diagnostics instead.

## Review gates
- State trigger, observed behavior, intended contract, evidence, exact tested commit/test count and limitations.
- Keep pure synthetic diagnostics, observed provider responses, candidate interpretations and independently verified semantics separate.
- Preserve all research data and raw timestamps. No source-store initializer in an inspection path; no migration or archive replacement without a separate approved plan.
- No executable return, options P/L or trading-edge claims from candle-close research.
- Do not merge to main without explicit approval.
