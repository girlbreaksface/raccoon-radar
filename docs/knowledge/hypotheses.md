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
