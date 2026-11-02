# Offline provisional receipt replay

`provisional_replay.py` is a standalone JSON replay view of sealed SPY/QQQ
one-minute SDK candle updates. It uses `capture.verify` before decoding and
validates the entire capture even for an early cutoff. Any integrity or decode
failure blocks the whole view; no partial export is emitted.

Run from the project root using the existing capture Python environment (installed
moomoo-api 10.11.7108 and protobuf required; no download or provider request):

```powershell
C:\Users\louis\radar-moomoo-test\Scripts\python.exe -B research/feed_contract/provisional_replay.py C:\Users\louis\Documents\RaccoonRadarCaptures\spy-qqq-20261102-105014-e006bec7 --sequence 388 --output new-replay.json
```

Omit `--output` for stdout. Output files use exclusive creation; choose a new
filename for each run. `--sequence` and `--cutoff-ns` (receipt wall nanoseconds)
are inclusive and intersect when both are supplied. Zero yields an empty view.
Cutoffs describe received evidence, not a market state or durable commit time.
The module reads only descriptor literals from the installed SDK files, into a
private protobuf pool. It never imports the moomoo package or opens a context.

Groups use the exact `(symbol, source_label)` strings, ordered by first receipt.
History preserves every row, including identical repeats; ordering is journal
sequence followed by original row index. `last_observed` is the last row in that
history, without OHLC aggregation or monotonic-field assumptions. Receipt
records retain original payload bytes as base64, source stamps and hashes;
decoded fields retain presence and values. Protobuf bytes remain authoritative
for unknown fields and exact serialization. Views are detached, mutable JSON
data, not a persistent canonical candle store.

Every view, group and revision remains `PROVISIONAL`, finality `UNKNOWN`, and
strategy status `DATA_BLOCKED`, including after later labels or capture sealing.
Source labels and numeric source timestamps are untouched. There is no inferred
minute start/end, -60 second shift, missing-minute fill, closed-candle promotion,
adjustment-factor interpretation, strategy, dashboard or trading integration.
No certification of completeness, provider accuracy, clock accuracy, entitlement,
latency, adjustment semantics or authenticity is provided. Hash chaining detects
local inconsistency, not malicious replacement of an entire evidence bundle.

Validation on November 2, 2026, Windows/Python 3.12.10:

- Guarded feed-contract suite: 57 tests, including nine new replay regressions.
- Real capture read under `OfflineGuard`, with no moomoo package import: 1,143
  receipts, 545 SPY and 598 QQQ; six exact-label groups, all revisions retained.
- QQQ label `2026-11-02 10:52:00`: as-of sequence 386 open/low 696.88; as-of
  sequence 388 open/low 696.9054. Inclusive receipt cutoff at 386 agrees.
- All three original evidence file hashes unchanged after replay. Journal SHA256:
  `42fa2dd2324b67a043f3ff26a75a5e52d43ccf7a842ee254db2e78c4c09fc19f`.
- Syntax parsed across project Python files. No GUI/provider/market validation;
  Linux and Python 3.11 not exercised locally. System Python lacks tzdata; the
  existing capture environment passes the feed suite without installing anything.

Run regressions using `python -B research/feed_contract/run_checks.py`; root
checks remain `python -B offline_checks.py`. This proposal is based on the
unmerged feed-contract branch `fb38c328c57cb2d819adaaa706d6eaf8ceb082bb`, and is
reviewed against that dependency, not represented as already on main.
