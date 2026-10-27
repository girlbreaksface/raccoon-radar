# PR #14 — availability and reproducibility review
Original head: 3c6646563d7b28695a56d86985eb2cad6347ac15, stacked on PR #13. This is technical-review preparation, not independent human approval or a real-history performance study.

## Defect reproduced and corrected before review
The original replay restricted decision times to outcome_as_of_et but built by_start from ALL supplied rows. A revision first available after that cutoff could:
1. change an earlier valid label into DUPLICATE_OUTCOME_BAR;
2. make an otherwise valid replay fail while parsing that future row's interval metadata;
3. change training outcomes when the revision was first available during the test period.

The new regression tests reproduced two failures and one exception on the original head. Replay now constructs one eligible_rows information set using available_at <= cutoff BEFORE building decision times, outcome lookup or as-of evaluations. This does not change engine formulas, thresholds, ingestion or production stores.

At an earlier cutoff, a record not yet available is absent; the missing-label reason must not reveal its later existence. The existing training-label test therefore now expects MISSING_OUTCOME_BAR rather than INVALID_OR_UNAVAILABLE_OUTCOME_BAR for a post-cutoff record. An invalid row that IS available remains a distinct invalid outcome.

## Verified causal boundaries
Five new tests check post-cutoff revision invariance of complete replay output, non-parsing of unavailable interval metadata, training outcome invariance under test-period revisions, train independence from test-price changes, and preservation of retrospective status regardless of inspection declarations. The full supplied-input manifest hash may change when a future revision is supplied; earlier train events/metrics must not. A hash change alone is not feature leakage.

Existing tests cover event features versus later prices, publication delay, next eligible minute open, full contiguous forward horizons, no skipped entry/overnight horizon, shared SPY/QQQ date splits, missing/duplicate/invalid outcomes, symbol normalization and planned cooldown independent of outcome values.

## Remaining risks / interpretation
- Next-open pricing at an exact availability boundary assumes zero decision/execution latency and an obtainable opening print. It is an optimistic LABEL assumption, not an executable fill; costs/spread/slippage are absent. Pre-register a lag sensitivity study before using real data.
- Evaluation points are distinct availability timestamps, not necessarily every market minute. Batched/late arrivals change opportunity and NO TRADE counts; disclose the observation unit.
- Revisions AVAILABLE BEFORE the cutoff remain duplicates and fail closed. There is no general bitemporal revision-selection engine. An adapter must not feed a final revised historical series with backdated availability. A future revision-aware frame/replay API needs separate review.
- Eligible/missing outcomes can be informatively selected. Report missingness by session, symbol, direction and reason; mean of available labels is not an unbiased profitability estimate.
- Greedy same-symbol windows reduce overlap but do not make SPY/QQQ, days or regimes independent. No probability or significance estimate is warranted.
- Config/engine version, code_revision/freeze_id, dataset hash and split dates make reruns identifiable, but code/freeze/inspection references are caller assertions. A string cannot authenticate a Git tree, prevent retuning or prove a holdout was unseen.
- Dataset hash identifies full provided JSON representation, including excluded/late data. Feature hashes are only one part of result identity; archive full symbol/session/as-of/config/evidence/schema/code context.
- Functions do not mutate caller inputs. They do not deep-freeze mutable caller-owned rows against concurrent writers. Use sealed snapshots from the proposed adapter.
- Naive ET strings are a v1 interface limitation; timezone/fold/calendar and original timestamp meaning are not validated here.
- Full validation remains synthetic. No real dataset, capture latency, cost model, execution semantics or statistical edge has been established.

## Review recommendation
Ready for independent technical review only AFTER the cutoff correction and exact-head Windows/Linux CI are green. Do not merge solely on this preparation; do not approve real-data/live/UI use until adapter and entry/latency/split policies are reviewed.

The new #13 review tests are inherited from the updated base branch; they are not duplicated as changes in this PR. Local cumulative suite: 69 main + 19 original engine + 8 math review + 1 provenance regression + 13 original validation + 5 availability review = 115 guarded tests. Windows/Python 3.12.14 passes; exact-head Windows/Linux Python 3.11 results are recorded in the PR. No network/provider, research-store writes, raw-data rewrite or orders were introduced.
