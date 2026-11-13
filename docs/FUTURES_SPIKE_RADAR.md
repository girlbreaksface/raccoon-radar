# Futures Spike Radar

This offline research module accepts caller-supplied snapshots. It has no network, broker, GUI, database, or order integration. It is independent of the candle-signal simulator in PR 61. Use synthetic inputs for development and CI.

## Replay entry points

1. Supply a verified common cash-session opening and closing time in UTC, including holidays and early closes. For `detect(root, futures, etf, session, as_of)`, pass exactly 21 consecutive, chronological, completed one-minute bars per instrument, labeled by interval end. ES pairs with SPY and NQ with QQQ. Use one dated futures contract throughout the window.
2. Inspect `Spike.flags`. An empty tuple and a nonzero direction identify a confirmed spike. Detection compares event volume with the preceding 20-minute median (at least 2.5×), absolute close displacement with the preceding median high-low range (at least 2× with a 0.25-point floor), and the closing price with the previous 20-minute high or low. The same-minute ETF close return must agree by at least 3 basis points. This is an intraday rolling baseline with no time-of-day calibration.
3. Pass the spike and one as-of chain snapshot to `rank(spike, quotes, as_of, entries=history)`. The hypothetical five-minute ETF move repeats the smaller of the observed absolute futures and ETF percentage moves from the current ETF close. The call or put model applies delta, gamma, time decay and a one-volatility-point adverse stress to bid-based exit scenarios. Entry uses ask, exit uses bid, with 0.5% slippage per side and a $0.65 fee per fill. Quotes require size on both sides, volume of at least 10, open interest of at least 50 and a spread no greater than 25% of ask. Ranking weights positive modeled P/L by displayed liquidity and divides by maximum loss, immediate round-trip friction and adverse scenario loss. These thresholds and costs are synthetic defaults. The scenario is neither a probability estimate nor a fill guarantee.
4. For paper replay, call `record_paper_entry` and carry the returned immutable history into the next decision, serially across both ETFs. It records one hypothetical contract, blocks an additional entry while the same ETF has open exposure and stops after three entries per session across both ETFs. The caller supplies closure timestamps from its paper replay. The $30 maximum applies to ask plus entry slippage for a standard 100-share contract. The maximum-loss field also includes the entry fee. This module does not simulate exits, persist a ledger or reserve capacity across callers.

The detector flags gaps, duplicates, instrument changes, unverified or delayed bars, bar receipt lag over five seconds, a decision more than ten seconds after the bar end, and information arriving after the decision. Quotes need an observation at or after the signal, availability by the decision, age at most five seconds and expiration beyond the five-minute horizon. The ranking window ends after 15 seconds or before the session close, with a full five minutes required for the modeled exit.

## Data needed before a provider-backed evaluation

- Entitled CME ES/NQ trades or finalized minute OHLCV with actual traded contract volume, dated contract identifiers and roll metadata. Supply provider bar semantics and local receipt timestamps.
- Real-time SPY/QQQ consolidated equity trades or finalized minute OHLCV with matching time boundaries, receipt timestamps and adjustment/session metadata.
- Real-time consolidated SPY/QQQ options bid, ask, bid size and ask size with event and receipt timestamps, contract identifiers, rights, expiration timestamps, standard deliverables, cumulative volume and latest published open interest. Supply contemporaneous delta, gamma, theta per calendar day, and vega per volatility point from the provider or a documented model.
- A verified common trading calendar, synchronized clocks, delay/entitlement indicators, and feed gap/revision metadata. Verify replay and storage rights before retaining vendor data.

Run `python -B -m unittest -v test_futures_spike_radar`. Synthetic tests exercise signal direction, data gating, quote eligibility, cost-aware ranking and paper exposure limits. Validate timestamp alignment, assumptions, fills and out-of-sample performance with appropriately licensed data before interpreting rankings as evidence of an edge.

## Compare volume baselines

