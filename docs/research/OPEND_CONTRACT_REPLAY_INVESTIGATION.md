# OpenD data contract investigation and SPY/QQQ replay design
Status: DESIGN / NOT FROZEN / NOT IMPLEMENTED / NOT EXECUTED.
Investigation date: 2026-10-29; public documentation observed around 16:10–16:14 UTC.

## Scope, authorization and evidence classes
Owner [authorization6501986475](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6501986475) plus direct coding-chat instruction permits documentation investigation/design only. The owner waived independent review as a prerequisite to this phase; earlier internal reviews remain non-independent. This neither approves merges nor verifies a source contract.
Only public documentation and repository text were read. No SDK imported, client instantiated, credentials accessed, market/history/account endpoint queried, research DB opened, test code written, replay/study executed or production changed. Documentation HTTP reads are not provider market-data retrieval. Public documentation examples are illustrative, not captures made by this project.

DOC_VERIFIED means the cited text was found, not that provider runtime behavior was measured. REPO_VERIFIED means the pinned repository artifact was read. UNKNOWN means unavailable evidence, not an assumed default. PROPOSED denotes a decision requiring approval. **No empirical SPY/QQQ provider behavior was verified in this phase.**

Existing design references, preserved rather than overwritten:
- [PR17 adapter](https://github.com/girlbreaksface/raccoon-radar/blob/9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3/docs/CANONICAL_COMPLETED_CANDLE_ADAPTER_DESIGN.md), blob876b29be4aecb6fba95e3fa2fa395aab8a35a4fb.
- [PR18 study](https://github.com/girlbreaksface/raccoon-radar/blob/eb683559a0ab685503627612ab22aa16a77066ed/docs/DIRECTION_INTEGRATION_STUDY_PROTOCOL.md), blobe4f381a8fa8d8ed968e01bd501b7a95b763df38a.
- [PR32 contract](https://github.com/girlbreaksface/raccoon-radar/blob/e71f8de950ead63b505b179ab2ee124b369f2741/docs/OPEND_ADAPTER_SPEC_CHARACTERIZATION.md), blob80809261ac706375ff3b9096e4548fdd467d8dc9.
- Synthetic consumer pins: PR31 24a5c5de529f99992ec331f6ea91c39c1f61fa6e; PR33 b7dd5e5100c2823701c8de639fc0e9048adde80e; PR34 ef749d88ae092aec4cd42dd34703539d84f053c9; rehearsal PR35 6e8530dca5171e40d8126d183199479dba0a7358. Their synthetic evidence is not provider evidence.
- Shared PR19head16bd05f5d694d7d2d472ff3d9ddf218ba32c0cad; handoffblob09e826b23f7fde82d16bab7c4a102ed91b2b4503; knowledgeindexblob6427019f678a58b67a63b3994df6009539904fb4. Main b0ad02dc996b00406e7da08fb33b6382f658ea40. Historical counts in older records are not current validation of this proposal.

## Documented facts and their precise limits
Sources S1–S8 below were read as public web pages, not downloaded SDK/package code. Opened OpenD pages identify themselves as v10.12; search caches sometimes identify v10.11. Some English examples import futu and contain unrelated copied labels. No installed SDK/OpenD version or package compatibility was established. Mutable web pages have no captured publisher commit/content hash here; the dated paraphrases and links are the evidence, not a claim of archived original HTML.

| ID | DOC_VERIFIED | Limit / implication |
|---|---|---|
| F1 | OpenD historical Python output specifies a formatted time_key string and US Eastern-time convention; request options include interval, adjustment, session/extended hours and page cursor. Its documented default is daily bars with forward adjustment. [S1](https://openapi.moomoo.com/moomoo-api-doc/en/quote/request-history-kline.html) | Timezone is not interval-start/end authority. Require explicit effective parameters; no defaults inferred suitable for research. |
| F2 | The history interface passes the returned cursor to subsequent requests. Current restrictions describe eight years for intraday bars up to60minutes, twenty years for daily bars, account-linked quota and request-rate constraints. [S1](https://openapi.moomoo.com/moomoo-api-doc/en/quote/request-history-kline.html) | Advertised capacity is not actual SPY/QQQ coverage, entitlement, revision history or point-in-time knowledge. Do not hardcode limits from this mutable page. |
| F3 | The callback describes asynchronous subscribed candles with OHLCV/time fields. The reviewed public field table supplies no explicit closed/final/revision-publication field. [S2](https://openapi.moomoo.com/moomoo-api-doc/en/quote/update-kl.html) | This is an inspected-schema gap, not proof that no other protocol/version can expose evidence. A callback or elapsed interval alone cannot certify completion/finality. |
| F4 | The published KLine protobuf defines time, an optional timestamp and isBlank; empty points can contain only time. Session definitions distinguish RTH, ETH, ALL and an unknown NONE value. [S3](https://openapi.moomoo.com/moomoo-api-doc/en/quote/quote.html) | Timestamp field does not establish publication time or start/end labels. Blank is not valid zero OHLCV. Resolve effective session explicitly. |
| F5 | Provider trading-calendar docs say weekends/holidays are excluded but temporary closures are not. Results include a trading-day type. [S4](https://openapi.moomoo.com/moomoo-api-doc/en/quote/request-trading-days.html) | Calendar endpoint alone is insufficient for halts, unscheduled closures or an evidence-backed expected minute grid. |
| F6 | Provider Q&A distinguishes API/app permissions and warns quotes/opening values can differ because of feed composition. [S5](https://openapi.moomoo.com/moomoo-api-doc/en/qa/quote.html) | App screenshot agreement is not automatically independent consolidated-feed validation; actual account entitlement and coverage remain UNKNOWN. |
| F7 | Official NYSE/Nasdaq pages describe09:30–16:00 ET core sessions and scheduled early-close dates. [S6](https://www.nyse.com/trade/hours-calendars), [S7](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule) | These schedules do not prove this provider's aggregation/auction inclusion or every historical session/exception. Pin date-specific calendar versions before study. |
| F8 | A separate HTTP history API documents millisecond time_key, next_time and has_more pagination rather than the OpenD Python string/cursor contract. [S8](https://open.moomoo.com/api/quote/basic-data/history-kline) | Do not import its units, limits or timezone examples into OpenD. Its displayed US daylight-offset example is not used as timezone authority. HTTP is outside the proposed OpenD scope. |

S1's displayed Python signature and parameter table differ in whether session appears; this is a documentation consistency warning requiring package/version-specific confirmation, not a compatibility finding. No raw timestamp is shifted based on these pages. A09:31–16:00 grid can support a hypothesis but cannot select a mapping.

## Unresolved source contract and required evidence
All items below are UNKNOWN for actual SPY/QQQ:
1. Exact distribution/version/schema and SDK conversion behavior; OpenD build; endpoint; market symbol identity; effective RTH/adjustment/units; feed coverage, delay, entitlement and redistribution/storage permissions. No license or account permissions inferred from documentation promotions.
2. Whether raw minute labels represent interval start, end or another aggregation anchor, including opening/closing auctions and16:00. Require scoped written provider confirmation or independently aligned opening/closing OHLCV evidence with matched feed/adjustment/interval and contrary cases retained.
3. Empty/no-trade minute versus outage/partial page/halt semantics; pagination consistency if pages change during a request; cursor expiry/retry identity; whether a terminal cursor certifies a coherent snapshot (not assumed).
4. Completion guarantee/watermark, correction/revision identity, finality policy and late-correction horizon. Current FINAL-only synthetic contract cannot be populated honestly by inventing a FINAL flag from a historical response.
5. Exact first availability of every revision, receipt/completion metadata timing, clock-error bounds and durable custody. Same values seen later cannot be assumed unchanged since the event.
6. Adjustment-factor vintages and corporate-action treatment. Later adjusted history may encode information unavailable earlier; do not combine current adjusted intraday bars with unversioned daily context.
7. Numerical freshness/delivery-lag tolerances and acceptable missingness are policy choices, not provider facts.

A future evidence request should bind every claim to symbol/session, endpoint/build/package hashes, complete effective request, entitlement scope without secrets, raw page/row/revision identity, fidelity, receipt ordering/clock uncertainty, mapping/calendar authority and reviewed conversion policy. Source hashes detect identity changes; they do not authenticate truth. Preserve SDK_ROW_SNAPSHOT as such; never call reconstructed SDK objects wire bytes.

## Historical availability feasibility
Existing trustworthy point-in-time market evidence was not supplied or inspected; original databases remain untouched. This is an evidence gap, not a declaration that no such archive exists.

| Evidence situation | Permitted interpretation under this proposal |
|---|---|
| Final historical OHLCV downloaded after the session | Descriptive latest-vintage history only. Cannot establish earlier decision-time eligibility or first availability. No primary point-in-time study. |
| Vendor archive with independently documented revision/publication times and custody | Candidate historical input only after mapping, scope, completeness, time/finality and licensing review; not automatically accepted. |
| Previously captured immutable revisions with full local receipts and bounded clocks | Can support that capture system's knowledge model after audit; does not prove first market-wide publication. |
| Future prospective capture after separate authorization | Could establish an untouched future observation window under a frozen protocol; none initiated here. |
| Assumed delay attached to latest historical candles | Explicit hypothetical sensitivity design only, never evidence-backed historical availability. Not authorized/executed. |
| Unknown revision knowledge or completion/finality | Block primary evaluation. Keep missingness and reasons; do not backdate fetch time to interval end. |

For a captured system, propose a conservative usable bound equal to the maximum of interval end, full-revision receipt and required completion-evidence receipt, plus the proven clock-error bound. Also require metadata/authority itself to have been known by the cutoff. Monotonic ordering complements rather than replaces UTC clock evidence. Unknown bounds block. Exclude proven post-cutoff revisions before examining their payload quality; unknown visibility blocks instead of being guessed.

Completion and finality remain separate. Decision D1: keep FINAL-only and accept that real evaluation may remain unavailable, or separately approve a completed-provisional profile retaining every later revision. The latter changes a consumer contract and requires scoped implementation/tests; it is not adopted here. No arbitrary wait or next-candle arrival is promoted to authoritative completion.

## Proposed replay architecture — pure and bitemporal
This refines earlier designs without replacing their original hypotheses or implementing a replay.

1. Immutable evidence catalog: read-only inputs already authorized/captured elsewhere; content-addressed pages, native typed values, revisions and errors; source/request/clock/calendar/authority lineage. No existing write-capable research helper.
2. Source-contract registry: versioned effective scope and reviewed mapping/completion/finality/availability authority. Missing evidence returns RAW_AUDIT / blocked; no provider fallback.
3. Deterministic availability ledger: event intervals and revision knowledge are independent axes. Explicit lineage selects at most one eligible revision per symbol/interval/as-of cutoff. Visible conflicts block unless an approved supersession rule resolves them; no last-row-wins, timestamp sort or later label corrections rewriting features.
4. Calendar/expected-grid service: immutable date-specific sessions and pinned timezone bytes, independently supplied completion watermark and exception policy. No grid inferred from last returned bar, weekday-only calendar or universal390 count.
5. Pure frame builder: immutable prefix, quality report and exclusion ledger; per-symbol failures isolated. Full context/bundle/report identity travels with every frame. No host clock/timezone lookup. Unavailable future payloads cannot poison earlier frames.
6. Strategy profile executor: sealed frame materialized into isolated copies for one explicitly selected engine profile, no filesystem/provider/account access. Store observations/reasons and separate DATA_BLOCKED from valid NO_CANDIDATE. All candidates remain research observations, not orders.
7. Independent label builder: exact horizon intervals, frozen label-availability cutoff and revision vintage. A later outcome never changes eligibility, cooldown, features or selected opportunities. Missing labels retained in denominators.
8. Reporter/manifests: deterministic content hashes, exclusive new evidence outputs under a separately approved custody design; source/code/dependency/calendar/tzdata/policy/arm/split/exclusion/seed/access identities. Replay calculation is pure; output persistence is separately scoped.

At cutoff t, only revisions and required evidence with conservative knowledge<=t enter features; end<=t alone is insufficient. Resolve equal-time events by a frozen deterministic rule with conservative precision handling. Preserve every original observation. Cache keys include as-of/source/contract/calendar/policy/code; updated evidence invalidates derived cache without overwriting raw records. Repeated execution must produce identical semantic outputs; wall-clock report time belongs in separate provenance.

## Strategy and study decisions — not frozen
D2 must select the engine profile before any evaluation:
- Existing PR18 arms A/B/C/paired ablation target PR13's session-reset SMA-seeded EMA and22-bar common warmup, strict opening-range/pattern/proxy conjunctions.
- PR31 uses first-close-seeded EMA,35-bar warmup and a different conjunction without implementing those OR/pattern arms. PR34 preserves that pinned kernel.
These are different hypotheses. Never label a PR31 replay as validation of PR13/PR18. Reproducing the older arms or defining successor-specific arms requires an explicit protocol amendment and separately authorized code. HLC3 and dashboard OHLC4 proxies remain distinct; neither is trade-level VWAP.

Recommended preservation of PR18 design, conditional on D2:
- Chronological development,60 eligible pre-freeze retrospective rehearsal sessions,5 scheduled-session embargo, then120 scheduled future evaluation sessions. Actual dates, source/calendar feasibility and access policy must be frozen before outcome access; a provider calendar's future coverage must be reconciled with the full scheduled window. Do not extend for missing/low-signal dates.
- Common non-overlapping5-minute grid after profile-specific common warmup, same dates for SPY/QQQ. Keep secondary per-minute observations explicitly overlapping.
- Example descriptive target: next-minute open strictly after the decision, then close of the third minute beginning there; earliest possible proxy entry is t+1minute, target close t+4minutes. Exclude horizons past the session close, retain missing label counts. Frozen session-close+24h label vintage is a proposed PR18 rule, not established provider finality. No primary horizon entry at a decision's already observed close.
- Paired NO TRADE ablation keeps all mandatory data guards; log rejected opportunities and exact reasons. Selection-frequency changes are not predictive edge.
- Keep same-date SPY/QQQ in the same split and inference cluster. Report both symbols, shared opportunities and date-level paired comparisons; overlapping events and common macro moves are not independent samples.
- Separate intraday momentum, developing session return from evidenced open, and prior-day trend using60 prior completed sessions with revision-specific availability. No current-day final daily values. Missing daily context is DAILY_CONTEXT_UNAVAILABLE, not automatic loss of an otherwise eligible intraday event.
- Preserve ordered signal pairs: matching directions, CONFLICT, SINGLE_CANDIDATE, BOTH_NO_TRADE and PEER_DATA_UNAVAILABLE. Never force consensus or erase conflicting SPY/QQQ observations.
- Freeze endpoints, all arms and sparse-data handling; preserve all null/negative results. PR18's date-cluster/block uncertainty proposal remains a proposal. No parameter search or hypothetical performance reported.

### Costs and slippage
Primary OHLC movement labels are not fills or net returns. Report them as signed underlying-price movement only. A separately approved analytical sensitivity design could subtract an explicitly hypothetical round-trip friction budget in basis points (commission/fees, entry/exit spread, latency/adverse movement and impact) from a compatible gross movement measure. This is not execution simulation or a profitability estimate; numbers must be prespecified as assumptions or independently sourced, never invented as observed costs.
No bid/ask, depth, trade-size/impact, borrow/locate availability or actual fills were examined. Those omissions particularly prevent interpreting bearish labels as executable short returns. No OHLC-only resolution of intrabar stop/target order, zero-cost fills or assumed midpoint execution. Missing required friction inputs yields COST_MODEL_UNAVAILABLE; no fallback net P/L. Any such study requires separate execution authorization.

## Proposed validation/acceptance matrix — SPY AND QQQ, Windows AND Linux
All rows are future requirements, not tests added or run by this phase. Existing synthetic rehearsal evidence is limited to its pinned contracts.

| Area | Falsifiable case / acceptance evidence | Failure disposition |
|---|---|---|
| API identity | OpenD strings versus HTTP milliseconds, exact SDK/build/session/adjustment/unit scope; reject unsupported/mismatched versions | SOURCE_CONTRACT_UNKNOWN; no numeric engine call |
| Entitlement/feed | Permission denied, delayed/empty response, app/API feed mismatch, one symbol succeeds | Per-symbol source status; no peer substitution |
| Timestamp mapping | Both START/END hypotheses at09:30/09:31/16:00 and13:00; raw bytes unchanged; independent aligned OHLCV or provider authority | MAPPING_UNVERIFIED; never shift silently |
| Calendar/timezone | Regular/holiday/early close, unscheduled closure/halt, DST offset and ambiguous/nonexistent wall times, absent rule bytes | CALENDAR_OR_TIME_UNKNOWN; no fixed-offset/grid guess |
| Completion/finality | End passed but no completion evidence; completed provisional; late correction; missing finality policy | Block under current FINAL-only profile |
| Visibility | Revision arrives just after cutoff, before/at cutoff, fractional precision, nonzero/unknown clock bounds, future authority | Earlier feature identity invariant; conservative boundary or block |
| Revisions | Identical retry, visible conflicting versions, out-of-order supersession, unknown knowledge, changed adjustment factor | Preserve all references; explicit resolver policy or block |
| Pagination | Terminal evidence, repeated cursor, timeout/later-page error, page mutation, budget truncation, missing whole symbol | PARTIAL_SOURCE; no completeness from successful prefix |
| Minute quality | Interior/tail gap, blank point, duplicate, zero/negative/nonfinite/incoherent OHLCV, cross-session row | Reasons and exclusions; no fill/deduplicate silently |
| Calculations | Independent arithmetic for selected EMA seed/warmup, prior20 volume excluding current, correct named proxy/OR membership/pattern geometry | Reject profile drift; no fixture-based claim of edge |
| Leakage/labels | Mutate later minute/daily revisions/outcomes; separately frozen label vintage; unknown label availability | No earlier candidate/feature/cooldown change; missing labels counted |
| Study selection | Common grid/warmup, horizon at close, missing days, all valid9 SPY/QQQ pair states plus invalid peer, daily context absent | Stable denominators; no outcome-driven exclusions/consensus |
| Costs | Absent bid/ask/size/borrow, assumed spread/latency/cost changes, intrabar ambiguity | Descriptive movement only or COST_MODEL_UNAVAILABLE |
| Reproducibility | Deep immutability, same input/config hashes twice, reverse call order, pinned timezone/Decimal behavior, source/capture-vs-SDK fidelity | Bit/semantic identity per declared serializer or explicit block |
| Safety/custody | No network/SDK/order APIs in replay; only synthetic temp stores for future tests; original evidence immutable; crash/partial manifest | No output promotion; preserve incomplete evidence and reasons |

## Recommendations and approval gates
1. Review this document and decide D1 finality profile and D2 engine/study profile; freeze neither automatically. Source/version/session/adjustment, calendar exceptions, freshness/delivery/clock thresholds, revision identity and label-vintage policies remain separate decisions.
2. Prefer a separately scoped documentation-only source-evidence questionnaire/authority checklist before acquiring anything. Written provider clarification must itself be separately authorized if it involves sending a message; none sent.
3. Once explicitly approved, bounded synthetic-only replay contract tests/implementation could address availability-ledger, frame/label separation, selected-arm parity and missingness. Current authorization ends at this design; no test code or implementation supplied.
4. Only with separate explicit permissions, design/approve provider verification and prospective capture/custody. Do not retrieve history merely because retention is advertised. If original availability remains unavailable, keep primary historical study blocked and report descriptive/hypothetical alternatives distinctly.
5. Future study execution requires approved source evidence, frozen protocol/date/access manifest and explicit execution authorization. PR integration/retarget/merge, production wiring, real-record use, provider connection and deployment retain their own gates. No reviewer identity or external approval invented.

Validation for THIS change: documentation/source citations and exact repository revisions inspected; no new tests/study/provider checks performed. Any inherited documentation-PR baseline CI confirms only repository compatibility, not this design or actual provider behavior.
