# Direction integration review and first-study protocol — design only
Date: 2026-10-27. No study executed. No provider connection, adapter implementation, ingestion change, data access or merge is authorized by this document.

## Reviewed artifacts and integration gates
Main: b0ad02dc996b00406e7da08fb33b6382f658ea40.
Engine #13: 6e7d1a8804b14aba9d08302bc5db48f31b0706ae.
Replay #14: 328135f2695543cde96bb434aaa07201c51c0582.
Adapter design #17: 9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3.

GitHub refs remain at those heads. #13 adds only the engine, two test files and two documentation files. #14's merge-base diff adds only replay, two test files and two documentation files. No existing ingestion, persistence or GUI source changes. #13 is ahead of current main without missing main commits. #14 diverges from current #13 because its branch point is 286eb9b1e7071ebbc83a125dc1062e4723efcad1; it must not be treated as a standalone replacement for #13.

Recommended sequence:
1. Maintainer approves exact #13 head; immediately recheck head/diff, mergeability and Windows/Linux jobs. Merge only after explicit approval.
2. Verify CI on resulting main and record merge/tree identity, especially if squash/rebase is chosen.
3. Retarget #14 to main after that merge; review its newly computed diff and reconcile branch ancestry without force-pushing reviewed work silently. Confirm updated #13 implementation/tests remain in the merge result.
4. Rerun cumulative Windows/Linux CI at the new merge candidate; review any changed head. Obtain separate approval before #14 merge; verify main CI afterward.
5. Adapter and study contracts require independent approval before implementation or real-history evaluation. No GUI/provider wiring follows automatically.

## Review conclusions and limits
Independent Decimal calculations agree with SMA-seeded EMA9/21, alpha=2/(N+1), session reset; HLC3 volume-weighted candle proxy; prior-20-bar volume mean excluding the current bar; strict opening-range breakout bounds and half-open interval membership. The engine's HLC3 proxy differs from market_intelligence's explicitly OHLC4-based proxy; neither is trade-level VWAP, and they must not be silently substituted.

Defaults are testable hypotheses. EMA slope is algebraically redundant given close versus current EMA, apart from floating-point boundaries. OR, EMA and proxy gates are correlated location filters; wide OR and 1.2x volume gates suppress some synthetic trends. That is not evidence of lost profitable signals. Inputs remain unchanged and repeated valid inputs give identical results. Caller-owned mutable objects still require sealing before concurrent use.

Replay filters records by availability cutoff before feature snapshots and label indexing. Post-cutoff revisions cannot alter earlier labels or reason codes in regression tests. Revisions known by label cutoff can change retrospective labels or cause duplicate exclusions; that is a declared label vintage issue, not permission to backdate corrected feature values. Current replay cannot resolve a full revision stream into bitemporal frames. Invalid canonical availability/session fields may raise; this API requires validated input and is not a raw-provider adapter.

No filesystem, database or network operations occur in the two modules. Guarded offline suites use disposable synthetic fixtures only. Source review and synthetic tests do not establish real-feed latency, timestamp semantics or comprehensive absence of every possible defect. This is a fresh review pass by the same coding agent, not a separate human or organizational approval.

## Exact proposed adapter interface (no implementation)
This refines #17; approve it together with that proposal rather than treating it as existing code.

Proposed pure function:
```python
def canonicalize(
    bundle: FrozenCaptureBundle,
    *,
    mappings: ApprovedMappingRegistry,
    calendar: PinnedSessionCalendar,
    request: AsOfRequest,
    policy: AdapterPolicy,
) -> CanonicalizationReport: ...

def engine_arguments(frame: SealedEngineFrame, *, config: Config) -> EngineArguments: ...
```
All named types below are proposed frozen records with recursively immutable fields. No hidden defaults, network calls, database connections or ambient system clock. The report always exists; engine_arguments rejects any ineligible report/frame. A missing interface implementation is not an available capability.

