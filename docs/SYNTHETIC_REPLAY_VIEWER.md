# Synthetic-only Raccoon Radar vNext replay/viewer
Status: PROTOTYPE / RETURN FOR REVIEW. Not a live scanner or a historical study.
Owner scope: direct coding-chat approval of the bounded FINAL-only PR31-profile replay/viewer, consistent with PR19comment6504026116. Original app/dashboard/research and protected PR heads remain unchanged.

## What this launches
A separate read-only Tk window with scenario selection, Previous/Next, a manual minute slider and arrow keys. It displays synthetic SPY/QQQ candidates, calculation observations, quality/failure reasons, canonical times, unchanged raw stamps and evidence identities. Result text cannot be edited.
No data-file loader, provider/client/SDK, network, credentials, subscription, orders, broker/paper/live execution, outcome labels, trade simulation, cooldown or P/L. No timer/ambient clock, automatic playback, alerts or persistence. Closing the window destroys only this new UI.
All seven scenarios and40 cutoffs are evaluated in memory BEFORE Tk widget creation; callbacks only select immutable cached results/render text. Startup can take several seconds. There are no worker threads or deferred callbacks.

## Launch
From this branch's checkout/snapshot, use Python3.11+ with Tk:
```text
python raccoon_replay_viewer.py
python raccoon_replay_viewer.py --text --scenario provisional --minute 35
```
Text mode works without Tk/display. GUI mode reports display/Tk initialization failures with a --text suggestion and nonzero exit. Other program defects are not broadly swallowed.
Supported options are --text, --scenario and --minute1..40. No external input path or provider switch. Python's ordinary import/runtime remains trusted; this is not a hostile-code or filesystem sandbox.

Current local isolated development entry:
C:/Users/louis/OneDrive/Desktop/Codex/.sprint/synthetic-replay-viewer/raccoon_replay_viewer.py
No original Raccoon Radar folder was installed into or modified. The absolute entry path can be passed to the same Python interpreter from another working directory.

## Profile and dependency identity
This PR stacks on PR34 ef749d88ae092aec4cd42dd34703539d84f053c9, retaining its exact PR33 canonicalizer and pinned PR31 numeric kernel:
- PR31 reference24a5c5de529f99992ec331f6ea91c39c1f61fa6e, sourceSHA2565e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29.
- PR33 b7dd5e5100c2823701c8de639fc0e9048adde80e.
- PR34 ef749d88ae092aec4cd42dd34703539d84f053c9.
No changes to these modules/tests/fixtures, their original FINAL-only rules, formulas or thresholds. This is not a replacement for the PR31 root module or its synthetic observation store; only the PR34 pinned numeric consumer is invoked.
Profile PR31_FIRST_CLOSE_EMA_35_FINAL_ONLY uses first-close-seeded EMA9/21,35-bar warmup, prior20 volume mean excluding current, HLC3 volume-weighted candle proxy and the existing conjunction. MIXED is not a candidate. All actions WAIT. HLC3 is not trade-level VWAP, and relative volume is not a confidence score.
PR13/PR18 use a different seed/warmup and OR/pattern study definition. This prototype does not implement, freeze, run or validate that historical study. No new signal thresholds/arms or finality relaxations.

## Fictional input and fail-closed presentation
synthetic_replay_demo.make_demo supplies exactly SPY/QQQ in a fictional40-minute UTC session on2026-10-23, not an actual exchange calendar or price history. Deterministic OHLCV sequences are invented. UTC09:30 here must not be read as New York09:30.
Scenario IDs: conflict, aligned, mixed, provisional, gap, partial, unknown.
Authorities, synthetic clock uncertainty0, completion/finality and120s event/knowledge/30s delivery parameters are fixture claims ONLY. Receipts occur1second after each interval solely as explicit synthetic data; not an inferred provider delay or approved policy.
Provisional QQQ at minute35 remains PROVISIONAL and blocks forwarding; it is never promoted to FINAL. Missing/partial/unknown-availability data blocks, with no fills, fallback candidates or fabricated knowledge.
Inputs are immutable tuples/frozen records. Pure replay accepts exactly one SPY and one QQQ Series, an explicit strictly ordered aware microsecond grid (1..120 steps), and synthetic=True. Real bundle markers and malformed/unordered grids reject. Invalid canonical data yields blocked reports; invalid caller schema may raise rather than fabricate a result.
No general revision supersession resolver is introduced: visible conflicting versions still block under inherited rules.

States:
- DATA_BLOCKED: canonical source/calendar/completion/finality/visibility/quality gate failed.
- PROFILE_BLOCKED: canonical frame exists but consumer warmup/volume/other profile condition prevents evaluation.
- NO_CANDIDATE: valid canonical data and evaluated MIXED/no conjunction.
- CANDIDATE: synthetic BULLISH/BEARISH research observation, always WAIT.
Pairs distinguish PEER_DATA_UNAVAILABLE, PEER_PROFILE_UNAVAILABLE, BOTH_NO_TRADE, SINGLE_CANDIDATE, matching directions and CONFLICT. Conflicting symbols retain their own original observations; no consensus/majority vote.

