# vNext 1.2 market-structure research specification
Status: SYNTHETIC HYPOTHESIS / prototype contract, not evidence of predictive edge.
Authorized by direct human instructions in this coding session. Separate sibling branch based on pinned PR33 b7dd5e5100c2823701c8de639fc0e9048adde80e. No edits/imports to PR37/vNext1.1 engine or UI, original dashboard, PR31 EMA profile, provider connections, orders, P/L or production stores.
A small pure prototype is justified to make the symmetric state transitions, timing and invalidation hypotheses falsifiable. It consumes the unchanged PR33 canonical FINAL-only gate; it does not replace any EMA research.

## Observable definitions — fixed before implementation and fixture evaluation
All price calculations use a private50-digit ROUND_HALF_EVEN Decimal context, native OHLCV converted through their decimal strings. Comparison thresholds are configurable decimal strings; no floating confidence score or synthetic optimization. Ratios are dimensionless; breakout/touch distances scale with the frozen range width.
For a candidate range ending at visible candle i, use exactly T preceding trend bars and C immediately following consolidation bars, with no overlap. No centered pivots or future confirmation candles.
Trend: sign of last minus first trend close. Require absolute close change / first close >= move threshold, efficiency abs(net)/sum(abs(close differences)) >= efficiency threshold, fraction of same-direction strict close steps >= directional threshold, and fraction of adjacent bars with BOTH strict higher highs/higher lows (or lower highs/lower lows) >= structure threshold. Zero net/path is insufficient.
True range for each bar = max(high-low, abs(high-previous close), abs(low-previous close)); first trend bar uses high-low. Consolidation true range includes the last trend close.
Consolidation: L=min lows, U=max highs across C; require positive width W=U-L, W/midpoint <= width threshold; mean consolidationTR/mean trendTR <= contraction threshold; fraction of adjacent overlapping high/low intervals >= overlap threshold; abs(last-first consolidation close)/W <= drift threshold; at least configured touches of BOTH support and resistance within touch_fraction*W of L/U.
The first qualifying range freezes L/U and its trend/range observation identities. Never widen/recenter an active range using a later breakout. New range discovery after terminal failure/continuation requires a wholly new T+C window after that terminal bar.

| Parameter | Default | Valid bounds / meaning |
|---|---|---|
| trend_bars | 8 | integer3..100 |
| consolidation_bars | 5 | integer3..100 |
| min_move | "0.015" | (0,1], directional close movement fraction |
| min_efficiency | "0.70" | [0,1], path efficiency |
| min_directional | "0.75" | [0,1], strict directional close-step fraction |
| min_structure | "0.60" | [0,1], directional high/low-step fraction |
| max_contraction | "0.55" | (0,1], rangeTR/trendTR |
| max_width | "0.015" | (0,1], width/midpoint |
| min_overlap | "0.75" | [0,1], adjacent high/low overlap |
| max_drift | "0.50" | [0,1], range close drift / W |
| min_touches | 2 | integer1..consolidation_bars |
| touch_fraction | "0.20" | [0,0.5] |
| breakout_fraction | "0.10" | [0,0.5], close must STRICTLY exceed boundary +/- buffer*W |
| retest_fraction | "0.20" | [0,0.5], symmetric boundary retest zone |
| confirmation_closes | 2 | integer2..10, consecutive closes beyond breakout threshold including initial breakout |
| max_retest_bars | 4 | integer1..100; last permitted later bar is breakout index+limit |
| max_range_bars | 20 | integer C..500; initial C bars count toward this age |

All min/max ratios are inclusive. Exact breakout boundary equality is NOT a breakout. No tolerance rounded to make a synthetic result pass. These defaults are illustrative fixed hypotheses, not recommended market settings. Different configurations start distinct research runs and require new hashes; no automatic parameter selection.

## Symmetric transitions
1. INSUFFICIENT_EVIDENCE until a qualifying trend AND consolidation exist. Report warmup versus weak trend versus failed range criteria separately.
2. On qualified range: REVERSAL_WATCH, stage CONSOLIDATING, potential direction opposite the established trend. This is a watch, not a confirmed direction.
3. A close through the established-trend boundary+buffer yields TREND_CONTINUATION in that direction; this is an OHLC structural classification, not a trade.
4. An opposite close through boundary+buffer starts REVERSAL_WATCH / AWAITING_RETEST. Same breakout candle cannot count as its own later retest, regardless of its wick.
5. A later bar retests the broken boundary when its [low,high] intersects boundary +/- retest_fraction*W. It must close beyond the original breakout threshold and total consecutive outside closes must meet confirmation_closes. Then CONFIRMED_STRUCTURAL_REVERSAL, with its direction.
6. An unconfirmed breakout closes back on/inside the broken boundary: FAILED_REVERSAL. If that bar intersects the retest zone but closes beyond the wrong side of its tolerance, reason FAILED_RETEST; otherwise BREAKOUT_REENTERED_RANGE. Later closes outside threshold but without a valid retest do not confirm.
7. Retest not completed by the inclusive deadline yields FAILED_REVERSAL / RETEST_TIMEOUT. A completed touch does not justify an unlimited wait for the configured confirmation count.
8. After confirmation, a close beyond the wrong side of the broken boundary's retest tolerance yields INVALIDATED_SETUP / CONFIRMED_REVERSAL_INVALIDATED. Past confirmation remains in immutable history, never erased.
9. While consolidating, age > max_range_bars invalidates with CONSOLIDATION_EXPIRED. Age==limit is allowed.
10. Before confirmation, a bar whose high and low exceed BOTH range boundaries+buffers is INVALIDATED_SETUP / AMBIGUOUS_TWO_SIDED_EXCURSION; OHLC cannot establish ordering. Wick-only excursions without a qualifying close do not confirm a breakout.
Terminal failed/invalidated/continuation results remain recorded while waiting for wholly new structure. Confirmed reversal is monitored until invalidation; no hidden reset/rearm, price-target/stop ordering, cooldown or trade events.