| Type | Required fields and invariant |
|---|---|
| FrozenCaptureBundle | bundle_id, source_capture_hash, fidelity WIRE_BYTES or SDK_ROW_SNAPSHOT, immutable payload/ref, observations tuple, request/page manifests, source contract metadata, capture clock provenance |
| RawObservation | observation_id, revision_id if evidenced, original symbol and raw_timestamp value/type/representation, original OHLCV values/types, payload/source hash, page/row refs, full_revision_received_at_utc with uncertainty, completion evidence refs, optional trusted point-in-time publication evidence |
| ApprovedMappingRegistry binding | immutable ID/hash/version, reviewer/approval date and authority, endpoint, SDK/OpenD scope, interval, market/symbol scope, session/adjustment flags, timezone, label meaning, evidence refs/hashes, precision rules and contrary evidence |
| PinnedSessionCalendar | calendar ID/version/source hash, exchange/session scope, tzdata version, explicit open/close UTC per date, holidays, early closes and halt/no-trade-minute policy |
| AsOfRequest | symbol, session ID/date, decision_cutoff_utc, target_completed_through_utc, mode RAW_AUDIT or ENGINE_READY |
| AdapterPolicy | version/hash, time precision and clock uncertainty rule, staleness limit, duplicate/revision identity policy, units/adjustment regime; no permissive fallback |
| CanonicalObservation | source observation/revision refs, raw_timestamp unchanged, canonical numeric OHLCV and conversion lineage, interval_start_utc, interval_end_utc, known_at_utc, complete evidence, finality status UNKNOWN/PROVISIONAL/FINAL with independent evidence |
| CanonicalizationReport | contract/policy/code IDs, source/mapping/calendar hashes, requested cutoff/watermark, decision_eligible boolean, statuses/reason codes, exclusions and coverage counts, sealed frame or None, deterministic manifest/frame hash |
| SealedEngineFrame | exactly one symbol/session, strictly ordered unique intervals, immutable rows/context/evidence, all eligibility checks satisfied; no future-known revision |
| EngineArguments | isolated compatibility copies: rows, symbol, session_open_et, session_close_et, as_of_et, interval_evidence, config; engine v1 keyword names unchanged |

Canonical interval is [start,end), exactly 60 seconds for this version. Raw label 16:00 is never assigned a meaning without an approved binding; start-labeled 16:00 and end-labeled 16:00 produce different session eligibility. Preserve out-of-session source records and record derived exclusions. Never rewrite raw timestamps or source OHLCV.

Mapping requires provider confirmation or independently aligned opening/closing OHLCV evidence scoped to the source contract. Coverage shape, missing 09:30, 390 bars, successful requests and fetch time do not establish label semantics. APPROVED synthetic bindings are fixtures only; real history cannot be passed as SYNTHETIC to bypass a missing mapping.

Completion is a closed-interval claim supported by a documented watermark/contract, not simply elapsed time. It is separate from finality, which may remain UNKNOWN. Availability belongs to the exact revision and required completion metadata: use a conservative upper bound no earlier than full revision receipt and interval end, unless a separately approved point-in-time source establishes historical knowledge. Today's download does not prove historical availability. Unknown time/clock bounds block the affected frame.

UTC instants are authoritative. Pin America/New_York and tzdata; ambiguous/nonexistent local time blocks forwarding. Calendar defines DST, holidays and early closes, not a universal 390 bars. A complete prefix does not prove expected tail/whole-session completeness. target_completed_through_utc must be an approved expected watermark at the cutoff, not chosen from the latest observed row.

For engine v1's naive ET second strings, interval boundaries must already be exact minute boundaries; availability rounds UP to whole seconds and cutoff DOWN. Preserve full precision separately. No rounding raw stamps or using host-local time. Any unsupported conversion blocks engine_arguments.

Filter proven known-at <= cutoff before unavailable payload inspection. Unknown known-at cannot be safely ordered and blocks the affected frame. Record page exhaustion, repeated cursor, errors, missing symbol, bounds and partial failures; successful earlier pages do not cancel later-page failure. Default v1: ambiguous known duplicates/revisions block. Coalescing identical retries requires a reviewed identity policy and retention of every raw reference. No last-row-wins or final-series flattening. Engine v1 can consume a unique as-of frame; replay v1 must not consume a general revision stream. A future frame-driven replay interface requires a separate proposal.

