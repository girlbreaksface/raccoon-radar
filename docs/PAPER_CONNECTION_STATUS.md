# Paper connection status — November 4, 2026

Integration HOLD. Live trading NO-GO. One reviewed external paper round trip completed.

## Verified locally

- The listener on 127.0.0.1:11111 belongs to moomoo_OpenD.exe.
- Isolated Python environment installed moomoo-api 10.12.7208. No SDK was added
  to the research app's default Python environment.
- Read-only SDK handshake and account query succeeded. Exactly one active US
  SIMULATE / STOCK_AND_OPTION account was found. Account numbers are not exported.
- Explicit SIMULATE queries returned zero positions and zero current orders.
- SPY and QQQ snapshots and option expiration queries succeeded. This does not
  establish all entitlements, exchange-time semantics or retention rights.
- An SPY next-day option snapshot and one-level order book were available.
  The initial snapshot was more than five seconds old, and the cached book's
  receive timestamps were empty. A subsequent live subscription, excluding the
  initial cached push, delivered two callbacks and populated both server receive
  timestamps (12:16:31.213 Eastern). We did not treat query receipt time as proof
  of quote freshness. New order checks still require newly received fresh data.
- PR #65's six workflows passed at db3c4964d6eee71363aa499b5036e69adcc22afe.

## Added review tools

`paper_account_preflight.py` performs read-only account discovery and explicitly
SIMULATE position/order queries for the one eligible account. It never unlocks
an account or submits, cancels or modifies an order; it closes the SDK context.
SDK imports are lazy, so fake-only CI does not install a broker package.

`paper_order_review.py` is a pure proposed pilot policy: long call/put, one
contract, SPY/QQQ, LIMIT/DAY, $30 entry cost including estimated round-trip fees,
$60 aggregate premium, three daily entries, $30 realized daily-loss stop,
five-second quote age, required session/account/reconciliation flags, kill switch.
These are new pilot proposals, not changes to existing simulator thresholds.
READY_FOR_REVIEW never enables orders. Caller assertions and estimated fees are
not independently authenticated; this is not a production risk gateway. Code
format checks do not verify a contract's existence, multiplier or tradability.
The realized-loss gate excludes unrealized losses and cannot guarantee loss caps.

## Completed paper connectivity pilot

The user's instruction to proceed with paper trading authorized a bounded,
internally reviewed connectivity test. The exact intent was recorded before
submission: one US.SPY261105C777000 call, BUY LIMIT .20, immediate SELL LIMIT .01
after confirmation of one sellable long contract. Explicit SIMULATE and the
verified account ID were used on every broker request; no unlock or live call.
The pilot did not use the synthetic fixture adapter as if it were a live feed.

Broker records confirmed entry order 830331 and exit order 830334 FILLED_ALL,
one contract each, both at .18. Final position quantity and sellable quantity were
zero. Both orders were fully filled; no pending order remained. Gross simulated
P/L was zero; paper fees were not verified. This is operational evidence only,
not validation of a strategy or executable profitability.

The initial one-second order polling hit the broker limit of ten queries per
thirty seconds and halted. A separate explicit SIMULATE position query confirmed
one sellable long; the reviewed close-out was submitted once and confirmed filled.
The original evidence was preserved. Polling now waits four seconds before each
query, with a regression test. Submissions are never automatically retried.

`paper_pilot.py` contains the narrowly scoped reviewed lifecycle with exclusive
durable intent logging, exact paper-account matching, explicit SIMULATE on every
query/submission/cancel, confirmed-long-only close and halt on ambiguous state.
It is not a background strategy runner. Any unresolved state requires explicit
paper-account reconciliation. The one-off operational wrapper additionally
verified the current date/session, option multiplier/expiry/type and fresh
timestamped live order book before invoking the lifecycle; callers of the
library must provide equivalent checks. No generalized order transport is added
to the dashboard, fixture adapter or simulator. No code was deployed or merged.

## Remaining external-order gate

Do not submit a paper order using an unverifiably fresh book or a stale snapshot.
A timestamped live update must be obtained for each prospective order; initial
cached responses are insufficient. Review the exact intent,
fresh quote, contract metadata, reconciled state and loss/exit handling before
any external submission. Broker operations must explicitly use SIMULATE and the
verified paper account. Never fall back to a live environment or default account.

Reference: [account identification](https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-acc-list.html),
[paper trading](https://openapi.moomoo.com/moomoo-api-doc/en/qa/trade.html),
[snapshot fields](https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-market-snapshot.html).
