# Historical options replay v1 — research implementation

Date: 2026-11-04. Base: PR #61 head a81e0710a319890a321834968f0b03d262f52bd9.
Recording HOLD; paper execution HOLD; live NO-GO. No order APIs or capture started.

## Provider feasibility checked first

Official moomoo documentation inspected on 2026-11-04:

- [Get Historical Candlesticks](https://openapi.moomoo.com/moomoo-api-doc/en/quote/request-history-kline.html): request_history_kline returns dated OHLCV/turnover, uses pagination, and describes US timestamps as Eastern. These are candles, not an ordered historical bid/ask/size path.
- [Get Real-time Order Book](https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-order-book.html): get_order_book is a subscribed real-time API, with separate bid/ask server receipt timestamps. Its signature has no historical date parameter.
- [Quote overview](https://openapi.moomoo.com/moomoo-api-doc/en/quote/overview.html) distinguishes these APIs.

Conclusion: no documented historical option bid/ask retrieval endpoint was found in these reviewed OpenD APIs. This is a documentation finding, not proof that every moomoo product lacks such data. No SDK/OpenD/account probe was performed. Historical expired-contract coverage, entitlements, retention rights, timestamp semantics, sizes, and historical chain completeness remain UNVERIFIED. A real-time quote cannot reconstruct an expired option's historical spread. No candles are converted into fictional quotes.

Next evidence needed: provider confirmation or an independently licensed historical quote archive, plus endpoint/version/entitlement/rights, pagination and coverage evidence, provider timestamp semantics, source hashes and a point-in-time contract universe. VERIFIED_QUOTES is the dataset supplier's assertion, not a certification by this program. Do not use it without the evidence above. SYNTHETIC fixtures are never empirical strategy results.

## Implemented contract

`historical_options_replay.py` is a separate offline research module; existing signal, adapter, UI and simulator behavior is unchanged. CLI:

```text
python -B historical_options_replay.py dataset.json existing-output-directory
python -B historical_options_replay.py dataset.json existing-output-directory --parameters "{...}"
```

A dataset has schema `historical-options-replay-v1`, quality SYNTHETIC or VERIFIED_QUOTES, a provenance object, and unique chronological sessions. Each session supplies date, calendar open/cutoff/close with explicit offsets, SPY/QQQ bars and option contracts. The regression fixture in `test_historical_options_replay.py` is a complete executable schema example, explicitly fictional.

Bars are contiguous one-minute end-labeled session prefixes, with strictly increasing end and availability times. Preserve raw provider stamps separately during normalization. Required fields: end, available, open/high/low/close/volume/pv as decimal strings, final=true, revision=0, generation=0. `pv` is actual trade price-times-volume notional for that bar, not OHLC4. Positive volume, internally consistent prices/notional, session boundaries and causal availability are checked. Missing minutes, duplicates, nonfinite values, revisions or reconnect generations abort rather than being silently repaired. Revisions/reconnects require a future independently verified as-of adapter; v1 does not implement that adapter.

Proposed research rule (not production verification): session-reset EMA9/21, seeded by first close, 21-bar warmup; cumulative trade-notional / cumulative volume session VWAP; close < EMA9 < EMA21 and close < VWAP; close below previous five lows; current high >= EMA9 and close < EMA9. All predicates on one finalized bar, PUT direction only. This is the bearish breakdown/rejection hypothesis requested; it does not replace the older bullish/bearish signal engine. Twenty-one bars do not establish convergence of an EMA. Exact production warmup and provider trade-VWAP availability remain open.

Contracts require id, symbol, right, strike, expiry, multiplier and metadata availability timestamp. Only SPY/QQQ same-session PUTs with multiplier 100 and metadata known by the signal are eligible. Quotes require available/observed timestamps; decimal bid/ask, bid_size/ask_size, volume and open_interest. Displayed size >=1, positive uncrossed quotes, <=$0.03 absolute spread, <=5-second quote age and signal age are default research policies, not evidence-backed broker settings. Negative/nonfinite numerical inputs and ambiguous duplicate quote availability abort. Stale/zero/crossed entry quotes reject; invalid post-entry paths become unresolved.

Candidate ranking was added after documenting provider feasibility: consider each candidate's first quote strictly after the signal; require observation after signal and known contract metadata. Reject over-budget candidates before ranking; freeze the earliest eligible opportunity time. Later arrivals cannot improve the selection. Among candidates at that time, rank by relative spread ascending, minimum displayed size descending, absolute strike distance ascending, then ID. No fitted weights, future volume, or hindsight P/L selection. The audit retains the ranking and rejection reasons. Volume/OI are exported but no predictive claim or unverified liquidity threshold is attached to them. Universe completeness/survivorship remains a provider requirement.

One contract, ask + explicit adverse slippage to enter; bid - adverse slippage to exit, floored at zero. Entry premium plus entry fee <=$30. Entry fee/side defaults to $1, slippage/side to $0.005; fees are illustrative, NOT verified moomoo fees. Spread is already represented by ask/bid and never subtracted twice. `cost_scenarios` runs $2 round-trip fees with $0/$1/$3 additional round-trip slippage.

All four variants A +20/-15, B +25/-15, C +30/-15, D +30/-20 receive the identical selected entry within a cost scenario. Bid triggers compare with modeled entry premium; fees affect P/L, not trigger thresholds. Trigger levels are not guaranteed fills: use the actual observed bid, including a bid gapping through a stop. Reject more than three shared entries per day by default. To preserve pairing despite different exits, reserve each symbol through cutoff for all variants: at most one accepted opportunity per symbol/session. This conservative research exposure policy deliberately sacrifices later opportunities; it is not a portfolio simulator. SPY/QQQ can overlap and are correlated.

Replay follows ordered point quotes only, never candle highs/lows. A >5-second gap or invalid quote after entry makes the position unresolved at that point; a later winning quote cannot rescue it. Duplicate timestamps abort because ordering is ambiguous. Exact cutoff observation is required for a time exit. Missing cutoff quote never implies a sale, zero loss, or expiration settlement. Sampled quotes do not prove no trigger happened between observations, even within five seconds. All CLOSED rows are modeled sampled-path outcomes, not broker-confirmed fills or executable returns. No liquidity queue, tick-rounding, partial fills, latency calibration or order reconciliation is claimed.

Exports contain the entire normalized input and provenance, all candle decisions and eligible-signal rejections, quote paths, per-variant entry/exit details, fees/net return/holding time, parameter/input/code/run hashes and Python version. Canonical JSON bytes reproduce under identical code/input/runtime. UUID filenames and exclusive creation preserve old evidence. Independent repeated runs test identical results and export bytes. Hashes detect changed inputs; they do not validate provider truth.

Summaries report completed counts, unresolved/rejected counts, win rate, mean net, profit factor, realized drawdown, loss streak and exit frequencies overall/by symbol. Undefined statistics are null. Unresolved exposure is excluded from closed metrics and remains explicitly counted; summaries cannot establish profitability. No synthetic count is a real sample-size claim. `evaluation_plan` creates 60/20/20 chronological partitions and expanding training windows and discloses previously inspected test dates. This is a frozen-plan helper, not implemented historical walk-forward performance or proof that a holdout is untouched. Freeze hypotheses, dataset hashes, costs and plan before empirical evaluation. Cluster by session and account for overlapping/correlated symbols before inference; uncertainty/sample-size analysis and time-of-day scorecards remain future empirical work.

## Evidence and six open gates

Phase 25: 224/224 standalone assertions and 1500/1500 stress cycles were REPORTED in the referenced conversation. Original executable evidence was not supplied here; these counts were not recreated or folded into CI totals.

PR #61 was verified draft/open/unmerged at a81e071. Its six reported workflow runs were successful: 41863250761, 41863250854, 41863250768, 41863250848, 41863250755, 41863250939. These predate this implementation.

1. Repository integration: partial progress through a new discoverable offline regression suite; Phase 25 equivalence remains unverified.
2. Broker reconciliation: OPEN; no order integration.
3. Production VWAP/warmup: OPEN; explicit research conventions only.
4. Real fees/slippage: OPEN; scenario assumptions only.
5. Historical validation: OPEN; no licensed real quote dataset or demonstrated edge.
6. Paper execution authorization: OPEN/HOLD; development approval does not authorize orders.

Tests run through existing `python -B offline_checks.py`, whose Python validation workflow covers Windows/Linux Python 3.11. Local runtime is Windows Python 3.12.10. See the accompanying validation evidence for results; do not claim Linux execution from a local Windows pass.

## Local validation evidence

Final code: 205 tests passed through the guarded repository suite (Windows Python 3.12.10, 145.472 seconds), including 21 replay tests. Focused guarded replay run: 21 passed. Compilation, CLI synthetic replay, byte-identical repeated exports and staged whitespace checks passed. One trailing blank line in the test file was removed after discovery; no executable test code changed. The two workflows discovering root tests now install tzdata for Windows. Linux/Python 3.11 validation is delegated to CI and must be checked separately. Full local output is preserved in `docs/evidence/historical-replay-windows.txt`; it is local evidence, not hosted CI evidence.
