# H-007 — isolated volume-ratio finiteness repair
Recorded-at UTC: 2026-10-28 01:13:09 UTC. Status: IMPLEMENTED / TESTED / RETURNED_FOR_INDEPENDENT_REVIEW; NO MERGE.
Direct human instruction in this coding chat: “H-007 is approved. Proceed within this exact scope. No further confirmation is required.” This authorizes only [H-007's bounded numerical repair](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6456118165), not other design/source/study/merge gates.

## Exact revisions and preservation
- Pinned #13 source: 6e7d1a8804b14aba9d08302bc5db48f31b0706ae, engine blob09497b013d65aebaa9f77f47212079f35445b74b.
- Separate branch fix/h007-volume-ratio-finiteness, [draft PR #21](https://github.com/girlbreaksface/raccoon-radar/pull/21).
- Repair head **48e184c67168724b1449ac8c36d209d4a2d72892**, repaired engine blob **8a4d091a24e2ea6f80e4d24b14dcebd400cf3586**, LF SHA256 e1db14c064159c53689c1228fcf8a8efc3de92b38561b76726c31c965bde7124.
- H-006 test file incorporated UNCHANGED: blob **c5c8c5aa5d611396696ec7afa11394aa021723c3** (same as PR #20); LF SHA256 aaff2c26ab897a4d0523af406a50c5c86fd21da9f52163a173de02d152eea60e.
- Six new focused boundary tests: test_volume_ratio_finiteness_repair.py, blob **861f13c791af644c53b3922d0ab2f2014146b6e8**, LF SHA256 6ab3c36f17fba23327f139b3a9fad8efc07df0f928a645f60cd72c2e555e2d14.
- Test-first pre-repair branch commit dc451d19b69e09987edf0d5115dd51ab4c70d7e2 contains both test files and original engine; local107/5FAIL. Initial inherited-test commit003c1e4033e4ec7cd9efb2161a6294f48e81585c.
- [Exact repair diff](https://github.com/girlbreaksface/raccoon-radar/compare/6e7d1a8804b14aba9d08302bc5db48f31b0706ae...48e184c67168724b1449ac8c36d209d4a2d72892): engine6 additions/1 deletion plus two added test files. No other production changes.
- #13/#14/#17/#18 reviewed heads and #20 preserved. PR #20 remains b4f0d14b9b83500337d5dd6375bcbf279142c6ba with deliberate red evidence; no test weakening, skip, expectedFailure, rerouting or retargeting.

## Minimal behavior change / explicit unavailable contract
The existing ratio last_volume/baseline is computed once. If it is nonfinite, the emitted volume_ratio is None (JSON null), and evaluation returns NO TRADE with sole reason **VOLUME_RATIO_OVERFLOW**, also in data_quality.issues. No finite cap, zero replacement or fabricated ratio is used. Signal selection is stopped before candidate emission for this numerical failure.

Valid input candle metadata remains data_quality.status=READY, eligible_bars=25, indicator_status=EVALUATED. READY describes accepted/available candles, not availability of every derived metric or permission to trade; existing warmup/zero-volume cases already distinguish data validity from a candidate. The unavailable ratio is explicitly explained; callers must use signal/reasons and nullable metric, never READY alone as an action predicate.
This preserves unchanged H-006 tests' valid-input preconditions while fixing their finite-output/strict-JSON invariant. Other derived overflow guards retain their existing NUMERIC_OVERFLOW/INVALID behavior. Normal finite ratios, zero-baseline reason, current-zero ratio, thresholds, volume confirmation comparison, EMA seed/recurrence, proxy, OR and patterns are unchanged. No unrelated signal redesign.

## Exact synthetic fixtures and outputs
Same H-006 25 rows: i=0..24, open=close=.01+i*.0001, high/low +/- .000025, starts2026-10-23 09:30..09:54 ET, one-minute end-available complete intervals; as-of09:55; evidence SYNTHETIC. Prior volume below means EACH first24 row volume; current means final row. Finite coherent schema-valid values only; economic realism/provider semantics NOT established.
| Case | Prior volume | Current volume | Emitted ratio | Signal / reasons |
|---|---|---|---|---|
| benign |100|200|2.0|BULLISH CANDIDATE / [] |
| original H-006 |1e-200|1e200|null|NO TRADE / [VOLUME_RATIO_OVERFLOW] |
| largest finite |1.0|1.7976931348623157e308|1.7976931348623157e308|NO TRADE / [VWAP_PROXY_NOT_ALIGNED] (normal rule) |
| above finite maximum |0.5|1.7976931348623157e308|null|NO TRADE / [VOLUME_RATIO_OVERFLOW] |
| smallest positive baseline |5e-324|1.0|null|NO TRADE / [VOLUME_RATIO_OVERFLOW] |
| zero baseline |0.0|1.0|null|NO TRADE / [ZERO_VOLUME_BASELINE,VOLUME_NOT_CONFIRMED,VWAP_PROXY_NOT_ALIGNED] |
| zero current |1.0|0.0|0.0|NO TRADE / [VOLUME_NOT_CONFIRMED] |

[observations.synthetic.json](observations.synthetic.json) records full actual output observations, quality/reasons, fixture hashes, source/test hashes and input preservation. Every case serializes with allow_nan=False and nonfinite_paths=[]; no archive string conversion needed. Full benign result (not just ratio) equals its saved output from the pinned pre-repair engine. This proves equality for that fixture, not an exhaustive normal-input equivalence proof.

## Test-first and cross-platform evidence
Local Windows11 / Python3.12.14, isolated snapshot:
- 44 pinned original Python/AGENTS source blobs plus unchanged H-006 test copied/verified before edits.
- Added six tests BEFORE engine change: **107 tests,5FAIL**. The two original H-006 finite/JSON failures plus three new overflow assertions fail; finite-max and zero controls pass.
- Applied only six-added-line/one-replaced-line engine change: **107PASS**.
- Exact source/test-byte pre-repair recheck in a separate temporary snapshot:107/5FAIL; repaired exact-byte rerun:107PASS. Original43 other source/AGENTS blobs unchanged.
- Compilation python -B -m compileall -q .: PASS. Guarded commands python -B offline_checks.py; existing disposable synthetic DB fixtures only, no production/research DB access. New tests themselves have no provider/DB/file adapters. No #14 historical replay/study code executed.

[Repair CI40613436015](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40613436015):
- [validate (ubuntu-latest) job122570256886](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40613436015/job/122570256886), Python3.11.17: compilationPASS, guarded suite **107PASS**, conclusionsuccess.
- [validate (windows-latest) job122570257183](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40613436015/job/122570257183), Python3.11.9: compilationPASS, guarded suite **107PASS**, conclusionsuccess.
Both actual checkout **a9a961a6af5b5fc81a8fd2cbe29005af1e1bad8c**, merging exact repair head48e184c67168724b1449ac8c36d209d4a2d72892 into pinned #13. All four H-006 tests and all six boundaries pass unchanged/as written.
[ci-evidence.json](ci-evidence.json) retains timestamped selected log excerpts and exact revisions; local source/test proof and red/green raw-log hashes in [local-checks.json](local-checks.json).
PR #20 is still a different original-source failing artifact (101 tests/2FAIL); repair-green CI does not erase or relabel it.

## Review limits / remaining gates
No clamp or change to finite trading calculations; ratio overflow alone becomes explicit unavailable+abstention. Fractional artificial volume extremes are numeric robustness fixtures, not realistic shares or historical research. None of this verifies provider timestamps, completion, availability, calendars, predictive edge, performance, options/0DTE P&L or fills. Underflow or broader semantic/schema policy was not redesigned.
READY plus nullable metric/reason is an explicit narrow contract for independent review; downstream consumers must not treat READY alone as signal availability. No UI or adapter integration is authorized here.
No provider/broker/network data, production DB/schema/ingestion/raw-data changes, historical replay/study, alerts, simulated trade/order or live/paper execution. No merge/retarget and no modification of pinned #13/#20. Only coordination evidence updates on #19.
Next: independent maintainer reviews exact repaired source/contract/diff and material risks; owner separately authorizes any integration. H-007 is a limited repair exception, not blanket G-H003-3 approval or reopening G-H003-1/2/4. No merge authorization received.
