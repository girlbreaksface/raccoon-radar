# Pinned proposal validation and sequential integration checklist

Main baseline: 0d9015cc3cba0977cafcb952cbb33a11870e2754 (PRs #4/#5/#8/#10 merged by maintainers). This PR changes only CI configuration and documentation. It does not merge any proposal or run user-store migrations.

## Combined Windows/Linux evidence
The additional path-filtered workflow checks out exact commits, assembles an allowlisted source overlay under RUNNER_TEMP and runs the guarded suite there. It never changes main or a real project database. No optional broker SDK or provider service is used. GitHub checkouts acquire source before the offline test guard starts.

Pins:
- baseline: 0d9015cc3cba0977cafcb952cbb33a11870e2754
- opening: 60bf76995fd9ab5bb319f38fca15f6f3b3a85514
- quality: c8ce0df5e339d47b2ce4f9a48b8a8f6b4a908acf
- dashboard: 359619777ca120937f564adfa65be123c23c7cfb
- offline: 5874e1f266595b020ee1413b00f5e03d0d233e15
- diagnostics: 1cd4f7d32ac32973336f6ef7b6e296c462ab938a
- ingestion: 106be9d2872adac16cd1c07cf18d4fb1eb04c75d

Expected combined inventory: 17 main (including callback/closure) + 5 opening-range + 10 quality-audit + 5 CSV-report + 8 initial offline-guard + 9 SQL-escape + 15 ingestion-characterization = **69 tests**. Local Windows/Python 3.12.14 passes all 69 through the guarded runner. Both Windows/Linux Python 3.11 results are recorded in the PR after CI completes. Ordinary CI on this validation branch still runs 17 main tests; the separate pinned integration job runs 69.

This is a reproducible compatibility snapshot, not a general filesystem sandbox or authorization to merge. Pins deliberately do not float. Refresh them and rerun after a proposal changes; do not use old green runs to approve a new head. The workflow is path-filtered to its own config/document, plus manual dispatch, so it is not a claim that future main is continuously checked against new proposals.

## Sequential preparation requested by maintainers
No merge was performed by this agent. Maintainers merged #8 and #10 during this session; their respective main push CI passed. The remaining sequence is #6 then #7, each requiring explicit approval and renewed exact-head checks.

| Order | PR | Session-reviewed head | Expected focused diff |
|---|---|---|---|
| 1 (maintainer merged; main CI green) | #8 | 359619777ca120937f564adfa65be123c23c7cfb | One callback-message capture line + fake-provider regression tests |
| 2 (maintainer merged; main CI green) | #10 | 1cd4f7d32ac32973336f6ef7b6e296c462ab938a | Explicit diagnostic connection closure + temporary-store regression tests |
| 3 | #6 | c8ce0df5e339d47b2ce4f9a48b8a8f6b4a908acf | Standalone quality audit/CSV report, tests and documentation; no GUI/ingestion integration |
| 4 | #7 | e627de927d9d0bf4ff171a6141c0a1f25d8e9841 | Persistence write inventory and proposed provenance strategy only |

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
