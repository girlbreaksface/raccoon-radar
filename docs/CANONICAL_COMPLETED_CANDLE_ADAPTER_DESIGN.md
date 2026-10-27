# Canonical completed-candle adapter — DESIGN ONLY, draft v1
Baseline: main b0ad02dc996b00406e7da08fb33b6382f658ea40. Consumers under review: direction engine #13 and replay #14. This proposal contains no adapter implementation, provider client, ingestion change, database access, migration or GUI wiring.

## Purpose and boundary
Proposed pure interface: adapt_read_only_bundle(raw_bundle, approved_mapping_registry, pinned_session_calendar, decision_cutoff_utc, policy) -> immutable eligibility report + sealed canonical frame.

Inputs are already captured immutable objects/bytes. The adapter does not fetch Moomoo data, read source databases, initialize schemas, update history or write archives. Capture, any future explicit mode=ro repository, and exclusive export/storage are separate services requiring their own review. Never call existing read-named helpers that initialize/migrate stores.

Two modes:
- RAW_AUDIT: preserve/reference every observation and report unknown/invalid/partial states; engine rows are empty and decision_eligible is false.
- ENGINE_READY: a unique complete and available per-symbol/session frame meeting ALL approved contracts. No permissive default or inferred VERIFIED status.

The adapter cannot infer provider semantics from 390 bars, a first 09:31 stamp or a supplied boolean. No live connection is authorized by this design.

## Immutable source envelope and fidelity
Retain original symbol/code, raw timestamp value and representation, original OHLCV values/types, request ID/page ID/row ID, endpoint/interval/session/adjustment flags, SDK/OpenD versions, entitlement/subscription state, request bounds, response/error/pagination metadata and captured receipt timestamps. Never replace, shift, relabel or normalize source values in place.

Keep immutable source bytes where captured, their hash and a fidelity label. If the SDK supplied only a DataFrame/object, label the frozen serialization SDK_ROW_SNAPSHOT, not original wire bytes. Numeric/datetime conversions already performed by the SDK must not be falsely claimed reversible. All canonical conversions link to the exact source observation/revision and conversion policy.

Source evidence ID/hash is not authentication by itself. Registry approval identity, review date, version/effective scope and supporting source artifacts must be independently inspectable. No account credential or order access is involved.

## Mapping evidence and time representation
Each approved binding is scoped to provider endpoint, SDK/OpenD version range, market/symbol class, interval, timezone, session/adjustment settings and response contract. It names the raw stamp meaning (start/end/other), offset/precision treatment, evidence artifacts and reviewer approval. Vendor confirmation or independently aligned opening/closing OHLCV evidence is required; coverage shape alone remains corroboration.

Authoritative canonical times are timezone-aware UTC instants with preserved precision. Pin America/New_York IANA/tzdata version for exchange-local views. Reject unknown timezone, ambiguous fold, nonexistent local time, unsupported precision or an unapproved binding. Do not infer from the host timezone, current date or a guessed fixed UTC offset.

For an independently approved one-minute binding, derive interval_start/end separately with start < end and exactly 60 seconds; do not overwrite raw_timestamp. A raw 16:00 stamp could refer to [15:59,16:00) or [16:00,16:01), depending on a verified binding. Neither is selected when semantics are unknown. Keep even out-of-session raw observations; explicit derived exclusions with reasons are not source deletion.

### Compatibility with engine v1
The proposed engine currently takes naive ET strings at whole-second resolution. Treat that as a limited VIEW, not the authoritative clock:
- start/end must already be exact minute boundaries under the approved binding; no rounding a raw stamp to make it fit;
- round a proven knowledge/availability instant UP when converting to a whole-second available_at_et view, never truncate it earlier;
- round a requested evaluation cutoff DOWN to supported precision, never forward;
- preserve full UTC instants, original precision and conversion policy in the manifest;
- ambiguous local-time serialization is unsupported and blocks forwarding.

These conservative conversions still require reviewer approval and tests. A future aware-UTC engine interface may be preferable; do not silently change #13's API.

## Completion versus revision finality
Interval end <= decision cutoff is necessary but not sufficient. complete=True requires a documented provider watermark/closed-bar guarantee or a captured event with independently approved semantics, for that exact revision. No invented SDK flag, arbitrary sleep/buffer or successful request substitutes for evidence.

A completed minute can later be corrected; completion does not mean immutable final market truth. Every revision remains a distinct observation with value/source hash, source sequence if trustworthy and first-observed/captured knowledge time. Never backfill corrected prices into an earlier decision frame.

## Availability — knowledge of THESE values
known_at/available_at refers to when these exact OHLCV values and required completion metadata could be used under the declared evidence model. For captured observations, it cannot precede receipt of the full revision or its interval end; uncertainty/clock bounds must be recorded and resolved conservatively. A raw market timestamp, interval end and retrieval timestamp are separate fields.

Historical bars downloaded today do not acquire historical availability merely because their timestamps are old. Do not set availability to bar end, overwrite it with a convenience field, or backdate final revised values to a first-publication time. A trusted point-in-time revision feed may supply historical knowledge evidence, but that contract needs explicit review.

Unknown historical availability -> AVAILABILITY_UNKNOWN / decision_eligible=false. Assumed latency on REAL data is a separate research-assumption class, not VERIFIED and not SYNTHETIC. Do not misuse #13's SYNTHETIC status to pass real history. Any engine support for historical assumed availability needs a new reviewed interface; this adapter v1 does not smuggle it through.

Filter the information set by proven known_at <= decision cutoff BEFORE inspecting unavailable payloads for frame quality, interval lookup or labels. Later revisions must not invalidate an earlier frame. The full raw-bundle hash may change; the same as-of canonical frame must remain unchanged. An observation with UNKNOWN known_at cannot safely be placed before or after a cutoff and blocks the affected frame instead of being silently ignored.

