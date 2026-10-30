# Raccoon Radar vNext 1.2 protocol reconciliation — MS12-R0 DRAFT

Owner review required before integration. Synthetic development conformance only.
This draft starts with MS12-S0; it does not replace, edit, merge or validate the
entire PR39 specification. PR40 remains an unchanged experimental comparator.
No provider, real data, orders, outcome returns, P&L or predictive claims.

## Provenance and isolation

| Source | Exact head | Role |
|---|---|---|
| [Draft PR39](https://github.com/girlbreaksface/raccoon-radar/pull/39) | `8d45bb39b298a8c7d9e01b17b12bc7b324c45e19` | Normative starting specification MS12-S0 |
| [Draft PR40](https://github.com/girlbreaksface/raccoon-radar/pull/40) | `6f282a88c41d345e744089b6dd880e93dd53a4af` | Separate percentage hypothesis, never called an S0 implementation |
| PR38 base of PR39 | `a984cc0b5e9f2f69b6ee99cca166221a632341fa` | Preserved UI stack |
| PR37 engine | `cee98fb094842921a5a0fcd8764cfaf1c444b803` | Preserved; no import or integration |
| PR40 base PR33 | `b7dd5e5100c2823701c8de639fc0e9048adde80e` | Provenance only |

The new branch starts at exact PR39 head. All differences are additions under
`research/reconciliation/` and one additional CI workflow. All existing blobs,
including PR39's document and existing workflows, must match PR39 exactly.
No original PR branch is pushed, retargeted, commented on, merged or modified.
Close the new draft PR for rollback; no application entry point depends on it.

`vendor/PIN.json` records original Git blob IDs for four byte-exact PR40 files:
canonicalizer, detector, generator, detector tests. A test checks their Git object
hashes without invoking Git. Vendoring avoids a runtime network fetch, dependency
on mutable branch heads, or importing the app. Imports select this isolated vendor
directory. PR40's default Config and every threshold remain unchanged.

## Proposed reconciled contract

Retain **all** PR39 rules and numbers as the proposed default, pending owner review:

- 20 immediately preceding trend bars, then 8 consolidation bars; first candidate
  locks, no hindsight selection. First TR is H-L; S is the 20-bar arithmetic mean
  of true range, not Wilder's smoothed ATR or a full-session estimate.
- Trend: net movement >=4S, efficiency >=0.60, >=12 strict directional steps.
- Frozen box W in [0.5S,2.5S], close drift <=0.25W, closes in the interior
  10%–90% band, two touches on each side separated by >=2 ordinals.
- Frozen epsilon=0.10S and tolerance=0.15S. Two consecutive strict outside
  closes lock either direction. A strictly later retest within five bars must
  intersect the tolerance zone and close on/beyond the boundary. A strictly
  later hold close >epsilon within three bars is the confirmation event.
- Failure close <-tolerance takes precedence over touch. Deadline bars are
  inclusive. No two-close break by box_end+10 expires. Session truncation before
  deadline is insufficient evidence, not observed failure. No backdated events.
- Apply the same full sequence to reversal and continuation. Reversal is b=-d;
  continuation is b=d. Labels describe the protocol, never market truth.
- Retain PR39 fail-closed session-prefix validation, no FINAL fallback behind a
  newer provisional revision, immutable as-known/corrected-as-of records, new
  28-bar cooldown, three-bar current-event age, and exact aligned pair statuses.
  These remain requirements even where this bounded harness is incomplete.

This is an explicit recommendation, not owner approval of the numerical choices.
Do not combine PR40's shorter windows with S0 thresholds and call that reconciled.
Any parameter change requires a new version and predeclared new case expectations.

## Why the comparator is different

| Aspect | PR39 / proposed starting point | PR40 experiment |
|---|---|---|
| Trend/box windows | 20 / 8 | 8 / 5 |
| Movement | abs(net)/S >=4 | abs(net)/first close >=0.015 |
| Efficiency / steps | >=0.60 / >=12 of19 | >=0.70 / >=0.75 fraction |
| Extra directional structure | No separate high/low-step gate | >=0.60 high/low-step fraction |
| Width | 0.5S..2.5S | W/midpoint <=0.015 |
| Contraction / overlap | Box bounds, interior closes, separated touches | TR ratio <=0.55, overlap >=0.75, unseparated touches |
| Breakout buffer / retest zone | 0.10S / 0.15S | 0.10W / 0.20W |
| Continuation | Two breaks, later retest, later hold | One qualifying close |
| Reversal confirmation | Two breaks, later retest, later hold | Later retest may be second qualifying close and confirmation |
| Retest close | z>=0 | Outside breakout threshold, consecutive-count gate |
| Retest deadline | Five after second break | Four after first break |
| Initial box expiry | Ten subsequent bars | Total range age >20, including initial five |
| Two-sided wick excursion | No separate veto; close-based protocol | Explicit invalidation veto |
| Later adverse move | Separate outcome, immutable event; current age <=3 | Current direction invalidation while preserving history |
| Pair | Age-bounded reversal/continuation/mixed agreement | Active-direction agreement/single direction |

Changing only normalization cannot reconcile these semantics. Matched experiments
identify observable consequences; they cannot establish which is economically better.

## Necessary invariances and their limits

1. **Causal as-of/prefix consistency and FINAL-only exclusion are mandatory for
   both hypotheses.** Unavailable future bars/corrections, hindsight labels and
   later invalid data cannot alter an earlier visible decision. Unknown finality,
   missing schedule intervals, duplicates or invalid OHLC must block eligibility.
   Audit hashes may change when excluded bundle payload changes; visible state
   must not. Known corrections create separate runs, never rewrite prior output.
2. **Positive unit scaling** is required when all OHLC, price units and tick size
   scale together. It means dollars versus cents, not arbitrary resampling or a
   corporate-action adjustment crossing the window. Neither experiment models
   execution ticks or real adjustment regimes. Fraction arithmetic in the small
   S0 reference makes equality checks exact; PR40 retains its private Decimal
   context and unchanged finite-precision behavior.
3. **Reflection is a required synthetic directional oracle for S0:** O'=K-O,
   C'=K-C, H'=K-L, L'=K-H, all resulting prices positive. Event ordinals and
   phases match, directions invert. Reflection does not imply equal real upside
   and downside economics, borrow constraints, option payoff or return symmetry.
4. **Translation is required for S0's local absolute-distance geometry**, with
   positive prices and consistent units. It is *not* a universal financial
   requirement: adding a constant changes percentage exposure and the economic
   relation to zero. Likewise arbitrary affine reflection is inappropriate as a
   mandatory invariant of PR40's percentage hypothesis. Its denominator changes
   are expected design consequences, not grounds for threshold tuning.
5. Do not require time-resampling, volatility-regime invariance, symbol identity
   equivalence, near-zero-price invariance, unchanged ticks after scaling, or
   invariance to partial/cross-window corporate actions. These alter information,
   resolution or economics. Equal-unit affine checks are mathematical conformance,
   not evidence of scale-free market behavior.

Analytically, for P'=aP+c with a>0, TR'=aTR, S'=aS, W'=aW,
net'=a*net and path'=a*path. S0's comparisons are preserved; reflection additionally
inverts signs and swaps high/low. For PR40, net/(first close) becomes
a*net/(a*first+c) and width/midpoint becomes a*W/(a*mid+c).
They preserve positive scaling with c=0 but generally not translation/reflection.
This algebra supports the oracle; a finite test grid alone is not a proof.

## Experiment and evidence

Run `python -B research/reconciliation/run_checks.py` and
`python research/reconciliation/verify_evidence.py` from repository root.
No third-party packages or runtime downloads are needed. The existing OfflineGuard
blocks network and subprocess activity during calculation/tests. The separate
workflow uses Windows/Linux Python3.11 and checks byte-exact evidence reproduction.
CI setup/checkouts use GitHub infrastructure; “offline” describes test execution.

Eleven invented families x two initial trend directions x four variants = **88
matched case variants**. Variants: base, scale3, translate+1,000,000,
reflection K=1,000,000. The uptrend family itself is K=20,000 reflection of the
downtrend. Both detectors consume identical OHLC sequences and native, unchanged
windows; candidate lock dates need not match. Shared fictional UTC metadata and
PR40's pinned canonical FINAL gate precede the price reference. No padding or
changing windows/thresholds to force equivalence. All cases are development cases;
fixture repairs during development are not threshold optimization or holdout.

Handwritten event/phase expectations are independent of detector outputs. An
additional seed12003940 produces 60 perturbed paths for S0 affine stress; these
are metamorphic development cases, not independent positives or hidden holdout.
`evidence.json` records source heads, code SHA256, per-case S0 traces/events and
PR40 events/classification/reasons. Ordinals in JSON/code are zero-based.

Observed base paths (one-based bar numbers; direction-reflected cases agree):

| Case | S0 reference | Unchanged PR40 |
|---|---|---|
| Reversal | Confirm bar32 | Confirm bar31 |
| Continuation | Confirm bar32 | Label bar29 |
| One outside close then return | No confirmation, box remains | Failed reversal |
| Wick-only | Box, no confirmation | Watch |
| Failed retest | Failed, no confirmation | Failed reversal |
| No retest | Retest timeout | Failed reversal |
| Close exactly S0 epsilon | No break, box expires | Confirmed reversal |
| Retest then no later hold | Hold timeout | Already confirmed on retest |
| Retest on S0 final allowed bar | Confirm bar36 | Failed reversal, earlier timeout |
| Box ten-bar expiry | Expired | Watch still active |
| Flat | Insufficient evidence | Insufficient evidence |

Across the 22 direction-family base paths, PR40 final classifications differ
from translated paths in20/22 and large-K reflected paths in20/22. These are
expected percentage effects; all 22 scale3 final classifications/events/reasons
match. S0 phase/event-ordinal comparisons have zero affine mismatches on the
declared grid; directions invert under reflection. Do not count transforms as
independent episodes or use these proportions as accuracy/false-positive rates.

New tests cover exact epsilon and immediately adjacent rational values, failure
precedence, adverse-wick tolerance, inclusive retest deadline, hold timeout,
baseline event timing, prefix truncation, incremental/batch classifications,
future extreme, unavailable malformed future revision, provisional/completion/
unknown-availability/invalid-OHLC/gap/duplicate gates, fractional late FINAL,
and corrected replay with preserved original PR40 history. PR40's39 vendored
regressions also run unchanged; their assertions remain PR40-specific.

## Evidence limits and unresolved owner decisions

The price reference is deliberately bounded to the first confirmed episode per
session. It returns diagnostic traces and immutable-by-return event tuples, not
S0's full hashed public audit schema. It demonstrates price transitions and some
retirement/cooldown behavior but is not full multi-episode S0 certification.
PR40's synthetic canonicalizer is reused as a common gate, not declared equivalent
to S0's explicit revision-sequence/supersession graph contract. The correction
test supplies separate corrected bundles and proves old history is retained;
it does not implement latest-revision selection with branching/cycle rejection.
Pair freshness/mixed classification, session-end censoring, full ingestion faults,
complete threshold matrix, outcome labels, latent confusion matrices, uncertainty
and holdout families remain unimplemented requirements. No real finality/calendar
or adjustment semantics are established. Do not infer general arbitrary invariance
from the finite grid or full S0 conformance from this subset.

Owner decisions before any integration:

- Adopt S0's absolute/volatility-relative geometry or explicitly choose a separate
  percentage hypothesis. Keep percentages as a comparator until that choice.
- Accept/revise 20/8 windows, 4S movement, separated touches, close-based retest
  with adverse wicks, and equal full continuation/reversal confirmation latency.
- Set desired handling for gaps, two-sided wick excursions, expiry/cooldown,
  event-age versus later invalidation, and pair freshness/mixed evidence.
- Review complete independent expectations and separately authorize implementing
  S0 revision graphs, multi-episode audit state, pair contract and censor labels.
  Any evaluation study requires separate authorization and a frozen protocol.

**Recommendation:** retain PR39 as the default research definition and PR40 as a
separate experiment; accept this as a draft reconciliation proposal only. Do not
select a protocol because it confirms more or passes a mirrored fixture. Obtain
explicit owner approval of definitions and remaining implementation scope before
integration. Neither synthetic test passage nor CI authorizes integration/merge.
