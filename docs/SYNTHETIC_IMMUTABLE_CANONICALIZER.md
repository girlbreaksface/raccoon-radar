# Synthetic immutable canonicalizer — offline draft

Approved directly in coding chat (“approve go”) for the bounded next stage recommended
by PR32 review5699292740. Contract reference PR32 e71f8de950ead63b505b179ab2ee124b369f2741;
design artifacts remain separate/unmerged. Mainbase b0ad02dc996b00406e7da08fb33b6382f658ea40.
This adds a pure SYNTHETIC-ONLY module, not OpenD capture, SDK integration, persistence,
dashboard wiring, real-record support, study execution or trading.

## Public API and immutable records

canonicalize(bundle:Bundle, context:Context, request:Request) -> Report
to_pr31_arguments(eligible_report:Report) -> isolated synthetic argument dictionary
identity(frozen_value) -> versioned typed-content SHA256
subjects(context) -> expected synthetic authority subject hashes

Constructors require recursively immutable FrozenRecord instances, tuples, bytes and
scalar values; lists/dictionaries/mutable nested values are rejected. All dataclasses
use frozen=True/slots=True. Output reports, frames, candles and complete context/request
are recursively immutable under normal Python APIs. This is not protection against
hostile Python object.__setattr__, code replacement or forged caller records.

| Record | Important fields |
|---|---|
| Source | Immutable(scope key,value) tuple; fidelity; source artifact hash |
| Mapping | START/END label; exact source scope hash; explicit ISO format profile |
| Calendar | Session date/open/close UTC; exchange timezone/version/known-at; complete approved interval grid; closed/explicit synthetic halt policy |
| Clock | Source name, proven uncertainty seconds, receipt-provenance hash |
| Policy | Explicit event age, knowledge age, delivery lag, FINAL_ONLY profile, SYNTHETIC_CAPTURE or separately bound SYNTHETIC_PIT |
| TimeRules | Name/version and immutable TZif bytes, or explicit fixed UTC with empty bytes |
| Authority | Role/reference/evidence hash; exact subject and source-scope hashes; synthetic marker |
| Observation | Original symbol/raw stamp/native OHLCV tuple; source snapshot bytes; observation/revision/page/row IDs; availability basis/reference; full/completion receipts; complete/finality states |
| Page | Request/cursor/terminal/status evidence and exact observation-ID references |
| Bundle | Immutable observations/pages, bundle ID, synthetic/committed claims, full contents hash |
| Request | Exact SPY/QQQ, session date, aware cutoff, independent target watermark, RAW_AUDIT or ENGINE_READY |
| Report/Frame/Candle | Explicit eligibility/status/reasons/exclusions, immutable lineage/values/times, input/context/request/run/frame hashes |

Input-domain misuse (wrong record type/mutable data/resource budget) raises explicitly.
Domain/evidence failures return a blocked report, no frame. RAW_AUDIT never materializes
engine inputs; an otherwise valid audit can have no failure reasons because its status
itself explains the requested non-forwarding mode. No default clock/source/calendar/
mapping/finality/freshness approval is fabricated.

## Scope and evidence bindings

Source requires provider,endpoint,sdk,opend,market,interval,timezone,tzdata,session,
adjustment,price_unit,volume_unit,entitlement fields. Current supported profile is
SYNTHETIC_* provider, PT1M, USD/SHARES, SDK_ROW_SNAPSHOT or SYNTHETIC_BYTES fidelity.
Real provider/bundle labels fail closed; the module cannot detect a dishonest caller
mislabeling real data. Synthetic markers are authorization assertions, not authentication.

Roles source/mapping/calendar/time_rules/clock/policy/completion/finality/availability
must bind exact content subjects and the declared source scope. Changing clock/policy/
calendar/mapping/availability model requires new matching synthetic subject bindings.
Evidence hashes and authority strings provide integrity/linkage, NOT independent review,
cryptographic source authentication, SDK truth or actual historical availability.
implementation_hash is caller-supplied by the host; this pure function does not read its
own source file. The host must bind the actual tested code externally; fixture IDs are
explicitly fictional. No I/O is used to self-attest code or source identity.

