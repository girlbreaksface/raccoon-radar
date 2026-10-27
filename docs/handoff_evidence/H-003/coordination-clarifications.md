# H-003 coordination-review clarifications — amendment C1
Recorded-at UTC: 2026-10-27 13:40:55 UTC. Owner: coding agent. Status PROPOSED / RETURNED_FOR_REVIEW, not design approval.
Responds to [Dex's coordination review](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443196332). That review ACCEPTS package 403fb62d4e2a2563ec5ca9074b5460b0871502d2 as documentation-only evidence; it does not approve contracts, implementation, execution or merges. Original package/definitions remain retrievable at that commit. This amendment clarifies the DRAFT replay-plan.md; no empirical study or code was executed.

| Review item | Proposed clarification | Approval gate |
|---|---|---|
| 1 revision/clock ordering | Conservative bounded-time rules and explicit conflict rejection below | G-H003-2 |
| 2 estimand/selection | Common-opportunity companion and missing-label sensitivity; conditional A-minus-B cannot establish incremental edge | G-H003-2 |
| 3 daily/peer denominators | Eligibility, context and label availability are separate axes; concrete examples below | G-H003-2 |
| 4 custody/freeze | Actual custodian/access evidence and prospective dates required; no self-authenticating string | G-H003-4 |
| 5 gross/cost proxy | Separate schemas, units and arithmetic scenarios; no executable performance claim | G-H003-2 |

## 1. Exact revision-knowledge and clock rules (proposed conservative v1)
All rules operate on immutable source envelopes already supplied; no provider access authorized. Pin mapping approval, source scope, UTC clock model, calendar and policy before evaluation. Raw stamps, payload types/values and every receipt remain unchanged. A hash establishes identity, not truth.

For each full revision r, retain interval identity I, source revision/sequence if evidenced, payload hash, raw refs and separate UTC uncertainty bounds:
- receipt of all values: [L_value,U_value];
- receipt of required completion evidence: [L_complete,U_complete];
- source publication bounds if independently evidenced, distinct from receipt.
For captured observations define conservative usable knowledge bounds K_low=max(interval_end,L_value,L_complete), K_high=max(interval_end,U_value,U_complete). All bounds must be finite, trusted and internally consistent. Timestamp precision/conversion uncertainty is included in these bounds. Publication alone never substitutes for full local usability. A historical point-in-time source needs separately approved evidence of availability to the declared observer; otherwise UNKNOWN. Authority review today does not backdate knowledge of today's corrected values.

At cutoff t, filter envelopes BEFORE reading unavailable payloads:
| Envelope state | Disposition |
|---|---|
| K_high <= t, interval ended, evidence valid | Definitely known; validate payload/coverage |
| K_low > t | Definitely not yet known; exclude from decision and its quality/duplicate checks |
| K_low <= t < K_high | Clock/order uncertainty straddles cutoff: block affected required frame, CLOCK_UNCERTAIN_AT_CUTOFF |
| Unknown receipt/completion bound | AVAILABILITY_UNKNOWN; block affected frame, never assign bar end/fetch time |
| Envelope cannot identify affected symbol/session/interval | Block requested frame SOURCE_SCOPE_UNKNOWN; cannot safely assume irrelevance |
| Conflicting clocks, receipt before impossible causal predecessor, unsupported precision | CLOCK_EVIDENCE_CONFLICT; fail closed, preserve original evidence |

A separate completion watermark W must state covered interval ends/source/pages and its own receipt uncertainty. Use W only if its entire required evidence was definitely known by t. W >= interval_end plus closed-bar semantics is necessary for complete=True; elapsed clock time or a watermark's market-time value without knowledge time is insufficient. W does not prove finality, pagination exhaustion, missing-tail completeness or absence of corrections. Validate expected coverage against a pinned calendar/target watermark; an incomplete/stale prefix is not made complete by selecting its latest bar.

Ordering/ties: definitely nonoverlapping knowledge bounds (U_a < L_b) establish an order; overlapping bounds do not. Equal timestamps never establish sequence by array order, page order, lexical revision ID, hash or host time. A trusted provider sequence is retained as evidence but is not, by itself, permission to select a revision.
Conservative v1 rejects multiple differing definitely-known revisions of a required interval, even if their arrival order is known: CONFLICTING_REVISION. No last-row-wins, final-series flattening or implicit correction selection. A future supersession resolver requires a separate approved policy/API and tests. Exact retry duplicates may be coalesced ONLY if a frozen policy proves same source revision identity, payload, interval, relevant flags and completion metadata, retaining every raw ref; default without that approval is DUPLICATE_UNRESOLVED. Matching canonical prices alone is insufficient. A tied different-value correction fails closed. Finality can remain UNKNOWN even for a completed eligible original.

Hypothetical examples (synthetic arithmetic, not provider evidence):
- At t=14:00:00Z, original definitely known at 13:59:59Z; correction definitely known at 14:00:02Z: ignore correction for t, earlier frame unchanged.
- Correction knowledge bound [13:59:59.900Z,14:00:00.100Z] straddles t: block affected frame rather than choose original or corrected values.
- Two different values both known at 13:59:59Z: CONFLICTING_REVISION; same clock timestamp does not break tie.
- Original/correction both definitely known by t, with trustworthy ordered sequence: still blocked in conservative v1; sequence-based supersession not implemented/approved.
- Closed minute ending 14:00 with watermark received no earlier than 14:00:01: at 14:00 no completion claim; at 14:00:01 or later revalidate with all evidence.
- Historical final bar fetched today, first historical arrival UNKNOWN: cannot replay it at historical bar end.
Apply the same rules independently to daily-context revisions and label-vintage cutoff. Unknown daily knowledge blocks context, not otherwise valid intraday primary eligibility. Current #14 does not implement this bounded-knowledge frame contract.

## 2. Conditional contrast, common opportunities and missing labels
The original selected-candidate conditional means remain descriptive only. A-minus-B can change because different events/dates survive selection, label missingness or both-symbol complete cases. It cannot establish incremental edge, causality, investable returns or out-of-sample efficacy. Do not interpret coordination acceptance as approval of that estimand.

PROPOSED companion, to freeze before outcomes:
- D is all 120 scheduled future session dates; G_d is the same fixed five-minute grid for all arms/symbols.
- E_d is the subset of grid times where BOTH symbols have mandatory intraday data eligibility/common warmup at decision time. It is defined without future outcomes or daily context. Record scheduled |G_d|, |E_d| and all blocked reasons. Data-blocked slots are not valid NO TRADE.
- For each symbol/time in E_d, let z_a be +1 bullish, -1 bearish, 0 valid no-candidate for arm a. Let r be the common direction-neutral delayed open-to-close ETF percentage movement, independent of arm selection, with the fixed label vintage. It is a gross OHLC label, not fill/return evidence.
- Common-opportunity full-data contrast: T_d=sum((z_A-z_B)*r)/(2*|E_d|). Each eligible grid slot/symbol contributes on the same denominator; no-event days with |E_d|>0 have T_d=0 as a defined zero-exposure DIFFERENCE when every coefficient is zero, not an imputed zero market movement. Dates with E_d empty are UNAVAILABLE, not zero. All scheduled dates remain in the coverage table.
- Also report each arm's common-opportunity gross contribution mean sum(z_a*r)/(2*|E_d|) where identified, selection rate and selected-candidate conditional mean. Common denominators deliberately measure a different descriptive exposure/selection policy; they do not isolate forecasting skill.

If any nonzero coefficient has a missing r, full T_d is UNKNOWN, not zero-filled. A missing label for a zero coefficient cannot change this contrast, but remains a missing underlying-label count. For per-arm means, zero signal similarly defines no exposure; a missing candidate label remains unresolved.

Common-observed-label companion: M_d subset of E_d where BOTH symbols' direction-neutral labels are known/valid. Compute sum over symbols/times in M_d divided by 2*|M_d| for ALL arms and A-minus-B on the identical subset. Never use arm-specific label sets. M_d empty => undefined. Complete-case bias still exists; report M/E attrition by symbol, reason, daily context, pair state, candidate status and date. Missingness is not repaired by using a shared subset.

Sensitivity alongside those conditional/common-observed results:
1. Publish identified known numerator, original full E denominator, unresolved nonzero-coefficient count, missing-label counts and whole missing dates. Never report known-sum/N as a point estimate when unresolved terms remain.
2. Unrestricted distribution-free full contrast is not generally finitely bounded from OHLC positivity alone (upside is unbounded). Say NOT_IDENTIFIED.
3. Hypothetical bounded-movement sensitivity, proposed L in {0.05,0.10,0.25,0.50,1.00} percentage points (5/10/25/50/100 bp). Assume EACH unresolved underlying r in [-L,L] only for the scenario. Then T_d lies in [(S-L*sum|z_A-z_B|)/N,(S+L*sum|z_A-z_B|)/N], with S known numerator, N=2|E_d|, sum restricted to unresolved labels. These are assumption-dependent intervals, NOT confidence intervals or empirical bounds; actual extremes can exceed L. Report every L and assumptions, not only favorable levels.
4. Tipping point: if U unresolved contrast contributions, mean contribution -S/U would offset the identified numerator (U>0). It is a diagnostic threshold, not estimated missing performance.
5. Date-level summaries use the same prespecified date sets for every arm; report undefined/unavailable dates, no-event dates and missingness sensitivity separately. Bootstrap only identified common-date statistics, retain scheduled-date coverage and disclose selection. Zero-exposure/no-event days participate as defined above; data-unavailable days never become zero. No favorable-window/date substitution.

Toy denominator example: one paired-eligible grid time gives N=2. Both arms no-candidate for both symbols => full contrast zero even if market labels missing; label coverage remains missing. If A is no-candidate, B bullish SPY and no-candidate QQQ, and SPY r is missing: N remains 2, contrast UNKNOWN; no-event A is not dropped to create arm-specific denominators. All numbers are algebraic examples, not study results.
Daily/trend strata, disagreement and missingness remain observational; no hypothetical sensitivity proves incremental edge. This companion and L grid require G-H003-2 approval and a new freeze, not silent replacement of #18's proposed primary label.

## 3. Daily context, peer validity and paired denominators
Daily context availability is independent of intraday E eligibility. Unknown daily context is an explicit stratum; it does not change arm signals or E/M. Invalid intraday peer removes that TIME from E, not automatically the entire session or the valid symbol's single-symbol report. For the secondary both-symbol daily-context-complete subset, require both contexts known at t, recompute all arms on the identical subset and disclose attrition; never relabel it the full primary analysis.

| SPY intraday/signal/daily | QQQ intraday/signal/daily | Pair state | E / daily-complete / M consequence |
|---|---|---|---|
| valid B / UNKNOWN | valid S / DOWN | CONFLICT, both candidates retained | In E; excluded ONLY from daily-complete secondary subset; M depends on labels |
| valid B / UP | valid N / UNKNOWN | SINGLE_CANDIDATE | In E; UNKNOWN context stratum retained; daily-complete excludes; M independent |
| valid N / UNKNOWN | valid N / UNKNOWN | BOTH_NO_TRADE | In E; no-event time retained; daily secondary excludes; no strategy rejection attributed to unknown context |
| valid B / UP | invalid frame / any | PEER_DATA_UNAVAILABLE | Not E for paired primary; SPY single-symbol candidate retained; QQQ invalidity recorded |
| invalid frame / any | valid S / DOWN | PEER_DATA_UNAVAILABLE | Not E; retain QQQ single-symbol report; no forced consensus |
| valid B / UP | valid S / DOWN, exit label missing | CONFLICT unchanged | In E, not M; contrast unresolved unless coefficient cancels; missing label does not retroactively invalidate decision |
| valid N / UP | valid N / DOWN, all labels known | BOTH_NO_TRADE | In E and M; zero-exposure contribution, not omitted day |
| both invalid / UNKNOWN | both invalid / UNKNOWN | PEER_DATA_UNAVAILABLE | No E; scheduled time/date counts retained, never BOTH_NO_TRADE |

B/S/N abbreviations match replay-plan.md. Both E and M are time-level paired sets; same-date SPY/QQQ dependence remains clustered. A date with some invalid peer times retains other E times, with equal date weighting and exposure counts explicit. A date with zero E is unavailable in paired outcome means and counted in scheduled coverage. Original conditional means may still be undefined for no-event dates; distinguish that fact from common-opportunity zero-exposure convention. Report the nine valid signal pairs and invalid-peer reasons separately for each arm.

## 4. Prospective freeze and access custody
Before the first evaluation session, human approval must establish:
- Named accountable study custodian and separate reviewer, roles/access permissions, authorized collectors and observers; identity/access evidence links. None currently designated by this amendment.
- Exact UTC T0 and independently timestamped approved freeze commit/hash covering actual 120 dates, five-session embargo, source/mapping/calendar/knowledge policies, code/dependencies, arm rules, all estimands/sensitivity grids, output schemas and deviations policy. Timestamp provenance and change protection must be documented; a mutable local clock or Git commit date alone is insufficient.
- An approved restricted location for raw captures/revisions and withheld labels, append-only/tamper-evident inventory, capture hashes, trusted receipt/clock evidence, access controls and a read/export/access audit covering ALL privileged roles and derived label channels. Hashes establish integrity only relative to recorded bytes, not who saw them or semantic truth.
- Evidence that data did not yet exist at freeze and capture began only in the authorized future window; approved collection is separate from viewing evaluation outcomes. Operational monitors receive limited quality metadata, not OHLC/outcomes sufficient to inspect labels. Unavoidable label-equivalent access by humans/agents must be disclosed.
- Predeclared unblinding date/authority after all scheduled sessions and label vintages, custody attestation, access-log completeness review and immutable analysis-code/protocol check before unsealing.
Record separate statuses FROZEN_PROTOCOL, CUSTODY_EVIDENCED, FUTURE_WINDOW_COMPLETE, AUTHORIZED_UNBLINDING, EVALUATED; no single string establishes all. A caller's DECLARED_NOT_VIEWED, freeze_id or manifest checksum cannot authenticate untouched data.

Missing/incomplete access logs, privileged bypass, early outcome exposure, protocol/head drift or unknown custody => UNTOUCHED_NOT_ESTABLISHED; block confirmatory claim. Preserve deviations and original freeze; no retrospective deletion or relabeling. Maintainer decides whether to retain a clearly exploratory exposed window or separately preregister a NEW future window after the final change. Do not silently extend/replace dates or call previously inspected data untouched. New prospective capture, implementation, unblinding and study execution each need authorization; none is granted here.

## 5. Gross labels and hypothetical cost proxies
Keep separate fields/tables:
- gross_directional_movement_pp = z*r for a candidate, using delayed ETF OHLC labels and fixed revision vintage. This is observed only IF an approved study later supplies eligible data; nothing is observed in this amendment.
- hypothetical_cost_adjusted_proxy_pp(k) = z*r - |z|*k/100 for k in {0,1,2,5,10} bp. For a valid no-candidate z=0, contribution/cost zero by exposure convention; missing candidate gross label remains missing even though hypothetical cost is specified.
- realized_execution_pnl/fill/spread/slippage/fees/capacity/borrow/market_impact = UNKNOWN / NOT_MODELED. No options or order APIs.
For common-opportunity A-minus-B cost contrast, subtract (|z_A|-|z_B|)*k/100 on the SAME grid/denominator; do not subtract one per-candidate cost from a per-opportunity statistic or compare arm-specific complete cases. Preserve gross alongside each scenario.

Hypothetical arithmetic only: gross +0.08 percentage point with 2 bp all-in round-trip cost yields +0.06 pp; gross -0.03 pp yields -0.05 pp. These examples are not observations, achievable fills, confidence estimates or profitability claims. Grid k is assumed all-in cost; actual spread/slippage/commission components UNKNOWN, no double counting. No costs charged to absent exposure; no zero-fill for missing candidate outcomes.
Unit-notional planned turnover =2 one-way notional units per candidate, separately count unlabeled candidates; actual turnover/fills remain UNKNOWN. Conditional mean gross bp is an arithmetic break-even scenario, not executable break-even. Differences in selection, time in market, missingness, correlated symbols and capital usage prevent compounding labels into a portfolio-return claim. A three-minute bar path, next-minute open and one-minute delay do not guarantee executable fills. All k levels and missing-label sensitivities must be shown without choosing a winner.

## Proposed acceptance checks and remaining gates
Future separately authorized synthetic tests: uncertainty bound equality/straddling, unknown metadata scoped conservatively, tied corrections, post-cutoff revisions ignored, watermark receipt after bar end, before/after daily revision knowledge; E/M membership independent of arm/daily context/outcomes; nine signal pairs plus concrete table; no-event versus no-data dates; missing-label bounds/tipping-point units; freeze/access drift and early-label exposure; gross/cost schema separation and candidate-weighted costs. These tests are NOT implemented or executed here.

G-H003-1 through G-H003-4 remain unapproved. Original package coordination ACCEPTED does not equal independent code review or approval of this amendment. Human maintainer must approve policies/estimands/custody before separately bounded implementation and evidence collection. Independent reviewer still unidentified. #13 unmerged, #14 stacked, #17/#18 proposals and #19 unmerged. No provider connection, data acquisition, ingestion/DB/trading change, study or merge.


## H-004 audit cross-reference — 2026-10-27T13:55:30Z
C1 [accepted as documentation response](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443579931), not G-H003-2 approval. See [H-004 mathematical/units audit](../H-004/mathematical-audit.md) and [decision matrix](../H-004/decision-matrix.md), package 8ae184d56f33d0c1405d1642ec608c6183e37ca9. They clarify faithful A subset B, identical-candidate missing-label cancellation without identifying arm means, contribution-vs-return tipping-point units, date weighting and exposure-weighted costs. This supplements the proposal without rewriting original C1. No study, code or empirical findings; all human gates remain unapproved.
