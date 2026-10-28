# H-011 engineering return — calculator-first implementation

Recorded 2026-10-28 18:52:04 UTC; direct user yes in coding chat after H011 scope explanation. IMPLEMENTED_CALCULATOR / STAGED_JOURNAL / RETURNED_FOR_INDEPENDENT_REVIEW. No merge approval.

## Source and scope
[Draft PR24](https://github.com/girlbreaksface/raccoon-radar/pull/24), branch feature/h011-manual-ledger-calculator. Pinned clean main b0ad02dc996b00406e7da08fb33b6382f658ea40 verified live. Code revision **889c966941efada4bdcb3c1f0d042a02f92d880d** (later additions are evidence only). No direction/replay/test-fixture branch dependency; no existing runtime file modified. Exact main40 Python blobs+AGENTS verified before local copy; no SQLite or research data copied.

Files: raccoon_ledger.py (pure Decimal model), raccoon_ledger_ui.py (standalone Tk panel/entry point), test_raccoon_ledger.py, docs/RACCOON_LEDGER_H011.md plus this evidence package. Model blobf1f22c84ae721004f89c9d88d47d675522b052cc; UI14c252a63fa742452eaa40c8fa1b6a30790a9255; tests043fe37b0f4f0992000def3ca2f20bff39295382. Local and remote Git blobs match exactly.

[Contract/staged plan](../../RACCOON_LEDGER_H011.md) documents all formulas, manual ticks/rounding, input bounds, fees and exclusions. Immediate premium/count edits produce adjustable15%/20% references and estimated net dollars with100 multiplier. Levels rounded toward entry; actual rounded price percentages displayed. Long premium/standard contracts only; no price feeds, sounds, automatic stops or orders. Invalid inputs clear prior outputs. Reference levels are not fills or guaranteed risk bounds.

H011 permits calculator-first fallback. Existing research_journal.py blob74e4df173a53102b41188f4af0d3761af4c614b3 imports strategy_validation.DB_PATH and initializes research tables; dashboard mounts research panels. Reusing that path would touch protected research stores. Manual-ledger storage policy and lifecycle not established. Thus no persistence/dashboard mount/CSV/realized journal/daily-weekly-monthly summaries implemented; separate staged criteria provided. Reload/export tests are NOT claimed. This stage changes neither research DBs nor protected PR19 branch. Evidence and plan are on PR24; return linked in PR19 comments per work order.

## Tests first and observed development failures
Test-first d8397a79a34c6823f1ecec9dfeb7efb3488d988e: importing new feature fails ModuleNotFoundError. This establishes missing feature, not a bug in existing market calculations. Initial16 tests then17 with caller-context regression. Public percentage outputs specified to cents before implementation.

Additional new-component regressions exposed ambient Decimal context dependence: fee quantize raised InvalidOperation under precision2, then display abs() raised Inexact with caller traps. Preserved local failure logs/hashes. Fixed by isolated Context(prec=50,rounding=ROUND_HALF_UP) around arithmetic and context-free copy_abs() for formatting. Expanded assertion checks view formatting and unchanged caller precision/trap. No assertion weakened, skipped or xfailed.

Final suite69main+17new=86PASS on local Windows11 build26200 CPython3.12.14,0.634s. python -B offline_checks.py; python -m compileall -q . PASS. Existing offline guard uses disposable synthetic DB fixtures only. Local withdrawn Tk smoke PASS: construct LedgerPanel without dashboard, set premium1.00/n2, immediate0.85/1.20 display, invalid edit clears displayed stop/error, clean destroy. No GUI screenshot, human visual/accessibility approval or Linux display validation claimed.

Tests cover defaults/fees once, adjustable percentages,0.01/0.05/0.10 ticks, rounding, binary-float-sensitive inputs, malformed/NaN/inf/zero/negative values, whole-contract validation, size limits, collapsed tick levels, fee cents, high-fee negative target net P&L, caller-context independence, input immutability/determinism, notice and stale values. Arbitrary economic/tick/quote assumptions are not verified; these are synthetic arithmetic/UI-state contracts.

## Exact CI on code revision
[Run40748984013](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40748984013), checkout **360659d538b7e6f04b8fe589a9ee35bab55747ea**. Both logs explicitly merge code889c966941efada4bdcb3c1f0d042a02f92d880d into mainb0ad02dc996b00406e7da08fb33b6382f658ea40. Logs read, not inferred.

|Platform|Python|Job|Compile|Tests|
|---|---|---|---|---|
|Windows|3.11.9|[123030252211](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40748984013/job/123030252211)|PASS|86PASS,1.915s|
|Ubuntu|3.11.17|[123030251725](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40748984013/job/123030251725)|PASS|86PASS,0.983s|

Evidence-only additions trigger new exact-head CI, recorded in PR19 completion notice rather than implying this checkout includes later evidence files. Unit CI is headless model/view validation; UI compilation is not interactive GUI approval.

## Local evidence hashes (SHA256)
- initial missing-module log122a3131088686c920e71f384e34d6cd309e14b2c3301d6b9b5db341465fd2f1
- Decimal quantize failure16e629b59eee1eae54df2ed0487dea33edec6f9152253f2a81db9e6bc1b6d1fb
- display formatting failure4155c8bed1b5f5a9fe31528a28fe9779ffb351209547e1269f368ec277248fa4
- final green log216b1e19c1c9be37f9e3e0f57b108a67ff068f5b65312c3967efd7a5ce0cc268
- modelda03ec4a80d7f2a81b5520b5c251219b88ab99068e93b2bbab96dc46e4f6480f
- UI61bbd95f5b7b9e167de1ac3a920b6139c2f17f20c50e5895715b834901373951
- tests0520a777f511a9c838d6c9f408ad266bdf1d42ddb821270238c8285174ad7b28

Five synthetic reference/display examples archived in observations.synthetic.json, strict JSON. Fees are explicit total position estimates, actual-fill/persistence fields absent intentionally. Prior research evidence remains unchanged.

## Next decisions and limitations
Independent reviewer to inspect exact source/tests, rounding/fee wording and staged choice; manual visual/accessibility check before dashboard mount. Separate owner review of NEW journal store/format, immutable manual fills/partial exits/corrections, timezone/session summaries and exclusive exports before implementing stage2. No default SQLite reuse, storage migration or real-time price/sound alerts authorized. No live/delayed data/provider/orders/trading integration, deployment or merge. Protected PR13/14/19/20/21/22/23 branches are unchanged; posting progress comments is coordination, not editing their branch/PR metadata. H011 does not resolve any older independent-review/design/source/custody/merge gate.
