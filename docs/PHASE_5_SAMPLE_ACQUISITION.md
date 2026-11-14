# Phase 5 licensed sample acquisition

Status as of November 14, 2026: awaiting an entitled account or vendor-provided evaluation sample. No provider connector or relevant configured environment credential was available in this workspace. Account plans, balances and exact request prices are unknown. No requests were submitted to providers and no licensed rows were acquired or validated. This is an acquisition runbook for the [Phase 4 pilot](PHASE_4_LICENSED_PILOT.md).

## Frozen request scope

All market windows below are half-open. The NYSE core open is 09:30 America/New_York. The six sessions are November 2, 3, 4, 5, 6 and 9, 2026, all on EST (UTC−05:00). Use 14:30–14:57 UTC for each session; quote each date separately. November 2–6 warm the baseline; November 9 is the evaluation date. Start calibration on November 9 at 14:49–14:57 UTC. Ask for a separately scoped receive-time tail through 14:58 UTC to expose late records and test the finalization boundary. Preserve each record's original timestamps. [NYSE calendar and hours](https://www.nyse.com/trade/hours-calendars).

For the OPRA format sample, request definitions as known by 14:49 UTC on November 9. For each of SPY and QQQ, select the earliest listed standard expiration after November 9 that has a call and put sharing a strike, then choose their common strike nearest the last eligible underlying midpoint observed and available strictly before 14:49 UTC. Break ties at the lower strike. Require a standard 100-share deliverable and record the definition evidence, midpoint, timestamp and four exact padded OSI strings before viewing sample-window quotes. Ask the provider to return those identifiers and selection evidence if the account cannot resolve them; never guess symbols or substitute based on subsequent quote activity. Format checks on four series cannot measure chain coverage or ranking.

## Databento first

