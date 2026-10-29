# vNext 1.2 synthetic market-structure prototype — results and limitations
Status RETURNED_FOR_REVIEW; no merge, integration or deployment.
Direct human engineering instructions authorize this isolated specification/prototype/fixtures/tests stage. PR19 is the shared return channel. Separate research/market-structure-v12-synthetic branch stacks on unchanged PR33 b7dd5e5100c2823701c8de639fc0e9048adde80e. No dependency on or modification to PR37/vNext1.1, its viewer/engine, PR31 EMA profile or original dashboard.

## Deliverables and reproducibility
- MARKET_STRUCTURE_V12_SPEC.md: fixed initial formulas/defaults/transitions, timing/state/pair contract and acceptance matrix. Initial pre-implementation spec commit d26c34a888985bd5526e70b83784808eb320e64a; subsequent clarifications append without threshold tuning.
- market_structure_v12.py: pure immutable FINAL-only/as-of structural prototype, explicit versioned Config, state/history/seals, measured trend/range, reversal/continuation/watch/failure/invalidation, and independent aligned symbol comparison.
- market_structure_v12_scenarios.py:26 deterministic invented paths, integer price reflection for mirrored cases, complete fictional UTC source/clock/calendar/custody declarations and text-only demo. No external input loader, network or persistence.
- test_market_structure_v12.py:39 regression methods.
- evidence/MARKET_STRUCTURE_V12_SYNTHETIC.json:52 final per-symbol fixture records, explicit config/source hashes, prior local development artifact hash and deterministic semantic identity. These records are not independent trials and have no success/profitability rate.

Run with Python3.11+ from this branch/snapshot:
```text
python -B offline_checks.py
python -m compileall -q .
python market_structure_v12_scenarios.py --scenario bullish_reversal --peer bearish_reversal
```
Demo prints strict JSON structural decisions and CONFLICT for those two mirrored examples. It does not execute trades, calculate labels/P&L or run a historical study.
Local isolated snapshot: C:/Users/louis/OneDrive/Desktop/Codex/.sprint/market-structure-v12. It is not installed into the original Raccoon Radar folder; no UI mount or v1.1 modification.

Final synthetic artifact semantic identity: f4c9a9924713aad9e352b022f40deacdac754663b5533619f3f0d7eddda6f775.
Recorded LF source SHA256 (Windows Git working-tree newline conventions may differ; remote blob preservation is checked separately):
- market_structure_v12.py: 71567736bfd890ef87789750fcf2f87e18cfa4fe67a1edf7a3f4870dd0a64e30
- market_structure_v12_scenarios.py: 3d70c301ecc6afc444bf12b963ee3fa996f084e266f26452b7161954f7d67bd0
- test_market_structure_v12.py: a3e183b0929d417d7582e81898d390c26eab7801931191860adea69f0e011a40

## Observed validation
Local WindowsPython3.12.14 **149 guarded tests PASS** =69main+41inherited canonicalizer+39new. Reverse-order full149PASS; compilationPASS; text demo strict JSON parsePASS.
The copied canonicalizer fixture was restored only in the NEW disposable snapshot to the exact pinned Git LF bytes before tests; original research/source files unchanged.
A shell-side smoke inspection initially assumed UTF16 for redirected JSON; reading the existing bytes with the JSON decoder succeeded. The CLI emitted valid JSON; no prototype/source or earlier evidence was rewritten to address that inspection mistake.
Windows/Linux3.11 CI inherits the unchanged workflow. This document is committed before final CI; exact final head/base/merge checkout, run/job URLs, versions, counts and conclusions will be returned on PR19 and this PR's description. Local results are not substituted for CI.
This149 suite excludes PR31's separate root/store25, PR34 bridge20, PR35 rehearsal4 and PR37 replay26; do not call it full cumulative vNext integration.

| Invented case | Demonstrated contract |
|---|---|
| Bullish/downtrend and bearish/uptrend reversals | Qualified frozen range -> opposite close breakout watch -> later retest + required consecutive closes -> structural confirmation; mirrored boundaries/directions |
| Both continuations | Original-trend close breakout classified separately |
| Continuation reentry, both directions | Wrong-side tolerance crossing clears current direction and appends invalidation; earlier breakout remains recorded |
| False close breakouts, failed retests | Failure reasons retained, never promoted to confirmed reversal |
| Confirmed reversal subsequently invalidated | Immutable earlier confirmation and later invalidation coexist |
| Wick-only or two-sided excursions | No close confirmation; two-sided ordering remains ambiguous |
| Prolonged range / retest deadline | Exact allowed boundary and strict expiry/timeout behavior |
| Insufficient/weak trend/no contraction/no overlap/too-wide/zero-width | Explicit insufficient reasons and nullable undefined ratios |
| Gaps/partial/provisional/incomplete/unknown/duplicates/invalid OHLCV | No eligible direction/range promotion; source failure distinct from valid structural rejection |
| Future payload/revision and changed accepted prefix | Earlier decisions invariant; full audit changes; accepted-prefix changes block instead of repainting |
| SPY/QQQ ordered pairs | Independent decisions retained across all9 active-direction combinations plus invalid peer |
| Config/context/symbol/version and Decimal mutation | Reuse mismatch rejects; fixed arithmetic unaffected by caller rounding or DefaultContext traps |