## Session calendar and completion watermark
Pin exchange/market session-calendar ID, version, source hash and timezone database. The [NYSE official hours/calendar](https://www.nyse.com/markets/hours-calendars) distinguishes core sessions, holidays and early closes; it is a source to review/bind, not a built-in calendar implementation in this proposal. The listing/quote venue and feed session scope must match the chosen schedule.

No weekday-only fallback, automatic nearest-day substitution or assumed universal 390-bar session. Explicit session bounds, expected one-minute intervals, declared target completion watermark, early-close/halt policy and source pagination state determine expected coverage. Do not call a snapshot complete solely because all minutes through its latest observed bar are present; report missing expected tail minutes too.

Missing entire symbol-days, absent/zero-volume minutes, partial current intervals and a stale tail are different states. Do not fabricate zero-volume candles or bridge gaps. Document any future halt/no-trade-minute exception through a separate approved rule.

## Pagination, units and source completeness
Collect immutable request/page references, repeated-key detection, page-limit/error state and exhaustion evidence upstream. An empty page, missing symbol response or later-page error is not complete coverage. The pure adapter validates that manifest; it does not issue retries.

Require consistent currency, price/volume units, aggregation period, adjustment regime and session scope. Do not mix cumulative volume with per-bar shares, split-adjusted with unadjusted prices, or different providers' revisions without explicit lineage/policy. Validate finite positive OHLC, coherent high/low/open/close, finite nonnegative per-interval volume and consistent interval identity.

## Duplicates and revisions
Default v1 is conservative: no implicit last-row-wins, no timestamp-only deduplication, no forward/back filling. Repeated/ambiguous revisions block the affected frame unless a separately approved identity/version policy proves which unique observation was known then. Byte-identical retry observations can only be coalesced under an explicit policy retaining ALL raw references.

#13/#14 currently accept one canonical row per interval and fail closed on visible duplicates. They are not a general revision engine. A future bitemporal policy needs immutable as-of frames selecting ONLY revisions eligible at that cutoff, trustworthy sequence/tie rules, and a replay API that consumes those frames. Do not flatten all latest-final revisions into one historical array or feed an entire revision stream to the current replay and claim correctness.

## Output envelope and fail-closed rules
A proposed envelope includes contract/adapter policy version, source bundle hash/fidelity, mapping/evidence registry IDs, calendar/tzdata IDs, requested cutoff/target watermark, canonical frame hash, row lineage/revision IDs, explicit exclusions, missing/duplicate/invalid counts, per-symbol/session status and decision_eligible.

Only a sealed ENGINE_READY frame may produce #13 arguments. Otherwise return adapter reasons and NO TRADE eligibility; do not manufacture a successful empty/verified frame. Example reasons include UNVERIFIED_INTERVAL_MAPPING, SOURCE_EVIDENCE_INCOMPLETE, CLOCK_UNTRUSTED, AVAILABILITY_UNKNOWN, CALENDAR_UNVERIFIED, PARTIAL_SOURCE, INCOMPLETE_INTERVAL, GAP, CONFLICTING_REVISION, INVALID_OHLCV, OUTSIDE_SESSION and STALE_DATA. Findings, hypothesis, caller assertion and independent verification remain distinct. No confidence score.

Use deep immutable data (bytes/tuples/frozen records and read-only nested mappings), not just a frozen outer object containing mutable dictionaries. Engine compatibility materialization must be an isolated copy. Pin and hash schema, full context/config, evidence/calendar and adapter code revision along with normalized inputs; a feature-data hash alone is not a unique run identity.

## Required implementation acceptance matrix
| Synthetic condition | Required disposition |
|---|---|
| Raw 09:30/09:31/16:00 with no approved mapping | Raw retained, no guessed shift; NO TRADE |
| Approved synthetic start/end bindings | Correct separate interval derivation; raw bytes/values unchanged |
| Full-minute endpoint but unproven completion | INCOMPLETE/UNVERIFIED, not complete=True |
| Exact end versus fractional-second receipt | No early visibility; conservative supported-precision conversion |
| Historical final values with unknown first availability | AVAILABILITY_UNKNOWN, no backdated labels |
| Revision arrives after decision/train/test cutoff | Earlier frames/outcomes unchanged; later frames retain new lineage |
| Conflicting versions before cutoff / uncertain order | Fail closed; no last-row-wins |
| Holiday/early close/DST/clock uncertainty | Pinned valid schedule or explicit blocked status |
| Missing interior/tail/whole symbol-day | Explicit coverage issues, no fabricated minutes |
| Empty symbol/page, repeated page key, later-page failure | PARTIAL_SOURCE even if some prices exist |
| Invalid/nonfinite values, wrong units or adjustment mix | Invalid frame with source-linked reasons |
| Result/input mutation and repeated runs | Source/snapshots sealed; deterministic same-context frame/hash |
| Missing evidence/hash/registry approval | No automatic VERIFIED |
| Existing research stores absent/legacy | No connection, creation, initializer or migration |

Before implementation, reviewers must approve the evidence authority, time/precision/knowledge model, calendar source, revision policy, frame/replay compatibility and fail-closed states. Then write synthetic tests before a separately proposed pure offline implementation. Real-data fixtures and empirical provider work require their own read-only authorization/evidence plan.

## Verification of THIS proposal
Design and a deliberately blocked synthetic JSON example only. No executable adapter, Moomoo connection, DB access or ingestion modification. Main's cumulative 69 guarded tests and source compilation are the runtime baseline; Windows/Linux CI checks the design branch. CI cannot validate unimplemented contract behavior. No merge or rollout approval is implied.
