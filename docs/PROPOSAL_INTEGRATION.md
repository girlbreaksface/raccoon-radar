# Pinned proposal validation and sequential integration checklist

Main baseline: 342c7389b735188ddf75867c1f62aca4f8176bb0 (PR #4 and PR #5 merged). This PR changes only CI configuration and documentation. It does not merge any proposal or run user-store migrations.

## Combined Windows/Linux evidence
The additional path-filtered workflow checks out exact commits, assembles an allowlisted source overlay under RUNNER_TEMP and runs the guarded suite there. It never changes main or a real project database. No optional broker SDK or provider service is used. GitHub checkouts acquire source before the offline test guard starts.

Pins:
- baseline: 342c7389b735188ddf75867c1f62aca4f8176bb0
- opening: 5aa151e3c61d8a25c1cd2865cbc3bf1fd2c74003
- quality: a7eb6c3e766d8c16dcdb05bcef413ab03df0138c
- dashboard: 359619777ca120937f564adfa65be123c23c7cfb
- offline: 1dffeb45198050e04d609f2dae46e31386e5d338
- diagnostics: 1cd4f7d32ac32973336f6ef7b6e296c462ab938a
- ingestion: ad06befd55ad9b79fbcbf69a787dabd329672062

Expected combined inventory: 10 main + 5 opening-range + 10 quality-audit + 5 CSV-report + 4 callback + 8 initial offline-guard + 9 SQL-escape + 3 diagnostic-closure + 15 ingestion-characterization = **69 tests**. Local Windows/Python 3.12.14 passes all 69 through the guarded runner. Both Windows/Linux Python 3.11 results are recorded in the PR after CI completes. Ordinary CI on this validation branch still runs ten main tests; the separate pinned integration job runs 69.

This is a reproducible compatibility snapshot, not a general filesystem sandbox or authorization to merge. Pins deliberately do not float. Refresh them and rerun after a proposal changes; do not use old green runs to approve a new head. The workflow is path-filtered to its own config/document, plus manual dispatch, so it is not a claim that future main is continuously checked against new proposals.

## Sequential preparation requested by maintainers
No explicit merge approval has been recorded in this session. These are review checkpoints, not completed merge steps.

| Order | PR | Session-reviewed head | Expected focused diff |
|---|---|---|---|
| 1 | #8 | 359619777ca120937f564adfa65be123c23c7cfb | One callback-message capture line + fake-provider regression tests |
| 2 | #10 | 1cd4f7d32ac32973336f6ef7b6e296c462ab938a | Explicit diagnostic connection closure + temporary-store regression tests |
| 3 | #6 | a7eb6c3e766d8c16dcdb05bcef413ab03df0138c | Standalone quality audit/CSV report, tests and documentation; no GUI/ingestion integration |
| 4 | #7 | c04a7fe07474b3dc2b99a135148aac4ea9022d7d | Persistence write inventory and proposed provenance strategy only |

PR #6 expanded since the earlier audit-only review; its CSV CLI and no-overwrite behavior require approval at the newer head, not the earlier commit.

Before EACH merge:
1. Obtain explicit maintainer approval for that PR and exact head.
2. Fetch current main and the PR again; compare the head to the approved SHA.
3. Inspect the current diff/file inventory for unexpected changes, including after rebases.
4. Verify Windows AND Linux checks apply to that exact proposal/current merge target.
5. Merge only if approved; then verify CI on the resulting main SHA before progressing to the next PR.
6. If main CI fails or the head changes, stop that merge sequence and resolve/re-review; continue unrelated non-destructive work if available.

No merge was executed by this agent. Pending source/runtime changes, calendar/provider assumptions and database migrations remain separate decisions.

## Additional reviews and precise limits
Draft #1 is synthetic coverage: its 390-row fixture is now positive-valued, and its 15 tests combined with main do not establish Moomoo interval semantics. Draft #2 distinguishes merged #4/#5 fixes from pending proposals and corrects the range-UI claim.

#9's connect-only SQL bypass was reproduced with disposable fixtures and corrected using managed connection creation plus a conservative SQLite authorizer. It blocks tested ATTACH/VACUUM paths, extension/file-function/virtual-table paths and directory PRAGMAs. Unmanaged pre-existing handles, deliberate policy replacement, native/UDF code, direct file APIs, VFS and filesystem races/hard links remain outside protection. It is not an arbitrary-SQL security service.

#11 characterizes existing ingestion without changing it. The public range handler rejects today/future; direct worker invocation lacks a cutoff. 16:00 exclusion and discarded pagination are verified code behavior; provider start/end labeling, real completed-bar status, calendar/DST correctness and trading usefulness remain unverified.
