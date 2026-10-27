# Ingestion completion/retention proposal — NO production behavior changes
Verified main: b0ad02dc996b00406e7da08fb33b6382f658ea40. PRs #1/#2/#4/#5/#6/#7/#8/#9/#10/#11 are merged. Main push CI 40496261547 passed Windows/Linux Python 3.11; local guarded baseline has 69 tests. PR #12 remains a separate pinned-overlay validation proposal.

## Completed characterization
The existing 15 fake-provider/clock tests cover completion guards, raw 16:00 filtering, missing minutes, duplicates, ignored pagination keys, partial symbol/day failures, invalid numeric data, weekend/early-close cases, context closure and public date validation. Three additional tests in this PR demonstrate:
- a synthetic 390-bar 09:31–16:00 RESPONSE becomes 389 bars per symbol in BOTH ordinary workers, without changing the fake source response;
- a completed past-day range is not cut off by the current day's clock;
- a directly invoked future-date range worker accepts that response, although the public UI already rejects today/future requests.

The first fixture is an end-stamp HYPOTHESIS, not evidence that Moomoo labels that way. The test establishes application filtering only. Existing behavior tests are characterization contracts, not endorsements.

Important distinction: the public range handler requires completed past dates. Therefore normal UI range requests cannot select today. Its duplicated worker lacks the same defensive request validation; this matters to direct/internal callers. Neither that asymmetry nor the 16:00 predicate establishes provider interval semantics.

## Proposed fixes — review separately before implementation
| Boundary | Proposed behavior | Required desired-behavior tests/evidence |
|---|---|---|
| Raw retention | Capture complete immutable provider responses and request/page metadata before derived filtering; keep raw 16:00 and all supplied stamps without reinterpretation | Exact raw bytes/values survive; source archives cannot overwrite earlier evidence; no writes to original research stores |
| Canonical intervals | Separate interval_start/end and available_at from raw_timestamp; require explicit documented mapping/evidence and session schedule | Both synthetic start/end mappings, no in-place shifts, unknown basis produces UNVERIFIED/NO TRADE, early-close/DST/calendar evidence separate |
| Completion | Use explicit verified interval boundaries/availability watermark; never equate fetching a row with knowing its completed historical value | Exact minute boundaries, real/caller-declared latency, partial updates, late corrections; unknown completion fails closed |
| Requests | Retain public past-date guard and add shared defensive worker validation without changing date policy | Today/future direct calls rejected, completed dates accepted, timezone/date errors explicit, context closure preserved |
| Pagination | Follow each key to exhaustion with bounded pages/repeated-key/error detection; preserve partial pages and record incomplete status | Multi-page success, repeated keys, later-page failure, duplicate keys/rows, interleaved symbols, no false complete flag |
| Coverage | Report symbol/session expected schedule, missing/duplicate/invalid observations and empty/error/partial distinction | SPY/QQQ missing independently, entire absent symbol-days, invalid OHLCV, partial sessions, no synthetic gap fill |
| Persistence/UI | Dry-run/adapt in a new read-only service boundary first; keep existing functionality while separately reviewing provenance/storage changes | No source-store initializer/migration/upsert in inspection; explicit staged/durable outputs only after approval |
| Direction engine | Feed only reviewed canonical complete/available inputs with evidence to #13; keep unverified raw history out of candidates | Missing mapping/evidence remains NO TRADE, wrong/mixed sessions rejected, source timestamps preserved |

These are proposals, not authorization for a production repair, new persistent store, schema migration, automatic backfill or replacement archive. Do not change a 16:00 filter to claim verified ranges without independent provider evidence. Preserving raw responses and deriving a session view are separate operations.

## Availability and historical validation
Historical bar values often lack captured publication/revision timing. Do not manufacture available_at from fetch time or silently equate it to bar end. A synthetic or explicitly idealized historical latency assumption must remain labeled, and cannot be treated as captured market availability. Real next-open/backtest claims require a reviewed capture/availability model; #14 currently provides only synthetic chronological event-study scaffolding.

Before review, collect official endpoint/SDK/OpenD version, entitlement/subscription state, explicit interval/session/adjustment flags, pagination completeness, timestamps and opening/closing OHLCV, plus independent chart/interval comparison or vendor confirmation. No empirical provider call was made in this sprint.

## Verification and approvals
Local Windows/Python 3.12.14: all 72 guarded tests (69 baseline + 3 characterization additions) pass. Windows/Linux Python 3.11 CI uses the same offline suite. Source changes are tests and documentation only; no ingestion, calculation, research DB or trading behavior changes. Approve a narrowly scoped request-validation/retention/completion contract first, then add desired-behavior failing tests before implementing each repair in its own PR.
