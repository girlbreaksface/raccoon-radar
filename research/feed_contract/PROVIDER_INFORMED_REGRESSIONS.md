# Issue #46 provider-informed regression evidence

## Scope and source
Stacked on draft PR #49 at `90b883ba33d44ad0b3ca6a8d27aeef6eb57c9918`; frozen #48 baseline `6c3acba2f22d582cbe9102d9e9aea3f12b31b62d` and its archive are unchanged. Test-only implementation directly authorized in the coding chat. No runtime changes.

Scenario source: [issue #46 support-response summary](https://github.com/girlbreaksface/raccoon-radar/issues/46#issuecomment-6594564671). This is attributed secondary evidence; the private email and capture were not accessed or copied. The comment labels its response 2026-11-03; this session's client date is 2026-11-02. Preserve that source date as reported, not as independently verified chronology.

Support reportedly describes end labels, revisions without guaranteed delivery order, no authoritative final flag, a one-second heuristic, current-date forward-adjustment reference, and NASDAQ-only real-time versus post-market consolidated history. Endpoint/version pinning, interval inclusivity, DST/early-close rules, correction horizon and factor version identifiers remain unresolved.

## What the 11 new tests establish
- Raw opening, closing, early-close-like and DST-adjacent labels remain exact strings, with no implicit shift or canonical interval authority.
- SPY/QQQ older labels can arrive after newer labels, with changes to all OHLCV/turnover fields and preserved receipt ordering.
- A later-arriving stale value is last observed, not authoritative truth; no greatest-label/latest-value truth claim.
- Inclusive receipt-time and sequence cutoffs exclude later revisions from earlier observation snapshots.
- One second after the next label, arbitrary later evaluation, identical repeats and a clean local seal never promote finality or completeness.
- Source payload bytes and sealed fixture files are unchanged by replay; caller mutations do not affect later reads.
- Test-only feed/endpoint/adjustment-anchor metadata survives observation deltas, without certifying feed equivalence, factors or provider accuracy.
- Repeat replay/quality outputs are deterministic and strict JSON.

These are passing characterization/safety regressions on existing behavior, not a behavioral repair; no deliberately failing production test is claimed. The injected decoder reads invented JSON. Journal's inherited payload-kind field remains SDK_PROTOBUF_SERIALIZATION, but fixture manifest explicitly says SYNTHETIC_JSON_NOT_PROVIDER_PROTOBUF. No SDK or genuine protobuf decoding is tested. fixture_* fields are invented metadata, not asserted wire fields. Cross-feed deltas are observations, not adjudicated provider errors or a safe production reconciliation implementation.

The date strings are deliberately not calendar-validated: neither DST mapping nor early-close eligibility is established. No end-label-to-interval adapter is implemented. Receipt-as-of is not market-event time or original historical availability. Whole-seal validation still examines later records before returning a prefix; a corrupt later record can block earlier replay by design.

## Reproduction
Use an SDK-free Python 3.11/3.12 environment with tzdata available:
```text
python -I -B research/feed_contract/run_checks.py
python -I -B offline_checks.py
python -I -B research/reconciliation/run_checks.py
python -B research/reconciliation/verify_evidence.py
python -m compileall -q .
```
Existing fake-feed CI automatically discovers the new test file on Windows/Linux, Python 3.11/3.12; no workflow changes needed. Other inherited workflows run broader/reconciliation/presentation checks.

Local Windows Python 3.12.14: baseline feed 85 PASS; new feed 96 PASS (85 inherited + 11 new); exact-byte reconciliation 54 PASS and 88 variants reproduced. Broader suite and final CI details are returned in the PR conversation after completion.

Local setup limitation preserved: initial text snapshot assembly added/normalized newlines, causing one vendor-hash regression and evidence reproduction to fail. Restoring the exact pinned UTF-8 source bytes resolved both without modifying archived evidence or assertions. An initial restore attempt used Windows default decoding and failed before writing; explicit UTF-8 corrected it.

## Gates
PROVISIONAL / UNKNOWN / DATA_BLOCKED; completeness NOT_ESTABLISHED. No provider contact, market acquisition, strategy integration, real historical study, production database access, raw-data rewrite, order API, deployment or merge. All live trading stays disabled. Independent review and exact-head merge authorization remain separate.
