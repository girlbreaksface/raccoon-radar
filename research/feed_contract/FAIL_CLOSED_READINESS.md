# Four fail-closed regressions and readiness gates

Scope: tests and documentation only, stacked on PR52 commit
87a9d73edf1e931094dc618570b48b3758fc014e. No runtime edits.

New synthetic tests exercise existing implementations:
- Invalid candle price/volume observations, malformed shapes, nonfinite and nonpositive
  prices, and impossible OHLC ranges block all IDs. An invalid visible replacement
  cannot resurrect a prior FINAL; the earlier receipt cutoff remains unchanged.
- Explicit HALTED, RESUMED and RECOVERING health states block until separately
  VALIDATED evidence is visible by both time and sequence. Recovery cannot fill gaps.
- Existing pinned comparator timestamp parser converts all six frozen dates at 10 ET,
  plus November DST boundary dates; rejects spring gaps, ambiguous fall times and
  contradictory explicit offsets; distinct valid fall offsets remain distinct.
- LIVE/HISTORICAL/MIXED context modes fail closed at the synthetic consumer boundary.

Limitations: invalid **bid/ask quote** validation is NOT_IMPLEMENTED. These are OHLCV
observations, not option quotes. No per-row source identity exists in this adapter;
mode rejection is NOT enforcement against mislabeled or mixed feed rows. Actual
live/historical adapter isolation remains NOT_IMPLEMENTED. Halt tests model externally
supplied health, not exchange halt detection or a safe automatic recovery protocol.
DST tests call the frozen comparator's parser, not a provider mapping or production
feed adapter; calendar/interval authority remains unresolved. These explicit gaps
must not be reported as completed production capabilities. No market packets,
options chains, fills, returns, or predictive evidence were tested.

## Zero-cost observation checklist (proposal; no authorization to run)

Every unchecked gate is HOLD. Record reviewer, exact code hash, evidence hashes,
date/time, scope, expiry and revocation for each approval. CI success cannot approve
integration or authorize collection. Budget stays $0; no cards, paid trials or purchases.

- [ ] Independent review of stacked drafts, tests and limitations; separate explicit
  approval before merge or runtime changes. Preserve original raw evidence and stores.
- [ ] Confirm existing no-cost entitlement and API/local retention rights using current
  official terms for the exact account, instruments and endpoints. If unclear, STOP;
  do not subscribe, contact providers or accept new terms on the user's behalf.
- [ ] Separately authorize one supervised read-only observation with exact pinned
  SDK/OpenD environment, symbols, duration, record/byte limits and local destination.
  Working native dependencies must satisfy host policy; no policy workaround.
- [ ] Verify no order/account/unlock paths, no trading credentials, no paper broker
  submission, no detector integration and no writes to user research databases.
- [ ] Retain existing CAPTURE_PLAN limits: SPY/QQQ K_1M, 120-second observation,
  300-second watchdog, bounded journal/queue, silence and clock checks, no reconnect
  or retry. Use a fresh exclusive destination; stop on any guard failure.
- [ ] Log entitlement, endpoint, versions, raw source timestamps/bytes, receipt and
  monotonic clocks, adjustment/session flags and sealed provenance. Keep private
  captures local. Missing coverage, unknown finality and mapping stay explicit.
- [ ] Verify journal integrity and offline replay determinism; separately establish
  authoritative calendar/DST/early-close semantics, interval mapping, corrections,
  finality, feed identity and source separation before strategy eligibility.

## Paper-readiness checklist (offline ledger first; still no orders)

- [ ] Implement and independently review actual bid/ask validation: missing/zero/
  negative/nonfinite/crossed quotes, stale/future timestamps, sizes, spreads, contract
  multiplier, expiry, entitlement and feed origin; reject invalid replacements.
- [ ] Implement source-scoped live/history namespaces and authority; test mixed rows,
  same-symbol timestamp collisions, history backfills and revisions without leakage.
- [ ] Authoritative halt/resume handling, fresh quotes and complete coverage after
  revalidation; disconnect/gap/restart scenarios must fail closed with no stale signals.
- [ ] Freeze paper protocol, observation window and acceptance thresholds before
  forward collection; record all exclusions, misses, censoring and failures. Previously
  inspected sessions are development evidence, never untouched holdout.
- [ ] Validate a fill model against executable bid/ask, spread, latency, fees and
  slippage; no midpoint/candle-close fills assumed executable. Define maximum loss
  and gap behavior; stops are not guaranteed fills.
- [ ] Preserve proposed research constraints ($30 premium, 20% target, 15% stop,
  three daily trades) as unvalidated hypotheses; do not reinterpret them as proven
  risk controls. Require a reviewed ledger and all predefined acceptance gates.
- [ ] Separate explicit authorization for any future paper broker connection or real
  orders. This document grants neither. Trading stays NO-GO; merge stays HOLD.

Frozen study sessions remain 2024-01-19, 2024-03-08, 2024-03-11, 2024-03-15,
2024-06-03, 2024-07-03 for SPY/QQQ. November cases are synthetic DST unit inputs,
not added study sessions. Existing research evidence, thresholds and study gates
are unchanged: PROVISIONAL / UNKNOWN / DATA_BLOCKED, completeness NOT_ESTABLISHED.
