# PR #13 — technical review preparation
Review baseline: main b0ad02dc996b00406e7da08fb33b6382f658ea40; original engine head 286eb9b1e7071ebbc83a125dc1062e4723efcad1. This preparation adds review tests/docs and a narrow provenance guard: null/non-string/blank raw timestamps no longer become stringified candidate metadata. No formula, threshold, conjunction, ingestion or production behavior changes. It is not an independent human sign-off or an empirical strategy validation.

## Mathematical checks
Eight new tests in test_direction_math_review.py use 50-digit Decimal arithmetic on irregular price/volume inputs, separate from the engine helper, to check:
- EMA9/EMA21: SMA seed of first N session closes, then E_t = E_(t-1) + 2/(N+1)*(C_t-E_(t-1)). Numeric agreement within 1e-10 for the fixtures; session-reset convention is explicit, not overnight EMA continuity. [Fidelity EMA reference](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/ema).
- Candle-weighted price: sum(((H+L+C)/3)*V)/sum(V), anchored to supplied session open, including current completed bar. This is a bar/candle proxy, not transaction VWAP. Zero-volume bars contribute no weight. [TradingView's bar-based calculation reference](https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/).
- Relative volume: current V divided by mean of PREVIOUS 20 bars, excluding current V. Threshold equality is inclusive (>=); zero baseline is separately gated.
- Opening range: first configured N intervals of a contiguous prefix from session open, i.e. [open, open+N minutes); the later event bar is excluded. Strict close > high or < low means a close equal to a range boundary is NOT a break.
- Prior five-bar levels exclude the event bar; EMA rejection/support compares against previous completed EMA9, not a future/current extrapolation.
The sources define indicator conventions; neither source validates this conjunction or its profitability.

A ninth review test first reproduced candidates from null/non-string/blank raw stamps. A strict nonempty-string gate now yields INVALID_RAW_TIMESTAMP/NO TRADE without altering any valid source string.

Other new checks demonstrate positive price-scale invariance and long/short reflection symmetry on synthetic fixtures; result mutation does not mutate inputs or later snapshots; frozen Config cannot be edited; output JSON stays finite. These are finite regression examples, not a proof over every floating-point input. Extreme finite inputs may fail closed on intermediate overflow rather than use arbitrary-precision math.

## Conjunction/suppression review
| Default rule | Verified effect / technical risk | Reviewer decision |
|---|---|---|
| Session-reset SMA-seeded EMA9/21 | Differs from charts carrying premarket/prior-session history; early-session values are seed-dependent | Approve session anchor before comparing with external charts |
| Fast EMA slope check | Given EMA_t = alpha*C + (1-alpha)*EMA_prev with 0<alpha<1, C>EMA_t implies EMA_t>EMA_prev (and the inverse for bears), apart from floating-point ties. This is algebraically redundant, not independent confirmation | Do not count it as another piece of evidence; no formula simplification in this review |
| 22-bar minimum | First default eligible snapshot is 09:52 for a 09:30 session. EMA21 itself is available at bar 21; current implementation deliberately requires an additional guard bar | Accept this delay or propose a separately tested 21-bar policy; no silent relaxation here |
| Opening-range outside + EMA alignment + proxy alignment | Multiple correlated price-location filters. A synthetic aligned/up-volume five-bar breakout inside a wide opening range is suppressed | Decide continuation-only scope; do not describe filters as independent confirmations |
| Volume >=1.2x previous 20 | Constant-volume trend is suppressed at 1.2x and admitted at a predeclared 1.0x synthetic comparison; no time-of-day adjustment | Pre-register sensitivity analysis; no useful-signal/performance claim from fixture counts |
| Complete prefix from session open | One early missing minute suppresses the rest of the session even with later clean history | Accept conservative data-selection effects; report excluded sessions/windows |
| EMA rejection/support body and opening-side rules | Some gap/wick configurations are excluded; OHLC cannot establish exact intrabar touch/rejection order | Treat as candle geometry hypothesis, not auction/order-flow confirmation |
| Repeated outside-range closes | Candidates can repeat without a fresh crossing. Replay cooldown reduces overlap, not correlation | Define observation unit before interpreting event counts |
| Strict float comparisons | Equality/tiny perturbations can flip classifications at boundaries | Preserve explicit inequalities; review any tolerance as a new hypothesis |
| 2-minute staleness | Can reject valid but delayed history; READY means input eligible under a policy, not live feed accuracy | Adapter must distinguish captured availability from assumed latency |

Synthetic paired comparisons show WHICH filters suppress examples, not whether those examples are useful trades. No measured false-positive/false-negative rate, score, threshold optimization or confidence estimate is justified.

Recommended analysis after adapter approval: pre-register a small ablation matrix (one gate at a time), count eligible/excluded decisions and valid/missing labels by session and symbol, keep dates shared across SPY/QQQ, and reserve a new test block. Do not pick the most attractive configuration after viewing holdout outcomes. Missingness, session anchoring and correlated price filters may introduce sample-selection bias even if the code is mathematically correct.

## Causality and reproducibility boundaries
Only available_at <= as_of contributes; incomplete/invalid/duplicate/gapped/out-of-order data fails closed. Raw timestamp is retained and never interpreted as an interval boundary. SYNTHETIC is explicit; VERIFIED is only a caller assertion with a reference, not authenticated provider semantics.

The engine does not mutate input rows and builds fresh result dictionaries. It does not deep-freeze caller-owned rows against concurrent mutation; the adapter must provide a sealed immutable snapshot. Its feature hash covers normalized visible inputs, not a full run identity: retain symbol/session/as-of/config/evidence/code revision and schema alongside it. Study manifests and raw source hashes remain separate.

## Review recommendation and tests
Ready for independent technical review as a standalone RESEARCH proposal after green exact-head CI. Not approved for live data, GUI wiring, real performance claims or automatic trading. Reviewers should approve/reject the declared session seed, extra warmup bar, proxy basis, conjunctions and strict coverage policy explicitly; do not approve solely because tests pass.

Main's cumulative 69 tests plus original 19 engine tests and eight math review tests + one provenance regression = 97 guarded tests locally on Windows/Python 3.12.14. Windows/Linux Python 3.11 CI results and final heads are recorded in the PR. No database/provider/ingestion connection or real-history study was run.
