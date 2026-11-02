# Offline as-of snapshot and revision impact

This research layer compares two explicit inclusive receipt cutoffs using one fully verified and decoded replay. It does not interpret source labels as candle boundaries. It is separate from the dashboard, strategies and persistence.

`revision_impact.analyze(capture, before={...}, after={...})` accepts `sequence` and/or `cutoff_ns` (receipt wall nanoseconds) in each nonempty cutoff dictionary. Both constraints intersect. Nonnegative integers only; booleans are rejected. The selected before observations must be a prefix of after. Equivalent selections are allowed even if their requested cutoffs differ. Wall-time ties include every tied receipt; row ties follow wire row order. Neither source timestamp order nor elapsed quiet time establishes finality.

Each snapshot includes every selected observation, exact source labels, per-label history (including repeats), and a detached last-observed row. Every intervening observation has a transition against the previous observation for that exact symbol/label: FIRST_OBSERVATION, REVISION, or EXACT_REPEAT. REVISION compares all decoded fields, including presence changes; field lists are sorted for reproducibility. A return to an earlier value remains a revision. These are receipt-observation differences, not executable returns, certified provider corrections or predictive evidence. Raw receipts remain attached via the inherited replay representation.

The entire capture is verified/decoded before either cutoff is selected. Corruption or decode failure after a cutoff still blocks output. Outputs retain PROVISIONAL / UNKNOWN / DATA_BLOCKED, boundary_semantics=UNKNOWN and completeness=NOT_ESTABLISHED. Provenance carries verifier/replay/analysis source hashes, schema identity, manifest digest and verified chain tail. Hash consistency is not provider authentication or protection against wholesale bundle replacement.

CLI (new exclusive destination; no output on validation failure):

```text
python -B research/feed_contract/revision_impact.py PRIVATE_CAPTURE --before-sequence 386 --after-sequence 388 --output NEW_LOCAL_FILE.json
```

Full JSON contains private receipts. Keep it local; do not commit or attach it to a PR. Large captures are held in memory and histories are copied for isolation. This increment is deliberately scoped to research-sized sealed captures.

## Reproducible private reference regression

Use the existing local environment with pinned moomoo-api 10.11.7108 and protobuf. The schema reader parses descriptor literals without importing or executing moomoo. No SDK installation or live connection is part of these commands.

```text
python -B research/feed_contract/reference_impact_regression.py PRIVATE_CAPTURE
python -B research/feed_contract/run_checks.py
```

The local regression pins all three original evidence byte hashes, checks 1,143 receipts/rows and six groups, preserves full observation history, compares repeated deterministic analyses and sequence/receipt-wall cutoffs, checks QQQ label 2026-11-02 10:52:00 open/low 696.88 at sequence 386 versus 696.9054 at 388, checks safety labels and SDK import isolation, and verifies unchanged evidence afterward. It emits only a pass summary. The private bundle is not included in this repository or CI.

Synthetic tests cover repeats, revisions/reversions, first observations, detached data, label order, same-receipt rows, empty/equal/intersected cutoffs, malformed or reversed selections, optional field presence, late decode/integrity failure, exclusive CLI output and safety flags. The fixture subclass also reruns nine inherited replay cases. Existing CI discovers these tests on Linux/Windows with Python 3.11/3.12; it does not run the private reference regression.

Provider boundaries, finality, completeness, clock accuracy and adjustment factors remain unresolved under issue #46. No production eligibility or trading behavior changes.

For field trajectories that distinguish unchanged endpoints from intervening
excursions back to an anchor, see [FIELD_PATH_AUDIT.md](FIELD_PATH_AUDIT.md).
