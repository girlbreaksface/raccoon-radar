# H-003 / A-007 — revision-specific availability gap register
Recorded-at UTC: 2026-10-27 13:15:21 UTC. Owner: coding agent inventory; evidence acquisition owner: human maintainer/research owner, not yet designated. Status RETURNED_FOR_REVIEW; primary historical evaluation BLOCKED.
No provider or store accessed. This register is bounded to repository main b0ad02dc996b00406e7da08fb33b6382f658ea40 and pinned #13/#14/#17/#18 source/design paths named in verification.md. Absence here does not establish absence from private archives, other branches, feeds or the world. No real candle record was supplied in the inspected scope, so invented session IDs/revision rows would be misleading.

Allowed statuses: VERIFIED_WITH_EVIDENCE (within stated scope), UNKNOWN (no establishing evidence), CONFLICTING (two actual contradictory evidence items), NOT_APPLICABLE. A proposal, caller boolean, filename or 390-bar coverage shape is never verification.

## Bounded source inventory
| Scope ID | Source | Symbol | Session / interval / exact revision bounds | Eligibility |
|---|---|---|---|---|
| AV-MIN-SPY | Moomoo raw one-minute candles | SPY | ALL UNSUPPLIED sessions/intervals/revisions | BLOCKED / UNKNOWN |
| AV-MIN-QQQ | Moomoo raw one-minute candles | QQQ | ALL UNSUPPLIED sessions/intervals/revisions | BLOCKED / UNKNOWN |
| AV-DAY-SPY | Prior-session daily context | SPY | Required 60 prior scheduled daily sessions per future study date; dates/revisions UNSUPPLIED | BLOCKED / UNKNOWN |
| AV-DAY-QQQ | Prior-session daily context | QQQ | Required 60 prior scheduled daily sessions per future study date; dates/revisions UNSUPPLIED | BLOCKED / UNKNOWN |

For EACH of those four scopes, the following separate fields are UNKNOWN; this is a scoped register rather than a claim that all periods exist:
| Evidence dimension | Status / missing value | Affected claim | Owner / required next evidence |
|---|---|---|---|
| Raw capture identity | UNKNOWN: no captured source payload/location/hash; no exact revision IDs | Cannot bind values to evidence or reproduce a historical information set | Research owner: identify approved existing artifact location/hash; do not acquire under this order |
| Endpoint and source contract | UNKNOWN: endpoint actually used, SDK/OpenD versions, entitlements/subscriptions, interval/session/adjustment flags, request bounds and source timezone | Cannot transfer one endpoint/version's semantics to another | Source evidence owner: complete per-request manifest |
| Timestamp mapping | UNKNOWN: raw label meaning/authority, independent OHLCV comparison/vendor confirmation, approval scope and contrary evidence | Cannot derive canonical start/end or settle 09:30/09:31/16:00 | Maintainer + independent evidence reviewer |
| Exact revision receipt / publication | UNKNOWN: full-value receipt/publication UTC, clock provenance/uncertainty, metadata receipt and first knowledge of each revision | No past event-time availability, features or labels can be asserted verified | Source evidence owner: trusted point-in-time capture/revision metadata |
| Completion | UNKNOWN: closed-bar watermark/guarantee for exact interval/revision | Elapsed time/fetch success does not establish completed candle | Mapping/completion contract reviewer |
| Finality | UNKNOWN: correction policy/finalization evidence | A completed interval can still be revised; final series cannot be backdated | Provider contract/evidence reviewer |
| Units / adjustments | UNKNOWN: currency, per-bar vs cumulative volume, share/split adjustment consistency and revision basis | Indicators across inconsistent values invalid | Research owner: scoped metadata |
| Calendar/time | UNKNOWN: pinned exchange/calendar/source hash/tzdata, holidays, DST/folds, early closes/halts and expected tail watermark | No universal 390 bars, weekday-only or local-host-time fallback | Calendar policy owner: reviewed versioned schedule |
| Pagination/coverage | UNKNOWN: all page refs/cursors/exhaustion, repeated cursor, errors, absent symbols, interior/tail/whole-day missingness | Partial source cannot count as complete | Capture manifest owner |
| Revision identity/resolution | UNKNOWN: trustworthy IDs/sequences and tie/supersession policy | Cannot silently last-row-win or flatten final corrections | Adapter reviewer: approve immutable frame revision policy |
| Daily-history knowledge | UNKNOWN: 60 prior scheduled daily observations, as-of versions, adjustment/units and aggregation lineage | Daily context unavailable, not an inferred macro/daily trend | Research owner: evidenced daily series known at decision |
| Existing-history inspection | UNKNOWN for any future real dataset; prior code/synthetic cases are inspected | Chronological later dates alone do not prove untouched holdout | Study custodian: freeze/access audit and actual future window |

