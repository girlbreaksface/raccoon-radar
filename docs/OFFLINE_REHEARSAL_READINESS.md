# Decision â€” November 5, 2026

Stacked on the durable daily risk proposal, above #73. The existing VWAP/EMA
chat was complete at 60f3dc6 before this work. Coordination message sent;
its checkout is untouched. New development uses a separate checkout and branches.

The fictional rehearsal calls the #73 indicator calculation for SPY/QQQ across
two sessions, applies an explicitly fictional close/VWAP/EMA directional
conjunction, binds fictional call/put identifiers, checks causal quote timing,
reserves capped exposure, accounts for simulated entry/exit prices and fees,
reopens the ledger using an external receipt, and compares independently
assembled fictional order observations through the existing reconciler.
Baseline arithmetic is independently asserted: two round trips at $20 entry,
$24 exit, $0.65 fee each side yield 540 cents. This is an invented software
fixture, not measured returns, an executable quote, or evidence of edge.
The simulator is a deliberately bounded deterministic fixture path; existing
legacy paper signal/simulator calculations and production GUI remain unchanged.
Production contract selection, exchange contract lifecycle, size/queue fills,
exercise, assignment and authentic broker recovery remain unverified.

Gap, pre-decision quote and missing-order observations block. Report tampering,
even after rehashing, fails exact rerun verification. All artifacts remain
exclusive-create. The unified report checks source inventory and each foundation
log/artifact hash. It binds synthetic reproduction and separately provided
redacted broker evidence; all eight operational gates remain HOLD. Hashes are
not signatures, independent custody, or authenticated-provider certification.

Read-only broker observations on November 5, 2026 at 06:32â€“06:34 UTC:
reviewed installed moomoo-api 10.12.7208, localhost OpenD; one uniquely eligible
ACTIVE US SIMULATE STOCK_AND_OPTION account selected and revalidated.
Two refreshed snapshots agreed: zero positions, two terminal order rows.
No local expectations for those orders were supplied: UNTRACKED_ORDER HOLD.
The explicit November 4â€“5 SIMULATE history-order query returned two rows;
this establishes observed access, not completeness, timezone or fee provenance.
Connections closed. No unlock, order, cancellation, modification or REAL
history query was made. Raw account IDs/order rows/provider errors are not
retained in shared evidence. Local fingerprint/hash summaries are retained.
No raw market recorder was enabled.

Moomoo documents historical deals as live-only, unavailable for paper:
https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-history-order-fill-list.html
The order query is separately documented:
https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-history-order-list.html
There is no REAL fallback. Full paper fill reconstruction requires an approved,
complete retained callback/deal lineage or a supported broker export with fees,
timestamps and account scope, reconciled against the terminal-order baseline.
No missing fill prices, fills, fees or opening balances are invented.

Run automation_foundation.py with a new --output directory, then
unified_readiness.py --foundation <directory> --output <new-json>.
Optional --broker <json> binds local redacted broker records; hosted CI uses
fictional inputs only and never connects to OpenD. Actual process crash checks
run outside the root suite's no-child-process guard, against disposable stores.

Paper HOLD; recording HOLD; live NO-GO; orders DISABLED; merge/deployment HOLD.
