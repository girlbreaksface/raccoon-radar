# Raccoon Ledger — H-011 calculator-first milestone

Status: isolated draft for independent review. No merge/deployment approval. Source baseline main b0ad02dc996b00406e7da08fb33b6382f658ea40; branch feature/h011-manual-ledger-calculator. No dependency on direction/replay proposals or expected-red artifacts. Direct owner H011 approval in coding chat after review of [PR19 work order](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6477170209).

## Delivered component
Run `python raccoon_ledger_ui.py` for a standalone manual Tk calculator, or import LedgerPanel later for a separately reviewed notebook integration. It does not import/launch the dashboard, create stores, read research files or access a provider. No inputs persist after exit. Existing application source remains unchanged.

Entering premium and whole contracts updates reference levels immediately. Adjustable defaults:15% stop and20% target, user-selected manual tick0.01/0.05/0.10. Entry and estimated exit fees are TOTAL position USD, default0, explicitly subtracted. Calculator is for long premium and standard100 multiplier only, not adjusted contracts or short-option writing. The prominent notice says reference levels only, no automatic stops/orders/alerts and actual fills may differ. No quote monitoring, sounds, price-triggered alerts or broker APIs.

## Arithmetic and rounding contract
- Quantity n is whole positive contracts. Entry debit =premium*100*n + entry fees.
- Raw stop =premium*(1-stopPercent/100); raw target=premium*(1+targetPercent/100).
- Stop rounds UP to chosen tick and target DOWN to chosen tick (both toward entry). These are manual reference policies, not verified contract/exchange tick rules. Input premium must already align to selected tick. Tick rounding can change requested percentages; actual rounded price-change percentages displayed to two decimals.
- Estimated P&L at a reference =(reference-entryPremium)*100*n -entryFees-exitFees. Dollars use decimal HALF_UP cents. Percentages use reference price change, not fee-adjusted return. Target P&L may be negative when entered fees exceed the price gain; it is displayed as such.
- Reject rounded levels that collapse to entry instead of silently displaying a zero-distance target or stop. Invalid edits clear all prior displayed values immediately.
- Plain finite decimal strings only, maximum8 fractional places and32 characters. Contracts1..100000 whole digits (fractional notation1.0 rejected). Premium>0 and<=1000000; stop0<percent<100; target0<percent<=1000. Nonnegative entry/exit fees<=100000000 each, whole cents. These are bounded calculator input limits, not market realism/position advice. No currency symbols/commas/scientific notation.
- Decimal context isolated at50digits; caller rounding/precision/traps do not change calculations or caller context.

Synthetic examples:premium1.00,n2 =>stop0.85,target1.20,estimated price-only P&L-30/+40. Entry/exitfees1.30each =>estimated-32.60/+37.40,entrydebit201.30. Premium1.05,tick0.05 =>stop0.90(-14.29%),target1.25(+19.05%),price-only P&L-30/+40 for2contracts. Neither level implies an actual fill or loss guarantee.

## Why calculator first
H011 explicitly permits a staged plan when the existing architecture cannot safely support the journal without unrelated changes. At pinned main, research_journal.py initialize()/record_run() uses strategy_validation.DB_PATH and creates research tables (lines6–19/28 onward). It stores candle research runs/notes, not a manual fill ledger. Dashboard build mounts many research panels; reusing these persistence paths would cross the existing-store boundary. No manual-ledger schema/lifecycle or safe new-store preference currently exists.

Deliver the self-contained calculator now; defer journal persistence and dashboard mount to a separate reviewed step. This keeps existing research stores and application startup behavior untouched. No reload/export tests claimed for unimplemented features.

## Staged journal proposal — NOT IMPLEMENTED
1. Agree a NEW user-selected journal path and format, independent of all four research SQLite stores, with no default existing-store access. Specify UTC recorded times versus user-entered fill/session times, timezone, contract identity/multiplier, long-only scope, totals/per-contract fee units and partial-close/correction policy.
2. Manual entry/exit records represent user-entered fills, distinct from calculator references. Append-only IDs and corrections; never revise original fills silently. Realized P&L only from explicit entry/exit quantities/prices/fees, not reference touches. Define lot matching and unclosed positions before summaries.
3. Implement persistence with atomic/exclusive creation and explicit error recovery, reload validation, no data loss on truncated/corrupt records, no replacement of unrelated files. Collision-resistant exclusive CSV exports, formula-injection handling for text and manifest/code hashes.
4. Add synthetic temporary-path tests: valid roundtrip/reload, malformed records, duplicate IDs, failed writes, corruption, partial exits/fees, chronology/timezones and DST, daily/ISO-week/month boundaries, summaries and export non-overwrite. No production stores used.
5. Mount reviewed component in the dashboard only after store/lifecycle and layout review. Windows/Linux tests plus actual GUI checks; independently review before merge.

These are proposed acceptance criteria, not completed features or permission for live operation. No real-time quote/sound/approach alerts authorized. If wider changes are needed, stop for separate owner scope rather than extending H011 implicitly.

## Validation scope
Tests written before feature code; initial import failed because module absent (new feature, not a reproduced baseline defect). Seventeen final pure offline tests cover defaults, fees, adjustable percentages, supported tick increments/rounding, boundaries, NaN/infinity/malformed/zero/negative/fractional input, input preservation/determinism, caller Decimal-context isolation and stale-display clearing. Original main69 +new17 =86. Local Windows3.12.14 guarded86PASS+compilePASS. Windows withdrawn Tk smoke: panel instantiation, immediate input updates, correct0.85/1.20 references, clearing invalid edit, clean destroy PASS. This is widget-state verification, not visual/interactive accessibility approval; no Linux GUI session claimed. Exact platform CI and immutable evidence returned on PR19 and docs/handoff_evidence/H-011/ in THIS branch; protected PR19 branch is not edited under H011.
