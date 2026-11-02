# Offline candle observation report and replay review

This milestone is stacked on draft PR #44 at `99ed196`, not on main.
`receipt_quality.py` calls the replay verifier and decoder for the entire sealed
journal before applying inclusive sequence/receipt-wall cutoffs. A later corrupt
or undecodable receipt blocks even an empty selected view. It imports no strategy,
dashboard, provider context or database code. Output is descriptive JSON only.

Run with the existing reviewed SDK environment:

```text
python -B research/feed_contract/receipt_quality.py CAPTURE_DIRECTORY --output NEW_REPORT.json
```

Optional `--sequence` and `--cutoff-ns` intersect, inclusive, as in replay.
Output uses exclusive creation. Failures return nonzero with DATA_BLOCKED and
verification/decode failures create no report. Source evidence is never written.
Provenance includes schema, replay, verifier, and report source hashes.

For each exact symbol/source-label pair, observations count every decoded row;
changed transitions compare field presence and values with the previous row;
identical transitions count decoded repeats. Unknown protobuf fields remain
authoritative in the original payload; these metrics do not compare wire identity.
Changed fields include all decoded fields, including provider auxiliary fields.

Per-symbol receipt counts, unique observed labels, first/last receipt wall stamps,
monotonic observation spans, and every adjacent monotonic receipt gap describe
only selected observations. A single receipt has a zero span and null maximum gap.
No cadence threshold, missing-candle inference, session denominator, coverage
percentage, interpolation, timestamp shift or candle aggregation is applied.
All report/group/symbol statuses remain PROVISIONAL / UNKNOWN / DATA_BLOCKED.
Sealing, later labels and quiet receipt periods establish neither finality nor
completeness, accuracy, adjustment semantics or usable strategy inputs.

Independent review found the cutoff selection, full decode before selection,
row ordering, exact labels and repeat retention consistent with PR #44's contract.
Found and fixed: capture verification accepted unsupported manifest safety/schema
metadata and summary finality/completeness/schema metadata. These now fail closed,
including for empty cutoffs. This checks consistency, not authenticity of a replaced
bundle. Hashes cannot independently certify provider truth.

Regressions cover tied receipt cutoffs, all rows per receipt, changed versus repeat
counts, selected coverage, empty views, contradictory seal metadata, exclusive
exports, blocked failures and production import isolation. Existing replay tests
cover later corruption/decode failure, revision preservation and safety labels.
The fake-feed CI matrix runs guarded synthetic checks on Ubuntu and Windows with
Python 3.11 and 3.12. CI needs no SDK, credentials, private capture or provider.
Timezone data is installed for existing DST checks; test execution is guarded.
Real SDK decoding is a separate local check, not claimed by synthetic CI.