Native captured field values and snapshot bytes are jointly hashed and retained by
reference. No SDK serializer/parser is implemented here: correspondence between snapshot
bytes and supplied native fields remains a trusted capture precondition, not proved by
the hash. No original wire-byte fidelity is claimed for SDK_ROW_SNAPSHOT.
No host/filesystem/provider/calendar lookup, ambient clock, schema initialization,
mutable cache or database connection occurs in canonicalize.

## Time, availability, calendar and as-of ordering

All decision instants are aware UTC. Supported strict ISO syntax is extended date/time
with seconds, optional1–6fractional digits and Z/±HH:MM offset; raw wall stamps may be
naive only with explicit scoped in-memory timezone rules. Unsupported/submicrosecond
precision BLOCKS instead of datetime silently truncating into earlier visibility.
Raw source timestamp strings are never shifted or overwritten; interval views separate.

TZif bytes/name/version are part of authority identity. ZoneInfo.from_file reads BytesIO
only, never the host timezone database. Missing/wrong/ambiguous/nonexistent timezone
rules block. Explicit offsets must agree with scoped timezone. Tests use pinned
America/New_York data from tzdata2026.5:
decoded1744bytes SHA256d7f2206b3a45989fc9ad63d558922532fa7352280d5f87176bf1db79cb1d1fa9.
Fixture origin: tzdata2026.5/zoneinfo/America/New_York (IANA timezone data); this is timezone
library evidence, NOT NYSE holiday/halt/provider verification. No installed tzdata needed.

Calendar must be known by cutoff, match session/version and provide a full explicit
minute grid from approved open through close. Current implemented halt profile is
SYNTHETIC_CONTINUOUS only; real halt/no-trade exceptions remain unsupported/unverified.
Target watermark is an explicit caller request, must be a grid boundary<=cutoff, and is
NOT selected from returned tail. Coverage claims are limited to that requested prefix,
not “whole session complete”. Closed calendar blocks without weekday fallback.
START/END mappings derive separate intervals;16:00/early-close examples exercise both,
never infer a real Moomoo convention or universal390bars.

SYNTHETIC_CAPTURE availability must be >=max(full-revision receipt,completion receipt)
plus approved clock uncertainty, and >=canonical end. Clock uncertainty is CEILED to
supported microseconds using the exact supplied native-number ratio, never rounded down;
a positive100ns bound therefore requires at least1microsecond. Conservative rounding can
add a microsecond for binary floats; input bound representation/hash is preserved.

SYNTHETIC_PIT requires a separately bound policy/availability subject. Its declared
point-in-time upper bound is not replaced by today's archive receipt. Unknown/fetch-only
availability cannot be safely ordered and blocks. This does NOT verify any real archive.
Per-row evidence reference must match the approved synthetic availability role.

Global immutable schema/capture hash/page/lineage integrity is validated first.
Then proven post-cutoff revisions are excluded BEFORE raw timestamp, OHLCV, completion or
finality quality evaluation. A valid future revision can change bundle/run hash without
changing the earlier frame hash. Invalid source/lineage/unknown knowledge can still block:
untrusted timing metadata cannot be used as an exclusion escape.
Visible duplicate/conflicting intervals block; no timestamp-only dedup/last-row-wins.
Missing expected interior/tail/whole-symbol intervals, stale event/knowledge, excessive
delivery lag, invalid OHLCV, source mismatch, unfinished or non-FINAL bars all block.
No indicators, profitability, predictive edge or trade instructions are calculated here.

## Pagination, custody and hashes

Page chains require explicit first/next cursor agreement, request identity, statusOK,
terminal final page and exact unique observation references. Repeated cursors, missing
terminal evidence, wrong types, row-reference mismatches and reused page/row identities
block. SPY/QQQ use independent pages/eligibility; counterpart success never certifies
a failure. Global capture-hash integrity is a prerequisite for trusting either symbol.
Budgets:10000observations,1000pages,10000calendar intervals; per-zone TZif<=1MiB.
These are schema/resource bounds, not a complete adversarial memory-sandbox guarantee.

