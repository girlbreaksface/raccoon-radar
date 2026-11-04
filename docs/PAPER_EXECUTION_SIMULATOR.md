# Synthetic paper execution simulator v1

PR58 emits directional events; this module adds fictional share fills and a
cash/position ledger without changing the signal calculation. The pure entry
point is `paper_execution.simulate(ReplayInput, tuple[Quote], Config,
synthetic=True)`. Signals are generated internally by PR58, never accepted from
an external live adapter. Real replay bundles or quotes marked non-synthetic
are rejected. Synthetic flags are trusted fixture declarations, not data-origin
authentication. No arbitrary code/data caller is treated as a security boundary.

## Frozen assumptions

| Rule | v1 behavior |
| --- | --- |
| Instrument | Fictional SPY/QQQ shares only; bullish long, bearish short |
| Quantity | Fixed integer per fill; default 1 share |
| Entry | First same-symbol quote strictly after decision and at/after configured latency |
| Deadline | Decision + 30 seconds by default; exact deadline included |
| Price | Buy at ask plus adverse slippage; sell at bid minus adverse slippage |
| Slippage | Configurable basis points, default 0; no stochastic model |
| Fees | Fixed dollars per fill, default 0; demo explicitly uses $1 |
| Exit | First same-symbol quote at/after fill time + 60 seconds by default |
| Exposure | One open or pending entry per symbol; later signals ignored while occupied |
| Data block | Subsequent DATA_BLOCKED/PROFILE_BLOCKED replay step cancels pending entry; valid quotes can still close open exposure |
| Capital | $10,000 default; entry requires notional plus fee in available cash |
| Short collateral | Lock proceeds plus 100% entry notional (2x entry notional total) until close |
| Missing exit | Leave open and report last known liquidation mark/time; no invented end-session fill |

Quotes have one fictional event/availability time and unlimited executable size.
They must be positive finite decimal bid/ask strings (up to 8 decimal places),
uncrossed, in the declared common session, and strictly ordered by (time, symbol).
Same-symbol duplicate times are rejected; different-symbol same-time quotes use
lexical symbol ordering (QQQ before SPY), which determines scarce-capital priority.
At an equal timestamp, replay gates and decisions precede quotes; a new decision
cannot use that exact quote for entry. A signal arriving on an exit timestamp
still sees the position open and is ignored. Ignored/canceled/expired entries
are not retried. Opposite directions never automatically reverse a position.

Inputs must explicitly model the quotes: no candle OHLC-to-bid/ask conversion,
midpoint fill, historical acquisition, hidden spread, random seed, ambient clock,
broker order object or API is used. Changes to future quotes cannot rewrite
earlier fills. Holding periods begin at entry fill, not signal time.

## Ledger and reports

All accounting uses a fixed 50-digit local Decimal context, independent of the
caller's precision/rounding. Values are decimal strings; no currency/tick rounding
is implied. Cash subtracts buy notional/fees and adds sell notional minus fees.
Realized net includes both entry and exit fees. Open marks use the last bid for
longs/ask for shorts plus adverse slippage; unrealized net includes the paid
entry fee, but no unexecuted exit fee. Equity = cash + signed marked positions;
equity minus initial cash equals realized net plus unrealized net.

Reports include each fill, each signal's terminal/current status, open positions,
last mark times, cash, collateral, available cash, realized/unrealized net,
configuration, input/run hashes, and the PR58 signal-run hash. `as_of` is the
later of the final replay cutoff and last quote. Pending entries expire against
that horizon; open positions do not disappear at the horizon. A last-known mark
can be stale; timestamps expose this and no current liquidation value is claimed.
Hashes identify inputs/results, not authenticated provenance. Source commit and
source hashes belong in the caller's export manifest.

This is not a margin engine: no mark-to-market collateral changes, margin calls,
borrow availability/fees, funding, dividends, halts, queueing, market impact,
partial fills, size/depth, trading-session extensions, stops, targets or options.
Adverse losses can produce negative cash/equity; no forced liquidation is
invented. Default zero costs are illustrative, not empirically calibrated.
No performance, probability or executable-return claims follow from this model.

## Review and reproduce

```text
python -B paper_execution_demo.py --scenario closed
python -B paper_execution_demo.py --scenario open
python -B paper_execution_demo.py --scenario expired
python -B -m unittest -v test_paper_execution
python -B offline_checks.py
```

The predefined fictional closed demo produces two entries and two timed exits:
SPY long $100 to $110; QQQ short $100 to $90; $1 per fill. Combined hypothetical
net is $16 and final cash/equity is $10,016. This fixture arithmetic is not
market evidence. The other demos expose open marks and missing-entry expiry.

Tests cover spread/fees/slippage, long/short cash and collateral, capital priority,
strict next-quote timing, latency/deadlines, holding boundaries, missing quotes,
pending cancellation, ignored reversal, expiry recovery, deterministic replay,
future-quote prefix invariance, invalid inputs and synthetic/data gates.

No provider SDK, network, user databases, raw callbacks or order APIs are used.
All output says SYNTHETIC_ONLY and broker_execution DISABLED. Live observation
and raw retention gates remain unchanged. No merging/deployment is authorized.
Rollback removes the four added files; no store/schema migration is involved.
