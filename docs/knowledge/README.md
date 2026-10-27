# Durable knowledge records

Canonical preservation index for the coding agent and coordinating/research agent. Start with [ENGINEERING_HANDOFF](../ENGINEERING_HANDOFF.md); PR #19 remains the single coordination thread. These records extend H-003, not its strategy definitions or action ownership.

## Locations
- [Dated conversation and decision summaries](conversations/2026-10-27-preservation.md): one file per UTC date/topic, stable entry IDs.
- [Hypothesis ledger](hypotheses.md): original predictions and separately appended outcomes.
- [Engineering and experiment history](engineering-history.md): exact change, execution, failure and approval evidence.
- H-003 deliverables stay at its proposed `docs/handoff_evidence/H-003/`; link them here rather than copy them. That proposed evidence directory is not created by this preservation setup.

## Required practice for both agents
1. At session start read the latest handoff, this index, relevant records and PR #19; record commit/blob read, acknowledgement, action owner and conflicts. Check for an existing ID/topic before adding records.
2. At each material decision, experiment/change, failure, handoff or session end append the relevant template below; link IDs between records. Record author/role, source session, recorded-at UTC and event-time UTC separately. Use UNKNOWN when time/evidence is unavailable; never backdate a reconstructed entry.
3. Label statements VERIFIED (with evidence and observed-at time), REPORTED (attributed source), INTERPRETATION, ASSUMPTION or PROPOSAL. Recommendations, acknowledgement, CI success and human approval are distinct.
4. Preserve original predictions, timestamps, assumptions, selection criteria and invalidation rules. Freeze by commit SHA before evaluation. Corrections, amendments and outcomes are new timestamped entries referencing the original ID and exact commit; never silently rewrite the original or erase failures. Git history alone is insufficient: link the superseding/correction ID visibly.
5. Re-fetch the current blob before writing; reconcile concurrent changes, retain one owner per action, and use the existing documentation branch/PR. Resolve conflicting accounts explicitly with evidence; do not create parallel handoff files. No automatic synchronization or agent acknowledgement is implied.
6. Link reproducible evidence by exact commit/hash and run/job URL. Keep secrets, credentials, private raw datasets and unnecessary personal information out of Git. If restricted evidence is needed, record its approved access-controlled location, hash and access owner.
7. These are concise decision rationales and evidence summaries, not private chain-of-thought exports. Do not claim to capture hidden reasoning, inaccessible chats or unobserved thoughts. Record the decision, explicit reasons, alternatives, assumptions and uncertainty that can be shared.

## Repeatable update checklist
- Unique ID/type; recorded-at UTC; event-time UTC; author/role; source session/evidence; revision read.
- Facts with verification scope; interpretations; rationale; assumptions; alternatives considered/rejected; open questions.
- Related decision/hypothesis/change IDs; owner/action/status/blocker; next evidence and approval requested/received.
- For predictions use the hypothesis template; for execution use engineering history. Leave unknown fields explicit.
- Return exact changed commit and evidence links through the handoff/PR #19. Human review and explicit authorization remain required; no merges or trading changes are authorized by a record.


## H-003 evidence return index — 2026-10-27 13:22:23 UTC
Recorded by coding agent; status RETURNED_FOR_REVIEW, not acceptance/approval. [Verification](../handoff_evidence/H-003/verification.md), [availability gaps](../handoff_evidence/H-003/availability-gaps.md), [DRAFT replay plan](../handoff_evidence/H-003/replay-plan.md), [proposed manifest](../handoff_evidence/H-003/manifest.proposed.json), [CI observations](../handoff_evidence/H-003/ci-observations.json). Immutable package commit 403fb62d4e2a2563ec5ca9074b5460b0871502d2; handoff return commit b59d8dff2cacfa95079ceea105c5f38b2b345f2a. Linked K-20261027-002 / ENG-20261027-004 / H-003-PROTOCOL-REGISTER. The earlier index's “directory not created” statement describes setup time and is superseded by this entry. Source availability and all human gates remain unresolved; no study executed. Coding agent curated this session's records; ongoing future curation ownership is not automatically assigned.


## C1 coordination-review amendment index — 2026-10-27 13:43:03 UTC
Original package coordination [acceptance](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443196332) is DOCUMENTATION ONLY, superseding prior pending status for that package. [Five clarification response](../handoff_evidence/H-003/coordination-clarifications.md), first commit f5dabc9a3bfb5bd88e45b10e09e08fdfe7ab59f4; plan/manifest linkage package b64a54819da88118295602b6b2440c4371f3c71d. C1 is RETURNED_FOR_REVIEW, not approved design/freeze. Related K-20261027-003, ENG-20261027-005, H-003-PROTOCOL-REGISTER-C1 and handoff A-012. Scheduler correction S-H003-1: actual saved ACTIVE every 30 minutes; next-run timestamp/first successful invocation UNKNOWN. All human scope/merge/source/study gates remain separate and unapproved.
