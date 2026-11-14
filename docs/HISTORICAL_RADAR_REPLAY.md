# Phase 3 historical replay

The offline importer starts at draft PR #79, based on draft PR #61. The
pre-Phase-3 heads were 43559cc and a81e071. Both had passing Windows and
Linux checks. The replay uses Python 3.11+ and the standard library. The
existing guarded test discovery includes its synthetic tests.

## Candidate sources reviewed November 14, 2026

| Input | Public offer | Replay and licensing considerations |
| --- | --- | --- |
| Dated ES/NQ | Databento GLBX.MDP3 historical CME trades, definitions and minute OHLCV. Historical usage is metered by uncompressed binary size. The public offer advertises $125 in credits for eligible new teams. | Estimate each exact request with metadata.get_cost before any download. Use raw dated outright symbols and the corresponding definitions. The minute bar's interval label is insufficient evidence of publication time. Prefer ordered trades with ts_recv plus a declared window finalization rule. |
| Consolidated SPY/QQQ | Massive Stocks Basic advertises $0/month, five REST calls per minute, two years of minute aggregates and consolidated US stock coverage. No flat files on Basic. The previous day's data is available after midnight ET. | Custom bars are start-stamped in UTC epoch milliseconds. Request unadjusted bars. Historical REST bars may incorporate later corrections and do not establish original bar availability. Use independently captured as-published bars or SIP trades with receive timestamps, eligibility and correction handling for strict replay. Massive's market-data terms require a license for non-display use. |
| Options NBBO and Greeks | Databento OPRA.PILLAR supplies consolidated historical NBBO. ThetaData individual Options Standard is $80/month with tick quotes from 2016 and historical first- and second-order Greeks endpoints. Options Value is $40/month at one-minute granularity and cannot resolve the five-second quote gate. Options Pro is $160/month and adds per-trade Greeks endpoints. | Databento ts_recv is vendor capture time, distinct from exchange event time and application receipt. Check exact OPRA schema dates and per-side freshness. Verify ThetaData's original quote timestamp, availability of model inputs, and Greek units. ThetaData's subscriber agreement permits internal personal research subject to its terms. Confirm export, automated replay and retention after cancellation in writing. |

