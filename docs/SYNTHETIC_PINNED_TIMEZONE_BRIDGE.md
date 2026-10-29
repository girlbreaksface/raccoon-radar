# Synthetic pinned timezone consumer bridge — isolated draft

Authority: direct coding-chat instruction to proceed and PR19comment6500339863.
Scope is OFFLINE SYNTHETIC ONLY. No provider/SDK connection, real data/history,
credentials, GUI, production ingestion/DB/CSV edits, paper/live orders, deployment,
merge or monitor restart. Review this draft separately; no real source approval implied.

## Safe dependency and unchanged protected work

New branchfeat/synthetic-pinned-timezone-bridge starts at PR33
b7dd5e5100c2823701c8de639fc0e9048adde80e. It is STACKED, not independently based on main.
PR33 canonical_candles.py and its old UTC-only to_pr31_arguments gate remain unchanged.
PR31 reference stays24a5c5de529f99992ec331f6ea91c39c1f61fa6e;
sourceSHA2565e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29.
No blind merge/retarget/protected branch modification. Main ancestry remains
b0ad02dc996b00406e7da08fb33b6382f658ea40.

## Implementation and public API

evaluate(canonical_report:Report) -> immutable BridgeReport
consumer_dict(bridge_report) -> NEW mutable display copy of consumer output, if present

The public gate only accepts the pinned canonicalizer's typed immutable Report. It
recomputes canonicalize from the retained Bundle/Context/Request and exact report identity
BEFORE calling any numerical kernel. A self-declared eligible flag/forged metadata cannot
substitute. Unknown source/calendar/finality/clock/policy/availability, inconsistent hashes,
unavailable revisions, malformed values or incomplete pages stay blocked by ALL original
canonicalizer checks. No output or data is promoted from legacy CSV fields.

Supported calendar zones are exactly UTC and America/New_York. _PinnedZones is immutable,
bound to the exact validated context, and resolves only the requested calendar zone.
It reuses canonicalizer's version/name checks and ZoneInfo.from_file(BytesIO(...)) path;
no ZoneInfo(name), installed tzdata, host TZPATH, fixed guessed offset or alias fallback.
UTC's explicit fixed rule matches prior UTC semantics. Unsupported aliases such as
US/Eastern are not silently treated as equivalent even if identical bytes were supplied.

_pr31_pinned_kernel.py is a PRIVATE statically extracted reference kernel, not a standalone
supported API. It contains the exact assess and its five pure helper ASTs plus the original
AUTHORITIES/NOTICE values. Only two changes to assess: a REQUIRED keyword-only zone_factory
parameter and replacement of the sole ZoneInfo(zone) call with zone_factory(zone).
No default resolver/host fallback. No filesystem/storage/provider functions or imports
copied. AST conformance verifies every reference check/formula unchanged after exactly
that transformation; UTC output is exact-equal to original PR31 output.

The kernel is a vendored, tightly pinned dependency; upstream changes require explicit
review/regeneration and conformance tests. It is not runtime dynamic patching of PR31
or a global ZoneInfo monkeypatch. Runtime source authentication is NOT provided.
Private helpers are unsupported entrypoints; trusted Python code can bypass private APIs
or replace modules, outside this integrity/trust model.

The bridge creates isolated rows/contract arguments from the validated frozen frame,
preserving original raw stamp, canonical UTC interval/availability, exact session/date
and source hashes. It does NOT rename New York sessions to UTC to bypass restrictions.
It preserves full supported microseconds; unsupported precision/conversions remain blocked.
Completion=True/FINAL in the derived contract comes only after revalidated FINAL_ONLY
evidence; source originals remain in the immutable canonical report. Independent event,
knowledge and delivery budgets remain enforced OUTSIDE the kernel; they are not replaced
by PR31's narrower event-age parameter.

All reference EMA9/21, HLC3 proxy, relative-volume, warmup, finality/source/availability/
session checks remain unchanged. The bridge adds stricter output-domain checks, not looser
eligibility. Unexpected nonfinite/malformed/contradictory results block explicitly.
No thresholds, confidence scores, options contracts, trade instructions or indicators added.
HLC3 stays a candle-weighted proxy, not true trade-level VWAP.

