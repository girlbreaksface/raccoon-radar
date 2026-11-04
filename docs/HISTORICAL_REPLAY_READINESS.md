# Historical replay and paper-readiness follow-up

## Scope and decision log — 2026-11-04

Inspected the open PR stack before implementation. #69 supplies the automation
foundation at 1d2bdedbc6237cbc8c70d9ba083579fe2e813fd9. #68 independently supplies
the offline historical replay at f69f97dfaa8e38e4cfbff84a6a96bd53e2ae7483.
This separate development PR targets #69 and brings #68's four replay/doc/evidence
files into that stack. Its two timezone workflow edits are already covered by
#69's pinned fallback and were not duplicated. Neither source PR is merged,
retargeted or modified. This is a combined development proposal, not permission
to integrate into main. The broker pilot branches #65–#67 are not included.

The original #68 description, documentation and 205-test Windows log are retained
as historical evidence, not this revision's validation. Provider feasibility
findings in that document are inherited documentation findings; no new provider
probe, account access, data purchase or market-data retrieval was performed here.
The six frozen historical sessions and research/risk parameters remain unchanged.

## Reproduced chronology defect and correction

Two new regressions failed against #68's engine: after an entry and one valid
non-triggering quote, a later quote with an earlier or repeated observation stamp
could close the fictional trade profitably. Availability order alone did not
establish an ordered underlying observation path.

The replay now requires each accepted exit observation stamp to be strictly later
than the preceding observation stamp. A duplicate/backward stamp leaves the
position UNRESOLVED with NONMONOTONIC_EXIT_OBSERVATION; no net P/L is supplied,
and a later winning quote cannot rescue it. Existing NONCAUSAL_EXIT_QUOTE checks
still handle observation stamps at/before entry availability. This conservative
offline policy requires future independently verified as-of handling before
out-of-order provider observations can be used. It is not a claim that a provider
cannot legitimately deliver delayed or repeated updates.

Input schema remains historical-options-replay-v1; engine_version is now
historical-options-replay-v1.1. Source/run hashes and the new field distinguish
the changed execution semantics. Valid ordered paths, cost parameters, entry
ranking, signal calculations and risk limits are unchanged.

## Automated rehearsal evidence

historical_replay_checks.py reuses the explicitly fictional regression fixture
and runs ten bounded scenarios: target, stop gap, exact cutoff, missing cutoff,
invalid path, regressed observation, duplicate observation, stale entry, late
metadata and entry-budget rejection. Each has all four paired variants, a checked
expected outcome and byte-identical repeated runs. The 40 variant rows comprise
12 CLOSED, 16 UNRESOLVED and 12 REJECTED modeled outcomes. They are not 40
independent trades, real observations or strategy-performance samples.

The guarded tool writes historical-replay.json with complete inputs, runs,
parameters, hashes, outcomes and an informational paper assessment. The parent
automation runner independently validates the artifact against current-code
recomputation before accepting the check. A zero child exit code with missing,
malformed, tampered or incomplete evidence fails. Repairing a hash after changing
profit, removing a scenario or forging readiness cannot pass this validation.
These hashes establish internal consistency, not external provenance or immunity
to an attacker who can modify the code and its tests together.

The assessment distinguishes evidence_integrity PASS from quote_path_gate
BLOCKED_UNRESOLVED. An expected failure-handling scenario can pass regression
tests while leaving the fictional position unresolved. No metric converts that
position into a close, zero loss or readiness approval. A VERIFIED_QUOTES label
remains a supplier assertion; it cannot release any gate, even after recomputation.

The six paper-specific gates preserve #68's inventory: repository integration /
Phase 25 equivalence; broker reconciliation; production VWAP/warmup; real costs;
historical validation; paper authorization. All remain HOLD. #69's six consolidated
engineering categories remain in readiness.json; these are two views of related
blockers, not twelve independently audited gates. Historical 224/224 assertions
and 1500/1500 cycles remain USER_REPORTED_NOT_REPO_CI.

## Reproduction and operational boundaries

```text
python -B automation_foundation.py --output work/a-new-evidence-directory
python -B historical_replay_checks.py --output work/a-new-rehearsal.json
```

The output parent must exist for the standalone tool. Both commands refuse to
overwrite evidence. CI runs the combined root suite, isolated feed/reconciliation
suites, exact 88-case evidence reproduction and the guarded historical rehearsal
on Windows/Linux Python 3.11/3.12, uploading diagnostics even on failure.
Current results belong in this PR description and its exact-head CI artifacts;
the older 205-test log remains scoped to #68. Offline tests do not establish
production GUI, provider, broker, empirical holdout or profitability validation.

Paper execution HOLD; live NO-GO; orders DISABLED; merge/deployment HOLD. The
assessment is an informational audit, not an execution interlock or authorization
token. No broker SDK, order/capture calls, account access, user databases,
migrations, risk-limit changes, notification hooks or deployments are introduced.
Routine diagnostics remain in CI artifacts. Only an action requiring separate
authorization should interrupt the owner. No approval is requested by this work.

Rollback closes this separate PR; neither source branch nor any store is changed.
