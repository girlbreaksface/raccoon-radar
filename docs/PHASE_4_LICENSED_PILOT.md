# Phase 4 licensed historical pilot

Reviewed November 14, 2026 against Phase 3 at b17e0f4. No account-specific
provider entitlements, quotes, or licensed pilot extracts were available.
Runtime and paper risk rules remain at their Phase 3 settings.

| Input | Public pricing and sample coverage | Blocker for strict replay |
| --- | --- | --- |
| Databento CME ES/NQ | GLBX.MDP3 trades and definitions are historically metered by uncompressed DBN bytes. $125 in credits advertised for new accounts. Exact per-request USD estimate and available credits require an entitled account. | Request dated outrights and original event/capture timestamps, sequence, flags, price/size and definitions. Confirm correction/bust coverage, capture gaps and replay rights. Minute OHLCV is only a retrospective comparison. |
| Massive consolidated SPY/QQQ | Basic is $0 for historical aggregates. Stocks Developer is $79/month and includes historical SIP trade flat files. Public trade schema shows participant and SIP timestamps, sequence and correction fields. | SIP receipt is not application receipt. Confirm original prints plus as-published cancel/correct lineage, clock and delivery lag, and non-display permission for the exact plan. Final REST bars incorporate late corrections. Ask for as-published bars with original delivery timestamps if the trade history lacks correction lineage. |
| Databento OPRA NBBO | OPRA.PILLAR historical usage is metered. The dataset advertises history from April 2013, with schema-specific ranges. Exact price and credit coverage are unverified. | Use CMBP-1 for selected raw OSI contracts. Require valid ts_recv, flags, observed quote time, both sides and per-side freshness evidence. Some historical source data substitutes event time for receive time and sets F_BAD_TS_RECV. Verify the precise dates with metadata and delivered records. A consolidated update can carry an older bid or ask. |
| ThetaData OPRA and Greeks | Options Value $40/month has one-minute intervals. Standard $80/month lists ten years of history, tick NBBO and first-/second-order Greek endpoints. Pro $160/month lists fourteen years. The public sample bundle advertises stock trade/quote/aggregate examples; free account access is primarily historical EOD, insufficient for the five-second quote gate. | Historical analytics are computed from historical option and underlying inputs. Require quote and underlying timestamp semantics, model version, theta/vega units, rate and dividend publication clocks, computation timing and a timestamped match to the actual NBBO. Label reconstructed analytics as such. The published retail agreement permits internal personal research during the term, prohibits redistribution and requires expunging data and derived works within 30 days of termination. Obtain written pilot-specific rights if longer retention is required. |

