# Recommended protocol and fake-only feed contract — 2026-10-30

Status: finalized engineering recommendation for review; no integration or live
access approval. This additive milestone is based on PR41 exact head
838851a3cfd248b19bd0a2a590a7bf55756eaed2. It follows PR42 specification head
0b1ddd72ca21556d3c7ee1fa2bd6af88926e6354 without modifying either branch.

## Unified research protocol recommendation

Adopt PR39 MS12-S0 in full as the recommended normative research protocol,
with PR41 MS12-R0's explicit interpretation and incomplete-implementation list.
Normative source: docs/VNEXT_1_2_MARKET_STRUCTURE_RESEARCH.md at
8d45bb39b298a8c7d9e01b17b12bc7b324c45e19; interpretation:
research/reconciliation/RECONCILIATION_DRAFT.md at
838851a3cfd248b19bd0a2a590a7bf55756eaed2. Both are preserved here unchanged.
PR40 6f282a88c41d345e744089b6dd880e93dd53a4af remains a separately named,
byte-exact percentage comparator; never mix its parameters or continuation rules
into S0. This settles a recommendation, not market superiority or owner acceptance.

Retain 20 trend / 8 box bars, 4S net movement, 0.60 efficiency, 12 strict
steps, S as mean true range over the trend window; frozen width 0.5S..2.5S,
interior closes and separated touches. Keep two strict breakout closes,
strictly later close-based retest within five bars, then strictly later hold
within three, for both continuation and reversal. Retain exact PR39 epsilon,
tolerance, deadline inclusivity, failure precedence, 28-bar cooldown,
three-bar event age, aligned pair/mixed states, causal revision handling and
independent outcomes/censoring requirements by reference. No thresholds changed.

Evidence supports coherent semantics and mathematical conformance only: the
88 matched development variants distinguish S0 bar32 confirmation from PR40
bar31 reversal/bar29 continuation. Percentage translation/reflection differences
are consequences of denominator changes, not evidence of poor prediction.
Local Windows rerun reproduces PR41's exact evidence. PR41's three published
CI runs remain successful at its pinned head. No holdout or real market study.
Full multi-episode audit, pair freshness/mixed logic, censoring/outcomes and
full S0 revision integration remain unfinished. This milestone implements none
of those detector features and does not connect this model to the detector.

## OpenD feasibility: verified documentation versus unresolved facts

Public official documentation reviewed 2026-10-30; no local SDK/OpenD queried.
The docs describe v10.12, not a verified installed or supported build.

