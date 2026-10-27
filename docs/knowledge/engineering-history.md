# Engineering change and experiment history

Append a new event for each material change, experiment, CI failure/rerun, review/approval or correction. Link existing PR/CI evidence rather than copy mutable status as timeless truth.

## ENG-20261027-001 — Preservation documentation setup
- Recorded-at: 2026-10-27T13:05:00Z. Author: preservation agent. Event time: this documentation session.
- Related decision: K-20261027-001. Branch: `docs/shared-engineering-handoff`; PR: [#19](https://github.com/girlbreaksface/raccoon-radar/pull/19).
- Change: add canonical knowledge index, dated summary, hypothesis and engineering templates; append handoff pointer. Documentation only.
- Starting handoff blob inspected: `c8016b54b926b2d0c3d353b7bffd364ce5f05817`. Resulting commit/verification: record in a separate follow-up once writes complete.
- Experiment/data execution: NONE. Code tests: NOT RUN (Markdown-only change); created paths/content must be fetched back.
- CI: UNKNOWN for this new documentation revision until inspected; earlier handoff CI is not evidence for this revision.
- Approvals: user authorized documentation; human merge approval NONE; independent review not claimed.
- Failures: initial direct fetch of absent `docs/knowledge/README.md` returned 404 before creation; expected discovery result, not CI failure.
- Outstanding: verify committed content/paths and handoff link; recipient acknowledgement and human review pending. Trading systems unchanged by scope.

## Event template — ENG-<unique ID>
- Recorded-at UTC / event-time UTC; author/owner; source session; event type/status:
- Related decision/hypothesis/experiment IDs; purpose and explicit rationale; assumptions/alternatives:
- PR URL; branch; base/head SHA; actual tested checkout/merge SHA; diff/files:
- Experiment ID; original hypothesis/freeze commit; code/config/data/manifest hashes; environment/dependencies/seeds:
- Commands actually run; CI workflow/run/job URLs; OS/Python; results/counts and observed-at UTC:
- Failures/cancellations/missing evidence; reproducible error/log location; limitations and remediation:
- Human approval/review identity, scope, exact approved SHA, timestamp/link; NONE or UNKNOWN where absent:
- Interpretation versus verified facts; open questions; owner/action/blocker/next evidence:
- Follow-up/correction/superseded event ID + original commit; preserve prior result, including failed runs:

A self-referential commit SHA cannot be embedded in its own content. Pin the resulting commit in a subsequent event or PR evidence; do not invent one. CI success, review, human authorization and merge/deployment are separate events.

## ENG-20261027-002 — Saved-path verification
- Recorded-at/event-time: 2026-10-27T13:08:00Z (approximate minute; verification occurred during this session). Author: preservation agent.
- References: ENG-20261027-001, K-20261027-001.
- VERIFIED at commit `fb545f12769a6d9b3af25878fe08ac388a0ea3f5`: fetched all four knowledge files and compared exact text to intended contents; all matched. Fetched handoff and confirmed relative knowledge-index link.
- PR #19 changed-file inspection showed only Markdown documentation: handoff and four knowledge records. No code/trading changes in this PR inspection.
- CI for this revision: UNKNOWN/not audited. No tests executed. Human merge approval NONE; no merge performed. Recipient acknowledgement pending.
- Outcome: documentation paths verified; ongoing record curation and human review remain open. This follow-up records verification separately from the original setup expectation.

## ENG-20261027-003 — Timestamp correction
- Recorded-at: 2026-10-27T13:07:23Z, verified UTC clock observation. Author: preservation agent.
- Corrects ENG-20261027-002 at commit `953b3004d47fd7a1a7d4aba67f8565929e599cd7`: its approximate 13:08 timestamp was entered ahead of the observed clock. Actual exact verification time is UNKNOWN; verification completed before 13:07:23Z in this session.
- Rationale: preserve the original while explicitly correcting an estimated timestamp; verification results remain unchanged. The original entry is retained.


## ENG-20261027-004 — H-003 documentation evidence package
- Recorded-at: 2026-10-27T13:20:38Z; event-time interval 2026-10-27T13:13:39Z through this observation; author/owner coding agent, actions A-006–A-009, status RETURNED_FOR_REVIEW (not accepted/approved).
- Starting branch commit f4930346019bfcb1ca2a633b8c09c5bcad8facbe, handoff blob 0e6d3819a8c237caf535edc22849f670ba3a2e69. ACK commit 38532d6c38b3d47f759b491969209b32b6c2d3a1. Package final commit 403fb62d4e2a2563ec5ca9074b5460b0871502d2; [verification](../handoff_evidence/H-003/verification.md), [gaps](../handoff_evidence/H-003/availability-gaps.md), [plan](../handoff_evidence/H-003/replay-plan.md), [manifest](../handoff_evidence/H-003/manifest.proposed.json), [CI evidence](../handoff_evidence/H-003/ci-observations.json).
- VERIFIED by GitHub readback: exact file contents and Git blobs, JSON parse, only docs paths in main-to-package diff. See verification.md for per-file blob IDs/source/tested commit identities. Runtime behavior impact NONE. Local code tests NOT RUN in H-003; existing hosted compilation/guarded logs read, counts verified rather than rerun. New PR #19 documentation CI is pending final revision inspection, not covered by protected PR jobs.
- Failure/discovery: wrong initial docs/INGESTION_CHARACTERIZATION.md lookup was absent; tree located correct docs/CANDLE_INGESTION_CHARACTERIZATION.md. No mistaken-path file created. Earlier branch/file-commit ambiguity resolved by fresh reads; return append preserves that correction.
- Research execution: NONE. Data access: repository text/synthetic fixtures only; no user stores/provider/network adapters. Late revision, calendar and source evidence gaps remain UNKNOWN. Cost appendix is hypothetical proposal; no outcomes/profitability reported.
- Human independent review/merge approval: NONE. #13/#14/#17/#18 unchanged. Next evidence: coordination reviewer A-010 accepts or returns docs, human owner A-011 identifies independent maintainer, then separately scoped contract/implementation/source/freeze approvals. Related K-20261027-002 and H-003-PROTOCOL-REGISTER.


## ENG-20261027-005 — five-point documentation amendment and scheduler correction
- Recorded-at: 2026-10-27 13:43:03 UTC; author coding agent; user-authorized documentation-only review response. Starting head fc96e0349441508b3d04cd45ac15083131e43ce8; original package 403fb62d4e2a2563ec5ca9074b5460b0871502d2 unchanged at that revision.
- Source [coordination review](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443196332) ACCEPTS original package as documentation only, not independent code/design approval. Corrects ENG-20261027-004's pending-review status by new evidence rather than rewriting it.
- Added coordination-clarifications.md commit f5dabc9a3bfb5bd88e45b10e09e08fdfe7ab59f4; plan/manifest append linkage package b64a54819da88118295602b6b2440c4371f3c71d. Five topics: revision/clock bounds/ties/watermarks; common opportunities and missing-label sensitivity; daily/peer truth-table denominators; prospective custody/freeze/access; gross versus cost proxies. No arms/production formulas changed, no study executed.
- Validation: new files/content require exact readback and JSON parse; final-head Windows/Linux CI will be linked in PR #19 after inspection. Local code tests NOT RUN for this documentation task. Existing H-003 job evidence remains scoped to its original checkout, not new design behavior.
- Scheduler: app confirmed creation ACTIVE. Initial create lacked required destination and was rejected; retry destination=thread succeeded. Actual saved recurrence readback every 30 minutes, contradicting submitted hourly intent; correction reported, cadence not changed. No local automation directory initially existed; it appeared after creation. Runtime next-run timestamp and successful invocation evidence UNKNOWN. No research stores opened; bounded read-only scheduler state/schema inspection found no next-run field; connections explicitly closed. No ChatGPT desktop UI automation performed.
- Limitations/approval: C1 pending coordination/design review, source availability UNKNOWN, independent reviewer absent, all G-H003 approvals NONE. Record first genuine scheduler run later; manual execution is not proof. Related K-20261027-003 / H-003-PROTOCOL-REGISTER-C1; next owner coordination reviewer. Protected PRs, ingestion, trading, DBs and raw research untouched.


## ENG-20261027-006 — H-004 algebra/units documentation
- Recorded-at 2026-10-27T13:55:30Z; owner coding agent. Starting head cbd49fe9ec1b72c04249c499d42d7bbff23e07e1; C1 blob 10b7844a2c8d5c910f9c92e9c31fc31092b0906f. Source [coordination acceptance and H-004](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443579931), superseding ENG-20261027-005 pending C1 review only, not approvals.
- New docs: mathematical-audit.md first commit 03a1c5d3a051e06e1d82aae31c84a0f724725e27; decision-matrix.md/package 8ae184d56f33d0c1405d1642ec608c6183e37ca9. Algebraic/tiny constructed counterexamples only; no code/test implementation, simulation or empirical output. Original C1 untouched except later cross-reference; hypotheses not frozen or evaluated.
- Mathematical findings: intended N=2|E|, identical-label coefficient cancellation, general box sum|c| and faithful-subset simplification, tipping point contribution-vs-return units, cost exposures and conditional/common sample reversal. Additional future test/wording requirements, not production behavioral fixes.
- Read-only manual refs/CI snapshots show no drift and completed-success existing protected runs; no local code test rerun. Final-head docs CI/readback results to be pinned in PR #19. Source, access custody and independent reviewer remain UNKNOWN. No error/failed test newly observed in this derivation session.
- H-004 scheduled-run condition not satisfied by this manual request; saved 30-minute ACTIVE cadence is not invocation evidence. No successful scheduled run or actual next timestamp verified. Owner coordination reviewer accepts/returns docs; human maintainer chooses alternatives and reserved gates, all unapproved. No protected PR/DB/provider/ingestion/trading/study change.


## ENG-20261027-007 — H-005 documentation/read-only source audit
- Recorded-at 2026-10-27 16:36:08 UTC; coding agent; explicit human H-005 documentation authority, no runtime/test authority. Start head f723f24be8353e7be1d77aaa0da4ab0b95ae65f5. H-004 documentation acceptance at [6444952998](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6444952998), not independent code or gate approval.
- Six new Markdown evidence files under docs/handoff_evidence/H-005/, immutable package e1d6e52eb82b79d31ff7313737c83ef6e9f09733. Exact readback MATCH; source/test Git blobs, commands as reviewer recipe, existing CI run/job/checkouts/Python/counts in package README. No tests, code, provider, research store or application path executed by H-005.
- Existing logs re-inspected: main69, #13 97, combined #14 115, #17/#18/#19 baseline69 tests each Windows/Linux, compilation success. These are historical executions, not validation of proposed controls or final H-005 head. Final docs CI pinned in return notice after inspection.
- Coverage gap: finite observation serialization and malformed-canonical-input edge contracts; risk review identifies ratio outside finite guard, NOT a reproduced defect. No failing fixture/test, behavioral fix or code change created. Source-dependent contracts and all paper/order risk controls remain unimplemented/unverified in inspected scope.
- Decision PROPOSED: owner may separately approve isolated test-only alternative A or B; otherwise hold. Roadmap not executed, no bugs “fixed” by writing docs. Reviewer and actual source/custody UNKNOWN, all G-H003 gates CLOSED.
- No new test failure observed because no tests run; no provider errors reproduced. Manual session only; prior heartbeat messages are not evidence of fully completed scheduled workflow. Related K-20261027-005 / H005-READINESS-REGISTER; coordination reviewer next, human alternative decision pending.


## ENG-20261027-008 — failing H-006 test artifact, no repair
- Recorded-at 2026-10-27 19:43:15 UTC; coding agent; direct human limited H-006 test-only authority. Original risk ENG-20261027-007 was UNREPRODUCED and remains preserved; this later entry records observed outcome.
- Source #13 6e7d1a8804b14aba9d08302bc5db48f31b0706ae, engine blob09497b013d65aebaa9f77f47212079f35445b74b. Test-only branch/PR20 commit b4f0d14b9b83500337d5dd6375bcbf279142c6ba; added file blobc5c8c5aa5d611396696ec7afa11394aa021723c3. Diff one new test; no existing edits.
- Local Windows3.12.14: initial setup two97/28-error incomplete dashboard-source attempts; final44source blobs byte-verified, baseline97PASS. New4 tests:2PASS,2FAIL; full101/2FAIL; compilePASS. Exact pinned rerun log hash35debf8f731524553df1a8c3a82bc87a0dc8b1c03d3b6c86079a0c9f9da5df52. No failing evidence erased.
- CI40570969484 Windows3.11.9/job122424733054 and Ubuntu3.11.17/job122424732818: compilationPASS;101/2FAIL each, checkout89512d771479eb79869e3d8df69352174e46ce4b. Evidence package a689fb61c8c0df8f85800a28b90de031a17b79d7 at docs/handoff_evidence/H-006/, readback matches/JSONvalid. Windows/LF source-byte hashes separately retained.
- VERIFIED inf ratio/strictJSON failure for finite synthetic extreme volumes; NO TRADE+READY output, not emitted candidate. No real/provider data or economics inferred. Assertions retained; no skips/expectedFailure/numerical clamps.
- Status REPRODUCED_FAILURE, PR20 NOT MERGE READY. No source fix authorized or made; H006-FIX separate owner decision. No productionDB/provider/order/replay/study/merge/retarget/threshold/strategy changes. Existing guarded baseline's temporary synthetic DB fixtures only; new tests pure. H-005 documentation acceptance recorded separately from code authority.