Fail-closed conditions include missing approval/evidence/clock/calendar, unknown availability, incomplete interval/source, wrong units, invalid OHLCV, gaps including expected tail, conflicting revision, stale frame and unsupported scope. Report explicit reasons, retain raw references, frame=None and decision_eligible=False. Consumers render NO TRADE with adapter reasons; do not invoke the engine with fabricated VERIFIED metadata. Hashes bind identity, not truth or authentication.

## First SPY/QQQ study: preregistration proposal
Status DRAFT, NOT FROZEN. No history inspected or study run for this proposal. No reported performance. A signed/dated immutable manifest and approved data eligibility are prerequisites.

### Questions and fixed arms
All arms use the SAME valid as-of information, mandatory data-quality/calendar/availability guards, 22 completed bars minimum, session-reset SMA-seeded EMA9/21, prior 20 volume baseline, RVOL >=1.2, 15-minute OR and HLC3 proxy where required. First possible feature decision is after the 22nd completed interval (09:52 for a normal 09:30 opening), possibly later due to availability. No cross-day warmup.

A: exact #13 conjunction: close > EMA9 > EMA21 with positive EMA9 slope (reverse for bearish), RVOL >=1.2, close outside aligned OR, aligned HLC3 proxy, and prior-five breakout or EMA9 support/rejection as implemented. No redefinition after seeing labels.
B: simpler EMA + volume: close > EMA9 > EMA21 (reverse bearish), RVOL >=1.2; no OR/proxy/pattern requirement. Slope omitted as redundant; explicitly a new study arm, not a production configuration change.
C: OR baseline: close > first-15-minute high (reverse below low); no EMA/volume/proxy/pattern gate. Direction is location outside the range rather than a fresh-cross trigger. All arms remain at the common 22-bar warmup to avoid differing exposure windows.
D: NO TRADE ablation paired within B: unfiltered candidate generation means B with mandatory validity guards; filtered generation retains only B events passing the additional A proxy/OR/pattern gates. Log every excluded B opportunity and reason. Never disable missing-data, completion or availability guards. The definition overlaps A deliberately and is not an independent strategy discovery or fourth independent statistical test. Report retained/excluded fractions and outcomes separately.

Direction ties yield no candidate. Five-bar history excludes event; touch/rejection is OHLC geometry, not evidence of intrabar trade sequence. No threshold/arm ranking or parameter optimization based on future results.

### Splits and genuinely future evaluation
At maintainer approval, freeze UTC T0, exact code/dependency/policy versions, data-source contract, all arm definitions, calendar, label rules and the full protocol hash before acquiring/viewing any evaluation outcomes.
- Development: eligible pre-T0 history used for implementation only, explicitly previously inspected; no untouched claim.
- Chronological rehearsal: last 60 eligible exchange session dates ending strictly before T0, with earlier pre-T0 eligible sessions used for development; no date randomly allocated, no hindsight search for favorable windows. If fewer sessions exist, block rather than shorten silently. Rehearsal is retrospective and may expose defects; fixes require versioned protocol and a new future freeze.
- Embargo: first 5 exchange sessions after freeze excluded from evaluation; capture only after approval. Verify this prevents any same-session feature/label overlap.
- Untouched future evaluation: next 120 scheduled exchange sessions after embargo, both SPY and QQQ on the SAME dates. Do not extend the end date because of missing data or low candidate counts. Actual calendar dates and inspection/access policy must be pinned before starting.
- No interim outcome inspection, adaptive stopping or configuration change. Operational quality checks may inspect capture health without labels. Record access audit. Any early outcome access invalidates untouched status; re-freeze and reserve a new future window before another confirmatory claim.

This does not assert existing history is suitable or that required availability evidence exists. Prospective capture needs separate authorization; this design initiates none.