Sources: [Databento pricing](https://databento.com/pricing/),
[CME dataset](https://databento.com/docs/knowledge-base/datasets/glbx-mdp3),
[OPRA dataset](https://databento.com/datasets/OPRA.PILLAR),
[timestamp conventions](https://databento.com/docs/conventions/common-fields-enums-types),
[cost and coverage metadata](https://databento.com/docs/api-historical/metadata?lang=python),
[Massive pricing](https://massive.com/pricing?product=stocks),
[consolidated history](https://massive.com/knowledge-base/article/how-much-historical-stock-data-does-massive-have),
[prior day availability](https://massive.com/knowledge-base/article/on-the-free-basic-plan-when-can-i-pull-the-previous-trading-days-data),
[custom bars](https://massive.com/docs/rest/stocks/aggregates/custom-bars),
[corrections](https://massive.com/knowledge-base/article/why-is-massives-market-data-different-from-other-providers),
[market data terms](https://www.massive.com/legal/market-data-terms-of-service),
[ThetaData pricing](https://www.thetadata.net/subscribe),
[endpoint entitlements](https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html),
[Greeks model](https://thetadata.net/docs/Articles/Data-And-Requests/Option-Greeks.html),
[subscriber agreement](https://www.thetadata.net/subscriber-agreement).

No account eligibility, exact historical request cost, downloaded sample, or
account-specific permission was verified. Vendor history depth describes the
requestable archive. Confirm locally retained raw extracts, internal non-display
replay, derived-result sharing and post-termination use under the applicable
vendor/exchange agreements before acquiring the data.

## Normalized import and replay

Run `python -B historical_radar_replay.py INPUT.json` to emit a deterministic
JSON report, including the input SHA-256, source manifest and per-decision
rankings, rejections and hypothetical exit results. The importer reads the
canonical JSON produced by an upstream exporter. It does not connect to
vendors, reinterpret start-stamped bars, or infer publication time from end
labels. See the runnable fixture in `test_historical_radar_replay.py` for a
complete example. Generate an input with:

```sh
python -B -c "import json; from test_historical_radar_replay import fixture; print(json.dumps(fixture()))" > synthetic-replay.json
python -B historical_radar_replay.py synthetic-replay.json
```

- Top level: version 1, kind synthetic or historical, sources, calendar,
  sessions, bars and quotes. Each source specifies provider, dataset,
  coverage, clock, artifact (immutable raw identifier or SHA-256), and
  rights_reference. A historical clock is recorded or capture_proxy. Those
  fields are importer assertions from the exporter and require independent
  verification. Preserve endpoint, schema version, timestamps, publication
  rule, adjustment flags, request parameters, entitlement, retrieval time
  and pagination evidence with the referenced artifact.
- Evidence rows carry source, observed and available in UTC with Z and at
  most six fractional digits. Retain native precision upstream. Round
  availability up when needed and resolve any microsecond collisions against
  vendor sequence numbers before import. Calendar evidence represents the
  published common cash schedule and must predate the first declared open.
  Each window supplies ID, root, dated contract, opening, closing, from and
  until. Both roots use the same cash bounds on shared sessions. Coverage
  spans consecutive minutes in (from, until], with separate windows for
  warmup and comparison as dictated by the study design.
- Bars carry session ID, symbol, instrument, interval end as observed,
  high, low, close, volume, complete and delayed. Keep raw records separate.
  The exporter must emit the original as-published version under its
  declared policy. Duplicate or revised minute bars are rejected.
- Options carry session ID, ETF symbol, contract ID, bid and ask as decimal
  strings, sizes and delayed status. The nested definition, greeks, volume
  and open_interest each have their own evidence clock and value. Use
  standard deliverables, actual expiry, as-of cumulative volume, last
  published open interest and Greeks with theta per calendar day and vega
  per percentage point. Inputs must be known by quote availability. For
  derived Greeks, their evidence time must account for the latest
  underlying, rate, dividend and model input and the computation delay.
- Decisions run five seconds after each eligible event minute with 20
  consecutive prior bars in the window. Missing bars suppress the signal.
  The same-minute median uses the latest five eligible observations of the
  same contract in the prior 30 calendar days. Roll transitions can leave
  the baseline unavailable. Options are evaluated with the latest visible
  quote per contract, observed no earlier than the event bar end.
- Each baseline runs its own paper ledger. An entry selects the top-ranked
  eligible contract. A five-minute exit requires a fresh displayed bid
  available by the exit clock. Entry uses ask plus 0.5% slippage, exit uses
  bid minus 0.5%, and each side costs $0.65. These research assumptions
  exclude price improvement, tick rounding, queue position and latency
  beyond the declared cutoff. Missing exits are unpriced and leave exposure
  open. The $30 premium cap includes entry slippage. The ledger allows one
  contract per entry, blocks another entry in the same ETF while exposure
  remains open and caps entries at three per common session across both ETFs.
- Reports include paired signal agreement, detector flags, contract scores,
  rejection counts, hypothetical entries, priced and unpriced exits and net
  P/L for priced exits. There are no observed fills. P/L over priced exits
  alone can be biased by missing exits.

The six-session fixture crosses a one-hour shift in the UTC cash open. It
yields one rolling-only signal, 35 decisions with neither signal, a second
candidate blocked at the premium cap, and one hypothetical $9.445 net
round trip. The five-session ratio is 1.5x at that signal versus 3x rolling.
These are expected fixture results.

## First licensed pilot

1. Freeze a small date slice with at least five prior eligible sessions and
   one evaluation session before looking at outcomes. Use one dated ES and
   one dated NQ contract without a roll inside the slice. Verify cash,
   futures and ETF options hours and early closes against the exchanges.
2. Confirm in writing the request entitlement, approved extraction,
   internal replay and retention terms. Check Databento metadata for
   date/schema conditions, exact costs and any credit eligibility. Use CME
   trades/definitions and OPRA timestamped NBBO; limit scope by times and
   point-in-time contract definitions. Obtain equivalent SIP coverage with
   as-published prices or receive timestamps. The public Basic REST
   aggregates are suitable for a price cross-check if licensed.
3. Calibrate the exporter on an independent opening/closing OHLCV sample.
   Audit bar boundaries, late trades and corrections, exchange versus
   capture clocks, cumulative volume and prior published OI. Reconcile
   contemporaneous option analytics against their original option and
   underlying inputs. Retain licensed files privately with hashes.
4. Replay the frozen slice and audit lag, gaps, excluded minutes, quote
   coverage, rankable chains and unpriced exits before any performance
   comparison. Then freeze a larger chronological holdout and report
   per-pair results and missingness alongside priced hypothetical returns.