## Before/after failure evidence
1. Test-first commit6be5b380c0f78fc715388d0ce67142ce30be2b8b:27 methods /34 missing-module errors including subtests before detector existed.
2. Initial local prototype passed27. c8c59ccbb0e14249231652d02604ebc3938c980b expanded36 methods:2FAIL+1ERROR for undefined ratios rendered Infinity, silent RAW_AUDIT blocking reason, and absent model-version binding. These contracts were repaired without changing hypothesis thresholds.
3. 70af18e6f2a4455bc787ab03deef4f5ea11abf07 added impossible confirmation/deadline and mutable Decimal.DefaultContext trap cases: targeted2 methods/1FAIL+1ERROR before repair. Explicit invariant validation and private traps/flags/clamp fix both.
4. Initial core preserved at24e61783e21453dfcfd4ac6fe0ee05e9ca116ff4; finite/versioned/arithmetic repair at e427fae1abb59106d1e0ff6ad899ea91acecf6d5. Exact local test source subsequently preserved.
5. Continuation test31585dcbbf5355f0e325c603ef43ca1bb56330b7 + mirrored fixtures9c1257ed4cc4ae162d0ac75a7681b1089adee83f reproduced1FAIL: stale continuation after reentry. Repair1092ca0a3214feea4e04d17ef2524a927f4e71ab invalidates current direction, preserving historical breakout.
6. Final39 new /149 full guarded methods PASS. Assertions not skipped/weakened, no real/provider data or parameter optimization.

Local log SHA256:
- structure-after.log: 50d4b0e3ba78579c2d396e864ca60b81be181e3ffa5b05dbea138b8a40ddd8d1
- structure-before.log: 188ce0528c6a53befcf8754d471e421e65a2691c1e0cd4a21e1bb26d44132172
- structure-config-before.log: 40c0acbc2f9b7bd024c4c44064ad264dc3fcee7e940b6ccb301641b06be58bf7
- structure-continuation-before.log: 20166625c21c456d71e19fef9e5b93b1dccbee16adb07f7aa2723135f6c8993d
- structure-edge-before.log: f54a205af525a985aa3630b1f8ebe691cb68790b5c1e295e660b4840304b9eaf
- structure-final-149.log: 4c6668d19daa8f36e46c49f0c3a3a75aa1b109cdee07519c93cf8cae085f827a
- structure-final.log: 6ad80cbf1f0f8aea1f4571efe1fd5a7e67215f4b87a6bf282545c452833a7b91
- structure-first-implementation.log: 70ac9f10b4bdf384140939bd8a839610d08a44ec090bdaab4af95b426bcd4579
- structure-reverse-149.log: 8ffd6423c10460d2601a8db9321e581cf34a5b0b56252265d4be5257bd0847d1
- structure-reverse.log: 52b9b12d2e0ad83acf714e50abbf5e081b7df5faa9bc2fee6e01c0e1bf9af787

## Limits, unresolved evidence and next review
- All names are operational hypotheses. CONFIRMED_STRUCTURAL_REVERSAL means the explicit breakout/retest/hold definition, not an objectively verified future market reversal, executable signal or profitable trade.
- Fixed illustrative thresholds were specified before implementation/fixture runs. Integer synthetic paths were constructed to exercise predicates, not to estimate predictive power, optimize settings or establish robustness. No genuine point-in-time data was acquired or evaluated.
- State is append-only in memory, not a durable research database/capture/recovery implementation. A caller must retain immutable assessments for audit. Seals/hashes detect identity changes, not malicious forgery, real source authentication or historical truth.
- Visible conflicting revisions block. Changed previously accepted candle/metadata identities block; no general revision resolver, retroactive state repair, last-row-wins or automatic reset. Start a separately identified run for a revised research view, preserving the prior one.
- Batch detections use current knowledge cutoff and separate trigger interval time. They are retrospective structural inferences made now, not claims those events were available/detected at their candle endpoints.
- Blocked requests preserve prior private state but expose no current eligible direction. The canonicalizer's global schema/custody gates still precede payload visibility; unchanged inherited limitations apply.
- Data availability, FINAL/completion and source/calendar/clock policy are declared synthetic fixture claims. Authentic SDK/build/feed/entitlements, interval mapping, auctions/early-close/halts, adjustment vintages, original availability and finality remain unverified. Fictional UTC fixtures do not validate actual SPY/QQQ calendars or provider behavior.
- No comparison to EMA strategy performance was performed. PR31's EMA seed/warmup, formulas and thresholds remain untouched. PR13/18 historical hypotheses and PR37 remain separate.
- No broker/API/feed/credentials, raw research rewrite, production DB/CSV, order/simulation/P&L, alerts, GUI integration, merge/retarget/deploy or monitor restart.
- Next: review the exact structural definitions, state lifetime/invalidation, availability evidence and test matrix. Any genuine point-in-time validation needs separately approved source/custody, frozen protocol/splits/access policy and execution authority. Any UI integration or merge needs separate approval. No provider-semantic or profitability promotion follows from green synthetic CI.