identity uses typed framing including exact float64 bits, bytes and record types; strict
JSON encoding contains no NaN/Infinity literal. Bundle hash includes full raw capture;
run hash includes request/context/code declaration. Frame hash includes only visible
canonical candles/lineage plus full context/request, not later excluded payloads.
Ordering preserves raw-capture identity while canonical rows sort by UTC interval.
No filesystem capture/commit/recovery process is implemented: committed=True is a trusted
synthetic input assertion, not durability proof. No files are written by this module.

## PR31 bridge and compatibility limits

Only sealed eligible reports may materialize. The bridge rechecks frame/context/request
hashes and returns NEW dictionaries/lists; mutating them does not change frozen evidence.
It copies original raw stamps and approved canonical interval/availability views;
synthetic=True is explicit, action/strategy decisions remain the consumer's responsibility.
A short valid frame may be data-eligible but still fail PR31's reference warmup; canonical
eligibility is not directional-signal eligibility or permission to trade.

**Current bridge supports synthetic UTC calendar only.** PR31 otherwise reloads host
ZoneInfo rather than using this frame's pinned in-memory rules, so New York forwarding
raises instead of silently claiming equivalent timezone authority. New York canonical
frames themselves are supported/tested. A future aware-UTC consumer or reviewed timezone
contract requires separate work; do not silently rewrite session dates/timezones.
No legacy CSV dictionary can bypass typed Bundle input. PR29 remains an unverified gate;
PR30 remains historical defect characterization; no blind merge or old scanner change.

Exact PR31 fixture head24a5c5de529f99992ec331f6ea91c39c1f61fa6e,
SHA2565e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29.
Definitions only execute with synthetic UTC materialization; storage methods not called.
No provider SDK/legacy scanner/watch loop or PR13/#14 engine/replay integration.

## Test evidence and review gates

Test-first2f304d2add1699b4c17b8f2b0617c29218464e4b:22missing-module errors.
7400707dc9cd2faa0fbfef36ee24881e7c934e08 expands tests/reproduces malformed page references,
invalid nested timezone type and submicrosecond truncation (2FAIL+1ERROR before correction).
41f950e00afb4c3765bf8307673bc0fb7a97aca1 exposes non-UTC host-timezone bridge acceptance.
a3fcf16a1c17b7227538c00eeb4384612d091846 exposes repeated page/row lineage acceptance.
adc960fddedd26b85dfbed6316225cdeac99f2fd exposes submicrosecond clock bound rounding down.
Each regression was observed locally before its corresponding change; assertions retained.

Local WindowsPython3.12.14: **109guarded offline tests PASS (69baseline+40new)**, compilationPASS.
Tests cover immutable inputs/outputs, policy bindings, no future-value leakage, duplicate/
gap/wrong-session/invalid/nonfinite rows, known-vs-fetch/PIT models, clock/precision, page
chains/partial symbols/capture integrity, DST/ambiguous/nonexistent rules,16:00 and13:00
fictional mappings, pure no-host-file calls, isolated blocked/eligible PR31 views.
CI inherits main Windows/Linux3.11 checks, standard library only; exact final-head CI
identities/results are returned on PR19. No live semantics, real exchange calendar,
source authority, crash recovery or consumer performance validated by these tests.

Unresolved: independent contract/code review; real source/SDK/mapping/timezone/calendar/
halts/completion/finality/clock/availability authority; numerical freshness policy;
non-UTC consumer bridge; capture/durable custody/recovery; real-data/feed or GUI integration.
No SDK/provider connection, credentials, real records/history/study, paper/live orders,
production databases/CSV/ingestion edits, merge or deployment. Recommended next only after
review: separately scoped offline consumer/timezone compatibility or expanded pure-contract
validation. Capture/provider integration needs its own evidence/permission gate.
