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
