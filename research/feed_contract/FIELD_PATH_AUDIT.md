# Offline field-path audit

PR #47 records all observation transitions. This layer answers a different audit
question: does an endpoint comparison hide intervening field excursions? A sequence
A -> B -> A has equal endpoints but two changes; an unchanged field has none.
No price arithmetic, strategy calculation, candle timing inference, or eligibility
change is introduced. Provider-contract issue #46 remains open.

`field_path_audit.audit(capture, before={...}, after={...})` calls the existing
revision-impact analyzer once. The entire sealed capture is verified and decoded
before either cutoff is selected. Cutoff validation and inclusive sequence/wall
intersection semantics are inherited unchanged. Invalid later evidence blocks even
empty selections. All embedded observations, revisions, repeats, and source labels
are preserved.

For each exact symbol/source-label group visible at the after cutoff:

- If visible at the before cutoff, the anchor is its last observation at that
  cutoff. Earlier excursions are outside this comparison.
- Otherwise `baseline_available=false`; the first later observation is the anchor.
  Its initial fields are not counted as revisions. This group has no before value.
- Each decoded field receives UNCHANGED (no changes), RETURNED_TO_ANCHOR (changes
  but equal endpoints), or NET_CHANGED (different endpoints). Field presence is
  separate from value, so absent, present-null and present-zero differ.
- Every change records before/after states and exact sequence/row-index references
  into `evidence.after.observations`, where raw receipts and hashes remain attached.
  References to previous observations include intervening exact repeats. Same-receipt
  rows follow wire order. Fields sort by name; groups follow first observation order.
- `return_count` counts transitions back to the anchor, including intermediate
  returns even when the endpoint is different. `change_count` excludes repeats.
  Top-level counts count field paths, not independent candles, samples or events.

The embedded PR #47 analysis remains intact. Detached summary states cannot mutate
its source observations. Provenance retains verifier, replay and revision-analysis
source hashes and adds the audit source hash. Reports retain PROVISIONAL / UNKNOWN /
DATA_BLOCKED, boundary_semantics UNKNOWN and completeness NOT_ESTABLISHED.
An unchanged path or a long repeat run provides no finality guarantee.

## Reproduction

Create a new exclusive output destination. Full reports contain private receipt
payloads: keep them local, never attach them to CI or a PR.

```text
python -B research/feed_contract/field_path_audit.py PRIVATE_CAPTURE --before-sequence 386 --after-sequence 388 --output NEW_LOCAL_AUDIT.json
python -B research/feed_contract/reference_field_path_regression.py PRIVATE_CAPTURE
python -B research/feed_contract/run_checks.py
```

The reference regression uses the previously pinned local schema environment;
it installs nothing and does not import the moomoo package. It first runs the
inherited reference regression and pins all three original evidence hashes.
It then checks deterministic QQQ field paths at 386/388, all 1,143 observations
and six groups, resolves every field-change reference, and rechecks evidence hashes.
Only pass summaries and aggregate field classifications are printed.

On the November 2 reference capture, first-observation anchors through sequence
1,143 yield 42 UNCHANGED fields, 36 NET_CHANGED fields, and zero
RETURNED_TO_ANCHOR fields. These are descriptive decoded-field counts across six
groups, not an independent statistical sample. Hidden endpoint excursions are
demonstrated by synthetic fixtures, not claimed for this capture.

Six new synthetic tests cover multiple excursions and repeats, net changes,
newly visible groups, exact-label/symbol isolation, presence/null/removal,
same-receipt row references, baseline isolation, detached evidence, equal/empty
cutoffs, receipt-wall agreement, integrity/decode failure after cutoffs, provenance,
safety labels, and exclusive CLI output. Existing feed CI discovers these tests
on Linux/Windows with Python 3.11/3.12; private evidence never enters CI.

Limits: all selected histories and the embedded evidence remain in memory. Value
equality follows PR #47's decoded Python field comparison, not bytewise protobuf
identity. Receipt clocks and provider authenticity remain unestablished; seal
consistency does not prevent wholesale bundle replacement. No elapsed-time,
completeness, correction-delay, predictive, or trading claims are supported.
