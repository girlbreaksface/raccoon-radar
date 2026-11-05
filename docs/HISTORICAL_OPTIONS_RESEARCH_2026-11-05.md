# Historical SPY/QQQ option quotes — decision November 5, 2026

Research completed from public primary vendor documentation. No subscription,
license acceptance, paid request, account mutation or data purchase performed.
Empirical validation remains BLOCKED. No quote dataset is acquired or certified.

| Candidate | Documented fit | Cost and rights status |
| --- | --- | --- |
| Cboe DataShop Option Quotes | OPRA-listed ETF options, NBBO price/size at one-minute or custom intervals; history from January 2012. Appropriate for a first interval-data feasibility study, not tick execution proof. | Symbol/date/interval/analytics selection determines quote. Public unconfigured subtotal is not a price. Obtain written SPY+QQQ-only estimate and retention/internal-use rights before purchase. |
| ThetaData historical quote/flat-file services | Option quote records distinguish interval end from last NBBO update time, allowing quote-age filtering. Flat-file delivery and per-contract historical services have different coverage/access constraints. | Retail page says personal use only; no redistribution/business use. Current numeric tier prices were not verifiable from accessible primary page. Obtain tier, history and usage estimate; confirm terminal/access requirements and rights. |
| Databento OPRA | OPRA schemas and definitions; historical pay-as-you-go and minute consolidated quotes documented. Candidate for granular causal reconstruction after schema/time audit. | Public Standard headline $199/month is not an approved SPY/QQQ historical query estimate or a complete license quote. Obtain dataset/schema/date estimate and applicable historical/non-display/retention terms. Do not extrapolate live licensing to historical rights. |

Cboe cautions that quote-size capture changed June 22, 2026: earlier size could
update without a price change; later size is taken at the most recent price
change. Early-close scheduled delivery may contain earlier closing quotes.
These regime boundaries must be audited rather than treating snapshot time as
fresh executable availability. ETF underlying bid/ask is included; optional
analytics are not needed for a first price-based test. Cboe's published annual
SPY one-minute file estimate with analytics is about 20 GB compressed, 145 GB
uncompressed; QQQ size and our stripped query need an actual estimate.

