# Raccoon Radar vNext 1.2 — Market Structure & Consolidation

Status: proposed, synthetic-only, specification-first research. Version MS12-S0.
Both bullish reversal after downtrend and bearish reversal after uptrend are in scope.
No detector implementation, integration, historical study, provider verification,
trade, order, return/P&L calculation, deployment or predictive-edge claim is included.
Synthetic correctness is not evidence of market usefulness.

## Isolation and review baseline

This proposal adds this document only, on a separate branch based on vNext 1.1
`a984cc0b5e9f2f69b6ee99cca166221a632341fa` (draft PR #38).
PR #37 engine remains `cee98fb094842921a5a0fcd8764cfaf1c444b803`.
Neither PR is merged, retargeted or edited. All pre-existing Git blobs must be
identical to the pinned base. No existing UI, engine, dashboard, thresholds,
fixtures, workflow, database or provider adapter is changed. Rollback consists
of closing this separate draft; no application behavior depends on it.

Implementation is deliberately deferred until review of the rules and labels
below. A future prototype must live under an isolated research directory, use
standard-library synthetic fixtures, import no application/provider modules,
and expose no orders or UI entry point. MS12-S0 parameters are hypotheses,
not inherited PR31 EMA thresholds and not tuned estimates.

## Input, clock, finality and fail-closed contract

Use fictional SPY/QQQ one-minute OHLC records, not actual history. A synthetic
manifest declares expected session interval ends, calendar version, timezone,
price units/tick, adjustment basis, and source identity. Interval convention is
explicit `[start,end)`; event time is end. Tests may use UTC and invented
sessions. They establish no real exchange calendar or provider convention.
Do not infer completion from a timestamp or a missing opening bar.

Each immutable observation has symbol, session_id, start, end, O/H/L/C,
status (FINAL or PROVISIONAL), available_at, revision_id, supersedes_id,
and content hash. Times are aware UTC instants; bar duration is exactly 60s.
As-of A includes only versions with available_at <= A and end <= A.
Select the latest available revision per interval using an explicit strictly
increasing revision sequence. Conflicting equal revisions, branching
supersession, cycles, or missing superseded records block the affected session.
Future unavailable revisions must not affect an earlier as-of result.

Require finite, positive O/H/L/C, L <= min(O,C) <= max(O,C) <= H,
known symbol/session, exactly one selected record per expected interval, no
overlap/gap, monotone chronology, consistent units/adjustment/source, explicit
FINAL status and known availability. A duplicate is an error, even if identical;
revision versions are distinct from duplicate ingestion. Booleans are not prices.
Invalid metadata, unknown calendar/finality, stale or missing current interval,
insufficient warmup, nonfinite intermediate arithmetic, or any invalid record
in the session prefix yields INSUFFICIENT_EVIDENCE with reason codes and no
eligible event. No filling, sorting away anomalies, rounding before comparison,
fallback to an older FINAL when latest is provisional, or cross-session carry.
Validation of gaps uses the declared expected schedule through the requested
event cutoff, not wall-clock guesses. After a fault, restart only from a new
fully valid session or an explicit corrected as-of replay of the same session.

Output records contain spec/code/parameter/manifest hashes, symbol, session,
as_of, event_cutoff, observation revision hashes, run_id, candidate_id,
state, reason codes, frozen boundaries, evidence indices and eligibility.
State means observed structure only; it is never a probability or action.

## Symmetric measurable rules

All constants below are frozen for MS12-S0. Inclusive vs strict comparisons are
intentional. Index bars by session ordinal. Use full precision comparisons in
the declared price units. No volume, EMA, future pivots or retrospectively
selected swing points are used.

At every valid prefix with no active episode, inspect the last 8 bars as a
potential consolidation, preceded immediately by 20 trend bars. Minimum
warmup is therefore 28 FINAL bars. Process candidates in increasing end time;
the first qualifying candidate locks. Never choose the best-looking past box.

On the 20 trend bars, define TR for the first bar as H-L and subsequent TR as
max(H-L, abs(H-previous C), abs(L-previous C)). S = mean(TR); require S > 0.
Let D = C_last-C_first, V = sum(abs(C_i-C_(i-1))), and efficiency E=abs(D)/V.
Require V>0, abs(D)>=4S, E>=0.60, and at least 12 of the 19 close changes
strictly in sign(D). Uptrend has d=+1; downtrend d=-1. All other prefixes
have no measurable trend. Ties do not count as directional changes.

For the next 8 bars, Lb=min(L), Ub=max(H), W=Ub-Lb. Require
0.5S <= W <= 2.5S; abs(C_last-C_first)<=0.25W; and each close in
[Lb+0.10W, Ub-0.10W]. Require at least two lows <= Lb+0.20W and two
highs >= Ub-0.20W, with each pair of touches separated by at least two
bar ordinals. Wick touches count; they are not breakout confirmation.
At the eighth close freeze Lb, Ub, W, S, d, trend/box indices and their
observation hashes. Boundaries never expand to absorb a breakout.

Let epsilon=0.10S and tolerance=0.15S, both frozen. For a breakout direction
b in {-1,+1}, set B=Ub for b=+1 and B=Lb for b=-1, and
z_i=b*(C_i-B). Breakout confirmation requires two consecutive subsequent
FINAL closes with z_i > epsilon. Equality is not enough. A single outside
close, wick, or gap is only provisional evidence. Direction must match
on both closes; no intrabar ordering is inferred.

After the second breakout close, require a retest on a strictly later bar
within the next five bars. Its [L,H] intersects [B-tolerance,B+tolerance]
and its close has z >= 0. A retest cannot also be a breakout-confirmation
bar. Before confirmation, any later close z < -tolerance fails that breakout
attempt. Failure takes precedence over touch logic on the same bar.
After a valid retest, require a strictly later close z > epsilon within the
next three bars. That close is the sole confirmation event. Until then the
classification is INSUFFICIENT_EVIDENCE, with BOX, BREAKOUT_PENDING or
RETEST_PENDING as diagnostic phase only. A retest may have an adverse wick;
this close-based convention is an explicit hypothesis to challenge.

The first two-close breakout direction locks the episode; failed confirmation,
opposite breakout, or timeout retires it without silently switching directions.
No two-close breakout by bar box_end+10 expires the box. Retest and confirmation
deadlines include their final bar. Session end before a deadline yields
INSUFFICIENT_EVIDENCE/SESSION_END, not a failed reversal. After retirement,
require 28 entirely new bars before another candidate; windows cannot overlap
the retired episode. This conservative cooldown is not a production choice.

At confirmation, b=-d gives POTENTIAL_REVERSAL_CONFIRMED; b=d gives
CONTINUATION_CONFIRMED. These are mutually exclusive, immutable event labels.
For d=-1,b=+1 the reversal is bullish; d=+1,b=-1 is bearish. For continuation,
down/down and up/up use exactly the same tests. Any missing prerequisite gives
INSUFFICIENT_EVIDENCE, never an inferred continuation. No confirmation can be
backdated to the breakout, box touch or trend pivot. Events cease to be current
pair evidence after three subsequent bars or session end, while remaining in
the audit log. Later failure is a separate outcome, never a rewritten event.

Symmetry oracle: reflect every price around a constant K large enough to keep
prices positive: O'=K-O, C'=K-C, H'=K-L, L'=K-H. Trend and breakout signs
must invert; confirmation ordinal, quality reasons, S/W, phase and eligibility
must match. Positive scaling must preserve classifications when ticks/units
scale too. Translation must preserve classifications. Test threshold equality
and values immediately on either side without display rounding.

## SPY/QQQ pair evidence

Compute each symbol independently. Pair at the exact same session and event
cutoff and the same as-of A, with complete synchronized expected prefixes.
No nearest-bar join, forward fill, asynchronous latest snapshot, or use of
QQQ information unavailable at the SPY event. Preserve both symbol outputs.

Pair statuses: UNAVAILABLE if either quality/warmup gate fails; CONFLICT if
both have eligible current confirmations with opposite b; AGREE_REVERSAL if
both current confirmations are reversals with equal b; AGREE_CONTINUATION if
both are continuations with equal b; MIXED_STRUCTURE if equal b but event
classes differ; otherwise INSUFFICIENT_EVIDENCE. Current means confirmation
age <=3 bars, with both sessions still open. A healthy pending symbol produces
insufficient evidence, not conflict. Pair agreement is descriptive and must
not promote either event, relax thresholds, or imply independent evidence.

## Causal replay and revisions

Replay in increasing availability order, evaluating only completed prefixes.
For every output at A, truncating the input at A must give exactly the same
output as a larger input containing later bars/revisions. Appending a future
extreme, bad bar or correction must not alter earlier output. A correction
available at A2>A1 creates a new replay result with new run_id and explicit
supersedes_run_id, preserving the A1 record. Record differences, including
withdrawn events; never mutate raw observations or silently replace evidence.
Report both original as-known and corrected-as-of results separately. A replay
at A2 is not evidence the corrected value was known at A1.

Outcome labels live in a separate evaluation layer and cannot be imported by
feature/state computation. No centered windows, future-confirmed pivots,
full-session normalization, future-adjusted inputs or data-dependent candidate
selection. Pair computation must satisfy the same prefix/revision invariants.

## Falsifiable synthetic evaluation protocol

Freeze this spec, fixture generator version/seeds, case manifest and expected
event ordinals before execution. Handcrafted conformance cases and randomized
stress cases are separate sets. Generator latent tags are retained independently
of detector output; expected outcomes cannot be generated by calling the detector.
Synthetic seeds inspected while debugging are development cases, not holdout.
Hold out generator families as well as seeds to expose shared-rule tautologies.

At confirmation t define oriented distance q_j=b*(C_(t+j)-C_t), for j=1..10.
Success: first close q>=S occurs before any close q<=-S. Failure: first close
q<=-S precedes success. Neither by j=10 is TIMEOUT. Missing/invalid/provisional
future bar, revision ambiguity or session truncation is CENSORED, not success,
failure or timeout. Use close-only labels; no wick ordering, execution or P&L.
Score both original available-at event inputs and separately versioned corrected
evaluation vintages. Once assigned for a vintage, labels remain immutable.

For each direction and each event class, report:
- N candidate boxes, attempts, confirmations, failed attempts, expiries,
  data-quality exclusions, censored labels, sessions and symbol/pair counts.
- Outcome false-positive fraction = (FAILURE+TIMEOUT)/(SUCCESS+FAILURE+TIMEOUT),
  alongside FAILURE-only fraction and all three raw counts. Zero denominator
  is UNDEFINED. Censored events never vanish from reporting.
- Against independent latent positive/negative episode tags: TP, FP, TN, FN,
  precision=TP/(TP+FP), recall=TP/(TP+FN), FPR=FP/(FP+TN), and abstention rate.
  A positive is detected only if exactly one correctly directed event occurs
  within its predeclared episode window. Wrong direction is FP and a missed
  positive is FN. Negative windows with an event are FP; without are TN.
  Unscorable windows are excluded with reasons, not counted as TN. Multiple
  events in one window are separately counted as duplicate false events.
- Detection latency from latent transition and from first breakout close,
  event frequency per 1,000 eligible bars, confirmation coverage and censor rate.
- Reflection/translation/scaling mismatches, prefix-invariance violations,
  revision replay discrepancies, and data-fault confirmations: required zero.
- Stratify SPY, QQQ, pair agreement/conflict, trend sign, range/noise/gap
  regimes and generator family. Report paired episode/session uncertainty,
  not independent-bar confidence intervals. SPY/QQQ are correlated; pair
  counts are not added as independent symbol samples. Small strata are descriptive.

Predeclared conformance acceptance is exact expected state and ordinal on every
handwritten case, zero causal/symmetry/fail-closed violations, and reproducible
hashes across Windows/Linux Python 3.11. Report all failures and all parameter
variants. There is no synthetic accuracy threshold that authorizes deployment
or establishes edge. Any parameter change creates MS12-S1 and reruns all cases;
never select the best variant using the same alleged holdout.

Required case matrix (each price case and its reflection): valid reversal;
valid continuation; flat/no trend; efficient weak drift; noisy net trend;
boundary equality; too-wide/narrow box; insufficient separated touches;
wick-only and one-close breaks; exact epsilon; successful late retest;
breakout bar falsely serving as retest; deep failed retest; retest timeout;
confirmation timeout; opposite break; gap over box without retest; success
then later reversal; failed confirmed reversal; horizon timeout; session end;
new session warmup; duplicate/gap/overlap/nonfinite/invalid OHLC; provisional
latest revision over FINAL; delayed FINAL; stale cutoff; future corrections;
ambiguous supersession; conflicting pair, mixed pair, lagging pair, unavailable
pair; future extreme appended; correction withdrawing an old confirmation.

## Review questions and next gate

Are 20/8 bars, 4S/0.60 trend strength, box touch rules, fixed box width and
close-based retest semantics a useful operational definition? Does strict
cooldown discard too much? Should retest depth use wicks? How should a gap
breakout be researched separately? Is a 10-bar close-distance outcome meaningful,
and how sensitive are conclusions to S and horizon? Can independent latent
labels avoid merely restating detector rules? How should disagreement age and
different symbol trend histories be presented without overstating agreement?
What authoritative finality/availability and adjustment evidence would be needed
before a separately authorized real-data study? None is established here.

Next review gate: approve or revise definitions and independent case expectations,
then authorize a bounded isolated reference prototype and its conformance suite.
Existing regression CI validates preservation only; it does not test an
unimplemented MS12-S0 detector or establish predictive performance.
