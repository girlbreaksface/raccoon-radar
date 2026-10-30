# SPY/QQQ live read-only observation — feasibility and scoped design

Review date: 2026-10-30 (America/New_York). Status: DRAFT, specification only.
Decision: proceed with offline design and mocked contracts; actual feed access and
strategy eligibility remain blocked. No live connection, secrets request, orders,
provider SDK import, account inspection, data acquisition, deployment or production
change is authorized or performed by this review. Forward paper observation means
locally recording research decisions before outcomes, not submitting paper orders.

## Repository reconciliation inspected first

GitHub metadata and locally fetched source were inspected on the review date.
Main is `b0ad02dc996b00406e7da08fb33b6382f658ea40`. This proposal branches from
main and adds only this document. Historical AGENTS.md test counts are stale;
they are not evidence of current results.

| Preserved draft | Inspected head | Current meaning |
|---|---|---|
| [PR41 reconciliation](https://github.com/girlbreaksface/raccoon-radar/pull/41) | `838851a3cfd248b19bd0a2a590a7bf55756eaed2` | Latest reconciliation draft; recommends S0 default and unchanged PR40 comparator. Not an approved or complete integrated protocol. |
| [PR39 S0 specification](https://github.com/girlbreaksface/raccoon-radar/pull/39) | `8d45bb39b298a8c7d9e01b17b12bc7b324c45e19` | Proposed 20/8 volatility-relative protocol. |
| [PR40 experiment](https://github.com/girlbreaksface/raccoon-radar/pull/40) | `6f282a88c41d345e744089b6dd880e93dd53a4af` | Different 8/5 percentage protocol; not implementation of PR39. |
| [PR38 approved vNext 1.1 presentation](https://github.com/girlbreaksface/raccoon-radar/pull/38) | `a984cc0b5e9f2f69b6ee99cca166221a632341fa` | Preserve purple side-by-side workstation and synthetic/FINAL-only behavior. |
| [PR37 replay viewer](https://github.com/girlbreaksface/raccoon-radar/pull/37) | `cee98fb094842921a5a0fcd8764cfaf1c444b803` | Preserved isolated synthetic consumer. |

These PRs were open, draft and unmerged in the inspected metadata. PR41 reports
54 isolated tests and 158 base tests on Windows/Linux with successful CI; those
are source-reported separate suites, not independently rerun tests in this review
or a cumulative main count. Its 88 comparisons expose confirmation differences:
S0 reversal/continuation at bar32 versus PR40 at bar31/bar29. Passing those cases
does not settle market accuracy. Revision graphs, multi-episode audit, pair
freshness/mixed states and censoring remain incomplete requirements. Feed design
can proceed independently; detector integration cannot bypass those decisions.

## Existing data-source research and refreshed public evidence

Read, preserve and build on:

- [PR36 OpenD investigation](https://github.com/girlbreaksface/raccoon-radar/blob/07a58f1d0650b8179fa9fbeb31b7fd53fd68988b/docs/research/OPEND_CONTRACT_REPLAY_INVESTIGATION.md).
- [PR32 synthetic source characterization](https://github.com/girlbreaksface/raccoon-radar/blob/e71f8de950ead63b505b179ab2ee124b369f2741/docs/OPEND_ADAPTER_SPEC_CHARACTERIZATION.md).
- [PR17 adapter design](https://github.com/girlbreaksface/raccoon-radar/blob/9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3/docs/CANONICAL_COMPLETED_CANDLE_ADAPTER_DESIGN.md).
- Main persistence provenance and ingestion characterization documents.

Public pages below were reopened on 2026-10-30. This is documentation evidence,
not empirical provider verification; no publisher snapshot was archived here.
Moomoo pages identify v10.12, not an installed or supported local build.

| Documented evidence | Design implication and remaining unknown |
|---|---|
| [Candlestick callback](https://openapi.moomoo.com/moomoo-api-doc/en/quote/update-kl.html) describes asynchronous subscribed candles and US Eastern time_key. The reviewed Python field table has no explicit closed/final flag. | Callback receipt is not completion/finality authority; interval label, revision identity and guarantee remain unknown for the installed provider. Absence in this table is not proof no protocol can supply authority. |
| [Quote Q&A](https://openapi.moomoo.com/moomoo-api-doc/en/qa/quote.html) describes subscription rights/quota and terminal conflicts. | API access is account-specific. App visibility is not proof of API entitlement, consolidated coverage, storage rights or redistribution permission. |
| [Historical candles](https://openapi.moomoo.com/moomoo-api-doc/en/quote/request-history-kline.html) exposes cursor pagination, interval/adjustment options and defaults unsuitable to assume for one-minute research. | Recovery must explicitly bind parameters and complete pagination. Later history cannot establish original decision-time availability. |
| [NYSE calendar](https://www.nyse.com/markets/hours-calendars) publishes holidays and early closes. | A pinned, date-specific session authority is required; a fixed 390-minute grid is insufficient. Actual feed/venue coverage must match the calendar. |

No provider is yet designated PERMITTED for this project. Local Moomoo OpenD is
the first candidate because it matches existing research, not because access or
semantics have been confirmed. Do not substitute an HTTP API, scrape a chart,
use an app-only entitlement, or silently fall back to a different/delayed feed.

## Source permission and credentials gate

Before separately authorized access, document per SPY/QQQ: legal provider/product
identity; API quote rights; real-time versus delayed status; venue/consolidated
coverage; one-minute subscription/history quotas; private non-display analysis,
local retention, derived-data/export and redistribution permissions; effective
license dates; local SDK/OpenD build and package hashes. Unknown rights remain
UNAVAILABLE. No purchase or entitlement activation follows from this proposal.

Future connector scope is quote-only, explicit `US.SPY`/`US.QQQ`, approved
one-minute session/adjustment configuration and bounded requests. No trade
context, unlock, order, positions or account-balance APIs. OpenD's shared process
may itself have broader capability: quote-only application code is not equivalent
to a provider-enforced read-only account permission. Verify that boundary before
claiming least privilege. Do not expose a local endpoint to other machines.

No secrets are needed for current work. Later, only after separate explicit
authorization, the owner authenticates through the provider's supported local
flow. Never paste secrets into chat, repository, fixtures, command arguments,
screenshots or logs. Use an OS credential facility or provider session, restrictive
local access and redacted reference IDs; avoid collecting account identifiers.
Review login persistence, session expiration, revocation and secure transport for
the actual build. Credentials must not be embedded in evidence hashes. A fake
transport must remain the default; configuration alone cannot initiate connection.

## Separate capture from strategy eligibility

Proposed flow: authorized quote transport -> bounded queue -> immutable raw
capture -> committed manifest -> pure adapter -> sealed as-of frame -> selected
offline research profile -> append-only decision journal. No component has an
order interface. No imports of existing dashboard or store-initializing helpers.
Use a new explicit output root, never the four existing research stores.

RAW_OBSERVATION may record provisional/unknown evidence with clear status;
ENGINE_READY requires every permission, mapping, calendar, availability, quality,
completion and finality gate. Blocked is DATA_BLOCKED, not a valid NO_CANDIDATE
decision. Raw retention itself needs licensing and capture authorization.

The current consumer stays FINAL-only. Never synthesize FINAL from an elapsed
minute, next candle, repeated value or successful fetch. Completion and correction
finality are separate. If OpenD cannot establish the required finality contract,
live raw observation may be feasible while FINAL-only analysis remains unavailable.
A completed-provisional profile is an alternative requiring explicit approval,
versioned semantics and new tests; this review does not adopt it. Finality must
describe a bounded provider guarantee/policy, not an impossible promise that
market data can never be corrected.

## Time, session and revision contract

Preserve exact raw timestamp/value/type and OHLCV without rewriting. Separately
record provider event time if supplied, derived interval start/end, full revision
receipt UTC, monotonic receipt order, completion-evidence receipt, provider
publication time only when authoritative, clock uncertainty, and durable commit
time. Label fidelity WIRE_BYTES only if actually captured; SDK_ROW_SNAPSHOT is
not wire data. Hash identity does not authenticate truth.

Approve start/end label mapping only for the exact endpoint/build/interval/session/
adjustment scope using provider authority or independently aligned opening AND
closing OHLCV evidence. A 09:31..16:00 grid is corroboration, not proof. Exchange
timestamps are not publication timestamps. Unknown timezone/precision blocks;
never attach host timezone. Preserve subsecond aware UTC and pin IANA
America/New_York/tzdata for display and conversion.

Pin date-specific market/session authority and UTC bounds, including holiday,
early-close, DST and unscheduled closure/halt policy. Initial scope is regular
session only; no extended-hours mixing or universal 390 assertion. Blank/no-trade
minutes, halted minutes and transport gaps remain distinct. No invented candles.
The expected grid reaches an independently evidenced completion watermark,
not merely the last bar returned. Session resets cannot reuse prior-day warmup.

Each immutable revision includes capture/request/page/connection epoch, symbol,
interval identity, source hash, receipt sequence, exact payload, completion/finality
authority, source sequence when trustworthy and supersedes links. Missing or
ambiguous revision order, branching/cycles and conflicting same-time versions
block selection. Identical retries may share a semantic identity only under a
versioned rule retaining all raw receipts. Never last-row-wins by arrival order.

Proposed conservative usable time is the maximum of interval end, full revision
receipt, required authority receipt and durable commit visibility, with bounded
clock uncertainty applied conservatively. Required policy/calendar evidence must
also be available then. Use the processing sequence to prevent wall-clock
rollback from admitting future records. Unknown clock bounds block eligibility.
No exact first market-wide publication claim is inferred from local receipt.

At cutoff t, select only uniquely eligible revisions and authority known by t,
then validate that information set. A correction received later creates a new
corrected-as-of run linked to the original; earlier decisions stay byte-identical.
Never fall back to an older FINAL behind a newer visible provisional revision.
Backfilled history is tagged RECOVERY_LATE, available no earlier than actual
receipt/commit; it cannot create a retroactive forward decision or hidden warmup.
Keep original-as-known and corrected views separate, including label vintages.

## Disconnects, gaps and recovery

Connection state: STOPPED -> CONNECTING -> RAW_OBSERVING; failures enter
DISCONNECTED/DEGRADED, then RECOVERING, and only return after explicit validation.
Transport health never implies engine eligibility. Entitlement loss, schema drift,
unknown clock, stale tail, queue overflow, disk-full, manifest failure, duplicate
conflict, missing expected minute or source failure blocks affected analysis.
SPY success cannot certify QQQ. Pair analysis blocks on stale/invalid peer or
misaligned cutoffs, while valid individual evidence is retained.

Future reconnect uses bounded exponential backoff with jitter and a retry budget;
no reconnect storm or automatic account/entitlement change. Pin numerical
heartbeat, stale-tail, queue, retry, capture-size and clock thresholds before any
provider experiment using documented limits and reviewed objectives. Unset limits
mean cannot start, not permissive defaults. Distinguish deliberate market closure
from absent data, including feed silence when no updates are expected.

Recovery queries, if later approved, must explicitly track cursor exhaustion,
repeated cursors, truncation, errors and changing pages. Do not certify a coherent
snapshot solely from a terminal cursor. Missing interior, tail and whole-symbol
coverage must be reported. Queue loss creates an explicit gap; never silently
drop data or replace a stale status with a fresh-looking cached price. Recovery
requires full source/grid/quality revalidation and warmup under the frozen profile.

## Observability, custody and audit

Future standalone status output should show mode, symbol/feed/delay, last receipt,
last evidenced complete interval, separate event/receipt ages, clock uncertainty,
session/calendar, reconnect epoch and exact blocked reasons. Preserve the current
UI; any integration requires its own review. A green socket is not a green frame.

Record counters and bounded distributions for receives, late/reordered revisions,
duplicates/conflicts, expected missing intervals, callback/queue/processing delay,
queue high-water mark/overflow, disconnect duration, retries, entitlement errors,
source throttles, capture write failures and blocked-frame reasons. Unknown
publication time means publication latency is UNKNOWN, not zero. Log operational
errors even when no decision is produced. Initial review uses local status only;
no external notification channel is implied.

Append-only audit events: session start/stop/config approval; source/contract/
calendar/version identity; redacted permission state; request/subscription/error;
connection changes; each raw revision reference; gap/recovery; committed manifest;
frame emitted/blocked; decision profile/code/config and frame hash; corrections;
operator actions and export/recovery. Record UTC plus monotonic sequence and
previous-event hash. Keep secrets and unnecessary account/path information out.
Hash chains detect some changes but do not prove authenticity or prevent tail
truncation; independently retained manifest checkpoints are needed for stronger
tamper evidence. Never promise tamper-proof logs.

Exclusive file creation, a single-writer lease, staged pages and committed hashed
manifests precede publication. Crash before manifest means no frame. Crash after
commit must recover the same identity or block; never duplicate a decision.
Permission-controlled storage, bounded capacity, crash/disk-full testing, explicit
retention under license and reviewed backup/recovery are pre-capture gates.
No automatic deletion of existing evidence; retention disposal needs a separately
reviewed plan. No durability/power-loss claim is established by this document.

## Mocked adapter acceptance plan — not implemented or executed here

Use dependency-injected fake transport, virtual UTC/monotonic clock and immutable
SYNTHETIC bundles. No SDK, network, account, provider credential, real record or
existing DB is needed. Guard test execution from network/process/DB access except
explicit disposable capture fixtures when custody testing is separately scoped.
Write failing observable cases before implementing a pure adapter; do not modify
existing canonicalizers or weaken FINAL-only tests.

| Mock condition | Required assertion |
|---|---|
| No permission/mapping/version/calendar authority | RAW_AUDIT only; no engine call; source unchanged |
| Minute end passed, next callback arrives, values repeat | No invented completion or FINAL |
| Completed provisional/newer provisional after old FINAL | Block current FINAL-only frame; no fallback |
| START/END mappings at opening, 16:00 and early close | Exact separate derived intervals; raw bytes preserved |
| DST, ambiguous/nonexistent time, backward clock, unknown error | Pinned conversion or explicit block; no premature visibility |
| Revision receipt at/after cutoff, late correction, future bad payload | Causal cutoff boundary; earlier sealed decisions unchanged |
| Duplicate retry/conflict, reordered supersession, branch/cycle | Preserve receipts; deterministic resolver or block |
| Disconnect, tail/interior gap, no-trade/blank, one-symbol loss | Separate causes; no fill; peer/pair status honest |
| Reconnect backfill and later-page failure/repeated cursor | Late availability retained; partial coverage never promoted |
| Queue overflow, throttle, revoked permission, schema drift | Block affected frames; bounded retries and observable error |
| Invalid/nonfinite OHLCV, mixed units/adjustment/session | Source-linked rejection, no numeric engine input |
| Future labels/outcomes and corrected history | No changes to as-known features, cooldown or decision journal |
| Same bundle/context twice, call-order/input mutation | Identical semantic hash; deeply immutable input/output |
| Crash/disk-full before/after commit and restart | No partial publication/duplicate decision; explicit recovery |

Acceptance requires Windows/Linux Python3.11, pinned dependencies/timezone bytes,
exact code/fixture hashes, test-first evidence and independent contract review.
Synthetic tests can establish these dispositions, not provider truth, licenses,
market prediction, strategy profitability or real durability. No executable tests
were added in this specification phase; the matrix is future work.

## Safe phased path and decisions

1. **Current phase: specification review.** Preserve all research/UI PRs. Accept
   read-only observation as the target, with raw capture separate from eligibility.
   Recommend OpenD as candidate only and keep current FINAL-only contract.
   No detector selection is made; PR41 remains a draft recommendation.
2. **Offline feasibility prototype.** Build an isolated fake-only transport/adapter
   and run the matrix above after the contract is reviewed. This request permits
   mocked tests; this deliverable deliberately stops at a reviewable specification
   because real authority and the finality/profile decisions are unresolved.
3. **Provider evidence plan, then separate explicit authorization.** Review exact
   quote calls, symbols, session/time window, limits, local credential flow,
   entitlement/license facts, output location/retention, clock evidence and stop
   conditions. No secrets request or provider connection before authorization.
   Provider correspondence is also a separate authorized communication.
4. **Bounded live raw observation, if authorized.** Standalone local capture only;
   verify opening/closing mapping, updates/corrections, reconnect, gaps, entitlement
   and timing against the approved scope. Produce an evidence report; remain
   DATA_BLOCKED wherever semantics are unknown. Do not wire the protected UI.
5. **Forward paper observation, only after eligibility/profile freeze.** Freeze
   code, parameters, source/calendar/finality, date/access manifest and decision
   cadence before outcomes. Record each decision before the outcome with no broker
   orders, including blocked/no-candidate/conflict cases. Separate label process,
   fixed horizon/vintage, censoring and missingness. Keep SPY/QQQ on the same dates;
   report correlated/overlapping observations rather than independent trial counts.
6. **Later validation.** Separately authorize a frozen study; report all exclusions,
   false/missed events, uncertainty, date clusters, and null results. Underlying
   candle movement is not a fill, option return or 0DTE evidence. Execution/cost
   modeling needs bid/ask/latency/fee evidence and separate scope. No real-money
   milestone, trading implementation, merge, deployment or production change is
   authorized by success at any preceding phase.

Outstanding decisions: permitted feed/license; exact SDK/OpenD and source contract;
timestamp/clock/calendar authority; finality feasibility versus a separately
approved provisional profile; revision/custody and operational thresholds; PR41
protocol selection/completion; and future capture/study scope. These are gates for
dependent work, not requests for credentials now.

Verification of this change: repository status/source documents and public source
pages reviewed; documentation-only addition. No runtime tests, provider checks,
GUI checks or study were performed, and no independent review is claimed. Rollback
is closing this separate draft; no runtime entry point depends on the document.
