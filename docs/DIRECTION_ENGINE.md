# Direction research engine — review proposal
Source baseline: main b0ad02dc996b00406e7da08fb33b6382f658ea40. This is a NEW standalone pure Python module, not a change to existing calculations, ingestion, GUI or research stores.

## Architecture and input contract
`direction_engine.evaluate(rows, symbol=..., session_open_et=..., session_close_et=..., as_of_et=..., interval_evidence=..., config=Config())` produces BULLISH CANDIDATE, BEARISH CANDIDATE or NO TRADE. A candidate is a descriptive research hypothesis, not an executable recommendation.

Each row is a single-symbol canonical 1-minute observation with:
- symbol and original raw_timestamp (opaque, nonempty and preserved);
- explicit interval_start_et, interval_end_et and available_at_et as naive ET wall strings YYYY-MM-DD HH:MM:SS;
- complete=True; finite positive open/high/low/close with valid bounds; finite nonnegative volume.

The upstream adapter must separately preserve provider responses and justify the interval mapping. The engine NEVER derives intervals from raw_timestamp. No adapter/provider is integrated here. interval_evidence requires a reference and status VERIFIED (caller assertion of independently reviewed mapping) or SYNTHETIC (fixture only). Missing/UNVERIFIED evidence yields NO TRADE. The module cannot authenticate that reference; labeling real data SYNTHETIC/VERIFIED without evidence is not acceptable. Explicit session bounds are caller supplied, not a calendar lookup.

Only rows with available_at_et <= as_of_et participate, and their interval must have ended by availability. Future prices/volume are not inspected or hashed. Current incomplete rows, gaps from session open, duplicate intervals, wrong symbol/session, ordering errors, invalid data and stale snapshots fail closed. Staleness tolerance (2 minutes) is a configurable hypothesis, not measured feed latency. No minute is fabricated or raw timestamp rewritten.

## Frozen version-1 hypotheses
- EMA9/EMA21 on session closes, SMA-seeded at the relevant period; alpha=2/(n+1), reset every session. Period labels are fixed; changing their meaning requires a new reviewed definition. [Fidelity's EMA reference](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/ema) documents this conventional recursive basis; it does not validate this strategy.
- OHLCV-only VWAP measure = cumulative HLC3*volume / volume. This is explicitly a CANDLE PROXY, not transaction VWAP. [TradingView's bar-based VWAP reference](https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/) describes typical-price aggregation; different inputs/anchors produce different measures. Existing Market Intelligence's OHLC4 proxy is unchanged.
- Current volume >= 1.2 times the mean of the PREVIOUS 20 bars; current volume is excluded from its baseline.
- Opening range: first 15 completed intervals after caller-declared session open; candidate is outside its high/low. All first-15 bars are required before classification.
- Five-bar level: high/low of the five bars BEFORE the event candle; close strictly outside that level. This is a close-location test, not an assertion that a fresh crossing occurred.
- EMA9 rejection: current high touches/exceeds PREVIOUS completed EMA9, opens at/below it and closes below it with a bearish body. Bullish support is the symmetric low/open/close condition.
- Bullish conjunction: close > EMA9 > EMA21, EMA9 rising, volume confirmed, close above the candle proxy and opening range, and five-bar upside break OR EMA9 support.
- Bearish conjunction: inverse trend/location plus five-bar breakdown OR EMA9 rejection.
- Minimum warmup is max(22, volume_lookback+1, opening_minutes+1, 6). No cross-session warmup carry.

All thresholds/conjunctions are testable design hypotheses, chosen BEFORE a real-data study. They have no fitted confidence score or demonstrated edge. Config includes volume/lookback/opening/staleness hypotheses; EMA periods remain 9/21. Zero-volume/zero-baseline, unavailable proxy and numeric overflow never create a candidate.

## Explainable output
Each result contains raw timestamp, interval end, as-of time, symbol, evidence status/reference, config, engine version, canonical visible-input SHA-256, data-quality state/issues and observations. Observations show EMA values, prior EMA line, proxy basis/value, previous-volume baseline/ratio, opening/five-bar levels, pattern and trend booleans. Invalid/warmup inputs clearly indicate indicators were not evaluated/ready. NO TRADE includes concrete reason codes, not a confidence estimate. READY data does not guarantee a candidate.

The hash identifies normalized visible feature inputs; it is not the original provider/CSV byte hash or evidence of source authenticity. All inputs remain unchanged. No file, database, socket, process, quote or order API exists in this module.

## Synthetic verification and limits
Nineteen tests were written before implementation/fixes. They cover hand-checkable EMA/proxy/volume values, both candidate directions and QQQ partitioning, independent EMA9 support/rejection branches, neutral/low-volume reasons, unknown interval evidence, incomplete data, delayed availability, future-tail invariance (including invalid future values), gaps/duplicates/order/session errors, malformed OHLCV/intervals, warmup/zero volume/staleness, deterministic input-preserving hashes, fixed labels, overflow and explicit 16:00 canonical boundaries.

Local Windows/Python 3.12.14: all 88 tests (69 main + 19 engine), guarded runner and compilation pass. Windows/Linux Python 3.11 CI runs this branch. Synthetic behavior does not establish Moomoo labels, real availability history, calendar/DST handling, statistical significance, fills, options performance or trading utility.

## Approval gates
Review the canonical interval/evidence contract and each conjunction/threshold before approving engine use. Historical evaluation is a separate dependent PR with frozen parameters and chronological splits; the dashboard remains a separate proposal. A real adapter cannot be enabled until raw-retention, completion, pagination and provider evidence contracts are approved. No automatic merge, UI integration or order routing is part of this PR.
