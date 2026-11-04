# Paper workflow readiness review — November 4, 2026

Integration HOLD. Live trading NO-GO. Automated broker paper strategy NOT READY.

## Evidence and scope

PR #61 remains draft at a81e0710a319890a321834968f0b03d262f52bd9;
all six associated workflows were independently rechecked as successful.
Later draft #65 adds synthetic rehearsal; draft #66 at
7adbbc4e35fb7e36e9879e3174e8c98a51edb703 adds the connectivity pilot.
The six #66 workflow runs were queued when checked; no remote pass is claimed.
No merge, deployment, new broker order, cancellation, unlock or purchase occurred
in this review. Existing research stores were not opened.

Read-only OpenD checks at 12:37 Eastern found one active US SIMULATE
STOCK_AND_OPTION account using moomoo-api 10.12.7208. The local process path was
moomoo_OpenD.exe. Explicit SIMULATE reconciliation returned two FILLED_ALL orders
and one zero-quantity position record: zero pending orders and zero open quantity.
Row counts alone do not establish exposure. Preserved prior records confirm the
SPY call connectivity buy and sell both filled at .18; gross paper P/L zero,
fees unverified. This is historical connectivity evidence, not a strategy test.
QQQ broker execution has not been demonstrated.

## Requested controls

| Control | Verified scope | Remaining gate |
| --- | --- | --- |
| Paper isolation | Explicit SIMULATE and exact account in pilot; fake REAL rejection | No integrated strategy broker gateway |
| EMA9 / EMA21 | Pinned first-close seeded recurrence, 35-bar warmup; synthetic replay regression | Provider candle finality, session calendar and point-in-time adapter not verified |
| VWAP | Existing HLC3 candle-volume proxy is labeled NOT_TRADE_LEVEL_VWAP | Verified trade-level VWAP unavailable; cannot relabel proxy |
| $30 premium | Simulator caps slippage-adjusted entry premium; tests include exact boundary | Simulator excludes fees from cap; separate all-in proposal policy is not wired to pilot |
| +20% / -15% | Simulator compares executable bid after slippage against entry, exact-boundary and gap tests | Broker pilot closes immediately, has no strategy target/stop supervision |
| 3 entries/day | Synthetic single-session fourth entry rejection tested | Restart-safe shared broker daily counter absent; proposal trusts supplied count |
| Logging | Synthetic hash chain and pilot exclusive fsynced intent journal | Durable cross-run idempotency, partial fills and cancel/fill races unresolved |
| Kill switch | New fail-closed entry callback; checked again before BUY, with verified risk-reducing SELL permitted | No pending-order cancellation monitor or operator control surface |

## Change proposed

The connectivity pilot previously accepted entry without any kill-switch check,
and its last account check omitted option-account type and US permission.
It now requires a callback returning exactly False before proceeding and before
BUY; missing, unknown, non-boolean or failed switch state blocks entry. Account
identity must occur exactly once and remain active, SIMULATE, US-authorized and
STOCK_AND_OPTION before either submission. Existing callers that omit the new
callback fail closed. No operational wrapper was modified or run.

The switch is an entry interlock, not an emergency flatten guarantee. A verified
long-only close remains permitted after a switch activates. Pending entries,
unknown submissions and unconfirmed cancellations still require reconciliation.
The fixed dated pilot is not reusable strategy execution and must not be promoted
as such. A new journal filename is not a daily-trade or idempotency boundary.

## Blockers to a verified broker strategy workflow

1. Obtain authenticated point-in-time SPY/QQQ inputs, completed candle/session
   semantics, fresh option book timestamps and a verified VWAP definition/source;
   entitlement and retention/provenance gates remain unresolved.
2. Implement and independently review a separate paper-only strategy gateway
   connecting signals and risk policy to broker fills/exits. Do not feed real
   data through modules that accept only fictional synthetic inputs.
3. Add durable daily entry reservations and restart recovery, contract metadata
   and fee validation, partial-fill/cancel-race handling, stale-feed handling,
   session close and an operator kill control with reconciliation.
4. Exercise both symbols and requested target/stop/limit behavior with fakes and
   then controlled external simulation after review. Connectivity alone is
   insufficient. No external strategy session has been authorized by this report.

Rollback: remove this change or revert its commit; no schema/data migration.
