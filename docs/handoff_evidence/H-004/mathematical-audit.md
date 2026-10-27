# H-004 — mathematical consistency and units audit of C1
Recorded-at UTC: 2026-10-27 13:52:33 UTC. Owner coding agent; status RETURNED_FOR_REVIEW. Documentation derivation only; no code, data, replay, statistical simulation or empirical output.
Review source: [H-004 / C1 acceptance](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443579931). Audited C1 at cbd49fe9ec1b72c04249c499d42d7bbff23e07e1, blob 10b7844a2c8d5c910f9c92e9c31fc31092b0906f. Coordination acceptance is not approval of any formula/design/freeze. Original C1 remains preserved.

## Definitions, denominators and units
Use one symbol/time unit i=(s,t) per symbol per eligible paired grid time. E_d contains paired times with BOTH intraday frames eligible; N_d=2|E_d| counts SYMBOL-TIME units. z_ai in {-1,0,+1}; r_i=100*(exit_close/entry_open-1), measured in percentage points (pp). A common label vintage/revision must define the SAME r_i for every arm at unit i. If arm-specific entry/exit or revisions differ, cancellation formulas below do not apply and a new design is required.

For N_d>0 and identified contributions:
G_ad=(1/N_d)*sum_i z_ai*r_i;
Delta_d=G_Ad-G_Bd=(1/N_d)*sum_i c_i*r_i, c_i=z_Ai-z_Bi.
These are descriptive unit-notional contributions per common opportunity, not percentages of an invested portfolio. N_d=0 => UNAVAILABLE, never divide by zero or replace with zero. A date's G/Delta weighting differs from pooling all dates; equal-date mean is sum of identified date statistics divided by their count, NOT sum of numerators divided by total opportunities. Record undefined/blocked dates and selection for every summary. Reuse date clusters for both symbols and all arms.

Denominator counterexample: one paired eligible time, only SPY contributes +0.10 pp and QQQ has a valid zero-exposure contribution. N=2, G=+0.05 pp. Dividing by |E|=1 gives +0.10 pp and double-counts the intended per-symbol opportunity scale. Aggregating a hypothetical SPY+QQQ basket first and then using |E| would require an explicit half-weight basket; it is equivalent only if the half weights are present.

## Selection counterexample: conditional advantage can reverse on common opportunities
Faithful A is a filtered subset of B with identical direction at retained units: A's EMA/volume requirements include B's and add OR/proxy/pattern gates. Thus A-only or opposite A/B directions are specification violations, not expected study states. Preserve that invariant in later tests; do not assume different baselines are independent samples.

Purely hypothetical algebra table, both symbols identical at each time:
| Time | SPY / QQQ common r | A signals | B signals |
|---|---|---|---|
| t1 | +0.20 pp each | bullish each | bullish each |
| t2 | +0.10 pp each | valid no-candidate each | bullish each |

Per-symbol conditional selected means: A=0.20 pp, B=0.15 pp, A-minus-B=+0.05 pp. Common denominator N=4: G_A=0.10 pp, G_B=0.15 pp, Delta=-0.05 pp. This is a counterexample to equating selected-candidate superiority with common-opportunity advantage; it predicts nothing about actual markets.

Subset algebra: on retained A/B units c=0; on B-only units c=-z_B; on both-no-candidate units c=0. Consequently Delta is minus the excluded B gross contribution divided by N. A-minus-B common-opportunity contrast measures the additional filter's selection/exposure policy under the SAME labels, not an independent forecast comparison or causal incremental edge. With equal N and known labels, G_a=selection_fraction_a * conditional_selected_mean_a; this identity explains the role of selection frequency. Zero-candidate conditional mean is undefined even though G_a=0 by exposure convention.

## Unknown label cancellation
Define coefficient cancellation before numeric multiplication by an unknown label:
- c=0 => contrast contribution exactly 0 because exposures are identical and the underlying label is shared. The label remains UNKNOWN; never evaluate 0*NaN and silently propagate/impute a price.
- z_A=z_B=0 => each arm's defined no-exposure contribution is 0, not a zero underlying market movement.
- z_A=z_B=+1 or -1 with missing r => contrast 0, BUT both individual gross arm contributions remain UNKNOWN. Cancellation in a difference cannot identify either mean.
- c!=0 with missing r => unresolved contrast term. No full-data point estimate unless all such terms are resolved.
This is a necessary explicit clarification to C1's wording: cancellation is not limited to no-candidate cases. Equal known hypothetical costs also cancel under equal exposure; actual unknown execution differences do not become known.

If one arm uses a corrected label and the other the original, equal z does NOT cancel differing r. Reject that label-design mismatch. A candidate's missing outcome must not retroactively change z, E, daily context or pair state.

## Missing-label intervals and tipping point
Let K contain units whose contrast term is identified (observed r OR c=0), U contain unresolved nonzero-coefficient units, S=sum over K of c*r with exact-zero terms defined above, N unchanged. In C1's hypothetical box scenario each unresolved underlying r_i lies in [-L,L] pp. Then:
Delta in [(S - L*sum_U |c_i|)/N, (S + L*sum_U |c_i|)/N].
Proof: each linear term is bounded by +/-L|c_i|; summing gives numerator bounds, dividing by positive N preserves inequality. Under an unconstrained per-unit box these bounds are sharp (endpoint signs can attain them); empirical cross-unit constraints might narrow them, but are not known/assumed. Correlation affects uncertainty estimation, not validity of a deterministic containing box. This interval is a scenario identification bound, NOT a confidence interval or observed range.

