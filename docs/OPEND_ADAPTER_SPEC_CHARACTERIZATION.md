# Canonical OpenD adapter specification and synthetic characterization
Status: PROPOSAL / NO PRODUCTION ADAPTER. 2026-10-29.
Scope approved in PR19comment6498737430 and directly in coding chat: specification
and synthetic characterization ONLY. No contract freeze, live capture, provider access,
real history, credentials, trading, deployment or merge approval.

## Reviewed identity and boundary

Main b0ad02dc996b00406e7da08fb33b6382f658ea40.
Prior design PR17head9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3,
designblob876b29be4aecb6fba95e3fa2fa395aab8a35a4fb.
PR18headeb683559a0ab685503627612ab22aa16a77066ed,
interface/study designblobe4f381a8fa8d8ed968e01bd501b7a95b763df38a; no study executed.
Consumers inspected as exact TEXT fixtures, not merged:
PR29head65cf3edb91c68c4247a92c71591825608862ab8d,
PR30head56b4a2f66afbd22196c12be01d0277aefc08e710,
PR31head24a5c5de529f99992ec331f6ea91c39c1f61fa6e.

Only tests/adapter contains executable scenario machinery. contract_oracle.py is a
TEST-ONLY disposition oracle, not a complete/raw-input-safe/approved adapter. It performs
limited synthetic derivations to make proposed assertions executable; importing it in
production is unsupported. It does not implement real evidence approval, capture, SDK
conversion, retries, storage or crash recovery. Production entrypoints remain unchanged.
Synthetic authority strings/booleans are fictional assertions, never OpenD verification.

## Proposed separate interfaces (not implemented)

1. ReadOnlyCapturePort.capture(request: HistoryRequest) -> FrozenCaptureBundle.
   Future SDK boundary only, separately authorized. No trading/account API dependency.
   Request: exact symbols, endpoint, interval, session/adjustment flags, date bounds,
   page/row/time budgets and immutable capture-policy ID; no permissive provider defaults.
2. canonicalize(bundle, approved_source_registry, approved_mapping_registry,
   pinned_calendar, AsOfRequest, policy) -> CanonicalizationReport.
   Pure/no I/O/no ambient clock. This stage provides NO supported implementation.
3. materialize_pr31(sealed_frame, approved_consumer_profile) -> isolated rows/contract/
   policy copies, or blocked reasons. NO direct provider/legacy CSV bypass.
4. Future evidence recorder and recovery service are distinct from capture/canonicalize.
   Read-only adapter must not initialize/migrate stores or call existing write-capable
   research helpers. Existing databases/CSV/raw records are out of scope.

Proposed records are recursively immutable bytes/tuples/frozen typed records; a frozen
outer object containing mutable dicts is insufficient. Engine views are separate copies.
Canonical candle interval is half-open[start,end), awareUTC, exact60seconds in this version.
Fields: original raw timestamp/value/type/representation, symbol and OHLCV snapshot;
request/page/row/revision IDs; canonical values/times with conversion-policy lineage;
source/mapping/calendar/tzdata/code/policy IDs/hashes; completion evidence, finality,
revision-specific system knowledge bound; explicit exclusions/quality states.
No raw value or timestamp is rewritten in place.

## Source identity, authority and custody

Source manifest binds endpoint/schema, SDK and OpenD versions, source artifact/hash,
entitlement/subscription state WITHOUT credentials, symbol market/class, timezone,
interval/precision, session flags, adjustment and units. Mapping registry must match that
entire effective scope/version/date range. A same filename, SHA alone, successful request,
390-bar sequence or absence of09:30 is not authority. Need provider confirmation or
independently aligned opening/closing OHLCV evidence, contrary evidence, review identity,
dated approval and immutable supporting artifacts. Real authority remains UNVERIFIED.

Distinguish original WIRE_BYTES (only if actually captured) from SDK_ROW_SNAPSHOT.
A DataFrame may already transform numeric/time types; do not claim original wire fidelity
or reversibility beyond what was captured. Preserve all raw pages/revisions/error records,
hash exact capture serialization and separately version derived canonicalizations.
Hashes detect identity/integrity changes, not truth, authorship or permission.

## Time, availability and per-symbol freshness