All four scopes require the full field set. Daily-specific 60-session requirement is NOT_APPLICABLE to the minute-only indicator warmup itself; it still matters when those events are stratified by daily context. Daily-context UNKNOWN must not silently remove otherwise intraday-eligible primary events; keep explicit DAILY_CONTEXT_UNAVAILABLE counts.

## What IS evidenced, and what it cannot prove
| Evidence | Status and identity | Limit |
|---|---|---|
| Main source/characterization documents | VERIFIED_WITH_EVIDENCE as repository text: [characterization](https://github.com/girlbreaksface/raccoon-radar/blob/b0ad02dc996b00406e7da08fb33b6382f658ea40/docs/CANDLE_INGESTION_CHARACTERIZATION.md), blob 2c4cd5b18198b16b87bb5eaf54006efaef2bb5b1 | Synthetic tests document filtering of 16:00, single-day minute cutoff versus range direct-worker asymmetry, ignored pagination keys, partial results and OHLCV validation gaps. They do not verify provider semantics |
| Synthetic CSV | VERIFIED_WITH_EVIDENCE that named fixture exists: [SAMPLE_SYNTHETIC_CANDLES.csv](https://github.com/girlbreaksface/raccoon-radar/blob/b0ad02dc996b00406e7da08fb33b6382f658ea40/SAMPLE_SYNTHETIC_CANDLES.csv), blob cc8696dcf8855c383f9e87d36a75d15a0466099d | Synthetic only, SPY example dated 2026-10-26, contains literal invalid clock strings 09:60 onward and lacks source/revision/availability/calendar evidence. Not an eligible provider dataset. Preserved unchanged |
| Engine synthetic fixtures and Decimal/rule tests | VERIFIED_WITH_EVIDENCE test files and recorded CI success at #13; see verification.md and ci-observations.json | SYNTHETIC evidence remains fixture metadata, not real-history VERIFIED authority |
| Replay cutoff tests | VERIFIED_WITH_EVIDENCE files and combined CI at #14 | Post-cutoff synthetic revision isolation does not resolve real revision ordering or publication latency |
| #17/#18 | VERIFIED_WITH_EVIDENCE as design documents, blobs 876b29be4aecb6fba95e3fa2fa395aab8a35a4fb and e4f381a8fa8d8ed968e01bd501b7a95b763df38a | Unimplemented contracts are not captured source evidence or approvals |

No actual provider evidence conflict is established; use UNKNOWN rather than CONFLICTING. Different proposed raw-label interpretations are hypotheses, not contradictory provider observations.

## Replay limitations and decision
#14 uses publication-event snapshots, not #18's fixed-grid frame replay. It lacks general bitemporal revision resolution; known conflicts can reject labels. Valid canonical schema is required; malformed availability/session metadata may raise. Idealized next-boundary open labels assume zero latency, omit execution costs/spread/fills and are vulnerable to missing-outcome selection. Freeze/inspection strings are caller assertions, not authenticated untouched data. #18's fixed-grid, delayed label and daily-context design is NOT IMPLEMENTED.

Unknown historical exact-revision knowledge time blocks primary historical evaluation. Neither bar end nor today's fetch timestamp substitutes for it. Preserve captures/raw stamps separately; no shifting, interpolation, evidence rewriting, DB normalization or assumed-latency relabeling as VERIFIED/SYNTHETIC.
Recommended next evidence request (NOT acquisition authority): owner locates existing restricted source artifacts and provides approved access location + hashes + manifests without publishing private datasets. Maintainer reviews mapping/knowledge/calendar policy, then separately authorizes bounded implementation/tests. If evidence remains missing, report UNAVAILABLE and do not execute the primary study.
