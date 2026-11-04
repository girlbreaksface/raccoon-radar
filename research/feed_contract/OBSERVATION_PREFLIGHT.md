# Read-only observation preflight v1

Prepared 2026-11-03 America/New_York on unchanged #56 head
e16a64abaf8cd539c56040dc5d5e7cac8eb3ef59. This document prepares a reviewable
experiment; it does not release the live-collection HOLD or authorize execution.

## One question and a frozen protocol

Question: in one bounded raw-only SPY/QQQ K_1M RTH callback window, are changed
OHLCV/turnover values for an already received exact source label observed after
a later label for that same symbol? Report observed receipt order, not inferred
event chronology, provider error, or permanent finality. A negative result means
only NOT_OBSERVED_IN_WINDOW, never that corrections cannot occur.

If separately released after preflight review, use the existing CAPTURE_PLAN.md
limits without widening them: localhost only, one context/subscription, both
symbols, 120 seconds, 300-second supervised lifetime, 5000 records, 10 MiB
journal, 64 KiB payload, 128 queued callbacks and 100 stamps per receipt.
No retry, history request, fallback feed or automatic rerun. Stop on every
existing clock, silence, disconnect, scope, queue, write and resource fault.
Abort on independently reported halt/session uncertainty; the runner itself is
not a halt detector or authoritative calendar. Predeclare the future observation
date and exact UTC/ET window before capture, using an independently verified
session that leaves the full bounded lifetime inside RTH. No date selected here.

Future observation is separate from historical feasibility: preserve BOTH
SPY/QQQ and the six frozen sessions 2024-01-19, 2024-03-08, 2024-03-11,
2024-03-15, 2024-06-03, 2024-07-03. No replacement, seventh historical date,
outcome-based selection, market dataset import or options study is authorized.

## Required evidence before any connection

Every row currently remains UNVERIFIED. Record exact evidence location, hash,
scope, checked-at time, expiry and reviewer decision in a new private preflight
record. A blank, stale, contradictory or unavailable item means HOLD. Historical
attestations and successful synthetic tests do not populate these fields.

| Gate | Required current evidence | Failure action |
| --- | --- | --- |
| Scope and release | Reviewed code SHA, dependency base, this question, exact date/window, explicit release for one bounded raw-only attempt | HOLD; no invocation |
| Access and retention | Current owner attestation for existing zero-cost quote entitlement and local retention; no activation, card, paid upgrade or account/order queries | HOLD; no entitlement probe |
| Environment | Approved SDK/native environment, Python and tzdata versions; SDK/OpenD 10.11.7108 and runner-required binary/source hashes | HOLD; no bypass or installation-policy change |
| Session and clock | Date/security-specific calendar source/version, early-close/holiday/halt checks, UTC conversion and independent clock uncertainty; window within RTH | HOLD; weekday check alone insufficient |
| Isolation and bounds | Reviewed runner/watchdog and stop settings; empty exclusive destination; no dashboard, default database or trade context | HOLD; no capture path execution |
| Evidence handling | Private destination, retention and access scope, sanitized reporting plan; no raw payload upload | HOLD; preserve prior artifacts |

Do not run opend_capture.py as a preflight command: it can connect. Environment
inspection, authentication, provider requests and live execution are not performed
by this document. Do not infer current runtime availability from the old failed
October 30 attempt or the later author-reported November 2 capture.

## Offline analysis and stopping interpretation

For a later approved capture, retain original journal/seal/supervisor files and
hashes before analysis; use a new exclusive output directory. Inspect supervisor
outcome and verify the full seal before reporting receipt-order counts. Missing
seal, kill, truncation, limit stop or scope fault is incomplete evidence; do not
silently retry or publish a successful-session conclusion.

Group exact symbol/source labels, retaining every receipt, repeat and revision.
Report counts of receipts, labels, repeats and changed fields per symbol, plus
receipt sequences and field paths for each qualifying late revision. Preserve
source labels, opaque protobuf serialization and adjustment flags unchanged.
Do not shift labels, synthesize missing records or compare historical and live
feeds. Raw labels do not establish interval order; any ordering interpretation
requires separately verified mapping. Existing audit grouping may mix feeds:
stop interpretation if endpoint/coverage/adjustment authority is unresolved.
The disconnected synthetic gate cannot authenticate these declarations or bytes.

Report denominators and missing/ambiguous cases, clock limitations, version and
scope evidence, termination reason, code/artifact hashes and every exclusion.
No observed revision, quiet period or repeated value establishes FINAL. A valid
seal proves retained bytes, not complete reception or provider truth. Local
receipt order does not establish upstream publication order or causality.

## Continuing gates and rollback

#46's provider summary is secondary evidence with unresolved version, interval,
calendar, correction horizon and factor-version details. #51's free historical
tick/chain blocker remains open. No qualified bid/ask adapter, authenticated row
provenance, point-in-time chain, complete availability lineage or executable-fill
model exists. #53/#54 are a sibling stack absent from this tree; no combined
integration coverage is claimed. Dependency/integration review and explicit merge
authorization remain separate gates.

Offline preparation only. Live collection HOLD; paper DATA_BLOCKED; finality
UNKNOWN; completeness NOT_ESTABLISHED; merge HOLD; trading NO-GO. Budget $0.
No provider contact, data acquisition, private-data access, runtime/DB change,
order routing, trade, purchase, deployment or merge. Rollback removes this
document and reverts the accompanying heading correction only.
