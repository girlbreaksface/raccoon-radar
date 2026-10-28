# H-009 — synthetic consumer integration evidence

Recorded 2026-10-28 15:36:37 UTC. Status: REPRODUCED_CONSUMER_CONTRACT_FAILURES / RETURNED_FOR_REVIEW / NOT MERGE READY. Direct human “yes” in coding chat approved exact test-only H009 scope. GitHub work order6473280473 supplies context; it was not substituted for direct approval. No production fixes authorized.

## Immutable integration
[Draft PR22](https://github.com/girlbreaksface/raccoon-radar/pull/22), branch test/h009-direction-consumer-contract, head ae3fda66055733bde371e1b0d7887f8157cf8c7f, base repair PR21 48e184c67168724b1449ac8c36d209d4a2d72892. Base retains root direction_engine.py blob8a4d091a24e2ea6f80e4d24b14dcebd400cf3586. Pinned PR14 328135f2695543cde96bb434aaa07201c51c0582 replay source copied byte-for-byte to tests/fixtures/h009/direction_validation.py, blob4eeaa8c1fdb595134096fa5ac13f52f8ecf82392. Test loads fixture via importlib; replay imports repaired engine from base. No root production source or protected PR branch changed. This is a test assembly, not an approved integration or retarget.

Only two added files,320 lines: fixture178 and test_h009_consumer_integration.py142, test blob66c753a5d259f92b3843b114c439cd3427a69006. Fixture creation8154517ccbc3a1307c71caf33cc864fb46501629; test commit ae3fda66055733bde371e1b0d7887f8157cf8c7f. Remote fixture blob exact equality and local test blob verified. Source identity regression checks both fixture and engine (normalizes CRLF only for Windows checkouts). H006test unchanged c5c8c5aa5d611396696ec7afa11394aa021723c3.

## Exact synthetic scenarios and results
Full executable fixtures/assertions at [pinned test source](https://github.com/girlbreaksface/raccoon-radar/blob/ae3fda66055733bde371e1b0d7887f8157cf8c7f/test_h009_consumer_integration.py). No real market input.

- Actual producer/replay:25 coherent minutes09:30–09:54, interval ends/availability+1minute, complete=True, explicit SYNTHETIC mapping, SPY2026-10-23. Price0.01+i*0.0001, open=close, high/low +/-0.000025. Prior24 volumes1e-200,current1e200. Final snapshot READY/EVALUATED, volume_confirmed=True, volume_ratio=None, signal NO TRADE,reasons[VOLUME_RATIO_OVERFLOW]. Events=[], no fabricated outcome. Recursive finiteness, strict JSON roundtrip and original input equality PASS.
- Actual synthetic study: same fixture on2026-10-21 train and2026-10-23 test, trainThrough21/testStart23/testEnd23, explicitly synthetic freeze identifier and exact combined code references. Both buckets events=[],valid_outcomes=0,missing_outcomes=0, overflow reasoncount1. Deterministic complete output, strict JSON and immutable inputs PASS. These function calls are unit tests, not historical study execution or a real research freeze.
- Routing/cooldown fake evaluator: two canonical synthetic intervals09:54–09:55 and09:55–09:56. Actual overflow result returned first; actual benign producer result (prior100/current200 =>ratio2,BULLISH CANDIDATE) second. Compare with ordinary NO TRADE first. Exactly one event known09:56 in both; rejection consumes no cooldown. Candidate has no forward horizon, so explicit missing label retained, not synthesized. PASS. Fake evaluator isolates consumer routing; not a claim the selected two-row feature frame itself warms up the engine.
- Known bullish/bearish enum routing controls PASS; no modeled returns claimed.
- UNKNOWN_H009_SYNTHETIC fake signal with otherwise benign READY/EVALUATED result: expected no events; observed one event admitted at09:55 with unknown string preserved. FAIL. This fixture has an incomplete outcome horizon, so directional_etf_move_pct=None. It proves invalid-event admission, NOT an observed bearish numeric outcome; source line89 shows the non-bullish else branch would assign -1 when a valid horizon exists. Current engine does not emit this fake enum.
- Missing signal key: expected explicit fail-closed result/no events; observed KeyError('signal') at copied replay line62. Assertion intentionally converts crash to failure; FAIL preserved. This is injected schema-contract evidence, not an observed malformed result from current engine.

Before expectations fixed as assertions; no production change, so no after-fix green result exists. No expectedFailure/skip/assertion weakening. Five new tests pass, two fail; inherited107 pass. The failing artifact is intentionally red.

## Executed validation
Local Windows11 build26200, CPython3.12.14: python -B offline_checks.py,114run/112pass/2FAIL,1.245s. Local log SHA256225d400d32eff83f960171ce3de5a012a0e818f88d363915bc2effe4c260a44d; exact test source SHA256b74692a3dc79cf590ab76a875f309dd26b5d3910a6ad59c5823f62fe4331fe9f. Focused seven first:5PASS/2FAIL. Log kept locally, no user DB accessed.

[CI run40717552033](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40717552033), actual tested checkout f2a8454fbc96e587a03976c5507534d14b6671b7. Logs explicitly merge head ae3fda66055733bde371e1b0d7887f8157cf8c7f into base48e184c67168724b1449ac8c36d209d4a2d72892.

| Platform | Python | Job | Compilation | Guarded tests |
|---|---|---|---|---|
| Windows |3.11.9|[122919248024](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40717552033/job/122919248024)|PASS|114run/112pass/2FAIL,4.128s|
| Ubuntu |3.11.17|[122919248509](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40717552033/job/122919248509)|PASS|114run/112pass/2FAIL,1.959s|

Both logs read and confirm same named failures: test_unknown_signal_is_rejected_not_routed_as_bearish and test_missing_signal_fails_closed_without_exception_or_event. Windows log was initially unavailable while running, then successfully fetched after completion; no false pass inferred.

## Boundaries and next decisions
H008 static-risk finding is now reproduced with injected consumer contracts, while H007 actual overflow integration passes. Independent qualified review is still missing. H009 does not authorize a repair, merge, retarget or readiness promotion. Proposed next bounded task, only after separate approval: explicit candidate-enum allowlist and defined malformed-result disposition in replay, keeping rejection/cooldown/reason evidence; preserve original red artifact.

PR13/14/20/21 pins unchanged; no provider/market history, production DB/schema/raw-data rewrite, ingestion/UI/calculation-threshold/strategy/trading/order changes. Existing guarded suite creates disposable synthetic DB fixtures only. No real historical replay/study or simulated trades/orders. No predictive-edge, timing-semantics or arbitrary-input correctness claim. Source/custody/design/independent-review/merge gates remain distinct and pending.
