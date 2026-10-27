# Research hypothesis ledger

Append originals and follow-ups separately. No empirical hypothesis is frozen or evaluated by this documentation setup. H-003 and #18 remain the authoritative proposed study design; do not duplicate or silently alter their strategy definitions.

## Original hypothesis template — HYP-<unique ID>
- Recorded-at UTC; proposed/predicted-at UTC; author; source/decision ID:
- Status: PROPOSED / FROZEN (explicit approval and freeze commit required).
- Claim and rationale; VERIFIED evidence versus INTERPRETATION:
- Expected outcome: direction, metric, units, effect/threshold, uncertainty and evaluation horizon:
- As-of data: knowledge cutoff UTC, event-time range, source/revision/receipt times, dataset hash, availability evidence, inspection history; UNKNOWN fields:
- Population/symbols/sessions; inclusions/exclusions; missingness denominators:
- Parameters, arms/baselines, costs, calendar/dependencies/code/protocol SHA; manifest/evidence location:
- Assumptions and alternatives:
- Invalidation/falsification criterion and decision rule fixed before evaluation:
- Split/holdout/freeze dates, leakage controls, stopping rule:
- Owner; open questions/blockers; approval link or NONE:
- Immutable original commit SHA (record in a later freeze entry once committed):

## Later entry template — HYP-<ID>-<event sequence>
- Recorded-at UTC; event/evaluation time UTC; author; type: FREEZE / AMENDMENT / INVALIDATION / OUTCOME / CORRECTION:
- References original ID and exact original/freeze commit; prior follow-up ID:
- New evidence as-of UTC; artifact hashes/run IDs; actual code/data/protocol SHA:
- Observed outcome and uncertainty, counts/missingness/exclusions, including null/negative results; deviations/failures:
- Comparison against ORIGINAL expected outcome and invalidation criterion:
- VERIFIED observations versus INTERPRETATION; limits and alternative explanations:
- Result: supported within scope / contradicted / inconclusive / not evaluated:
- Correction/amendment rationale and effective date; never replace original prediction or timestamp:
- Owner/next action/open questions; approval evidence or NONE:

Current state: EMPTY / NOT EVALUATED. Do not invent historical predictions from later knowledge or treat proposed study arms as proven effects.


## H-003-PROTOCOL-REGISTER — proposed study design, NOT an empirical prediction
- Recorded-at: 2026-10-27T13:20:38Z. Author: coding agent; related K-20261027-002 / ENG-20261027-004. Status PROPOSED / NOT FROZEN / NOT EVALUATED. Original EMPTY/NOT EVALUATED state above remains historical; no empirical hypothesis was invented or run.
- Canonical candidate definitions remain #18 commit eb683559a0ab685503627612ab22aa16a77066ed, blob e4f381a8fa8d8ed968e01bd501b7a95b763df38a. H-003 [replay plan](../handoff_evidence/H-003/replay-plan.md) at 403fb62d4e2a2563ec5ca9074b5460b0871502d2 reconciles those arms and proposes cost/estimand clarifications. Do not duplicate/redefine arms here.
- Expected effect/direction/magnitude, empirical invalidation threshold and actual future dates: UNKNOWN / human preregistration decision required. Synthetic suppression is implementation evidence only, not a forecast of relative arm performance. No “successful” outcome claimed.
- Proposed evaluation and assumption details: [manifest](../handoff_evidence/H-003/manifest.proposed.json); source/revision/knowledge/calendar evidence UNKNOWN; inspected code/synthetic cases disclosed. Untouched future data status NOT ESTABLISHED. No outcome access or study execution in H-003.
- Amendment: hypothetical 0/1/2/5/10-bp cost sensitivity and explicit undefined-date weighting need approval before freeze, unlike #18's existing no-cost statement. Reference separate later FREEZE/AMENDMENT/OUTCOME entries with exact IDs/commits if approved; never backdate or overwrite this proposal. Owner human research maintainer UNKNOWN; approval NONE; next action A-010 review and separate design decisions.


