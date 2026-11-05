# Offline execution recovery — 2026-11-05 decision log

Status: draft engineering evidence only. Recording HOLD; paper execution HOLD;
live NO-GO; orders DISABLED; merge/deployment HOLD.

## Scope and reuse

Base: PR #71, `ci/read-only-paper-reconciliation`, exact commit
`8d616d7db9e7f420412f03dcaa3bb56f961afc22`, stacked on #70.
Inspected active PRs #12–#71; no competing execution recovery PR found.
Inspected #66/#67 `paper_pilot.py`: fsynced intent/ack journal, uncertain-submit
halt and bounded lifecycle; it has no generic restart interpreter. It remains
on its separate branch, unchanged and unimported. #26 `manual_ledger.py` provides
SQLite recovery for a synthetic manual accounting store, not broker execution
reconciliation. Its stores and recovery paths remain separate and untouched.
Reuses #71 normalization, quantity/status checks, report hashes and fake SDK.
No SDK, account connection, pilot execution, market request or order operation
is invoked by this milestone.

## Contract

`execution_recovery.py` provides an exclusive new journal writer, verified
replay and an offline recovery assessment. The first event explicitly declares
a flat starting inventory. Intent, acknowledgement, cumulative order
observation, cancellation intent and connection events have strict schemas.
Account fingerprint, sequence, parent hash and canonical bytes bind every row.
The writer flushes and fsyncs before returning a count/head checkpoint receipt;
a failed write poisons the writer. Existing files cannot be reopened for writing.
The caller must retain the checkpoint independently. Missing, extra, reordered,
changed, torn or truncated bytes against that receipt fail closed. Evidence is
never repaired, deleted, truncated or silently migrated.

Replay starts from scratch and counts each cumulative order quantity once.
Repeated identical event IDs are idempotent; conflicting IDs halt. Order
identity changes, decreasing fills, terminal changes and unknown states halt.
A cancel request changes no fill quantity. Pending/partial orders, unconfirmed
cancels, dangling intents, rejects, disconnection and nonflat fills remain HOLD.
Position differences never generate a fill, trade price, fee or P/L.

Recovery consumes a retained #71 reconciliation report plus the two explicit
snapshots whose hashes that report recorded. It checks the report hash, pinned
account, context closure, snapshot hashes/equality, exact order rows and net
position quantities. Broker differences are reported rather than imported into
the journal. Both local replay and broker reconciliation must agree before the
informational label CONSISTENT_OFFLINE can appear; every operational gate still
remains HOLD/DISABLED. This label does not resume or authorize execution.

## Automation and reproduction

```
python -B -m unittest test_execution_recovery test_automation_foundation -v
python -B automation_foundation.py --output work/unique-recovery-evidence
```

`execution_recovery_checks.py` produces `execution-recovery.json` under
OfflineGuard with fictional identifiers only. Fixtures include partial fills,
rejects, cancels, late fills, disconnect/reconnect, unknown status, duplicate and
conflicting replay, order/position/account discrepancies, closure failure,
tampering, torn writes, retained-checkpoint loss, every durable event boundary,
and an explicitly observed flat round trip. Root discovery includes recovery
unit tests and fault injection. The existing Windows/Linux Python 3.11/3.12
foundation matrix uploads the additional artifact with existing log/artifact
SHA-256 and source hashes. The parent recomputes the exact scenario evidence;
a successful child exit or repaired artifact hash cannot conceal missing cases
or changed gates. No new workflow permissions or notification hooks.

## Limits and remaining gates

Hashes establish consistency against retained receipts, not authenticated broker
truth or protection against replacing a journal and its checkpoint together.
Checkpoint custody, directory/power-loss durability, multiwriter arbitration,
process-kill/native filesystem behavior and bounded production journal retention
are not certified. Writer is single-owner, new-file-only; recovery never appends
or resumes submissions. A crash between fsync and external receipt retention
requires investigation. Fault injection and prefix replay simulate crash
boundaries; they do not certify actual broker or OS crash behavior.

A declared flat origin is an assumption, not a historical inventory proof.
Retained broker reports are non-atomic and not freshness or complete fill-history
certification. Unknown/unacknowledged submission cannot be matched by guessing
an order identity. Prior pilot journals are not silently converted to this schema.
No daily-risk counters, production strategy gateway, real fee/slippage model,
kill-driven pending-order cancellation or live reconnect automation is enabled.
Private real-account records must never be passed into hosted fixture artifacts.

Remaining gates: independent design review; authenticated full broker ledger and
account provenance; production crash/receipt custody and restart-safe risk
limits; pending-order kill policy; verified provider/finality/calendar and signal
conventions; real fees/slippage; frozen historical/holdout validation; separate
owner decisions for any recording, paper execution, merge or deployment.

## Optional convention inspection

Inspected `_pr31_pinned_kernel.py`: first selected close seeds EMA9/EMA21,
alpha 2/10 and 2/22; fewer than 35 canonical bars blocks. Its volume-weighted
HLC3 candle proxy is explicitly NOT_TRADE_LEVEL_VWAP. `historical_options_replay.py`
uses first-close seeds per symbol/session, the same alpha values, eligibility
from bar 21, and cumulative supplied trade price*volume / volume. These are
different documented research profiles. Neither verifies production VWAP,
provider trade notional or production warmup. No convention or threshold changed.

## Rollback

Close the isolated draft PR. Base #71/#70 and pilot/manual-ledger branches remain
unchanged; no existing data/schema or account state was modified.