Call `compare_volume_baselines(root, futures, etf, session, as_of, history)` for paired `Spike` results keyed by `rolling_20_minute` and `prior_session_same_minute`. Use `detect(..., time_of_day_history=history)` to evaluate the second baseline alone. Supply an iterable of `(Session, Bar)` pairs from verified prior cash sessions. For the time-of-day baseline, the denominator is the median of the five most recent eligible observations for the same dated contract at the same minute offset from each session's cash open. Observations must be available by the current cash open. The offset handles daylight-saving changes when session opens are supplied correctly. The comparison uses the same 2.5× threshold and all the same price, ETF and freshness gates.

Missing, incomplete, delayed, wrong-contract and wrong-minute observations are skipped. Duplicate eligible session opens or fewer than five eligible observations suppress the normalized signal with `TIME_OF_DAY_HISTORY_UNAVAILABLE`. Supply a bounded recent history window and audit its coverage. The harness can skip missing days within that window and does not apply a calendar-age cutoff. Contract rolls can leave the normalized baseline unavailable. Early closes only contribute minutes that occurred in those sessions. The same 21 aligned input bars are required by both baselines, so the first 20 minutes are outside the comparison.

Synthetic fixture results, with all price and ETF gates passing:

| Fixture | Rolling ratio and result | Same-minute ratio and result |
| --- | --- | --- |
| Busy minute in prior sessions | 3.0×, signal | 1.5×, below threshold |
| Quiet minute in prior sessions | 2.0×, below threshold | 4.0×, signal |
| Latest five eligible observations | 3.0×, signal | 3.0×, signal |
| Insufficient or ambiguous history | 3.0×, signal | Unavailable |

The harness compares detector decisions only. The fixtures show expected threshold behavior and provide no estimates of signal quality, execution, fill rates or returns. Carry full paper history across sessions so outstanding exposure in the same ETF continues to block entry. The three-entry limit counts entries in the active session.

## Feed feasibility at a zero-dollar budget

Reviewed November 13, 2026. No account, entitlement, quote, or data download was tested.

- **ES/NQ.** Databento lists historical CME Globex trades and minute OHLCV. Use dated contracts and verify bar finalization and roll handling. CME's June 2026 fee schedule lists $1.55/month per exchange for qualifying nonprofessional top-of-book display. Display pricing does not establish programmatic or non-display rights. Confirm API use, storage, and replay terms with the provider. [CME fee schedule](https://www.cmegroup.com/market-data/files/june-2026-market-data-fee-list.pdf) · [Databento CME feed](https://databento.com/docs/knowledge-base/datasets/glbx-mdp3)
- **SPY/QQQ.** Alpaca Basic provides real-time IEX coverage. Its historical equity table lists a restriction on the latest 15 minutes. For historical SIP evaluation, verify endpoint access after that window, bar semantics, and usage rights. Alpaca lists all-exchange real-time equities and OPRA at $99/month on Algo Trader Plus. [Alpaca market data plans](https://docs.alpaca.markets/us/docs/about-market-data-api)
- **SPY/QQQ options.** Alpaca Basic's real-time indicative feed does not satisfy the consolidated quote requirement. Databento lists historical OPRA national best bid and offer and sizes, including SPY and QQQ. Use time-resolved quotes for the five-second freshness check. Verify point-in-time open interest, chain definitions and Greek coverage separately, including any inputs needed to compute Greeks. [Alpaca market data plans](https://docs.alpaca.markets/us/docs/about-market-data-api) · [Databento OPRA feed](https://databento.com/datasets/OPRA.PILLAR)
- **Possible zero-dollar historical pilot.** Databento advertises $125 in historical credits for eligible new teams. Confirm eligibility, research rights, and a pre-download estimate for a small date and contract slice within available credits. No complete zero-dollar feed meeting all requirements was verified. Vendor capture timestamps can support a historical availability proxy. They cannot establish receipt latency at the application, and delayed feeds cannot validate real-time timing. [Databento pricing](https://databento.com/pricing/) · [Databento CME timestamps](https://databento.com/docs/knowledge-base/datasets/glbx-mdp3)