- [Quote Q&A](https://openapi.moomoo.com/moomoo-api-doc/en/qa/quote.html):
  API quote rights can differ from app rights; quotas/terminal conflicts can
  prevent subscriptions. Described US sources include Nasdaq and Arca feeds.
  Do not infer consolidated SIP coverage, a lasting free entitlement, or this
  account's rights from a public promotion. Account permission, feed/delay,
  SPY/QQQ coverage, retention/non-display/derived-data rights remain UNKNOWN.
- [Candlestick callback](https://openapi.moomoo.com/moomoo-api-doc/en/quote/update-kl.html):
  asynchronous subscription updates; Python table describes US Eastern time_key.
  That table does not expose explicit completion, finality or revision lineage.
  Neither start/end label nor first-publication availability is established by
  the timestamp wording. Missing fields in one table are not proof that no
  other provider mechanism can establish them.
- [Historical candles](https://openapi.moomoo.com/moomoo-api-doc/en/quote/request-history-kline.html):
  cursor pagination and explicit adjustment/session options. Later retrieval
  is not evidence of what was available at a prior decision time. Tag all
  recovery with actual receipt/commit visibility; no point-in-time history claim.
- [Global state](https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-global-state.html):
  quote-login status and server version are exposed. Login success is neither
  symbol entitlement nor continuity, finality, accurate clock or complete coverage.
  Do not query trade login/account fields for this research; redact broad responses.

Decision: OpenD remains a candidate for raw observation only. Current FINAL-only
consumer is not demonstrated feasible on this feed. Unknown evidence blocks;
never promote FINAL because a minute elapsed, another candle arrived or repeated
values matched. A weaker completed-provisional profile needs separate approval.

## Future source contract, required before any connection

Use a separately approved quote-only plan: US.SPY/US.QQQ, K_1M, regular session,
explicit adjustment/session options (proposed unadjusted), exact SDK/OpenD build
and hashes; no alternate endpoint/provider fallback. Provider-enforced quote-only
rights must be distinguished from quote-only application code on a shared OpenD.
The owner authenticates locally only after authorization; no secrets in chat.

Bind permission/feed/delay/license authority to symbol, endpoint, versions,
session, units and validity period. Pin authoritative exchange calendar and tzdata,
including DST, early close, holiday/halt/no-trade policies. Preserve raw timestamps
and values; derive start/end in a separate reversible version. Unknown/ambiguous
mapping blocks. Independently verify opening AND closing OHLCV or obtain explicit
provider confirmation; a 390-row grid is insufficient. No missing-bar fabrication.

Record full receipt UTC/monotonic sequence, source/publication time when supplied,
clock uncertainty, epoch/request/page IDs, completion/finality evidence, exact
payload hash, durable visibility, revision identity and supersession. Availability
is no earlier than interval end, full receipt, required authority and durable
commit, with conservative clock bounds. Source timestamps are not publication
or receipt times. No original-as-known rewrite by late history or corrections.
Newer provisional evidence blocks older FINAL. Original and corrected views stay
separate. Unknown/branching/cyclic lineage blocks, not last-arrival-wins.

Disconnect, feed login loss, entitlement revocation, queue overflow, stale tail,
missing interior/tail/symbol, write failure or schema change invalidates affected
frames. Reconnect enters RECOVERING, not READY: recheck scope/rights, subscriptions,
clock, complete expected grid and source quality first. A new socket alone is
insufficient. Confirm automatic reconnect/resubscription and continuity behavior
for the actual SDK/OpenD build empirically; this review establishes no such guarantee.
No retry/backoff/heartbeat defaults authorized here: numerical budgets must be
reviewed before capture. Recovery paging must detect repeated cursors, errors,
truncation and cross-page revisions; a terminal cursor alone is not a snapshot.
SPY cannot certify QQQ or pair readiness. Distinguish closure from transport silence.

## Implemented offline subset

adapter.py is a pure, fake-only eligibility model accepting trusted frozen typed
SYNTHETIC envelopes. It has no SDK, transport, credential, file/database writer,
engine call, detector integration, CLI live mode or connection option. MOCK_READY
returns IDs only, never a real engine-ready assertion. Synthetic UTC integer
microseconds are used; fixtures compress a minute to 60 units for readability.
Authority names/health events are fixture attestations, not provider verification.

22 tests cover causal time AND sequence cutoffs, receipt equality, later commit
and authority visibility, uncommitted replacement blocking, provisional/no-final
fallback, completion separate from finality, revision roots/branches/cycles/orphans,
input reordering, conflicting identities, missing grid/tail/whole symbol, finite
positive OHLC and nonnegative volume, disconnect/degraded/recovering dispositions,
late recovery, immutable earlier results and rejection of LIVE context.
The grid is independently supplied; model does not discover source completeness.
VALIDATED is explicitly supplied after recovery, not calculated or inferred here.
Identical fixture receipts are semantically deduplicated; durable raw receipt
retention is not implemented. All known symbol graph faults conservatively block.

Not implemented/tested here: real wire/schema parsing; scope-bound authority
validation/expiration/revocation; timestamp mapping/DST/calendar; staleness/clock
uncertainty derivation; pair status; paging/queues/backoff; durable capture, hashes,
crash/disk-full recovery or power-loss guarantees. Frozen dataclasses rely on the
typed tuple/bytes contract and are not an adversarial input boundary. No claim to
complete PR42's matrix. These are follow-up offline work before a provider adapter.

Run python -B research/feed_contract/run_checks.py. Its inherited OfflineGuard
is active before test discovery, prohibiting network/process activity and existing
DB access. Isolated Windows/Linux Python3.11 CI runs this subset plus the unchanged
54 reconciliation checks and exact88-case evidence reproduction. Existing guarded
158-test workflow and presentation smoke remain unchanged. Counts are separate
suites, not a cumulative union of all draft PRs.

Test-first commit 1259b89 records missing-module failure before implementation.
First implementation found two test fixtures whose expected tail exceeded the
cutoff; corrected cutoff to 200 without weakening the model or coverage assertion.

## Remaining approvals and gates

Before any live connection: explicit bounded provider-evidence authorization;
verified account-specific API and storage license, source/build/config identity;
reviewed timestamp/calendar/clock/completion/finality contract or approved raw-only
scope; capture directory, duration/request/storage/retry limits, stop conditions,
local authentication flow and redacted evidence plan. Credential requests, paid
activation and provider correspondence are not authorized by this milestone.

Before detector integration: accept/revise recommended S0 definitions; complete
and review remaining protocol/adapter matrix; freeze numerical operational limits,
source/finality policy, labels/horizons and independent evaluation design. Owner
approval of a recommendation is not evidence that a feed meets it. No paper or
live orders, trading, deployment, merge/retarget or protected dashboard changes.
Rollback: close the new draft; no existing entry point imports these additions.
