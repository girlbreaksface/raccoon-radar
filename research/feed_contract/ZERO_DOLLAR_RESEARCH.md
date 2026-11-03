# Operation Zero-Dollar Raccoon

Public documentation checked 2026-11-03 America/New_York. Research only.
PROVISIONAL / UNKNOWN / DATA_BLOCKED; completeness NOT_ESTABLISHED;
merge HOLD; trading NO-GO. No real backtest accuracy or provider qualification.

## Scope and review

Reviewed issues [46](https://github.com/girlbreaksface/raccoon-radar/issues/46)
and [51](https://github.com/girlbreaksface/raccoon-radar/issues/51), and draft
[50](https://github.com/girlbreaksface/raccoon-radar/pull/50) at
`d7f78fd118821282640f6ba6ccca0294f658e92c` (249 added lines, two files).
Its injected JSON tests preserve observations; they bypass protobuf decoding,
do not verify interval mapping, and do not enforce feed compatibility. Whole-seal
verification precedes cutoff selection. Issue 46's provider summary remains
attributed secondary evidence; no private correspondence was opened.

Frozen sessions remain **2024-01-19, 2024-03-08, 2024-03-11, 2024-03-15,
2024-06-03, 2024-07-03**, each for SPY and QQQ. Preserve issue 51's 10:00 ET
selection rule, maximum 12 contracts per underlying/session, and all missing-case
rules. No replacement dates, price queries, optimization or expanded universe.

## Free-source findings

**No suitable free historical options dataset was verified for the six-session
tick-quote / point-in-time expired-chain requirements.** This bounded search
does not prove that none exists. Free EOD data and format samples do exist.
Advertised coverage below is not a checked date/contract inventory. No market
dataset was imported or redistributed; only documentation was inspected.

| Source and primary documentation | Coverage / access / rights | Decision |
|---|---|---|
| [Theta subscriptions](https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html), [sample](https://thetadata.net/docs/Articles/Getting-Started/Sample-Data.html), [terms](https://www.thetadata.net/terms-and-conditions) | Free EOD table starts 2023-06-01, 30 requests/minute, one-day delay; prose instead says one year, 20/minute. Terminal required for API. Historical options quotes are excluded from FREE. No-account sample describes one day of UTP/CTA stock quotes/trades; date, symbols and OPRA options not established. Personal noncommercial license; section 2.1 also restricts archiving, downloading and automation. Sample/replay permissions unresolved. | Not verified for 2024 free access; no free tick options evidence. No Terminal, account or entitlement probe. |
| [Massive pricing](https://massive.com/pricing?product=options), [individual terms](https://massive.com/legal/individuals-terms-of-service), [market-data terms](https://massive.com/legal/market-data-terms-of-service) | Basic $0: EOD/minute aggregates, reference data, five calls/minute, two-year history; quotes require Advanced. All six frozen dates precede a rolling two-year window as of this review. Signup/API credentials needed; no signup performed or card-free onboarding certified. Personal nonbusiness license, no redistribution grant for this project. | Bars are not bid/ask ticks. Expired discovery alone cannot prove intraday listed-as-known chains. |
| [Cboe EOD sample/product](https://datashop.cboe.com/option-eod-summary), [interval product](https://datashop.cboe.com/option-quote-intervals), [policies](https://datashop.cboe.com/data-policies), [license](https://datashop.cboe.com/documents/Cboe_LiveVol_DataShop_License_Agreement.pdf) | Public sample links; product history from January 2012 is not sample coverage. EOD supplies two snapshots, intervals are snapshots rather than ticks. Exact sample dates/SPY/QQQ membership not inspected. Order-scoped license does not establish unrestricted sample replay/redistribution. Interval page repeatedly timed out in this review; do not silently treat prior issue evidence as a fresh page verification. | Free format candidate only; sample-specific license and required session coverage UNKNOWN. No cart or order. |
| [HistoricalData.net samples](https://historicaldata.net/samples.html), [terms section 1](https://historicaldata.net/terms.html) | Explicit free download/evaluation permission without purchase, subject to redistribution restrictions. Options: July–December 2022, 127 EOD files, SPY/TSLA/KO/SPX including SPXW; no QQQ, no frozen dates, no ticks. Public ZIP link, no signup shown. Quote-time field blank in this sample period. | Genuinely free, documented evaluation route, but unsuitable here. No 239 MB download needed. |
| [HistoricalOptionData samples](https://historicaloptiondata.com/sample-files/), [free-data description](https://historicaloptiondata.com/free-data/) | Public delayed 5-/15-minute and EOD sample links. Monthly micro-subset starts January 2003, one changing symbol per month; name/email requested for instructions. Page explicitly permits a short sample backtest, but broader retention/redistribution rights and exact frozen-date SPY/QQQ membership remain unknown. | No tick data; do not submit contact details or assume monthly symbols. |
| [Databento registration explanation](https://www.databento.tech/blog/why-payment-information-required) | Official dated explanation: payment card required to register; $125 historical credits shared across team, expire after six months, excess usage billed. No present account or OPRA entitlement examined. | Excluded by no-payment-card-trial boundary; credits are not an unconditional free archive. |
| [Alpha Vantage docs](https://www.alphavantage.co/documentation/), [Tradier docs](https://docs.tradier.com/docs/market-data) | Alpha Vantage historical options chain is explicitly premium despite demo links and free-key wording. Tradier explicitly excludes expired-option history; tick timesales retention five days and unavailable in sandbox. Brokerage/token access is not a public 2024 archive. | Neither supplies the required free historical sample. No account or demo endpoint used. |
| [Public preservation mirror](https://github.com/anahatsingh-ui/options-dataset-hist), [license](https://github.com/anahatsingh-ui/options-dataset-hist/blob/main/LICENSE), [second mirror](https://github.com/waterscep/sks-options-dataset-hist) | Publisher claims SPY 2008–2025, QQQ 2011–2025 EOD contract-days, public files and MIT attribution. Original author repositories returned 404. Mirror's license text grants Software rights; upstream market-data redistribution authority and original acquisition provenance were not established. Exact 2024 rows and lifecycle coverage not inspected. | EOD only even if licensed; mirrors do not independently verify upstream rights. Not imported or called legally cleared. |

[OCC/OIC's public data directory](https://www.optionseducation.org/referencelibrary/market-data)
links volume, open interest, series/listing and adjustment reports. These are
useful reference sources, not a demonstrated historical tick/10:00 chain archive.
Public reading does not imply bulk redistribution permission. Issue 51 retains
the primary calendar, DST, expiry and disruption references. June 3's contextual
incident does not establish a real SPY/QQQ halt or OPRA quote outage.

## Bounded synthetic plan and implemented fixtures

Warrant for a stacked test-only PR: #50 lacks explicit absent quote/chain and
missing-minute cases tied to the frozen sessions, and its cutoff test does not
compare separately sealed short/extended inputs. `test_zero_dollar.py` adds six
tests using disposable, invented JSON journals: 12 date/symbol cases, at most
three messages each, no option contracts or real quotes. Values 99–102 are
invented. Arbitrary receipt clocks are not historical UTC timestamps.

1. Missing quotes and chain stay null; no bid/ask is generated; DATA_BLOCKED.
2. Missing 10:01 observation remains absent. Invented disruption annotation is
   retained, with no claim of actual halt or generated replacement bar.
3. Old-label revision arrives after a newer label; inclusive receipt cutoff
   changes the selected observation only when the revision arrives.
4. Separately sealed short and extended streams have identical earlier selected
   source observations. Full output/provenance is intentionally not claimed
   prefix-invariant; later corruption can still block replay.
5. Raw labels across all dates remain unchanged, mapping/finality UNKNOWN.
   This does not test timezone conversion or actual session eligibility.
6. Conflicting invented feed/endpoint metadata survives without qualification.
   The observer still groups by symbol/label; this is not feed isolation.

Fixtures use the existing journal's injected JSON decoder, not moomoo packets.
The inherited payload-kind name remains SDK_PROTOBUF_SERIALIZATION; fixture
metadata explicitly says SYNTHETIC_JSON_NOT_PROVIDER_PROTOBUF. No SDK claim.

Remaining plan, **not implemented or qualified**: a separate future offline quote
adapter must reject absent/stale/crossed/zero-sided quotes, absent as-of chain
membership and incompatible stream identities before any selection/fill model.
Use invented expiry identifiers and scenario manifests only; preserve all six
dates, 144-contract maximum, and no replacement for absent rights/strikes.
Test event/SIP/available-at/decoder clocks independently, delayed correction and
cancel linkage, equal timestamps/channel resets, reconnect gaps, known-at-time
action factors, and feature-prefix invariance. Require an explicit versioned
calendar layer for the two DST offsets and July 3 equity/option/expiry closes;
never implement a universal -60-second shift. Simulate a halt/resume and bad
price-band/cancel sequence on June 3 only as invented stress, preserving the
real affected-SPY/QQQ case as missing. Test missing final liquidation quotes as
unfilled/UNKNOWN. No midpoint fills, P/L, accuracy, or profitability claim.

No production adapter is warranted by documentation alone. These tests protect
the existing observer's limited behavior; they do not solve the data blocker.
Rollback is removal of the two added files. Existing runtime, archives, study
definitions and CI workflows are unchanged.