Sources: [CME feed](https://databento.com/docs/datasets/glbx-mdp3),
[OPRA feed and capture caveats](https://databento.com/docs/datasets/opra-pillar),
[Databento pricing](https://databento.com/pricing/),
[metadata](https://databento.com/docs/api-historical/metadata?lang=python),
[Massive trades](https://massive.com/docs/rest/stocks/trades-quotes),
[trade flat files](https://massive.com/docs/flat-files/stocks/trades),
[corrections](https://massive.com/knowledge-base/article/why-is-massives-market-data-different-from-other-providers),
[Massive terms](https://massive.com/legal/market-data-terms-of-service),
[ThetaData prices](https://thetadata.net/pricing),
[endpoint entitlements](https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html),
[sample bundle](https://thetadata.net/docs/Articles/Getting-Started/Sample-Data.html),
[Greek endpoint](https://www.thetadata.net/docs/operations/option_history_greeks_first_order.html),
[Greek calculation](https://www.thetadata.net/docs/Articles/Data-And-Requests/Option-Greeks.html),
[ThetaData agreement](https://www.thetadata.net/subscriber-agreement).

## Quote-only sample request

Use November 2–6 and November 9, 2026 as a proposed frozen slice, pending
exchange calendar and official contract definition checks. The first five
sessions warm the same-minute baseline. Request 14:30–14:57 UTC on each day
for the equity and futures bars. Use ESZ6 and NQZ6 once confirmed against
CME definitions. Ask for records received around the last minute boundary
as well, so the finalization cutoff can be tested. For calibration only,
start with November 9, 14:49–14:57 UTC and request an independent minute
OHLCV reference for the same window. Compare venue and sale-condition
rules, regular-session eligibility and unadjusted prices.

1. In Databento's historical portal, obtain a quote without submitting a
   download. An existing entitled account can use metadata.get_dataset_range,
   get_dataset_condition, list_unit_prices and get_cost. For the CME trade
   quote pass dataset GLBX.MDP3, schema trades, stype_in raw_symbol,
   symbols ESZ6 and NQZ6 and explicit half-open UTC times. Quote definition
   evidence separately and cover the last definition known before the slice.
   For OPRA, quote CMBP-1 for exact OSI symbols (including root padding)
   and quote definitions, trades and statistics separately. Ask support
   for a sandbox sample or an all-in estimate with written confirmation of
   credit eligibility, balance and zero out-of-pocket cost. Record each
   estimate, currency, scope and expiry. Metadata estimates are based on
   request size; billing follows actual bytes sent.
2. Ask Massive for two unadjusted, consolidated SPY/QQQ extracts for the
   calibration window with participant, SIP and dissemination/capture
   times where available, trade IDs, sequence, venue, eligibility
   conditions and original/cancel/correct messages linked by ID. Include
   a known late or corrected message if the target window has none. Ask
   whether an entitled historical CTA and UTP capture is available as an
   alternative. Databento's EQUS.SUMMARY covers daily summaries and is
   insufficient for this purpose. An EQUS.SIP ID in publisher metadata
   alone does not establish historical access.
3. On November 9, freeze a small set of standard SPY and QQQ call/put
   contracts selected from definitions available before the evaluation
   window. Use one verified expiry and one strike per side per ETF for a
   format calibration sample. Request tick quotes and first- and
   second-order Greeks over 09:49–09:57 America/New_York for those
   contracts from ThetaData. Ask for an example showing whether original
   quote time survives interval sampling. Include underlying bid/ask and
   input timestamps, model settings and effective rate/dividend records.
   Request the full OPRA quote state immediately before the window or
   expand backwards for the same contracts to establish both sides.
   Request trades from the vendor-defined session start for cumulative
   volume, and the last available published OI with original publication
   time. Verify actual expiry clock and multiplier from definitions.
   A limited preselected strike sample validates format only. Ranking
   comparisons require the complete prespecified eligible chain.
4. Ask each vendor to confirm the user/account plan, included exchanges,
   allowed local storage and backups, retention period and deletion terms,
   automated internal non-display replay, derived report sharing, and
   post-cancellation rights. Databento passes through publisher-specific
   terms. Save the agreed rights reference, exact request, schema/version,
   response counts, pagination proof, timezone, entitlement and raw SHA-256
   privately. Keep licensed extracts and derived rows out of GitHub unless
   the applicable terms expressly permit that sharing.

## Adapter acceptance

Before a source is eligible, verify event ordering at minute boundaries
and the first available version, using witnessed publication or a
documented conservative capture proxy and finalization delay. Validate
late records, corrected market data, missing minutes, flags, per-side
quote age, crossed markets and nanosecond ordering before rounding up
availability into Phase 3 microseconds. For Greeks and other ranking
inputs, require observation at or before quote time and availability by
the normalized quote availability clock. Phase 3 rejects revisions and
requires definitions, Greeks, cumulative volume and published OI for
every quote row, including rows used for simulated exits. Verify how
missing inputs affect rankable chain coverage and unpriced exits before
using results. Tick-level fixtures must reproduce a corrected trade, a
stale carried option side, ties at the decision boundary, and a late
analytics input. Use synthetic tests alongside private sample
reconciliation. No calibrated adapter was promoted in this phase.
