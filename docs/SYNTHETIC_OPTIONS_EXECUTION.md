# Synthetic options paper execution v1

This isolated pure module stacks directly on PR #58 c562f805. PR #59's share
simulator is a separate proposal and is neither changed nor used.

`synthetic_options_execution.simulate(replay_input, tuple_of_quotes, Config(),
synthetic=True)` generates PR58 signals internally. Real bundles and quotes
marked non-synthetic are rejected. Flags are fixture declarations, not provenance
authentication. Nothing connects this function to the dashboard, feed or broker.

## Fixed assumptions

- One fictional long option contract per entry; multiplier 100. Bullish buys a
  call, bearish buys a put; neither opens a short option position.
- Buy at ask plus configured adverse basis-point slippage; sell at bid minus
  slippage. Fixed configurable dollar fee per fill, default zero. Defaults are
  illustrative and uncalibrated. Decimal arithmetic uses an isolated context.
- Maximum entry premium $30 total per contract including slippage, excluding
  fees. This means option price <= $0.30. No cash account or margin is modeled;
  fees can make total cash cost exceed $30. No cumulative capital constraint.
- Profit target +20% and stop -15% compare executable bid after slippage to paid
  entry price, before fees. Exact boundaries trigger. Actual exit uses the first
  supplied valid crossing quote, including gaps; the threshold is no fill promise.
- Maximum three filled entries per declared session, shared across SPY/QQQ and
  both directions; an exit does not restore a slot. One open position per symbol.
- First eligible quote strictly after signal cutoff may enter. No cached quote,
  same-time fill, automatic reversal, retry of rejected entry, or forced close.
  No entry timeout is assumed. Missing quotes never create fills.
- Availability times must be strictly sorted by (time, signal ID), within the
  replay's common fictional session. This explicit tie order determines scarce
  trade-slot priority. Bid/ask must be positive finite uncrossed decimal strings.
  Observed quote time cannot be in the future; maximum age defaults to five
  seconds inclusive and can be configured from 0 to 60 seconds.
- Invalid/stale market values emit QUOTE_BLOCKED and invalidate cached marks.
  A later fresh quote can resume processing. Structural ambiguity (duplicate or
  unordered quote, wrong right/contract binding, unknown signal or real flag)
  aborts the pure run with no returned result. Contract IDs cannot change within
  a signal lifecycle. IDs identify fictional fixtures, not validated securities.
- DATA_BLOCKED/PROFILE_BLOCKED gates latch entry blocking for the symbol for the
  rest of the session. Valid quotes can still exit existing exposure. Gates and
  signals precede quotes at an equal timestamp.

## Audit and accounting

The immutable ledger includes ordered buys, target/stop sells, blocked quotes,
rejections and unfilled signals. Every row hashes its predecessor, with the
signal-run hash as anchor. Fills include contract, time, observed quote time,
price and fee; sells include realized net. Quantity and multiplier are fixed
above. Realized P/L = (exit - entry) * 100 - both fees. Open-position net is a
hypothetical liquidation estimate including both fees and adverse slippage.
At the later of last replay cutoff and last quote availability, absent/stale
marks make total unrealized/net P/L null, never zero or an invented fill.
Realized P/L remains available. There is no persistence or cross-call daily
counter: reruns start from scratch; callers must not concatenate duplicate runs.

Input/result hashes bind quotes, config, signal output and ledger. They provide
reproducibility, not authenticated provenance or signatures. Preserve exact
inputs, source revision and result together when independently exporting evidence.
The engine itself performs no I/O and exports nothing.

## Limits and boundaries

No real options dataset, chain selection, expiry/strike validation, listed-as-known
universe, quote size/depth, liquidity, partial fills, tick rounding, order latency,
assignment/exercise, settlement, halt model or independent fill validation exists.
The invented UTC demo session is not an exchange calendar. No candle-to-option
conversion occurs. Results establish fixture arithmetic only, not profitability,
execution feasibility, data entitlement or permission to record raw callbacks.

Budget remains $0. No paid data, signup, purchase, live request, callback recording,
user database, real order, deployment or merge. Trading remains NO-GO, orders
DISABLED, live data DATA_BLOCKED and recording HOLD. Frozen historical sessions
remain 2024-01-19, 2024-03-08, 2024-03-11, 2024-03-15, 2024-06-03, 2024-07-03.
The fictional test date is not a seventh research date or historical study.

## Verification

`python -B -m unittest -v test_synthetic_options_execution` runs focused synthetic
regressions. `python -B offline_checks.py` discovers them under OfflineGuard along
with inherited tests. The dedicated CI workflow also runs focused tests under
OfflineGuard on Windows/Linux and Python 3.11/3.12. No external service is used
by tests. Rollback removes this document, module, test and dedicated workflow;
there are no schema or existing research-data changes.