## As-of data and state contract
assess(bundle,context,request,config,previous=None,synthetic=True) returns immutable Assessment(decision,tracker,canonical_report,audit_hash). Inputs are typed recursively immutable PR33 records. Completion/finality/calendar/source/availability/pagination validation is delegated to the exact unchanged canonicalizer. Request must be ENGINE_READY for analysis.
Only completed FINAL candles with proven declared availability<=cutoff can enter structure calculations. Unknown/provisional/gapped/partial/duplicate/bad data blocks the new decision. No interpolation, last-row-wins or timestamp shift. These are synthetic declared authorities, not verified real source evidence.
Tracker binds exact symbol/session/context/config, strictly increasing request cutoffs, accepted immutable candle prefix, transition log and immutable decision history. Prefix revisions relative to an accepted tracker block with PREFIX_REVISION_CHANGED; start a separately identified research run rather than silently repainting history. Visible conflicting revision streams already block at canonicalization. A changed context/config or forged state seal is rejected, not silently reset.
On a blocked step, retain last accepted candles/setup privately, append a blocked INSUFFICIENT_EVIDENCE decision with no current direction/range promotion, and advance evaluated cutoff. No stale state is shown as eligible. A later valid prefix can resume only if previously accepted candle identities remain unchanged.
A batch of newly available bars can reveal several structural events at once. All newly recorded events are observed_at=current evaluation cutoff; their trigger_interval_end is separate. Never backdate those detections to bar time or present retrospectively inferred events as previously emitted decisions.
A decision's visible-content identity excludes unavailable future bundle payloads. Full audit identity includes the complete immutable bundle and context, so it may change when excluded later evidence changes. State carries visible evidence/history only; earlier decisions are append-only and never recomputed.
State seals detect accidental substitution, not malicious source authenticity. Canonical caller assertions and this local prototype are not a hostile-input/security sandbox.

## SPY/QQQ independence and output
Analyze each symbol using its own source/calendar/quality/state first. A separate comparison requires exact SPY/QQQ decisions at the same cutoff/config and retains both decision hashes/classifications. Data failures and insufficient structure remain distinct from valid directional disagreement.
Only TREND_CONTINUATION and CONFIRMED_STRUCTURAL_REVERSAL expose current structural direction; watches expose potential direction separately. Compare active directions as AGREEMENT_BULLISH/BEARISH, CONFLICT, SINGLE_DIRECTION or NO_CONFIRMED_DIRECTION; report PEER_DATA_UNAVAILABLE/PEER_INSUFFICIENT_EVIDENCE separately. No averaging/forced consensus or peer-driven mutation.
Every decision includes symbol, timestamp, classification/stage, reasons, trend/range measurements and boundaries when eligible, setup/transition IDs, visible frame/config hashes and action WAIT. A failed setup remains in history after later invalidation/new formation.

## Acceptance matrix and evidence limits
Required synthetic cases: mirrored up/down reversals, both continuations, wick-only and close false breakouts, failed retests, confirmed-then-invalidated, retest timeout, prolonged range expiry, min/max/equality boundaries, unknown/provisional/missing/duplicate/partial inputs, insufficient warmup/weak trend/no contraction/wide or drifting range, opposite SPY/QQQ directions, independent peer failures.
Verify Decimal/caller-context determinism, immutable inputs/history, source/prefix revisions and state/config binding, future payload/revision exclusion, fractional receipt cutoffs, strict FINAL/completion, all directional pair combinations, frozen boundaries and batch knowledge timestamps. Run bounded offline Windows/Linux3.11 checks with unchanged guards.
These demonstrate contract behavior on invented paths only. Price structure names are hypotheses; confirmed means this definition's conditions, not market reversal truth. Authentic source/mapping/calendar/finality/availability, real false-positive rates, threshold sensitivity, economic costs, generalization and predictive value require separately authorized genuine point-in-time data and frozen evaluation. No history is acquired or study executed here.

## Explicit contract clarifications from regression evidence
No default threshold was tuned. Undefined contraction/drift denominators are nullable observations with explicit reasons, never Infinity strings. RAW_AUDIT cannot produce analysis and has ENGINE_READY_REQUEST_REQUIRED. Decisions/trackers bind the model version in their seals; unknown prior model versions reject even with a self-consistent old seal.
A configuration requiring more confirmation closes than max_retest_bars+1 is impossible and is rejected. Private Decimal context explicitly fixes traps/flags/clamp as well as precision/rounding/exponent bounds; changing caller DefaultContext must not alter behavior.
Resource bounds are1000 accepted frame bars and512 evaluated steps per tracker; exceedances block/reject explicitly. Public typed inputs/state remain trusted cooperative research objects, not a malicious-input/authentication boundary.

Continuation invalidation clarification: after TREND_CONTINUATION, a later close beyond the wrong side of its broken trend boundary by more than retest_fraction*W records INVALIDATED_SETUP / CONTINUATION_INVALIDATED, clears current direction and preserves the earlier breakout decision. This uses the same symmetric tolerance, not a new tuned threshold. New mirrored regression scenarios reproduce stale-direction behavior before this repair.