### Timing and revisions
Primary study requires evidence-backed first-observed revision knowledge and closed-bar evidence. Decisions at fixed canonical minute boundaries; visible set known by that boundary. This differs from #14's publication-event snapshots and requires separately reviewed replay implementation. No unknown-latency values admitted.
For descriptive labels, use next minute OPEN strictly AFTER decision time, followed by the close of the third completed one-minute interval starting there. This intentional one-minute delay differs from #14's zero-latency boundary assumption and requires new tests/review; it is still an OHLC proxy, not an executable fill. Label vintage: same-session close plus 24 hours, exact availability cutoff; unknown/unresolved label revisions excluded with reasons. Feature snapshots never inherit label revisions.
No same-session future outcome influences decision eligibility or cooldown. All horizon minutes must be available by label cutoff, unique, valid and same session. No horizons crossing session close. Missing labels remain in denominators. Unknown real historical availability blocks the primary study. A separately approved assumed-latency sensitivity study could be retrospective only, explicitly not verified or untouched; none is authorized here.

### Overlap, correlation and paired comparisons
Primary analysis uses a common non-overlapping decision grid every 5 minutes after common warmup: first decision open+25 minutes, then +5 until the 1-minute delay plus 3-minute horizon fits before close. Thus arms share times, exposure opportunity and quality exclusions; no outcome-dependent cooldown. Retain raw per-minute candidates as secondary descriptive counts only, marked overlapping.
SPY/QQQ remain a paired session-date cluster, not independent observations; never split same date across development/evaluation. Summarize each symbol and equal-weight date-level paired differences; dates with one symbol missing are excluded only from paired primary comparisons, with single-symbol results/counts reported separately. Report intraday/time-of-day and long/short counts and shared missingness. No claim that cooldown alone eliminates dependence.

### Separating intraday momentum, daily context and cross-symbol disagreement
Design amendment 2026-10-27; no evaluation executed. These are prespecified descriptive strata, not new engine filters or authorization to tune strategies.

Keep three horizons separate:
1. Intraday momentum: session-reset EMA9/21 and event-time features already defined in arms A–C. Also retain continuous close/open-to-date movement computed only from eligible completed intervals. Neither is called a multi-day trend.
2. Prior daily trend: for each symbol, compute SMA-seeded daily EMA9/21 from the latest 60 scheduled completed regular sessions strictly BEFORE the study date. UP if previous completed daily close > daily EMA9 > daily EMA21, DOWN for the reverse; otherwise MIXED. Require all 60 approved daily observations, consistent adjustment/units and revision-specific availability by the decision. No current-day final close, final daily high/low/volume or later revision enters this feature. Daily aggregate derivation, mapping and knowledge evidence must be approved separately; missing evidence yields DAILY_CONTEXT_UNAVAILABLE, not an assumed trend. This contextual warmup is separate from the 22-bar intraday warmup.
3. Developing session direction: sign of latest eligible completed intraday close / evidenced session open - 1, with exact zero FLAT. Use only the as-of prefix; the current day's eventual close-to-open direction may be displayed only as an ex-post outcome, never a decision stratum or filter.

For each candidate, report WITH_PRIOR_DAILY_TREND, AGAINST_PRIOR_DAILY_TREND, MIXED_DAILY_CONTEXT or DAILY_CONTEXT_UNAVAILABLE; cross-tab with developing-session direction and fixed session-relative time bands [open,open+60m), [open+60m,open+180m), and [open+180m,close). Retain continuous measures and exact definitions. Report arm selection rates and movement outcomes within strata so broad daily-context composition cannot be silently credited to intraday rules. These observational comparisons do not establish causal separation or incremental predictive value. Do not introduce trend gating or optimize thresholds after inspection.

