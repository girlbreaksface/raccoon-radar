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
