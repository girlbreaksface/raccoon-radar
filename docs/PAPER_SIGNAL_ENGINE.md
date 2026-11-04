# Synthetic paper-signal engine v1

The existing PR31 replay exposed qualified observations but no discrete signal
events. `paper_signal_engine.run` now emits the first qualifying candidate per
symbol, direction and session, with stable event IDs and the decision hash.
This is a new event-emission policy, not a change to the pinned calculation.
It is frozen for this version and has not been evaluated for profitability.

Each run accepts a complete, explicit single-session synthetic ReplayInput.
Warmup, incomplete/provisional candles, missing minutes and unknown availability
retain the existing block reasons. Repeated candidates emit once; opposite
directions remain independent. SPY/QQQ conflicts remain visible and do not veto
either symbol. This preserves the current independent observation semantics;
it does not claim two correlated symbols are independent statistical evidence.

The core is pure and deterministic. It does not access OpenD, files, databases,
accounts or order APIs. It has no positions, simulated broker orders, fills,
stops, exits, P/L or future-outcome labels. Every output is SYNTHETIC_ONLY with
execution DISABLED. Rerunning a full session returns the same event IDs; callers
must not treat repeated results as new events. Chunked/incremental ingestion,
restart persistence and live feed integration are not implemented.

Use the existing fictional demo to review behavior:

```python
from synthetic_replay_demo import make_demo
from paper_signal_engine import run
result = run(make_demo('conflict'), synthetic=True)
assert len(result.signals) == 2
```

Local quote connectivity does not establish final candles, point-in-time
availability, clock accuracy, consolidated coverage, free entitlement pricing
or raw-retention permission. Real inputs remain rejected. No raw recorder or
live paper monitoring was enabled. This code is reviewable preparation for a
later adapter, not release of the existing observation/data gates.

Validation: targeted synthetic tests cover deduplication, pair disagreement,
warmup and source blocks, deterministic reruns, prefix invariance and later
invalid observations. Run the repository's guarded offline checks for regressions.
Rollback removes the two new Python files and this document; no data migration.