For faithful A/B, |c|=1 on U, simplifying width to L*|U|/N. General arm comparisons can have |c|=2 for opposing directions, so do not use unresolved count alone as a universal substitute for sum|c|.

Toy bound: one known contrast contribution -0.02 pp, one unresolved c=-1, N=2 and assumed L=0.10 pp yields [-0.06,+0.04] pp. Ignoring missingness and reporting S/N=-0.01 pp as the full estimate would be unjustified. Proposed L={.05,.10,.25,.50,1.00} pp corresponds to {5,10,25,50,100} bp; endpoints can be exceeded in reality, so report every assumption and unrestricted NOT_IDENTIFIED. Positive prices give r>-100 pp but no finite upside bound; without additional assumptions the range is not generally finite on both sides. Do not call both sides unbounded in every special sign case.

Tipping point with U_count>0: the required arithmetic MEAN MISSING CONTRAST CONTRIBUTION is -S/U_count pp per unresolved symbol-time unit. It is not automatically a mean underlying return or the final daily Delta. If the required missing contribution lies outside the chosen scenario's attainable range, that scenario cannot flip sign. U_count=0 => no missing-term tipping point; N=0 => no statistic. If all missing c equal a nonzero constant c0, the mean missing underlying return required is -S/(c0*U_count); mixed coefficients need the weighted equation sum_U c_i*r_i=-S, not a single unweighted-return threshold.
Counterexample to a units/sign misreading: with S=+0.20 pp and two missing c=-1 terms, required mean contribution=-0.10 pp, whereas required mean underlying return=+0.10 pp. Treating the contribution threshold as a return gives the wrong sign.

Shared observed-label M_d requires both symbols' labels at each retained time; denominator 2|M_d| across all arms, even no-candidate ones. This can discard identified zero-coefficient terms and remains complete-case selection. Report M/E attrition and full-grid identification bounds alongside conditional/common-observed means. A day with N>0 and all c=0 has Delta=0 even if M empty; individual G may still be UNKNOWN if equal candidates lack labels. A day with N=0 is unavailable. Neither unknown daily context nor label failure can change decision-time E. No-event days, blocked days and partially identified dates need separate counts.

## Cost audit under unequal exposure
Let q_ai=|z_ai| (0 or 1), k total round-trip scenario cost in bp, h=k/100 pp. Gross candidate m=z*r. Scenario contribution g_ai(k)=z_ai*r_i-q_ai*h. On common N:
Delta_cost(k)=Delta_gross - h*(sum(q_A-q_B)/N).
Same k assumed for both arms, actual components UNKNOWN. For faithful subset A/B, sum(q_A-q_B)=-number(B-only units), so Delta_cost=Delta_gross+h*B_only_count/N. An avoided hypothetical cost can improve A-minus-B without improved direction prediction.

Using the four-unit selection table: B-only fraction=2/4. At k=2 bp, Delta_cost=-.05+.02*.5=-.04 pp. At k=10 bp this hypothetical difference reaches zero; that arithmetic does not establish profitable execution by either arm.
Counterexample to subtracting k directly from a common-opportunity mean: one selected event in four eligible symbol-time units, k=2 bp. Total cost effect on G is .02/4=.005 pp, not .02 pp. Conditional candidate mean cost is .02 pp per selected event; those are different denominators. No-candidate units incur no hypothetical cost. Missing candidate label leaves gross/net arm contribution unknown; deterministic cost subtraction does not identify it.

Unit conversion: 1 bp=.01 pp=.0001 in fractional-return units. Do not subtract k/100 from a fractional return. Round-trip grid {0,1,2,5,10} includes both legs; applying it to each leg doubles the intended cost. Negative directional movement subtracts cost too; do not multiply cost by direction sign. Planned turnover=2 one-way unit-notional legs per candidate; per-opportunity turnover=2*selection_fraction. Neither is observed fill turnover, capital usage or options P/L. Real borrow/spread/slippage/fees/market impact are UNKNOWN; equality of hypothetical costs cannot establish actual cost cancellation.

## Audit disposition and proposed wording corrections
C1's linear full-grid statistic, two-symbol denominator, box bounds and candidate-weighted cost formula are algebraically consistent under their stated common-label assumptions. Required precision improvements, not production changes:
1. State A subset B/same direction and filtering interpretation explicitly.
2. Define zero-coefficient difference before multiplying UNKNOWN; identical candidates can cancel while each arm mean remains unknown.
3. Name tipping-point units missing CONTRAST CONTRIBUTION; supply coefficient-weighted return equation.
4. Distinguish date-equal weighting from pooled opportunities; publish exact included date sets and all unavailable/no-event dates.
5. Keep common observed M complete-case bias, scenario bounds, conditional results and cost proxy distinct; no empirical/causal edge inference.

All examples are constructed algebra checks, not synthetic market backtest results or test-suite additions. Future implementation tests require G-H003-3 approval. Human review of the chosen estimand/cost/missingness assumptions remains G-H003-2; source/custody/study G-H003-4; independent review G-H003-1 all unapproved. No merge, provider, code, DB, data ingestion, replay/study or trading work performed.