BridgeReport retains the full canonical report, immutable nested consumer map/list records,
status/reasons, consumer_hash and audit bridge_hash; action is ALWAYS WAIT.
SYNTHETIC_CANDIDATE means fictional data passed both data and reference hypothesis checks,
not a verified live signal or trading recommendation. MIXED/insufficient warmup are NO_TRADE.
consumer_dict is a disposable DISPLAY copy, not independent proof of eligibility; retain
BridgeReport/context for lineage. Later excluded raw revisions can change bridge audit hash
without changing the earlier frame hash or consumer observations.

## Test-first and exact compatibility evidence

First test commit34c2a95bdf6afb524a7a1a9dd56090b395488f06:17missing-module errors
before bridge/kernel existed. Initial implementation then17PASS.
Follow-upe2650fbb8371abd0de3977b1568ea94cc6d6ce56 adds unsupported alias/offset cases
and fault-injected dependency outputs. Before correction, that one fault-injection method
has1assertionFAIL+2ERROR across3subcases: contradictory eligible-with-error output admitted,
nonfinite freeze raised, mixed malformed reason codes raised. Those now yield explicit
INVALID_CONSUMER_OUTPUT; no skipped/weakened assertions or original kernel formula changes.

20bridge tests cover:
- Exact unchanged PR31 UTC parity and AST/helper/constant conformance.
- New York comparison against independently injected pinned reference semantics.
- No host timezone/file fallback, missing rules and unsupported alias rejection.
- Pinned spring/fall DST offsets; ambiguous/nonexistent wall times and contradictory offsets.
- Synthetic13:00 early-close and16:00 START/END boundaries, raw stamps unchanged.
- Fractional availability/cutoff and rejected submicrosecond precision/clock uncertainty.
- Post-cutoff invalid revisions do not affect feature or consumer outputs; unknown/visible
  conflicting revisions block, audit raw/bundle identity still changes.
- Source/calendar/finality/clock failures and forged reports do not reach kernel.
- Immutable outputs/lineage, isolated copies, deterministic repeated results, no global mutation.
- MIXED and warmup exclusions; invalid/nonfinite/contradictory dependency outputs block.

Local WindowsPython3.12.14: **130guarded offline tests PASS**
(69mainbaseline+41inheritedPR33+20new), compilationPASS. No new dependencies/workflow changes.
Pinned NewYork TZif from inherited tzdata2026.5 fixture,1744decodedbytes,
SHA256d7f2206b3a45989fc9ad63d558922532fa7352280d5f87176bf1db79cb1d1fa9.
Tests use synthetic schedules/data only, not actual NYSE holidays/early closes, OpenD labels,
provider chronology or historical-availability evidence. No installed SDK/provider used.
Exact final Windows/Linux CI checkout/jobs are returned on PR19 after verification.

## Limits and review gates

Authority strings, hashes, synthetic/commit markers, declared code identity and capture
snapshot interpretations remain trusted CALLER claims, not authenticated provenance or
proof of actual source semantics. Real data relabeled synthetic cannot be detected.
No capture/storage/crash recovery was implemented, no historical study executed, no actual
provider/bar finality/calendar/clock/freshness authority approved. No power-loss, security
sandbox or source authenticity guarantees. Standard library imports and trusted source
files are part of the execution environment; this is not hostile-Python isolation.

This staged bridge does not mount in Radar, replace local files, alter original PR31/PR33,
or authorize real feeds. Other consumer timezone profiles and legacy engine/replay APIs
remain unsupported until separately designed/tested. Consumer output alone is not a
durable research artifact; keep full immutable lineage and separately reviewed custody.

Recommended next: pinned-head technical/contract review and proposed cumulative integration
plan. Any source-permission/empirical timestamp investigation, capture/recovery, GUI, real
records, provider connection or merge/deployment requires a separately bounded approval.