Primary sources checked:
- [Cboe Option Quotes](https://datashop.cboe.com/option-quote-intervals)
- [Cboe contracts and data policies](https://datashop.cboe.com/data-policies)
- [Theta quote schema](https://www.thetadata.net/docs/operations/option_flat_file_quote.html)
- [Theta pricing/use categories](https://www.thetadata.net/pricing)
- [Databento OPRA specifications](https://databento.com/docs/datasets/opra-pillar)
- [Databento OPRA historical plans](https://databento.com/blog/introducing-new-opra-pricing-plans)
- [Databento pricing/estimator](https://databento.com/pricing)

## Acquisition questions and acceptance evidence

For each vendor obtain a fixed SPY/QQQ scope, expired/delisted contracts and
point-in-time instrument definitions, correction policy and version, timezone,
DST, event/receipt/publication timestamps, interval endpoint convention, quote
conditions and size units. Verify zero/crossed/locked quotes and stale carry
semantics against independently sampled records. Preserve source values exactly.
Distinguish exchange event time, vendor capture, interval boundary, file delivery
and hypothetical strategy availability; historic delivery is not a live receipt.
No timestamp field alone proves production latency or original availability.

Rights review must cover private algorithmic/non-display research, local raw
storage and backups, retention after cancellation, derived results, uploading
to a private repository/CI/cloud/AI service, commercial use and redistribution.
Default acquisition design keeps licensed raw quotes outside GitHub and cloud CI;
share hashes and permitted aggregate evidence only. Public availability is not
permission. A written quote/license and separate user purchase approval remain
external dependencies. No vendor contacted on the user's behalf.

Budget request should separate one-time historical bytes, subscription/terminal,
exchange/license/non-display charges, taxes, storage/egress and renewal. Start
with an approved sample rights review, then a small SPY/QQQ-only quote for a
fixed date/contract range; never trigger a metered download to discover cost.
Selection decision is deferred until the same scope has comparable total costs.

## Execution costs and model

Buy at the first eligible ask after decision plus prespecified delay; liquidate
at eligible bid. Respect displayed size, nonnegative spread, contract multiplier,
tick size and contemporaneous contract definitions. No midpoint fills, last-trade
fills, synthetic option pricing or guaranteed standing-size execution. No quote
means unavailable, not a free exit. Record censored positions and missing exits.
When only minute snapshots are licensed, delay to the next complete snapshot;
do not assert subminute fills or infer intraminute stop/target order from OHLC.

Primary test uses one contract and 1 second decision delay on tick data, or next
complete snapshot on interval data. Stress delays 250 ms and 5 s only where tick
timestamps support them; stress adverse slippage 1 and 2 valid contract ticks per
side, quote age/size and rejection assumptions. Include premium, spread, both
sides' commissions/platform/clearing/regulatory fees and any minimum/rounding.
Fees must be versioned by trade date, broker entity, account plan and product;
paper fills cannot prove actual paid fees. The current U.S. schedule is a source
to audit, not historical account-specific proof:
[Moomoo U.S. fees](https://www.moomoo.com/us/support/topic4_66).
The rehearsal's $0.65 per-side amount is fictional, not a claim about this account.

## Chronological frozen validation plan

The adjacent JSON freezes this proposed protocol and candidate date partitions,
not unseen-data eligibility. Dataset/source/license/fee/calendar hashes are empty
and all empirical gates remain BLOCKED. Before any outcome is inspected, inventory
all prior research and dates; a previously inspected period cannot be relabeled
untouched holdout. If candidate holdout is contaminated, reserve a later genuinely
unseen period and record a new version before opening it. Keep the old protocol.

Candidate development 2023–2024, tuning 2025, final holdout January–October 2026.
Use complete exchange sessions in chronology; no random row split. Freeze code,
features (HLC3 VWAP/SMA-seeded continuous EMA9/21, 100 prior bars, 09:45 gate),
contract rule, fees, delays, exits, exclusions and all tried hypotheses before
outcomes. The offline indicators currently accept only 2026 scheduled sessions;
historical calendar support and authentic finality must be separately validated
before these earlier partitions can run. The proposal is not a runnable dataset.

Candidate contract rule: same-day-expiry standard multiplier-100 SPY/QQQ options,
call for bullish and put for bearish, nearest strike to contemporaneous underlying
midpoint with deterministic lower-strike tie break, ask premium <= $30/contract,
one contract, no substitution when unavailable. This is a proposed research rule,
not approved production configuration. Freeze exact spread/size/age eligibility
after vendor schema acceptance, before outcomes. Exit target +20% or stop -15%
of executable premium (fees included in net results); exit by 15:45 ET or 15 minutes
before an early close, whichever is earlier. No overnight/expiry exercise model.
Three entries/day across the pair; existing operational limits remain unchanged.

Purge events whose outcome horizon crosses a partition; embargo one full session
after each boundary. Warmup may use past features only, never future labels.
Use expanding training windows with fixed validation blocks; final holdout runs
once with a frozen manifest and no retuning. Any change after inspection creates
a new hypothesis and needs a new untouched evaluation period.

Report every evaluated setup, exclusions and missingness, eligible contracts,
trades and sessions, net expectancy, drawdown, turnover, fill assumptions and
cost sensitivity. Cluster uncertainty by session jointly across SPY/QQQ;
report symbol dependence and overlapping observations, avoid treating trades as
independent. Prespecify session bootstrap intervals and multiplicity adjustment
for the complete hypothesis registry. Insufficient independent sessions or
nonpositive cost-adjusted lower confidence bound yields inconclusive/no edge;
passing software tests never substitutes for this evidence.