At each shared decision-grid instant, independently compute each symbol/arm from its own eligible information. Record full ordered SPY/QQQ signal pair, then classify:
- AGREEMENT_BULLISH or AGREEMENT_BEARISH: both candidate directions match.
- CONFLICT: one bullish and the other bearish.
- SINGLE_CANDIDATE: exactly one candidate and the other's data are valid.
- BOTH_NO_TRADE: valid data for both, no candidates.
- PEER_DATA_UNAVAILABLE: either symbol lacks valid eligibility; distinguish from valid NO TRADE and retain original pair/reasons.

No majority vote, averaged direction, forced consensus or dropping conflicting cases. A conflicting candidate remains a candidate for its own symbol; report conflict-specific selection, missingness and outcomes, including prior-daily-trend alignment of EACH symbol. Cluster both symbols on session date and retain arm-specific conflict denominators. Do not present a combined SPY/QQQ signal as established behavior.

Primary arm comparisons retain intraday-eligible events when daily context is absent; label that stratum explicitly. A secondary daily-context-complete analysis uses a common eligible subset across arms, with exclusions/counts and sensitivity to missingness disclosed. No imputation. Freeze these context definitions and access/evidence requirements before future evaluation; insufficient daily availability blocks contextual conclusions even if intraday analysis is otherwise eligible.

Required future synthetic tests: changing same-day final daily OHLCV cannot change event strata; future daily revisions cannot alter earlier context; known late prior-session daily values become visible only after their knowledge time; missing daily session blocks context; daily and intraday warmups remain separate; all nine valid directional/NO TRADE symbol pairs classify deterministically; peer invalidity is never called disagreement or NO TRADE; conflicts never mutate either symbol's candidate. This amendment changes documentation only.

### Missingness, denominators and outputs
Expect scheduled dates including whole missing days. Record mandatory exclusions by symbol/date/grid time: unknown mapping/availability, partial pages, gaps, invalid OHLCV, revisions, missing opening range, incomplete/stale tail and missing outcomes. No interpolation, forward fill or calendar substitution. Any prefix gap prevents later engine eligibility in that session under v1; report resulting selection. Halt exceptions need approved rules. Zero-candidate and NO TRADE days remain in session denominators.
Primary descriptive endpoint: equal-weight date-level difference A minus B in direction-adjusted 3-minute ETF percentage movement among their selected candidates; show unequal selection explicitly. Also report A/B/C conditional movement, event/session counts, median, sign fraction, NO TRADE rate, retained/excluded B movement and missing-label fractions. Pair opportunity-level selection comparisons separately; do not pretend differently selected events are identical paired trades.
Report date-cluster bootstrap uncertainty (10,000 resamples, fixed seed 20261027) and a prespecified 5-consecutive-date block sensitivity to serial dependence. Intervals may be unstable with sparse events; disclose sample counts and do not promote significance. No p-value fishing, winner selection or profitability claim. All arms/results/exclusions are published, including null/negative results. No transaction costs are modeled because these are movement labels, not returns.

### Reproducibility and gates
Manifest binds source capture/revision hashes and fidelity, mapping approval, calendars/tzdata, UTC cutoffs, code/dependency versions, all config/arms/splits/grid/label rules, prior-inspection/access log, exclusions and deterministic seed. Deep-seal inputs; materialize isolated engine copies. Store immutable outputs under collision-resistant exclusive names, never overwrite evidence. Full-run hash includes context/config/evidence, not only feature hash.

Before execution: approve #17/interface, define revision-aware frame-driven replay, implement synthetic cross-arm/timing/calendar/late-revision/missingness tests on Windows/Linux, validate deterministic manifests and absence of persistence, establish source/knowledge evidence, freeze exact dates/access policy, then obtain explicit study-execution approval. No experiment or parameter search is performed by this design.

## Validation of review preparation
Fresh guarded local Windows runs: #13 97 tests; combined #13/#14 115 tests; both pass. Existing exact-head Python 3.11 Windows/Linux CI logs confirm the same counts:
- https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948
- https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504949071
- #17 documentation baseline: 69 tests each, https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504257980

These tests establish synthetic implementation contracts and compatibility, not provider behavior, edge, actual fills or this unimplemented study/adapter.
