# H-006 — isolated synthetic numerical-output results
Recorded-at UTC: 2026-10-27 19:41:25 UTC. Disposition: **FAIL — reproduced nonfinite volume_ratio and strict-JSON failure. TEST-ONLY BRANCH NOT MERGE READY.**
Direct human authorization in this coding chat: “acknowledge that authorization and return the isolated test results” for extreme valid inputs; [bounded H-006 scope](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6448303594). This resolves the previous direct-confirmation blocker ONLY for the isolated test artifact. No fix or broader G-H003-3 reopening authorized.

## Exact source, artifact and diff
- Pinned #13 source: 6e7d1a8804b14aba9d08302bc5db48f31b0706ae.
- Engine Git blob: 09497b013d65aebaa9f77f47212079f35445b74b; local/LF SHA256 572c8f290cca3c5a9139f16c0d08c0144e2bdd91c41f5709613c6f42188b418b.
- NEW branch: test/h006-extreme-volume-ratio.
- Test commit: b4f0d14b9b83500337d5dd6375bcbf279142c6ba.
- Added file: test_extreme_numeric_output.py; Git blob c5c8c5aa5d611396696ec7afa11394aa021723c3; LF SHA256 aaff2c26ab897a4d0523af406a50c5c86fd21da9f52163a173de02d152eea60e.
- [Draft PR #20](https://github.com/girlbreaksface/raccoon-radar/pull/20), base #13 feature branch at pinned source. [Exact diff](https://github.com/girlbreaksface/raccoon-radar/compare/6e7d1a8804b14aba9d08302bc5db48f31b0706ae...b4f0d14b9b83500337d5dd6375bcbf279142c6ba) adds ONLY that test file, no existing-file edits.
- [Actual CI merge checkout](https://github.com/girlbreaksface/raccoon-radar/commit/89512d771479eb79869e3d8df69352174e46ce4b) 89512d771479eb79869e3d8df69352174e46ce4b merges test head into exact pinned #13. No PR merged into main.

## Fixture and expected contract
25 explicit SYNTHETIC one-minute intervals, session 2026-10-23 09:30–16:00 ET, starts 09:30 through 09:54, availability=end, complete=True, as-of=09:55. Source stamps retained; no provider semantics inferred.
For i=0..24:
- open=close=0.01+i*0.0001;
- high=open+0.000025; low=open-0.000025;
- benign: first 24 volumes 100.0, final 200.0;
- extreme: first 24 volumes 1e-200, final 1e200.
Every supplied OHLCV is finite, prices positive and coherent, volume positive; exact values satisfy CURRENT ENGINE NUMERIC SCHEMA. Fractional extremely small volume is NOT realistic share-market evidence; no physical plausibility/provider constraint is claimed. Decimal mathematical quotient 1e400 exceeds finite binary64 range.
Expected contract being probed: all emitted numeric observation fields finite and entire result strict-JSON serializable; inputs preserved; existing invalid/incomplete conditions still NO TRADE. No assertion weakened, expectedFailure, skip or production guard added.

Fixture recipe is frozen in test commit; [observations.synthetic.json](observations.synthetic.json) records first/last values, exact floating outputs, fixture SHA256s, source/test byte hashes and input preservation. Hash encoding: json.dumps(rows,sort_keys=True,allow_nan=False) with default separators/ensure_ascii; SHA256 over UTF-8.
- Benign fixture hash bb97895227e3f46ce229bcb13d36698634b31f0bfe30700449b6d2b2c1203923.
- Extreme fixture hash 04586719bd8292cc9c857dd477569e9d5d46c6f6333f8fceb92132023f2c6a3d.

## Exact observed result
| Case | Quality/eligible bars | Signal | volume_baseline | volume_ratio | Nonfinite paths | Strict JSON |
|---|---|---|---|---|---|---|
| benign | READY / 25 | BULLISH CANDIDATE | 100.0 | 2.0 | none | PASS |
| extreme | READY / 25 | NO TRADE | 1e-200 | positive infinity (float inf) | $.observations.volume_ratio | FAIL / ValueError |

Extreme proxy=last_close=0.012400000000000001, so this fixture's proxy-alignment condition prevents a candidate. That does NOT make its nonfinite observations serializable or quality INVALID. Do not claim an emitted candidate with inf from THIS fixture. Other inspected observations remain finite; inputs unchanged.
Local Python 3.12.14 exact error: “Out of range float values are not JSON compliant: inf”. CI Python 3.11 reports “Out of range float values are not JSON compliant” without the value suffix. Both fail the same strict serialization operation.

Source explanation: finite checks include EMAs, baseline, total volume, volume_multiplier*baseline and proxy; volume_ratio is computed afterward as last_volume/baseline outside that checked tuple. All checked intermediates remain finite in this fixture; quotient overflows. This explanation is source-linked and reproduced, not a performance/predictive claim.

## Commands and results actually run
Local Windows 11 / Python 3.12.14; fresh isolated snapshot, 43 tracked Python files + AGENTS (44 source blobs) byte-verified against pinned tree before successful baseline. New test bytes also match Git blob after normalizing only its local creation artifact's extra trailing newline; no engine change. No user DB copied.
1. Pinned baseline BEFORE new test: python -B offline_checks.py — **97 PASS**, exit 0.
2. New test plus suite: python -B offline_checks.py — **101 run, 2 FAIL**, exit 1 (99 pass).
3. Targeted: python -B -m unittest -v test_extreme_numeric_output — **4 run, 2 FAIL**, exit 1; benign and invalid/incomplete fail-closed tests PASS.
4. Compilation: python -B -m compileall -q . — PASS, exit 0.
5. Pure fixture/snapshot inspection wrote a NEW exclusive local synthetic observations archive; no replay/study/provider/order call.

Failures retained:
```text
FAIL: test_extreme_valid_inputs_emit_only_finite_observation_numbers
AssertionError: Lists differ: ['$.observations.volume_ratio'] != []
... volume_ratio=inf

FAIL: test_extreme_valid_result_remains_strict_json_serializable
AssertionError: Strict JSON rejected the valid-input result:
Out of range float values are not JSON compliant
... nonfinite paths=['$.observations.volume_ratio']

Ran 101 tests
FAILED (failures=2)
```
Existing 97 tests pass, plus 2 new controls pass. Original guarded suite may use disposable temporary synthetic SQLite fixtures under its established runner; NO production/research DB opened/changed. The new numeric file itself uses no DB/network and performs no file IO. No #14 historical replay code is included/executed by this test branch.

## Windows/Linux CI — deliberate FAIL is expected evidence, not green readiness
Run [40570969484](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40570969484); exact test head b4f0d14b9b83500337d5dd6375bcbf279142c6ba, actual merge checkout 89512d771479eb79869e3d8df69352174e46ce4b:
- [validate (ubuntu-latest), job 122424732818](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40570969484/job/122424732818), Python 3.11.17: compilation PASS; guarded suite 101 run, 2 FAIL, job conclusion failure. Benign/control PASS, same two extreme assertions FAIL.
- [validate (windows-latest), job 122424733054](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40570969484/job/122424733054), Python 3.11.9: compilation PASS; guarded suite 101 run, 2 FAIL, job conclusion failure. Benign/control PASS, same two extreme assertions FAIL.
[ci-evidence.json](ci-evidence.json) preserves selected timestamped log lines, per-OS source/test byte hashes and checkout; Windows checkout byte hashes differ from LF hashes, while repository blobs stay fixed. No failed result hidden or converted to expectedFailure. Draft PR #20 is NOT MERGE READY.

## Setup failures preserved separately
Two initial incomplete local-snapshot baseline attempts produced 97 run / 28 errors due to missing dashboard AST fixture source, not a numerical assertion or pinned-project defect. Full pinned source bytes were then assembled (text fetch normalization was insufficient for some versioned dashboards; base64 file fetch established exact blobs). Corrected complete-source baseline passes 97.
A blob-endpoint response was decoded text rather than assumed JSON; that setup parsing error is not CI/engine evidence. No production file altered in fixing isolated fixture assembly. [local-log-summaries.json](local-log-summaries.json) records original raw log SHA256s and selected summaries (paths redacted/omitted); raw local logs retained under isolated workspace. These summaries are not a claim to archive full logs. First failed setup attempts are not silently erased.

## Limits and next approval
Reproduces a software numeric-output defect under an artificial but currently accepted finite schema; not evidence of real-market frequency, provider semantics, trading edge, economic realism, fill/P&L, all-input correctness or production readiness. Four tests do not prove completeness.
No engine fix, numerical clamp, threshold/indicator/strategy/ingestion/UI/persistence change, provider/data acquisition, simulated trade/order, replay/study, PR retarget or merge. #13 reviewed head remains pinned. Any repair requires SEPARATE owner authorization defining finite-output/fail-closed semantics and exact scope; preserve this failing artifact and normal-case behavior. Independent review and G-H003-1/2/4 remain unresolved; test-only exception grants nothing else. Return to coordination reviewer for evidence acceptance, then request bounded fix scope rather than implement it.
