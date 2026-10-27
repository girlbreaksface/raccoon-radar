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