Keep distinct:
- raw_timestamp: original source representation, semantics unknown until scoped approval.
- interval_start/end_utc: derived only from an approved mapping.
- full_revision_received_at: local receipt of THESE values, not market publication.
- completion_metadata_received_at: receipt of required completion evidence.
- first_seen_revision_at: immutable original local capture, not reset on retries.
- optional provider_published_at: source claim requiring its own authority.
- historical_available_at: proven point-in-time knowledge under the declared study model.
- decision_cutoff_utc and target_completed_through: supplied, not ambient now/latest row.

For prospective captured system knowledge, conservative bound is
max(interval_end,full_revision_receipt,completion_metadata_receipt)+proven clock-error bound.
This is an upper bound for that capture system, not proof of first market publication.
Wall-clock provenance/uncertainty and monotonic receive order must be captured; unknown
clock bounds block. Never assume zero uncertainty or an arbitrary latency buffer.

Historical download today does NOT establish what was available yesterday. A trusted
point-in-time revision archive or separately approved prospective capture can establish
its own knowledge model. Missing original availability stays AVAILABILITY_UNKNOWN.
No fetch-time-to-bar-end backdating, no real-data SYNTHETIC relabeling.

Proposed freshness dimensions, separately reviewed and per symbol:
A.event_age=cutoff-latest canonical interval_end;
B.knowledge_age=cutoff-latest proven revision knowledge bound;
C.delivery_lag=knowledge_bound-interval_end for required revisions.
No numerical production defaults. Recent receipt must not refresh an old interval; an
old unchanged capture must not become current because its filemtime changed.
The test120s/30s examples are fictional scenario parameters only.
PR31 currently gates age by interval end only: a future adapter must enforce approved
B/C externally and preserve those checks/evidence rather than silently translate them
into its max_age_seconds. Which bars require lag limits is an unresolved owner/reviewer
decision; the oracle's all-required-bars rule is a conservative TEST profile, not policy.

Filter proven knowledge<=cutoff BEFORE examining unavailable payload values, gaps or labels.
Late invalid revisions can change bundle hash, not the earlier sealed frame/hash.
Unknown knowledge cannot be ordered and blocks. Conflicting/duplicate visible revisions
block by default; no implicit last-row-wins. Coalescing byte-identical retries requires a
reviewed identity rule retaining every raw reference. Do not flatten latest final history
into earlier frames or feed an entire revision stream to PR31/replay.

Legacy naive-ET whole-second compatibility, if approved: availability rounds UP, cutoff
rounds DOWN; canonical interval boundaries must already be exact minutes. Preserve full
UTC/subsecond instants and conversion metadata; block ambiguous local serialization.

## Calendar, timestamp mapping, completion and finality

Pin calendar/source/version/hash, exchange/session scope, tzdata version and explicit
open/close UTC for EACH date. No weekday-only nearest-Friday fallback or universal390 grid.
Expected intervals extend to an independently supplied completion watermark; never choose
watermark from latest returned bar. Missing interior/tail/whole-symbol minutes are distinct.
Holidays/halts/no-trade minutes/early closes need explicit reviewed rules; fabricate nothing.

A16:00 raw stamp could map to[15:59,16:00) under end labels, or[16:00,16:01) under start
labels. Only scoped authority chooses; retain raw observations either way and record
derived OUTSIDE_SESSION exclusions rather than deleting evidence. Same principle for
synthetic13:00 early-close examples. No actual Moomoo/NYSE calendar semantics are verified.

IANA timezone conversion is separate from exchange-calendar approval. Tests load bundled
tzdata2026.5 explicitly (not host fallback), characterize spring/fall offsets and reject
ambiguous/nonexistent naive New York wall times. That verifies library behavior only.
Unknown raw timezone/fold/precision blocks; never silently attach host timezone.

Interval end<=cutoff is necessary, not completion proof. Require documented source
watermark/closed-bar evidence for exact revision. completed and finality are separate:
a completed bar may be PROVISIONAL/revised. PR31's current FINAL-only profile rejects
PROVISIONAL/UNKNOWN; retain those states, do not promote them to FINAL. Whether a future
consumer may use completed provisional revisions needs separate explicit policy approval.

