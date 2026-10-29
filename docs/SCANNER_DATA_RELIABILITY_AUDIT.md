# Scanner data reliability audit — 2026-10-29

Read-only source audit authorized directly in coding chat, following PR19 priority
comments6496274312/6496289595. No ingestion behavior, providers, databases, research,
calculations or trading changed. Sidebar implementation deferred.

## Pinned evidence

Main b0ad02dc996b00406e7da08fb33b6382f658ea40; entry point
raccoon_dashboard_v1_5_14.py blob fb9e1309823af269ebe2383517b29d79f0762a89.
price_action_engine.py blob7a46402cf8a27110e0a9c6b1646820779a0687bf;
market_intelligence.py blob7662b1a3ccdd836b7ffd2161a1a89564c3d7498f;
test_candle_ingestion_characterization.py blob4a7f3139d7ae8324d6348fc866737befd803c484.
Remote files read at that commit; local copies used for line inspection/tests.
Prior handoff head16bd05f5d694d7d2d472ff3d9ddf218ba32c0cad,
handoffblob09e826b23f7fde82d16bab7c4a102ed91b2b4503,
knowledgeblob6427019f678a58b67a63b3994df6009539904fb4 remain unchanged.

## Verified source findings

1. Normal single-day and range workers discard the history pagination key
(entry708–752 and1045–1075). A successful first page is not proof of complete history.
Existing fake-provider tests explicitly demonstrate ignored pagination, gaps,
duplicates, empty QQQ success, malformed OHLCV acceptance and partial failure behavior.
2. Both filters exclude16:00 and retain09:30 through15:59; no timestamp rewrite.
The single worker excludes current/future minute stamps today, but does not require
each returned date to equal its requested session. Range does enforce requested date.
The range worker lacks the minute cutoff, **but public fetch_range rejects end>=today
ET before dispatch** (1027–1043). Do not describe today's range as a normal UI path.
Completion under either timestamp-label convention is not established by these filters.
3. Weekend logic is weekday-only; no exchange holiday/early-close calendar. Clock is
captured before requests, not actual per-bar information availability. Responses do
not establish finality or revision arrival time. Moomoo start/end labeling remains
unverified; a390-bar shape is hypothesis support, not authority.
4. Normal ingestion converts tofloat without a finite/positive/consistent OHLCV gate.
Duplicates/missing minutes are retained by workers. market_intelligence filters some
invalid inputs and deduplicates by raw stamp, but does not provide immutable revision
custody; price_action_engine uses supplied row order and per-symbol history without
session reset, and lacks comprehensive finite/positive validation.
5. refresh_intelligence (158–196) merges DB+memory bysymbol/raw stamp, memory wins.
Date-only stale check uses max session across symbols: one current symbol can mask
another's older session, and same-day hours-old data is not rejected by a per-symbol
age rule. On fetch/CSV failure status changes, but old loaded values/labels may remain.
This is warning behavior, not a comprehensive fail-closed downstream eligibility gate.
6. CSV latest-bias tiles (1082–1097,1136–1160) trust last matching file row and arbitrary
bias text, using substring symbol matching rather than exact normalized symbols.
No timestamp ordering, signal allowlist, per-symbol age or source authority is required.
File mtime tracks refresh, not event freshness or original information availability.
7. Scanner launcher (find_scanner/start_scanner near1170 onward) delegates to a selected
external raccoon_radar_v3.py, normally under Downloads. Its actual runtime source,
hash/version, provenance and behavior were not inspected or launched in this audit.
Thus the on-disk external scanner is UNVERIFIED; dashboard CSV labels do not demonstrate
reliable live SPY/QQQ sentiment.
8. News, economic events, VIX/yields/breadth are explicitly UNAVAILABLE in the UI
(152–155). SEC filings are a separate evidence lab, not a verified real-time news feed.
No connected news source or validated news sentiment is demonstrated. This explicit
absence should be preserved, not filled with inferred or synthetic sentiment.
9. Normal successful candle events call persist_history; strategy_validation.store_candles
upserts bysymbol/time with conflict UPDATE and no revision provenance. Inspection did
not invoke those paths or open any existing database. Fetch-time metadata is not proof
of historical availability. Existing connection-context use also warrants explicit-handle
lifetime review in these paths, separate from already-fixed diagnostic connections.

## Ranked proposed fixes — separate implementation approval required

P0: Freeze reproducible source/availability contract first. Identify external scanner
artifact with owner-supplied source/hash without launching it; characterize CSV symbols,
time zones, ordering, missing/stale/unknown bias and stale-label retention with synthetic
fixtures. Define per-symbol freshness/session states and fail-closed candidate admission.
Never promote a CSV bias string into validated sentiment. Preserve old evidence visibly
as historical, separate from current eligibility.

P0: Review canonical completed-candle adapter and authority gates before ingestion fixes.
Specify immutable raw response/request/evidence hashes, endpoint/SDK/OpenD version,
entitlements/session/adjustment/timezone flags, pagination completion/loop detection,
per-page errors, exchange calendar, exact raw-to-interval mapping, completion vsfinality,
per-bar receipt/revision availability and deterministic exclusions. No silent shifting.
Test exact16:00, delayed responses/revisions, duplicates and partial symbols first.
Whether16:00 should be retained requires mapping evidence; simply including it is not
a reviewed correction. Missing authority means UNVERIFIED/UNAVAILABLE.

P1: Read-only quality diagnostics per symbol/session: finite positive OHLC/consistent
ranges, nonnegative volume, duplicates/conflicts, missing expected intervals under an
explicit calendar/mapping, incomplete pagination and sessions. Report exclusions.
Append-only source/revision provenance design must precede persistence changes; never
migrate/rewrite original research stores under this authorization.

P1: Source selection decision record before any integration. Price/volume candidate is
the existing OpenD history endpoint, subject to verified entitlement, coverage, adjustment,
timestamp authority and locally documented versions. News candidate must be a licensed
timestamped publisher/aggregator with original publication, first receipt, corrections,
deduplication, ticker association and redistribution/retention terms. SEC is a filings
source only. Owner must approve vendor, permissions, cost and budget; current prices,
licensing, subscriptions and access have NOT been verified or purchased. No vendor
recommendation or performance promise is made here.

P2: Only after provenance/availability review, compare technical directional hypotheses
and separately sourced news facts against frozen chronological/out-of-sample data.
Distinguish intraday momentum from daily trend, report conflicting SPY/QQQ directions,
correlated sessions, warmup, missing-data exclusions and availability unknowns. No replay,
study, profitability result, strategy threshold change or paper/live bot authorized here.

## Validation and outstanding decisions

Existing15 ingestion characterization tests use fakes/controlled clocks; included in
the69-test guarded offline suite, passing locally on Windows3.12.14 during this work.
Tests establish current application behavior only, not real provider semantics.
No GUI dashboard, OpenD, SEC, news, paid feed, external scanner, history acquisition,
database access or market study was executed. Windows/Linux documentation-PR baseline
CI is reported separately in PR19 when completed.

Needed decisions: approve one bounded next test-only scanner/CSV characterization
work order; provide external scanner source identity; review adapter timestamp and
historical availability authority; choose evidence-custody and calendar policy;
approve any later fixes/source license separately. No merge/deploy/real records.