## Determinism and availability
Each requested cutoff re-enters canonicalize and the sealed pinned bridge; no mutable indicator cache or accumulated state can leak future values backwards. Declared knowledge is filtered before unavailable payload quality; unknown knowledge remains blocked.
The view displays only canonical visible rows/calculations, not future payloads. Input/run hashes bind complete immutable supplied evidence, including excluded future observations; therefore they can change when later evidence changes. Per-point decision_hash binds visible frame/consumer state/reasons, intentionally excluding future payload identity. It remains invariant in late-row/revision regressions; full audit hashes need not.
Hashes identify content under the typed serializer, not authentic provider authority. Version/profile constants and pinned dependency identities do not attest the Python code currently loaded by an adversarial caller. Trusted local source execution remains a prerequisite.
No original historical availability or provider semantics have been established. Synthetic markers do not authenticate whether arbitrary caller-supplied data are fictional; no real-record input path is provided.

## Regression evidence
Initial test-first commit e10233984877e42ae8c3001f3080aa656481e253:22 missing-module errors before implementation.
Extended test commit a55e46518e6a484424da53390b5a0f3f286270c4 covers fractional receipt, delayed revisions and display unavailability. Local mocked headless error reproduced1ERROR before the GUI failure handler fix; afterward handled with exit2/--text suggestion. A local patch-assembly syntax error was corrected before reproduction; it is not engine-defect evidence.
26 new methods plus inherited130 = **156 guarded tests**, local WindowsPython3.12.14 PASS. Reverse full-suite order also156PASS. CompilationPASS.
Coverage: strict synthetic/typed/pair/grid bounds; all9 valid pair states; warmup versus data block versus MIXED; provisional/partial/gap/unknown; exact microsecond boundary; late invalid payload/revision invariance; immutable results/inputs/Decimal state; no core I/O/provider/UI imports; blocked frame no numeric call; display projection; text CLI/no external path; controls model, headless handling and calculation-free cached scenario changes.
Windows Tk smoke: root creation/update/close, disabled result Text, Next movement, scenario change and displayed FINALITY_UNVERIFIED all PASS. This is a bounded lifecycle/control smoke, not exhaustive visual/accessibility validation.
Linux GUI has not been launched; CI is headless and does not claim Linux Tk/display validation. No screenshot, GUI integration or real data/provider test is claimed.
Windows/Linux Python3.11 CI uses the unchanged inherited workflow; exact final head/merge checkout, jobs and results will be returned on PR19 and this PR description. This document is committed before that CI completes.
The156 suite =69main+41canonicalizer+20bridge+26new. It does NOT include PR31's separate25 root/store tests or PR35's4 rehearsal tests; do not call it the185-test cumulative union. The inherited pinned-reference conformance/AST tests still run.

Local log SHA256:
- replay-after.log: 74f9e9edd385aabfcc47651bc54b821ac5a86668037fc17a8044ec4feacf3158
- replay-before.log: e48d6a55b7b240129f68a2cc22f137bb0b69c49202edcec37afb3c2809ac1a77
- replay-final-156.log: ab503fccef98e45eade3d976fbe5a9a3c530fa6458697015e105b62511e819ad
- replay-final.log: c893fad698a17b3c220dc1ed39874116417e976aade4b0848b94cfed2d9cffda
- replay-gui-before.log: ffccec5403ccec19d89d0c12940bace7f0b89f3f2fb98e4781890ac9574c380c
- replay-gui-reproduced.log: f0bca4a057fd573a9c02515655363d725bcfc19c88510e4cb28398f9d95b4aed
- replay-reverse.log: bc90ce8ce811599ba6183dc4013f8407323075669c516436156bab57ede32858
- replay-text-smoke.log: 20ef6fc09691b50ba40942b93cb30de356003662ff207fdb5d7796592168020a

## Remaining gates
No approval to merge this stack or PR35/36, retarget, deploy or wire the original dashboard. No provider/OpenD connection/history retrieval/capture, real records, research DB/CSV mutation, source timestamp rewriting or study execution.
Actual source authority/SDK/build/entitlements, raw interval mapping, calendar exceptions, clock/custody, completed versus final, original availability, adjustment vintages and real freshness remain unresolved. The real-world state stays unavailable.
Next separately authorized work could review this bounded UI/profile/availability contract or add selected synthetic cases. Provider capture, completed-provisional research, labeling/study logic and integration remain separate decisions. Preserve existing evidence and report changes/failures honestly.
