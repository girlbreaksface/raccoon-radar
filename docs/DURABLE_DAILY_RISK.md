# Decision — November 5, 2026

Offline accounting only, stacked on #73. No runtime order consumer is connected.
Explicit new SQLite stores use synchronous FULL transactions and replay a chained
event log. Account fingerprint and caller-supplied limits are bound into every
hash. Reopening requires an independently retained count/head receipt; rollback,
unreceipted commit, concurrent writer, conflicting IDs and corruption block.
No automatic repair or resubmission. Receipts are integrity checks, not signatures.

Amounts are integer cents per contract with the multiplier already applied.
Long-only average cost uses exact rational arithmetic. Entry fees are expensed;
realized exits subtract average cost and exit fees. Trade count is distinct
filled entry intents, partial fills count once. Pending reservations consume
exposure and trade capacity. Exposure uses paid premium plus unspent reservation.
Bid marks establish unrealized liquidation P/L; missing/stale marks block.
Positive unrealized gains do not offset realized loss for admission checks.
Daily scope is America/New_York. Overnight inventory or pending intent blocks
without inventing a daily opening baseline. Flat books start fresh daily counters.

Limits are explicit fictional fixture parameters, not approved production policy.
No existing configuration or risk limits changed. A loss/exposure gate can also
block a new exit reservation: a future production adapter needs separately
reviewed reduce-only/cancel/kill semantics. Existing fills/terminal facts can
still be accounted for while blocked. Full entry/exit policy is not certified.

Tests cover partial entries/exits, fees, idempotence, checkpoints, account/limit
binding, stale marks, overnight state, overfills and an actual child-process
death before commit. Root tests retain their no-network/no-child-process guard;
the explicit crash check runs separately. Tests use disposable synthetic stores.
FULL SQLite is not certification of hardware power-loss durability, filesystem
directory durability, external receipt custody, authentic fills or atomic
broker reconciliation. Manual deletion/replacement of a store is unsupported.

Paper HOLD; recording HOLD; live NO-GO; orders DISABLED; merge/deployment HOLD.
