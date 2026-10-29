# Scanner evidence eligibility draft — 2026-10-29

Direct coding-chat yes approved bounded test-first scanner reliability work following
PR19comment6496640404 and PR28audit552262ca78f081d3f6221d44de8784adb7b44b89.
New branchfix/scanner-evidence-eligibility from main
b0ad02dc996b00406e7da08fb33b6382f658ea40. No protected branch edits/merge.

## Shipped behavior

raccoon_dashboard_v1_5_14.py preserves imported raw CSV rows in the existing table,
but labels the two tiles VERIFIED BIAS and refuses to promote unchecked CSV text.
Each symbol is normalized exactly asSPY/QQQ orUS.SPY/US.QQQ, never substring matching.
Unknown/missing bias is UNAVAILABLE; well-formed bias without reviewed source,
availability and freshness policy is UNVERIFIED. The dashboard currently has NO such
reviewed policy/authority, so it cannot display an eligible directional bias.
This is deliberate and visible; old raw recordings remain inspectable.
Signal CSV errors clear both old tiles; failed load does not create data.
Unchanged file mtime still triggers evidence reassessment on each active poll.
No file-mtime or fetch-time substitution for event/availability time.
News/macro signals remain explicitly unavailable.

The pure scanner_reliability.evaluate_signals API can assess a caller-supplied reviewed
contract: aware controlled now; explicit finite positive max_age_seconds; sourceSHA256
and nonempty authority; availability_verified=True; per-row source binding, awareevent_at
andavailable_at. It selects latest EVENT time independent of file order, rejects future
information, availability-before-event, source mismatch, per-symbol stale events,
conflicting latest bias, malformed matching rows and missing symbols. NO TRADE is not
a candidate. SPY/QQQ conflicting valid directions remain separate, not forced into agreement.
Malformed matching rows conservatively block that symbol even if an older row looks valid.

**Trust boundary:** authority/hash/availability metadata are supplied by a trusted caller;
this function cannot authenticate a provider or prove metadata truthful. No dashboard
code supplies this contract. SourceSHA256 is a binding, not a signature or independent
review. The synthetic120-second policy in tests is not an approved production threshold.
No exchange-session, completed-candle, finality or verified historical-availability claim.

## Offline helpers, deliberately not integrated into ingestion

collect_pages accepts an injected request returning(status,data,key), status0success.
It collects raw copied rows across bounded pages, detects repeated keys/page limits,
and preserves already collected evidence on page error/exception. Pagination completion
is NOT candle/session completion, authority, or downstream eligibility. No SDK imported.
assess_candles reports finite positive/consistent OHLC, finite nonnegative volume,
requested-date mismatch, raw duplicates and raw-stamp gaps. It preserves input stamps
including16:00 and never shifts/fills/canonicalizes data. Raw gaps are NOT confirmed
missing intervals without a reviewed mapping/calendar. It always marks candle eligibility
false with INTERVAL_COMPLETION_AVAILABILITY_UNVERIFIED. Partial sessions remain unverified,
not silently completed. Rows of other exact symbols are ignored for the requested symbol.

Normal production fetch workers are **unchanged**: page keys still discarded,16:00 still
excluded; gaps/duplicates/partial sessions remain as characterized by original15tests.
Public range still rejects today/future; worker minute-completion limitations remain.
This draft fixes CSV admission and supplies tested offline building blocks, NOT a full
ingestion repair or completed-candle adapter. Review adapter authority and page/error
integration policy before a separate ingestion patch. Existing persistence/upserts,
timestamp mappings, calculations, thresholds, research stores and trade paths unchanged.

## External runtime source check

Read-only checks at2026-10-29 in the two find_scanner default locations:
C:/Users/louis/Downloads/raccoon_radar_v3.py and
C:/Users/louis/Downloads/raccoon_radar_v3/raccoon_radar_v3.py returned UNAVAILABLE.
No runtime source/version/hash could be established; no script launched. No claim about
other directories, a selected custom path, installed software or active process source.
Owner must supply accessible actual source identity before a verified binding is possible.
No credentials, providers, feeds, paid sources, market acquisition or studies accessed.

## Test evidence and remaining gates

Test-first3cab4178e216ef45be5ea3cc396a8041077d0612:16 tests,3assertionFAIL+13ERROR.
Twelve errors are missing new module; one is absent prior label-clear call.
Three assertions expose substring/unknown/unverified CSV text promoted to bias.
Additional test-firstd4b1a5e88e152e8ddb285d1b4b6c5b76cc59b536 includes20tests;
local first implementation exposes2FAIL(generator symbol loss/NO TRADE display)+1ERROR
(extreme integer policy). Final implementation resolves all with unchanged assertions.
Code revision650c34c252239537de119c6f7bc128959c7dd8b2: localWindowsPython3.12.14
**89 guarded offline tests PASS** (69original+20new), compilationPASS.
Tests invoke actual dashboard method ASTs with mocked widgets and explicit temp CSVs,
fake providers/controlled aware clocks. No Tk dashboard initialized, no DB opened.
They establish Python behavior, not provider semantics or market performance.
Windows/Linux3.11 final-head CI/checkout identities are returned on PR19 after verification.

Unresolved: external scanner source; provenance/availability authority; calendar/completion/
finality contract; reviewed freshness policy; pagination integration; underlying stale
market-intelligence snapshot and revision persistence design; real GUI/user acceptance.
No real records, scanner launch, provider connection, raw-data rewrite, trading/order APIs,
historical study, merge or deployment. Existing Ledger/calculator branches untouched.

Follow-up test-firstd6d78ccdf23b0dd44b6373c77def7021f8c294c0 reproduces one assertion
failure when an exception's message is empty. The error sentinel now checks is not None,
so every read failure invalidates the prior snapshot. Final local suite is **90PASS**
(69unchanged+21new), compilationPASS. Earlier89PASS evidence above remains attributed
to its earlier checkout. Final-head Windows/Linux results are reported on PR19.
