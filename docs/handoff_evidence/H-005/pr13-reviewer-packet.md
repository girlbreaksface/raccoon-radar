# H-005 — independent technical reviewer packet for PR #13
Review target [PR #13](https://github.com/girlbreaksface/raccoon-radar/pull/13) **6e7d1a8804b14aba9d08302bc5db48f31b0706ae**; base main **b0ad02dc996b00406e7da08fb33b6382f658ea40**. Engine blob 09497b013d65aebaa9f77f47212079f35445b74b. Reviewer identity, qualifications, willingness, access and authorship independence all UNKNOWN; no review requested/assigned here and no signoff claimed. This packet supports, not replaces, independent review.

## Architecture and exact scope
Standalone standard-library direction_engine.evaluate(rows, symbol/session/as-of/evidence/config) -> new dictionary. Frozen Config, SMA-seeded session-reset EMA9/21, session HLC3 candle-volume proxy (NOT trade VWAP and distinct from dashboard OHLC4 proxy), prior-20 relative volume, first-15 OR, prior-five breaks and previous-EMA touch/rejection geometry. Output is BULLISH CANDIDATE / BEARISH CANDIDATE / NO TRADE with observations/quality/reasons/hash.
No GUI, provider, order, file/network/SQLite call in this module. It accepts caller-supplied canonical intervals and whole-second naive ET strings. VERIFIED is a caller assertion, not source verification. Raw timestamp nonempty strings retained unchanged; raw mapping never inferred.

PR adds engine, test_direction_engine.py (19 tests), test_direction_math_review.py (9), docs/DIRECTION_ENGINE.md and docs/DIRECTION_ENGINE_REVIEW.md. Main 69 + 28 = 97. No existing production ingestion, calculations, persistence or GUI file changed. Material scope/head changes require renewed review.

## Reproducible check procedure — instructions only, not executed in H-005
Use a NEW isolated checkout without user databases/credentials; never copy/open production research stores or launch a dashboard. Verify remote repository and full expected SHA before commands. The existing guarded runner contains test safety controls, not a general filesystem/security sandbox.
```text
# In a fresh isolated repository checkout of the exact review candidate:
git rev-parse HEAD
python --version
python -m compileall -q .
python -B offline_checks.py
```
To reproduce recorded CI, checkout exact synthetic merge d1be5dcf7193bfacaa4bb6a53b72c8a1a3b82fd4 (head #13 into pinned main), not an unpinned moving pull/13/merge ref. Use Windows and Linux Python 3.11; CI patches observed Windows 3.11.9 / Ubuntu 3.11.17. Confirm HEAD exactly before testing. Compilation creates bytecode in disposable checkout. The commands are a reviewer recipe; no commands/replay/test suite executed by H-005.
Existing evidence:
- [Ubuntu job 122191737325](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948/job/122191737325), 97 PASS.
- [Windows job 122191738058](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948/job/122191738058), 97 PASS.
- Both checkout d1be5dcf7193bfacaa4bb6a53b72c8a1a3b82fd4; compile and guarded runner successful; freshly re-inspected logs, not freshly rerun.
Stacked #14 head 328135f2695543cde96bb434aaa07201c51c0582 tested with engine head via a9f01f8c0b43697f9102e1424809645315b4fc64, 115 per platform. #14 does NOT contain latest engine changes on its branch ancestry. It remains a separate review/integration gate.

## Invariants to independently verify
- Read-only deterministic evaluation on stable inputs; no persistence/order/network dependencies. Config immutability does not deep-seal caller rows against concurrent mutation.
- Only completed/available canonical intervals at as-of; future payload excluded after valid availability parsing; source quality/unknown timing must fail at adapter.
- Unique ordered contiguous session prefix, finite positive coherent OHLC and nonnegative volume; explicit missing/duplicate/order/stale/invalid reasons. Expected tail coverage is NOT proven by prefix alone.
- EMA SMA seed plus recurrence alpha=2/(N+1); baseline excludes current volume; OR/reference patterns exclude event where defined; ties strict for price breaks, inclusive volume threshold; long/short geometry.
- Raw strings not shifted/reformatted, valid original inputs unchanged, outputs detached; data hash is feature identity, NOT full run/provenance authentication.
- Hypothesis status/no confidence scores/no returns or actual VWAP claims.
- For the proposed A/B study, subset/same-direction relation is a contract ASSUMPTION requiring independent implementation verification; H-004 algebra alone is not a production property test.

## Targeted review questions and risk priorities
1. Confirm Decimal oracle independence, SMA seed/session choice, HLC3 vs OHLC4 naming, threshold ties, warmup=22 and OR/proxy/pattern interactions. Are any strict conjunctions unintentionally selecting contexts? No profitable-edge inference from synthetic trend fixtures.
2. Re-examine all availability/session contradictions, malformed metadata, trusted/caller evidence boundary and raw identity. Engine parses naive ET seconds; no DST/calendar/watermark/clock-bound authority exists.
3. Validate numeric-output finiteness for every observation, not just checked intermediates. SOURCE-DERIVED RISK, NOT REPRODUCED HERE: volume_ratio=last_volume/baseline is outside the derived-value finiteness tuple; extreme finite ratios may overflow even when EMA/proxy checks pass. Request a synthetic reproducer before proposing any fix.
4. Are serialized result inputs full context/config/evidence/code hashes and canonical units unambiguous? Feature hash alone omits those run dimensions; caller alias/coercion/schema conventions need limits.
5. Confirm all early failure paths produce bounded explicit quality/reasons; invalid row metadata must not become a candidate; malformed availability cannot be safely ignored as future without evidence.
6. What does complete=True establish? It is supplied, not independently validated. A completed interval can be revised; current module rejects visible duplicates, not a revision resolver.
7. Examine exact max-age equality, availability>=interval_end, session-close and prefix-gap behavior; document conservative exclusions rather than silently relax them.
8. Independently check source diff for accidental IO and test imports; callbacks/GUI remain out of scope. Offline safety controls are regression safeguards, not malicious-code isolation.
9. Review synthetic long/short reflection and numerical precision near ties; geometry cannot establish intrabar causal rejection or fill.
10. Record limitations: caller rows mutable under concurrency, repeated candidates/overlapping labels, correlated SPY/QQQ, synthetic cases not provider/edge/custody proof.

## Required independent review record
Provide reviewer username/identity evidence, relevant Python numerical/testing and point-in-time market-data competence, willingness/access, independence from authorship; scope exact head/base/tested checkout; material findings severity/reproduction with synthetic data only; required tests; accepted residual risks; decision and UTC evidence link. UNKNOWN stays UNKNOWN. Review must be tied to pinned SHA; head drift invalidates carried-forward readiness. Human merge authorization is separate after findings/CI; no merge or main mutation by this packet.