In the signed-in portal, inspect account credits, expiry, payment terms and historical entitlements for GLBX.MDP3 and OPRA.PILLAR. Use the Historical download form to stage each request and preview its estimate without submitting. Alternatively use the free [Historical metadata API](https://databento.com/docs/api-historical?lang=python). Check dataset/schema bounds with `get_dataset_range`, dates with `get_dataset_condition`, and then call `client.metadata.get_cost(dataset=..., schema=..., stype_in="raw_symbol", symbols=..., start=..., end=...)` for each row and date. Pass explicit ISO UTC timestamps. For example:

```python
client.metadata.get_cost(
    dataset="GLBX.MDP3",
    schema="trades",
    stype_in="raw_symbol",
    symbols=["ESZ6", "NQZ6"],
    start="2026-11-09T14:49:00Z",
    end="2026-11-09T14:57:00Z",
)
```

| Dataset | Schema and symbols | Estimate separately |
| --- | --- | --- |
| GLBX.MDP3 | `trades`, ESZ6 and NQZ6 dated outrights | Calibration, tail, each six-session window |
| GLBX.MDP3 | `definition`, same two outrights | UTC whole-day range Nov 2 00:00 through Nov 10 00:00, plus any earlier day needed for an effective definition at the first open |
| OPRA.PILLAR | `cmbp-1`, four verified raw OSI symbols | Calibration, plus 14:30–14:49 UTC seed window or separately confirmed pre-window state |
| OPRA.PILLAR | `definition`, same four contracts | UTC whole-day Nov 9 00:00 through Nov 10 00:00, plus earlier effective definition if needed |
| OPRA.PILLAR | `trades`, same four contracts | Nov 9 14:30–14:57 UTC for regular-session cumulative volume, extended back if the vendor's session starts earlier |
| OPRA.PILLAR | `statistics`, same four contracts | Nov 9 UTC day and prior publication day if required for the most recent OI available by 14:49 UTC |

Databento advertises $125 for new users. Verify remaining credit and eligibility on the specific account. Estimates can overstate short windows and definition estimates are accurate only for whole-day multiples. Usage is billed on actual uncompressed DBN bytes sent. Capture the USD estimate, account/plan, timestamp, coverage, credit terms and all fees privately for each request. An estimate or a credit balance alone cannot cap a charge. Proceed only with written permission and a provider-confirmed zero-out-of-pocket sample or a hard zero-out-of-pocket limit that covers the exact extract and fees. Leave streaming and batch job submission untouched otherwise. [Pricing](https://databento.com/pricing/) · [CME feed](https://databento.com/docs/datasets/glbx-mdp3) · [OPRA feed and historical capture](https://databento.com/docs/datasets/opra-pillar).

### Inquiry draft for Databento

Could you confirm historical eligibility and provide separate account-specific USD estimates for the CME and OPRA requests in the table above? Our first deliverable is a small DBN evaluation sample for November 9. Please confirm the dated futures symbols from effective definitions and help resolve the four exact OSI symbols using the stated pre-window rule. Can you provide a permitted zero-cost extract, or confirm a hard zero-dollar limit and available credit for the exact scope including any fees? Please confirm CME trade corrections/busts, sequence and capture gaps and their representation. For OPRA, please include pre-window NBBO state and identify the source time and provenance of each carried bid and ask, including during best-venue changes. If CMBP-1 cannot establish independent side age, what corresponding event evidence can you supply? For OI, please identify original publication time and how duplicate venue statistics should be treated. Please also confirm the rights described below for each publisher.

## Consolidated equities

### Inquiry draft for Massive

Can you provide a permitted zero-cost evaluation extract for unadjusted, consolidated SPY and QQQ trades on November 9, 2026 from 14:49 through 14:57 UTC, plus a separately identified receive tail through 14:58 UTC? Please include the original as-disseminated prints, cancels and corrections in observed order, with linked IDs, tape, venue and TRF, sale conditions, sequence, price/size, participant/SIP/TRF timestamps and actual dissemination or capture timestamps where recorded. Please include a linked example outside the window if no correction is present. Can your service preserve the first known version of a print and provide the time at which the correction was first knowable? Please identify coverage gaps, timestamp precision, any delivery lag and exact account entitlement. If a true trade-message lineage is unavailable, can you supply as-published minute bar versions with original delivery timestamps, or historical CTA/UTP captures? Please also supply an independent unadjusted minute OHLCV reference for the same window with sale-condition and session rules. Confirm the rights below and quote a separate estimate for all six windows.

Massive documents cancel records alongside annotated trades in REST and flat files. Test whether the original values and linkage are recoverable before using the stream as of any cutoff. SIP receipt precedes downstream reception. Corrected aggregate responses serve as retrospective comparisons. [Trade schema](https://massive.com/docs/rest/stocks/trades-quotes) · [Trade FAQs](https://massive.com/knowledge-base/categories/trades) · [Market data terms](https://massive.com/legal/market-data-terms-of-service).

## Point-in-time options analytics

### Inquiry draft for ThetaData

Can you provide a permitted zero-cost extract for the same four November 9 SPY/QQQ series, using tick NBBO and quote-based first- and second-order Greeks from 09:49 through 09:57 America/New_York? Please identify the matching v3 endpoint, interval or tick parameter, plan and date eligibility, and whether end time is inclusive. Include pre-window NBBO state, original timestamps for each side, underlying bid/ask and timestamps, and a join key to the precise option quote. Please distinguish observation, capture, computation and publication times and indicate which are measured. Include model/version and settings, theta and vega units, expiration clock, deliverable and multiplier, effective dividend and rate inputs with original publication times, and one example showing whether interval rows retain original quote time. If historical values are reconstructed, can you demonstrate that the same inputs and model could have been used at the time and establish a defensible availability bound? Please also confirm the sample and derived-report rights below.

ThetaData documents history Greeks computed from quote and underlying inputs. Treat these as reconstructed unless contemporaneous computation and publication can be evidenced. Standard and Pro are listed for first-order quote Greeks. Free EOD data and minute-sampled snapshots cannot establish a five-second per-side gate. Confirm exact access and terms before retrieval. [Greek endpoint](https://www.thetadata.net/docs/operations/option_history_greeks_first_order.html) · [Greek methodology](https://www.thetadata.net/docs/Articles/Data-And-Requests/Option-Greeks.html) · [Subscriber agreement](https://www.thetadata.net/subscriber-agreement).

## Evidence and replay acceptance

- Obtain written plan, publisher and user classification, permitted feeds, automated internal non-display replay, local storage and backups, retention and deletion deadlines, post-termination use and derived-report sharing. Ask whether any exchange filing or fee applies. Keep extracts, licensed derived rows and account details private.
- Save the exact request and entitlement/rights references, quote and expiry, download time, dataset/schema and SDK versions, clock definitions and resolution, record counts, completeness/pagination, and the raw SHA-256. Preserve event, publication and receive times without rewriting raw data.
- For CME verify dated definitions, sequence and event/capture ordering, corrections/busts and gaps. For equities show what was knowable at finalization using a documented downstream availability proxy and compare first-known and corrected OHLCV, including condition-driven inclusion and missing minutes.
- For OPRA verify capture timestamps and reject bad receive flags. OPRA's event clock is the consolidator block time; Databento's receive clock is at its capture server. Earlier subsampled OPRA data before March 28, 2023 lacks CMBP-1 and valid capture time. Inspect flags on delivered rows regardless of date. Rebuild freshness by bid and ask from observed state; a new consolidated row can carry a stale side. Check malformed, crossed and stale quotes and quote availability separately.
- Hold nanosecond ordering through the decision cutoff, then round availability up into replay microseconds. Verify correction arrival, equal-time sequence, a stale carried side and a late analytics input. For rankable rows prove definitions, cumulative eligible volume, OI publication and Greeks available by the quote availability clock. Record missing chain coverage and any unpriced exits. Keep synthetic assertions separate from licensed sample reconciliation.
- Paper settings are $30 including entry slippage, one contract, no averaging down and at most three entries per session. This work changes documentation only.
