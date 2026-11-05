# Provisional production indicator profile v1

Decision log — 2026-11-05. Base: draft #72, exact head
`de68494065d5a4d8cbb9053580b832f6d5f71c35`, stacked on #71.

## Scope and decisions

`production_indicators.py` implements the approved provisional SPY/QQQ
one-minute candle calculation conventions as a separate pure offline module.
It is not a production feed adapter, signal strategy, order gateway, or a
replacement for any existing research engine. Every result retains paper HOLD,
recording HOLD, live NO-GO, orders DISABLED, merge HOLD and deployment HOLD.

VWAP uses sum(HLC3 * volume) / sum(volume) for RTH only, resetting at
09:30 America/New_York. This is the approved candle VWAP convention; it is
not trade-level VWAP. EMA9/21 use finalized closes, independent SMA seeds of
the first 9/21 closes, then alpha=2/(N+1); no session reset. The first eligible
candle has 100 prior finalized candles (101 including current). The profile
uses RTH history for both EMAs; extended-hours EMA history remains an unapproved
alternative. Numerical computation uses an isolated Decimal context of 50 digits.
Prices/volume must be exact decimal strings, integers or Decimals, never floats.

No entry eligibility before 09:45 ET, or at/after the exchange close.
The candle ending 09:45 may be eligible once actually available. A 09:44
candle delayed until 09:45 remains blocked. Both the candle boundary and actual
evaluation time must satisfy the opening restriction. This conservative timing
interpretation is provisional. No strategy conditions or risk limits changed.

## Calendar evidence and bounded support

The [NYSE published calendar](https://www.nyse.com/trade/hours-calendars),
reviewed November 5, 2026, defines the bounded 2026 holiday table, including
Good Friday, observed Independence Day July 3, Thanksgiving and Christmas.
November 27 and December 24 close at 13:00 ET. The NYSE Arca section lists
09:30–16:00 core hours. `zoneinfo` maps ET to UTC across DST; CI pins
tzdata 2026.5. Tests cover both DST transitions, holiday/weekend continuity,
early-close continuity and rejection outside calendar coverage. Other years
fail closed. No general weekday-only fallback exists.

Unscheduled closures, emergency notices, clock accuracy, current authoritative
calendar custody and provider-specific session/auction assignment remain
unverified. This published static table does not clear the session-calendar
operational gate. Extension requires a reviewed calendar update and fixtures.

## Data and timing contract

Call `evaluate` with a complete immutable per-symbol receipt snapshot, an explicit
`required_through` interval-end completeness watermark, evaluation receipt time
and sequence. Start at a session open, include every subsequent RTH minute
across complete intermediate sessions. Never sort, fill gaps, drop revisions,
normalize source timestamps or silently replace a candle. Mixed symbols fail;
evaluate SPY and QQQ separately. The supplied completeness watermark must equal
the last candle end. Missing tail detection depends on that caller watermark;
this module does not infer provider completeness from clock time.

Each candle retains separate start/end boundaries, actual `available_at`,
monotonic receipt sequence, explicit FINAL and VERIFIED_START_END assertions,
and revision=0. These labels are caller assertions, not authentication. Future
availability, availability before candle end, regressed availability or receipt
sequence, unknown finality/mapping, corrections, duplicates, gaps, out-of-order
bars, zero/nonfinite volume, invalid OHLC and insufficient history block the
entire snapshot without indicator outputs. Extended-hours inputs fail closed.
The API accepts as-of snapshots only: a caller must not include future receipts
then expect them to be silently filtered. Prior session tails must be complete.

`available_at` in the result is the latest actual candle knowledge time;
`evaluated_at` records when the computation is consumed. Neither is backdated
to the candle end. `causal_quote` requires the same symbol, quote event time
at/after evaluation, receipt at/after event, a strictly later sequence in the
same ordering domain, and receipt before the same session close. Equal wall
times require a later sequence. This is only a timing predicate, not a quote
freshness, spread, entitlement or execution certification.

There is no mutable streaming cache. A correction in any supplied history
invalidates the whole snapshot; rebuild only with independently verified
history after resolving it. This module cannot detect corrections omitted by
a caller, revoke previously exported results, authenticate receipt clocks, or
retain an invalidation latch across calls/restarts. Any future production
integration must retain revision lineage, revoke dependent signals, bind
snapshot/watermark provenance, enforce freshness and prevent reuse of an old
READY_OFFLINE result. No production consumer is connected in this PR.

## Provider inspection: unresolved, no guessed mapping

Existing `research/feed_contract/PROVIDER_CONTRACT_REVIEW.md`, capture and
adapter paths were inspected. Capture keeps raw `time_key`, UNKNOWN finality
and DATA_BLOCKED. Current official [UpdateKL documentation](https://openapi.moomoo.com/moomoo-api-doc/en/quote/update-kl.html)
describes asynchronous candle callbacks and US Eastern `time_key`; its listed
Python fields do not expose a final/closed flag. The page does not establish
the interval start/end contract required here. Label boundaries, watermark,
revision horizon, immutable-after rule, historical availability, adjustment,
completeness, entitlement and auction assignment remain unresolved. Repeated
values, next labels and elapsed time never promote finality. No SDK/network
capture, broker import or provider adapter integration was performed.

## Duplicate-work inspection

Inspected the open PR stack #12–#72, with special attention to #13, #31,
#43–#50 and #68–#72. #13 `direction_engine.py` at
`6e7d1a8804b14aba9d08302bc5db48f31b0706ae` already uses SMA seeds but resets
within a supplied session, uses shorter configurable warmup and naive ET.
The pinned #31 kernel uses first-close EMA seeds, a 35-bar gate and HLC3 proxy.
`historical_options_replay.py` uses session-reset first-close seeds, 21-bar
eligibility and supplied trade-notional VWAP. These are different research
profiles; their outputs/tests and existing stores are preserved. #72 handles
execution recovery and does not implement these indicator conventions.

## Independent evidence and reproduction

`generate_indicator_golden.py` imports no production code: it computes EMA
with an exact Fraction geometric weighted sum, not the production recurrence.
Fixtures contain exact rational numerators/denominators for 101, 120 and 405
candles. The 405 case spans a full prior session plus 15 opening candles;
its VWAP sums only the second session while EMA includes both sessions.
Tests compare values within 1e-24 absolute error. The input formula varies
price and volume periodically and uses nondegenerate H/L/C values.

The committed JSON is independently regenerated and compared by
`production_indicator_checks.py`; its SHA-256 is retained in evidence.
The checker runs the regression suite under OfflineGuard, writes exclusively,
and is integrated as the eighth foundation evidence suite. Foundation
recomputes exact evidence and rejects tampering even if a child exits zero.
Existing Windows/Linux Python 3.11/3.12 CI archives preserve logs, artifact
hashes and Python source hashes. The new JSON fixture hash complements those
Python hashes. Counts are scoped suites, not empirical sample sizes.

Reproduce with `python -B automation_foundation.py --output work/NEW_DIRECTORY`.
The output directory must not exist. Direct numerical tests:
`python -B -m unittest test_production_indicators -v`.

## Remaining gates and rollback

Independent design review, verified provider/finality/clock/calendar provenance,
authenticated broker history, production crash durability, restart-safe risk
counters, kill/cancel policy, actual quote/executable-cost validation and frozen
historical/holdout validation remain open. Separate owner decisions are required
for recording, paper execution, merge and deployment. No notifications or
approval hooks were added. No user databases, schema, order or account state
were changed. Rollback: close this isolated draft; existing profiles remain intact.