## Pagination, partial errors and crash-state proposal

Capture immutable per-page request/cursor/hash, returned cursor, status/error, row count,
receive-time bounds and exhaustion evidence, with bounded pages/rows/duration.
Repeated cursors, later-page failures, empty/missing symbol responses, inconsistent units/
adjustment, truncated budgets or missing terminal evidence yield PARTIAL_SOURCE.
Successful earlier pages do not certify the full symbol; SPY success cannot certify QQQ.
No provider retry/rate-limit/status-schema behavior is verified in this stage.
PR29 and PR31 injected helper result names differ (pagination_complete vs complete);
translation must be explicit and tested, not dictionary-field guessing.

Proposed custody lifecycle:
CAPTURE_STARTED -> IMMUTABLE_PAGES_STAGED -> HASH_MANIFEST_COMMITTED -> SEALED_ASOF_FRAME.
A crash before committed complete manifest publishes NO frame; partial files remain
preserved/quarantined with reasons, never deleted automatically. Later explicit recovery
must validate owner/source/schema/sequence/hashes and sole-writer evidence, then create a
NEW completion/recovery record. Preserve original and append corrections.
Crash after manifest but before publication must recover same sealed identity or block;
do not duplicate/rewrite original observations. Durable ordering/fsync/directory atomicity,
exclusive lock/ACL/path races, disk-full behavior and physical power loss need future
implementation tests. This stage SIMULATES manifest states; it does not execute actual
process-crash/filesystem recovery or promise durability.

## Pinned compatibility and characterization limits

PR29 scanner_reliability.py blob174ded7902384ef30665d8759498e60e6b5c97f6,
SHA256bfedd03ac70a5291329a82fa98d9de52bfd8d23d62c0e74f395534c6fc359e7d.
Legacy v3 CSV stays UNVERIFIED; recent availability does not override stale event time.
MIXED is not silently mapped to NO TRADE or an eligible direction.

PR30 v3 fixture blobd906fcdce2a8e356244e6cecd49c90f01aab76bf,
SHA25628bcd08df43b93f4f19818975d470cdc592c72a49d29fb71027d74e04d69eb0d.
Only analyze AST executes with fake DataFrame/provider. It still ignores pagination and
retains stale BULLISH bias. This stage neither repairs nor endorses it.

PR31 successor blobaa6b7c0f364acfcce2c294d9fd2dbbf10f049865,
SHA2565e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29.
Pinned stdlib definitions execute, no storage functions called. A unique explicit SYNTHETIC
as-of frame can satisfy it; absent authority remains blocked. No direct compatibility
claim with PR13's differently seeded EMA/replay APIs or full revision-stream support.
No production or protected PR changed/merged.

30 local synthetic characterization methods PASS, plus69unchanged guarded baseline,
compilePASS (WindowsPython3.12.14). Dedicated suite uses numpy2.3.5,pandas3.0.1,tzdata2026.5.
All fixture hashes verified before execution; .gitattributes preserves bytes across OSs.
Provider SDK imports/network/subprocess/SQLite operations blocked by test-process audit
hooks after test dependencies load; guard behavior tested. No actual DB opened.
This is not an adversarial-code sandbox. These are executable PROPOSED dispositions and
selected pinned compatibility cases, not a full consumer-suite run, empirical OpenD
verification, approved calendar or implementation acceptance. CI final identities/results
are returned on PR19 after verification. No historical study or strategy evaluation run.

## Decisions and proposed separately authorized next stage

Remain blocked: actual SDK/OpenD contract/version scope; raw timestamp authority; calendar
source/session/early-close/halt rules; receipt/clock custody and original availability;
completion/finality guarantees; per-symbol freshness dimensions/thresholds; duplicate and
revision identity; durable capture/recovery; approved consumer profile and independent review.

Recommended next ONLY after contract review: separately scoped pure offline canonicalizer
implementation using immutable synthetic bundles and expanded adversarial fixtures.
No SDK/client/capture integration, real source acquisition or empirical timestamp check
follows automatically. Any later provider experiment needs a separate read-only evidence/
permission plan. Real records, feeds, production databases/ingestion, GUI, paid services,
broker/paper/live execution, merge and deployment remain unauthorized.
