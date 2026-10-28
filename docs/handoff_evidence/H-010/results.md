# H-010 — malformed replay signal repair evidence

Recorded 2026-10-28 16:30:31 UTC. IMPLEMENTED_AND_TESTED / RETURNED_FOR_INDEPENDENT_REVIEW, no merge. Direct human H010 implementation approval in this coding chat is limited to unknown/missing/null/malformed signal rejection; PR19 work order6473731887 supplies scope. No broader repair/deployment/data authority.

## Pinned integration and source identities
[Draft PR23](https://github.com/girlbreaksface/raccoon-radar/pull/23), NEW branch fix/h010-replay-signal-validation, head **fa3f3640ea473cb3421b6153f424040470fdff29**. Base is unchanged H009 PR22 ae3fda66055733bde371e1b0d7887f8157cf8c7f, containing H007 repaired engine from PR21 48e184c67168724b1449ac8c36d209d4a2d72892, engine blob8a4d091a24e2ea6f80e4d24b14dcebd400cf3586. Replay source and existing replay tests from pinned PR14 328135f2695543cde96bb434aaa07201c51c0582. PR14's root replay was NOT edited on that branch; copied here into root direction_validation.py, then targeted repair applied.

| Artifact | Git blob |
|---|---|
| Root repaired direction_validation.py |649d3ce288535056e2434690cff64b2b4ec56a43|
| Unmodified original replay fixture tests/fixtures/h009/direction_validation.py |4eeaa8c1fdb595134096fa5ac13f52f8ecf82392|
| H009 tests on repair branch, loader-only change |90424bcdea3d090b64fc54fdc94cdc464ce41bb9|
| Original H009 tests in preserved PR22 |66c753a5d259f92b3843b114c439cd3427a69006|
| New test_h010_malformed_signals.py |95196488548e053693011ec0c91b7f08fb134507|
| Exact PR14 test_direction_validation.py |25a5904d8092cbf3525023909b7379274e3088ef|
| Exact PR14 test_direction_availability_review.py |b9f13f2eb90a637fbb21fdd9abc1634c3e6e57b7|

Five changed paths relative to base: root replay (copied178 lines +6 guard lines), two unchanged copied regression files, four new H010 test methods, one H009 loader line to load root repair rather than original fixture. No H009 assertion changed. Original fixture remains available and provenance identity tests retained. Original protected PR13/14/20/21/22 branches untouched. No engine, ingestion, DB, GUI, indicators or strategy thresholds changed.

## Exact behavioral contract
Only exact built-in string BULLISH CANDIDATE or BEARISH CANDIDATE may proceed to candidate event handling, using existing engine enums (not new BULLISH/BEARISH labels). NO TRADE preserves original snapshot/reasons and skips. Missing, null, unknown, empty, non-string, or other malformed signal becomes a shallow copied snapshot with signal=NO TRADE and a NEW reasons list preserving prior reasons plus INVALID_SIGNAL. Original producer result is unchanged. Quality/observations are retained, not relabeled as bad candles. Rejection happens before entry, cooldown and outcome code.

Six added lines in production replay relative to pinned source/test-first commit. Missing signal read via get(); exact type check prevents unhashable/list/dict and odd signal types from entering enum routing. No arbitrary-value coercion into BEARISH. Invalid original signal is not echoed into JSON (e.g. inf/nan); explicit reason preserves rejection evidence. No valid candidate arithmetic or label formula changed.

## Test-first and after-fix evidence
Test-first assembled commit **6835841b2d5fadb7963b721d6db91ed612409359** has original replay blob4eeaa8c1fdb595134096fa5ac13f52f8ecf82392, same tests/assertions, and loader routed to it. Local guarded Windows3.12.14:136 test methods,48 failing assertions/subtests and6 errors. These counts include malformed-value matrix subtests, not54 distinct test methods. H009 unknown/missing failures remain part of red baseline. Before log SHA25646ec69b9bcd76fcf83dd8bdbc42ee610a7fdce61cb1355ea7e308bd1d2ce61e6.

Repair commit fa3f3640ea473cb3421b6153f424040470fdff29 changes ONLY root replay by6 additions relative to red commit. After local exact-byte source/tests:136PASS,3.440s; compileallPASS. After log SHA256118f4c88f00195a9bd8b9b4589360c591283aa33225f8f26e17937d3accba13a. No assertion edits/skips/xfails used to turn green. Setup initially imported a TestCase class into new module and duplicated seven discoveries (143 tests); corrected to module import before exact136-test red baseline; initial setup log retained locally as distinct evidence.

Inventory: inherited107 engine/research tests, seven H009 consumer tests,18 existing PR14 replay/availability tests, four new H010 methods =136, with matrix subtests. Thirteen malformed variants: missing,None,empty,UNKNOWN,BULLISH,BEARISH,space/case-mismatched text,0,True,[],{},inf,nan. Both valid exact directions and overflow NO TRADE controls tested. New tests verify rejection reason, no events, unchanged quality and original producer/input records, strict JSON/finiteness; every malformed variant followed by each valid direction matches NO TRADE control events/cooldown; synthetic study has zero events and preserved INVALID_SIGNAL counts. H009 actual overflow tests remain green, including no events/outcomes and ratio null/reason.

Additional local synthetic SPY and QQQ32-bar ordinary replay checks compare complete original-fixture and repaired-root outputs: both equal, inputs unchanged. These are contract/regression checks, not edge/performance/provider claims. Exact fixtures/assertions are pinned in PR23; observations.synthetic.json archives full returned snapshots for13 injected signal cases. Input signal values represented by type/repr strings so evidence itself remains strict JSON, not nonstandard NaN tokens.

## Cross-platform CI
[Run40726530880](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40726530880), actual checkout **e37ea1461edea833ead63babd99d7626a5c0053c**, explicitly merges repair headfa3f3640ea473cb3421b6153f424040470fdff29 into baseae3fda66055733bde371e1b0d7887f8157cf8c7f. Logs independently read, not inferred from PR description.

| Platform | Python | Job | Compilation | Offline suite |
|---|---|---|---|---|
|Windows|3.11.9|[122951207078](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40726530880/job/122951207078)|PASS|136PASS,3.015s|
|Ubuntu|3.11.17|[122951207430](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40726530880/job/122951207430)|PASS|136PASS,2.284s|

Existing original PR22 remains expected114tests/2FAIL at head ae3fda66055733bde371e1b0d7887f8157cf8c7f, run40717552033, checkoutf2a8454fbc96e587a03976c5507534d14b6671b7. Its immutable red evidence not overwritten. PR20 also preserved expected red.

## Limits and decisions
The guard validates the SIGNAL FIELD of an otherwise existing engine-result mapping, including list-valued reasons. It is not a general decoder for malformed result objects, missing/invalid reasons/quality or arbitrary untrusted metadata. It does not certify provider timestamp conventions, availability/custody, finality, economic realism, future-history performance or all-input numeric behavior. Existing strategy/calendar/revision limitations remain.

Injected malformed signals demonstrate consumer protection, not an observation the current engine emits malformed enums. Valid NO TRADE warmup/data rejection and numerical-unavailable contracts remain intact. No fills/trades executed; replay events are synthetic research records. Synthetic unit study calls only, no market/historical study run.

Independent qualified review and exact-head merge approval remain outstanding. PR23 is a reviewable stacked assembly on failing evidence PR22, not permission to merge PR22 or retarget/integrate protected branches. Maintainer must separately decide reviewed integration sequence; no deployment/merge performed. No providers/data acquisition, production DB/raw research, ingestion/UI/order APIs modified or accessed. Existing guarded suite uses disposable synthetic DB fixtures only.