## H-003-PROTOCOL-REGISTER-C1 — clarification proposal, not a freeze or outcome
- Recorded-at 2026-10-27 13:43:03 UTC; author coding agent; follows H-003-PROTOCOL-REGISTER at 611b09821ae038cdfb096b05aa8c62cd34dc91bb. Source coordination review 6443196332; original evidence acceptance is not methodology approval.
- AMENDMENT PROPOSED at f5dabc9a3bfb5bd88e45b10e09e08fdfe7ab59f4, [coordination-clarifications.md](../handoff_evidence/H-003/coordination-clarifications.md), linked manifest package b64a54819da88118295602b6b2440c4371f3c71d. Original arms/parameters and prior records preserved. Common-opportunity estimand, missing-label scenario grid, uncertainty/tie/completion policy and custody requirements are candidate design details, not empirical hypotheses validated by data.
- Expected effect/superiority and untouched-data status NOT ESTABLISHED. No study executed, source availability remains UNKNOWN. Gross labels distinct from hypothetical cost proxies; neither is actual profitability. No results or invalidation threshold invented.
- Approval/freeze NONE; coordination acceptance of C1 still pending. Future changes require explicit human scope, exact approved version and separate freeze/implementation/source/execution gates. Owner A-012 coordination reviewer next; all G-H003 gates unapproved.


## H-004-AUDIT-REGISTER — interpretation amendment, NOT an outcome
- Recorded-at 2026-10-27T13:55:30Z; author coding agent. Follows H-003-PROTOCOL-REGISTER-C1 at 17a00799189b3bbc7d73a9724c26c6add6858843. Source review 6443579931 accepts C1 as DOCUMENTATION, not a frozen methodology.
- [Mathematical audit](../handoff_evidence/H-004/mathematical-audit.md) / [decision alternatives](../handoff_evidence/H-004/decision-matrix.md), immutable package 8ae184d56f33d0c1405d1642ec608c6183e37ca9, PROPOSED precision corrections. Preserve original arms/expected-effect UNKNOWN and all source gaps. Equal-label coefficient cancellation and A subset B are algebra, not predictive findings. Conditional/common reversal examples are constructed arithmetic, not evaluated synthetic-market outcomes.
- No claimed direction/effect, freeze, performance, empirical invalidation or causal result. Same common labels/exposure definitions are required assumptions; no data supplied. Future testing/estimand/policy decisions remain unapproved G-H003-1/2/3/4. Owner coordination reviewer next; status RETURNED_FOR_REVIEW, not accepted study design.


## H005-READINESS-REGISTER — engineering proposals, not research outcomes
- Recorded-at 2026-10-27 16:36:08 UTC; coding agent; follows H-004-AUDIT-REGISTER. H-004 documentation acceptance source 6444952998 preserves assumptions and requires independent A/B implementation verification. No frozen empirical prediction, effect estimate, option contract or trading claim added.
- [H-005 package](../handoff_evidence/H-005/README.md) e1d6e52eb82b79d31ff7313737c83ef6e9f09733 distinguishes existing synthetic tests, unimplemented designs and source-dependent evidence UNKNOWN. Paper readiness is design only; no option P&L/fill/market edge or performance inferred.
- Source-derived numerical-output risk is an engineering hypothesis NOT reproduced here. Proposed test-only next step requires separate explicit G-H003-3 scope; original engine/thresholds/hypotheses unchanged. No study/replay/simulation/data collection or code/test execution.
- Owner choice A/B/C pending; all G-H003-1/2/3/4 CLOSED. Reviewer/source/custody evidence missing. Status RETURNED_FOR_REVIEW / NOT IMPLEMENTED / NOT EMPIRICALLY EVALUATED. Original entries preserved; any future reproduction/outcome must be a separate dated exact-revision record.
