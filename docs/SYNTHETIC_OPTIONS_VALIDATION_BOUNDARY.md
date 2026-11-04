# Synthetic options research — validation boundary

**Status:** Draft-only. $0 spending. No merges, no broker orders, no live trading, no provider callback recording.

## What the current components do

- `synthetic_contract_selector.py`: choose one eligible fictional SPY/QQQ same-day contract from a supplied immutable candidate tuple. Selection uses a fictional cutoff-time quote, spread, size, and ask-premium filters.
- `synthetic_options_pipeline.py`: connect a fictional signal to that selected contract, then pass matching fictional observations to the options simulator.
- `synthetic_options_execution.py`: simulate ask-side entry and bid-side exit, configurable **5% or 20% gross exit target**, **15% gross stop**, maximum three filled entries per session, $30 entry premium including configured slippage, and fee-adjusted net P/L.
- `synthetic_target_comparison.py`: compare 5% and 20% targets against identical fictional simulator quotes.
- `synthetic_target_scorecard.py`: aggregate those simulator comparisons across multiple fictional replay sessions, counting net wins/losses only on closed trades.

## Critical interpretation limits

1. **No empirical success probability.** Fictional scenario counts are not actual SPY/QQQ 0DTE win rates, historical performance, or forecasts.
2. **The paired scorecard currently bypasses contract selection.** It compares the same provided quotes at the simulator layer. Do not label it an end-to-end contract-selection backtest.
3. **No forced end-of-session liquidation is modeled.** Open positions are unresolved, not wins or losses. Report them separately. Net P/L may be unknown for stale marks.
4. **5%/20% triggers are gross executable-price changes before fees.** Net results may be zero or negative after commissions/slippage. A 5% target is not a guarantee of profit or of an exit.
5. **The 15% stop is a trigger, not a guaranteed fill price.** The first valid bid after a gap may realize a much larger loss.
6. **No actual exchange calendar or market-hours proof.** Synthetic timestamps and fictional session calendar are not evidence of a real U.S. market session.
7. **No validated OpenD entitlement, option-chain provenance, provider retention permission, real-time feed, or historical 0DTE data.** Recording HOLD, trading NO-GO.
8. **CI tests must pass at the exact PR head** before the implementation can be described as validated. Committed tests alone do not establish a pass.

## Evidence gate before comparing strategies

- All relevant stacked PRs and Windows/Linux CI checks green at their current heads.
- Independently reproduce deterministic fictional results and audit hashes.
- Add end-to-end multi-session comparisons that run **signal -> contract selection -> execution -> scorecard** without bypassing the selector.
- Confirm provider rights and timestamp/quote provenance before any permitted non-fictional research.
- Compare net expectancy, fee/slippage sensitivity, target hit rate, stop rate, unresolved exposure, and time-to-exit on the *same* permitted observations. No conclusions from fictional examples.

This document is a boundary statement, not a claim that any of the above gates have passed.
