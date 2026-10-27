# Conversation and decision summaries — 2026-10-27

## K-20261027-001 — Preserve shared research and engineering knowledge
- Recorded at: 2026-10-27T13:05:00Z. Event time: current request on 2026-10-27; exact source-message time UNKNOWN. Author: preservation agent, coordinating documentation role.
- Source: user request in Codex session 01a17d76-5572-7910-ba6e-cc36db5c08c9, continuing ChatGPT conversation 6ae09c1f-15b0-83ea-90db-733bdcf63564, “Raccoon Radar Discovery Brief.”
- VERIFIED: GitHub fetch found the shared handoff at `docs/ENGINEERING_HANDOFF.md` on `docs/shared-engineering-handoff`, blob `c8016b54b926b2d0c3d353b7bffd364ce5f05817`, including H-003. Contributor instructions were read. No research study or code tests were executed by this preservation task.
- REPORTED: earlier Work sessions created PR #19 and updated H-002/H-003. Their dated PR/CI claims remain attributed historical snapshots, not newly audited code results. The cached ChatGPT preview contains inaccessible assistant reference markers; it is not a complete transcript or reasoning export.
- Decision/proposal: extend the same PR with `docs/knowledge/` and link from the existing handoff; adoption/merge pending human review.
- Rationale: durable versioned records let both agents resume with provenance while separating original expectations from later observations.
- Assumptions: both agents can read the repository branch/PR when resuming; acknowledgement still required.
- Alternatives: chat-only history risks loss of context; a second handoff risks conflicts; embedding every ledger in the work order makes it hard to maintain. Retain one handoff and linked specialized records.
- Open questions: who owns ongoing curation; which independent reviewer qualifies; what evidence-access location is approved for restricted artifacts; which study hypotheses and thresholds will be authorized/frozen.
- Owner/action/status: both agents follow the preservation templates on their next authorized work; READY_FOR_REVIEW. No recipient acknowledgement or empirical outcome is claimed.
- Scope: documentation only; preserve existing H-003 gates. No merges, provider connections, database access or trading changes.

## Template — append a new entry
### <K-ID> — <topic>
- Recorded-at UTC / event-time UTC (UNKNOWN if unavailable); author/role; source session/link; revision read:
- VERIFIED facts + evidence/observation time:
- REPORTED claims + attribution; INTERPRETATIONS:
- Decision/status; explicit rationale; assumptions:
- Alternatives and why selected/rejected:
- Open questions; related hypothesis/change IDs:
- Owner/action/status/blocker; next evidence; approval evidence or NONE:
- Corrects/supersedes ID + original commit, if applicable (preserve original):


## K-20261027-002 — H-003 coding-agent evidence return
- Recorded-at: 2026-10-27T13:20:38Z; event interval this authorized session, starting observed 2026-10-27T13:13:39Z. Author: coding agent; source: explicit user request to begin H-003 and return documentation in PR #19. Read handoff branch f4930346019bfcb1ca2a633b8c09c5bcad8facbe, blob 0e6d3819a8c237caf535edc22849f670ba3a2e69 and knowledge records.
- VERIFIED: exact package commit 403fb62d4e2a2563ec5ca9074b5460b0871502d2; [evidence root](../../handoff_evidence/H-003/verification.md). All five files fetched back and matched; two JSON files parsed. Existing CI job logs independently show main 69, #13 97, combined #14 115, #17/#18 69 tests per Windows/Ubuntu job; exact merge checkouts in verification.md, not inferred from run head. No new code/study execution.
- INTERPRETATION: CI closes the missing checkout-identity evidence gap for those historical jobs, not independent review/provider semantics. Historical revision availability and source scope remain UNKNOWN. Synthetic CSV invalid clock strings are recorded, unchanged.
- PROPOSAL: reconcile #18 grid/delay/daily/pair design, cost sensitivity and undefined-date weighting clarification in replay-plan.md. These require approval and are not predictions or validated findings.
- Rationale: preserve scope-bound evidence and explicit blockers; alternatives were inferring semantics or running final-series replay, both unsupported. A-006–A-009 RETURNED_FOR_REVIEW; A-010 coordination review pending; A-011 independent reviewer unassigned.
- Decisions/approvals: documentation/read-only preparation authorized by user; all merge, provider/data acquisition, implementation and study approvals NONE. Owner next: coordination reviewer reconciles; human maintainer decides each gate. No protected PR changed.
