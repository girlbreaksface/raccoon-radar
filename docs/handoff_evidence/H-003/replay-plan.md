# H-003 / A-008–A-009 — DRAFT read-only replay plan
Recorded-at UTC: 2026-10-27 13:15:21 UTC. Owner: coding agent. Status RETURNED_FOR_REVIEW; DRAFT / NOT FROZEN / NOT EXECUTED.
Authoritative starting proposal: [#18 at eb683559a0ab685503627612ab22aa16a77066ed](https://github.com/girlbreaksface/raccoon-radar/blob/eb683559a0ab685503627612ab22aa16a77066ed/docs/DIRECTION_INTEGRATION_STUDY_PROTOCOL.md), blob e4f381a8fa8d8ed968e01bd501b7a95b763df38a. Interface authority proposal: [#17](https://github.com/girlbreaksface/raccoon-radar/blob/9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3/docs/CANONICAL_COMPLETED_CANDLE_ADAPTER_DESIGN.md). This evidence package reconciles those proposals; it does not silently replace their definitions or authorize implementation.

## Hypotheses and arm fidelity
No empirical effect direction, superiority, confidence score or profitability is asserted. Confirmatory hypotheses/effect criteria still require human freeze. Preserve exact arm candidates:
- A: #13 conjunction: close > EMA9 > EMA21 and rising EMA9 (reverse bearish), current volume >=1.2 times prior 20-bar mean, outside aligned first-15-minute opening range, aligned session HLC3 candle-volume-weighted proxy, plus prior-five breakout OR EMA9 support (bearish: breakdown OR rejection). Seed EMA with SMA, then alpha=2/(N+1), reset each session; strict range/price comparisons and inclusive volume threshold.
- B: close > EMA9 > EMA21 (reverse bearish) AND the same volume threshold. No slope/OR/proxy/pattern gate; slope is redundant algebraically given close versus current EMA, apart from floating ties. This baseline is a proposed study arm, not a new engine configuration.
- C: close above first-15-minute high / below low. Location, not fresh-cross detection; no EMA/volume/proxy/pattern gate.
- Paired ablation D: among B opportunities, retain those passing A's extra OR/proxy/pattern gates and separately report excluded opportunities/reasons. It overlaps A by definition; do not count as independent discovery or pretend four independent statistical tests.
- All arms keep identical mandatory data/availability/completion/session guards and common 22 completed intraday bars minimum. Volume baseline excludes current bar; reference five bars exclude event; OR covers [session_open,session_open+15m). No future daily close/high/low/volume, no filled gaps.

Strict conjunctions reduce selections in synthetic cases; whether excluded signals are useful is UNKNOWN. Wide ranges and missing prefixes can suppress later aligned trends. Record selection and each failed gate across ALL eligible opportunities, including no-candidate sessions, rather than interpret more/fewer events as an edge.

## Calendar, UTC grid, knowledge and label timing
Pin exact exchange calendar/source/tzdata and explicit per-date UTC open/close; retain America/New_York view only for interpretation. No host-time conversion, weekday-only fallback or universal 390 bars. Calendar/interval/knowledge evidence UNKNOWN blocks real-data eligibility.
For scheduled session open O and close C, decisions are t=O+25m+5m*k for integer k>=0 while t+4m<=C. All arms and both symbols use this grid, even when no row arrives exactly at t. At each t, request an immutable unique per-symbol frame containing only exact revisions proven known at or before t and supported complete intervals ending no later than t. Do not select t from the latest observed bar or publication batching. Partial/missing tails are checked against an approved expected completion watermark, with explicit staleness policy (proposed #13 default max_age_minutes=2); absence of evidence cannot establish the watermark.
Normal 09:30–16:00 example: first 09:55 ET, last 15:55 ET. Hypothetical calendar-verified 09:30–13:00 early close: last 12:55 ET. These examples specify arithmetic, not evidence that a particular real date follows that calendar.

Primary descriptive movement label: entry OPEN of [t+1m,t+2m), exit CLOSE of [t+3m,t+4m); exactly three consecutive same-session one-minute outcome intervals. The minute after the decision is intentionally skipped. No horizon past C. This is a delayed OHLC label proxy, NOT a verified executable fill.
Fixed label knowledge cutoff per session: C+24 HOURS of elapsed UTC duration, not assumed next-day ET wall time across DST. Use only outcome revisions proven known by that cutoff; pre-cutoff unresolved conflicts cause missing label. Later corrections cannot rewrite this label vintage. Features always use t, never label cutoff. An earlier event's label may become known later, but must not affect earlier selection/cooldown/arm definition.
This delay is a hypothesis. Real revision-specific arrival must satisfy evidence; assumed latency never substitutes for it. Missing intervals/entry/outcome, invalid values or unknown label knowledge retain an event with missing reason and denominator membership; do not impute zero movement.

## Gap relative to current #14
| Current code | Proposed study need | Required separately approved work/test |
|---|---|---|
| Decisions at distinct available_at times | Fixed calendar grid, even without arrivals | Explicit grid schedule / as-of sealed frames; batching invariance |
| Rows filtered at global label cutoff, evaluate at each knowledge time | Per-decision revision selection, no final-series flattening | Frame-driven/bitemporal contract; late-revision/unknown-known-time tests |
| All known conflicts retained as duplicates | Approved revision identity/tie policy | Ambiguity fails closed; no last-row-wins; lineage retained |
| Next minute boundary at/after known time, potentially zero delay | Entry t+1m with three complete bars | Boundary/availability and precise horizon tests |
| Greedy event cooldown | Common five-minute grid for all arms | Arm comparisons share opportunity grid; no outcome-based cooldown |
| Single engine conjunction | A/B/C and paired filter ablation | Independent arm oracles without modifying production engine |
| Naive ET seconds and supplied sessions | UTC/calendar-aware authoritative schedule | DST, early close, holiday, precision, blocked timezone cases |
| Caller-supplied freeze/inspection strings | Immutable preregistration plus restricted access log | Freeze cannot authenticate itself; actual dates/approval/source custody |
| No daily-context/pair classifier | Prior-only daily context and separate pair states | No same-day/future daily leakage, all nine valid pairs + invalid peers |
| Mean conditional available labels | Explicit denominators and date-cluster reporting | Missingness, zero-event dates and common-date analyses |

Current #14 is not a turnkey implementation of this plan. No code/tests for this revised replay were added or executed in H-003.

## Daily trend versus intraday momentum
Preserve #18 amendment exactly:
- Intraday: session-reset EMA9/21 and event features; also record continuous latest eligible close/session open - 1 as developing-session movement (not a multi-day trend).
- Daily context: latest 60 scheduled completed daily sessions strictly before study day, ALL evidenced and available by decision t. SMA-seeded EMA9/21 across those daily closes; UP when prior completed close > daily EMA9 > daily EMA21, DOWN reverse, otherwise MIXED. Adjustment/units, revisions and daily aggregation lineage must be consistent and approved.
- Never use the study day's eventual daily close/high/low/volume in a decision stratum. A final day's direction can only be a clearly ex-post outcome, never an as-of condition. Revised prior-day data becomes usable only when its revision was known.
- Context strata WITH_PRIOR_DAILY_TREND / AGAINST_PRIOR_DAILY_TREND / MIXED_DAILY_CONTEXT / DAILY_CONTEXT_UNAVAILABLE, cross-tabbed with developing-session UP/DOWN/FLAT and session-relative [O,O+60m), [O+60m,O+180m), [O+180m,C) bands.
- Daily-context missingness remains an explicit primary stratum, not a reason to silently discard otherwise intraday-eligible observations. A common-context-complete secondary subset must disclose selection/missingness. Do not introduce a trend gate.
Observational stratification can reveal daily-context composition; it does not prove causal separation, incremental prediction or independence from the broader market trend.

## Data eligibility versus strategy NO TRADE
1. Adapter blocked data => decision_eligible=False, no engine invocation, NO TRADE display with adapter reason. NOT a valid strategy rejection.
2. Valid frame, insufficient common warmup => not yet a study opportunity. Grid schedule avoids first 22 bars by design; delayed/insufficient history still receives explicit WARMUP/DATA exclusion.
3. Valid eligible arm opportunity but conditions fail => strategy NO TRADE with arm-specific failed gates.
4. Valid candidate => preserve symbol direction, reasons/observations, frame timestamp/hash and separate eventual label status. Missing label never retroactively changes a candidate.
Always retain raw per-symbol signal, eligibility and reasons, including if peer invalid.

For two data-eligible symbol opportunities, B=bullish, S=bearish, N=valid NO TRADE:
| SPY | QQQ | Pair classification |
|---|---|---|
| B | B | AGREEMENT_BULLISH |
| B | S | CONFLICT |
| B | N | SINGLE_CANDIDATE |
| S | B | CONFLICT |
| S | S | AGREEMENT_BEARISH |
| S | N | SINGLE_CANDIDATE |
| N | B | SINGLE_CANDIDATE |
| N | S | SINGLE_CANDIDATE |
| N | N | BOTH_NO_TRADE |

If either/both symbols are data-ineligible, classify PEER_DATA_UNAVAILABLE regardless of the other's candidate; retain each original signal and invalidity reason. Never call invalid data a valid N. Retain one valid symbol's descriptive result even when paired analysis is unavailable. Compute pair state separately per arm/time, including both symbols' daily contexts. No forced consensus, averaging direction or dropping CONFLICT cases.

## Dates, splits, overlap and dependence
Freeze UTC T0, actual calendar dates, code/dependency/source/evidence/calendar hashes, parameters, arms, label vintage, access policy and protocol before viewing evaluation outcomes. Until then all dates remain UNKNOWN.
- Development: explicitly inspected pre-T0 history, never untouched by renaming.
- Rehearsal: 60 eligible exchange session dates ending strictly before T0, as specified in #18; eligibility determination/selected dates must be recorded using pre-outcome quality rules, with skipped scheduled dates/reasons visible. Do not search among alternative windows. If insufficient evidence, block; no silent shortening.
- Embargo: first five scheduled sessions after freeze excluded. Proposed separation convention, not proof of statistical independence.
- Future evaluation: next 120 FIXED scheduled sessions after embargo; SPY/QQQ identical dates. Do not replace missing dates, extend for low counts, tune, stop adaptively or inspect interim labels. Operational capture-health checks do not inspect outcomes. No capture authorized here.
- Exact access/custody and freeze records must establish whether future data stayed unviewed. Any early label access invalidates untouched status and requires new prospective window/freeze. No present code string proves non-inspection.
- Grid spacing five minutes exceeds delayed three-minute outcome interval window, so planned within-symbol primary label windows do not overlap. Features still overlap and serial dependence remains. Per-minute candidate logs are secondary and overlapping.
- Never split same session date across train/test or across symbols. Pair SPY/QQQ by date; date-cluster and five-consecutive-date-block uncertainty sensitivity preserve correlation. Both correlations and selection effects remain risks.

## Denominators and estimands
Retain all scheduled dates, grid opportunities, symbol eligibility, no-candidate dates, daily-context-unavailable strata and missing labels. No fill, manufactured bars, raw revisions or source deletion. Peer/date exclusions in paired analyses do not erase single-symbol diagnostics.
Preserve #18's proposed primary descriptive A-minus-B date-level contrast conditional on selected valid labels, with unequal selection disclosed. Proposed clarification requiring approval: per arm/date first average each symbol's observed candidate labels, then equal-weight SPY/QQQ only when both have defined means; paired A/B contrast uses dates where both arms' two-symbol means are defined. NO EVENTS or ALL LABELS MISSING => undefined, not zero. Record dropped-date reason, all scheduled-date counts and a single-symbol/all-date coverage sensitivity. This conditional comparison is vulnerable to informative selection and cannot be sold as a fixed-exposure portfolio return.
Also report A/B/C counts, median/sign fraction, conditional movement, selection rate, valid NO TRADE rate, quality-blocked rate, retained/excluded B results, long/short/time/daily/conflict strata and missing-label fractions. Bootstrap paired date clusters 10,000 times with seed 20261027; five-date moving-block sensitivity prespecified. Undefined sparse resamples remain undefined with counts; no invented intervals or claims that more tests establish edge. All null/negative arms/results remain visible; no winner selection or p-value fishing.

## Proposed hypothetical cost-sensitivity appendix — needs explicit design approval
This is an AMENDMENT PROPOSAL to #18's current “No transaction costs are modeled” clause, not a runtime change or assertion about actual broker costs.
Primary labels remain descriptive gross direction-adjusted ETF movement. Separately, for each labeled candidate with gross movement m PERCENTAGE POINTS and assumed total round-trip cost k BASIS POINTS in {0,1,2,5,10}, define adjusted proxy m-k/100 percentage points (or gross bps 100*m minus k). Applies identically to long/short labels. No entry without a candidate; do not charge no-candidate opportunities.
Interpret k as all-in round-trip spread crossing + adverse slippage + commissions/fees. Actual components, bid/ask quotes, execution delay, capacity, borrow and market impact are UNKNOWN. Do not add the grid cost on top of separately assumed costs or claim components were measured. Equal entry/exit allocation k/2 is an arithmetic scenario only; no evidence it describes fills. Rebate/favorable execution unsupported.
Use fixed unit notional per hypothetical candidate; define planned turnover as 2 one-way notional units per candidate. Report selected-event count and missing-label event count separately; realized turnover is UNKNOWN. Do not sum labels as a compounded portfolio, and do not infer actual concurrent capital usage.
Per-event break-even round-trip cost = gross bps (negative means no nonnegative cost makes that proxy positive). Conditional sample mean break-even = mean gross bps, with missingness/date weighting explicit; “break-even” is scenario arithmetic, not achievable execution. Report every grid level with the same denominators and date clusters; do not select favorable k or calibrate it after outcomes. OHLC cannot establish fills, capacity, market impact or options P/L. No hypothetical adjusted result may be reported as observed profitability.

## Proposed synthetic acceptance matrix — no tests executed here
| Case | Expected invariant / evidence |
|---|---|
| Same inputs/context/versions | Deep-sealed inputs unchanged, identical frames/manifest/deterministic labels |
| Late revision after decision | Earlier features/pair/daily context unchanged; label vintage separate |
| Revision after label/train/test cutoff | Earlier labels/reason codes unchanged |
| Known conflicting revision / unknown known-at | Explicit blocked frame or missing label; never latest-final flattening |
| Batch receipt schedule | Same as-of minute information gives same fixed-grid opportunities |
| Fractional availability, exact t boundary | Never visible earlier through truncation; no same-instant executable-open assumption |
| 16:00 raw labels under unknown/start/end mapping | Raw retained; unknown blocked; approved synthetic bindings yield distinct intervals |
| Gap/duplicate/missing tail/whole symbol/day/partial pagination | Correct exclusions/denominators and no fill or fabricated completion |
| DST/holiday/early close | Pinned UTC schedule; t+4m<=C; no unsupported time conversion |
| Daily future/same-day final mutation | No earlier context change; 60-day and 22-minute warmups distinct |
| Nine valid pair combinations and invalid peer cases | Exact table; reasons preserved; CONFLICT never alters original candidates |
| Arm boundaries and A/B/D relation | Independent formula oracle; common guards; correct retained/excluded B membership |
| Horizon/entry/exit and missing outcome | Exactly t+1 to t+4; same session; missing not zero |
| Cost units/sign and k grid | 1 bp subtracts .01 percentage point for both directions; no double charging; no missing-label imputation |
| Zero-event/undefined dates/sparse bootstrap | Counts retained; undefined means/intervals explicit; no zero-return substitution |
| Future test data/labels mutated | Earlier train decisions/labels/strata and preregistration unchanged |
| Outputs/storage behavior | Exclusive versioned artifact creation only in later authorized run; no network/store/order calls |

## Approval requests and return
A-010 coordination review must accept or return these documents with reasons. Separate human decisions:
1. Independent reviewer identity, qualifications, willingness, access and authorship independence for exact #13 head. No candidate established.
2. #17/#18 mapping/knowledge/revision/calendar/interface and this cost/estimand clarification: accept, amend or defer before freeze. Rationale: current code does not provide proposed as-of/frame/grid behavior; alternatives are explicitly retrospective sensitivity only or keeping study blocked.
3. Separately bounded pure offline implementation and synthetic tests; no provider/DB permissions implied.
4. Source eligibility, actual dates/custody/freeze and explicit study-execution authority after evidence exists.
Each decision must link exact revision, approver/time/rationale in PR #19. None received. Merge approval is separate and later; no protected PR modified by H-003.
