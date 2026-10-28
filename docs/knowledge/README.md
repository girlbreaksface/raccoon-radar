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


## H-004 documentation audit index — 2026-10-27T13:55:30Z
[C1 coordination acceptance/H-004](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443579931) supersedes earlier pending C1 status as documentation only. [Mathematical audit](../handoff_evidence/H-004/mathematical-audit.md) and [maintainer decision matrix](../handoff_evidence/H-004/decision-matrix.md), package 8ae184d56f33d0c1405d1642ec608c6183e37ca9, RETURNED_FOR_REVIEW. No empirical study or implementation. K-20261027-004 / ENG-20261027-006 / H-004-AUDIT-REGISTER preserve interpretation corrections and all open gates. A manual pin snapshot is not a successful scheduled invocation.


## H-005 readiness/risk evidence index — 2026-10-27 16:36:08 UTC
Direct human authorization in coding chat covers docs/read-only H-005 only. [Package index](../handoff_evidence/H-005/README.md), [blocker map](../handoff_evidence/H-005/dependency-blocker-map.md), [#13 reviewer packet](../handoff_evidence/H-005/pr13-reviewer-packet.md), [coverage audit](../handoff_evidence/H-005/test-coverage-gaps.md), [paper checklist DESIGN ONLY](../handoff_evidence/H-005/paper-readiness-design.md), [roadmap NOT EXECUTED](../handoff_evidence/H-005/implementation-roadmap.md). Immutable package e1d6e52eb82b79d31ff7313737c83ef6e9f09733; six-file exact readback match. H-004 documentation [acceptance](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6444952998) now recorded with qualifications, no gate approval. H-005 RETURNED_FOR_REVIEW; owner alternative A/B/C decision pending, all G-H003 gates closed. K-20261027-005 / ENG-20261027-007 / H005-READINESS-REGISTER. Current session manual, not completed scheduler-run evidence.


## H-006 test-only reproduction evidence — 2026-10-27 19:43:15 UTC
[Results](../handoff_evidence/H-006/results.md), [synthetic observation archive](../handoff_evidence/H-006/observations.synthetic.json), [CI evidence](../handoff_evidence/H-006/ci-evidence.json), [local setup/failure summaries](../handoff_evidence/H-006/local-log-summaries.json). Immutable package a689fb61c8c0df8f85800a28b90de031a17b79d7. [Draft #20](https://github.com/girlbreaksface/raccoon-radar/pull/20) test commit b4f0d14b9b83500337d5dd6375bcbf279142c6ba is deliberately failing/NOT MERGE READY. Finite schema-valid synthetic volume extremes reproduce inf ratio and strict JSON rejection on both Windows/Linux; not market realism/edge. Direct human test-only approval resolves earlier H-006 authorization blocker, but NO FIX authorized. H-005 accepted as documentation-only (review6448015492); no other gates reopened. K-20261027-006 / ENG-20261027-008 / H006-NUMERIC-OUTCOME preserve original risk and later reproduced evidence separately.


## H-007 isolated repair return — 2026-10-28 01:14:42 UTC
Direct human exact H-007 repair approval in coding chat supersedes prior no-fix state ONLY for this scope. [Results](../handoff_evidence/H-007/results.md), [synthetic outputs](../handoff_evidence/H-007/observations.synthetic.json), [CI](../handoff_evidence/H-007/ci-evidence.json), [local checks](../handoff_evidence/H-007/local-checks.json), immutable package 3428d73af2c55bd502e6b516c4de8a6fc0c30c18. [Draft PR21](https://github.com/girlbreaksface/raccoon-radar/pull/21) head48e184c67168724b1449ac8c36d209d4a2d72892: overflow ratio null + explicit NO TRADE reason, finite calculations unchanged; unchanged H006tests + six boundaries,107PASS each Windows/Linux. Original PR20 still expected red. K-20261028-001 / ENG-20261028-001 / H007-NUMERIC-REPAIR-OUTCOME; [UTC-date conversation record](conversations/2026-10-28-h007.md). Independent review and merge/source/study gates remain open, no merge authorized. UTC record date28 corresponds to Oct27 evening America/New_York.
