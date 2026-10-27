# Chronological direction validation — dependent review proposal
Depends on direction engine PR #13. This branch targets its engine branch so reviewers can assess validation separately. Do not merge/retarget into main until the engine is approved; no merge is performed here.

## Purpose and assumptions
This is a deterministic ETF event study, not executable P/L, order simulation, options selection or evidence of edge. No real research history is supplied or accessed. `replay_session` evaluates the engine only at distinct available_at_et times <= a declared cutoff. It records as-of snapshots first; future price outcomes are separate labels.

Inputs are the engine's explicit completed 1-minute canonical rows and caller evidence. Session objects contain symbol, session_open_et, session_close_et, interval_evidence and rows. No provider labels, calendars or publication latency are inferred. Invalid outcome OHLCV/intervals, duplicate rows, missing minutes and unavailable labels remain missing; they are never repaired.

For each candidate, the hypothetical entry is the first minute boundary AT OR AFTER information availability (not the event close and not an earlier open). An exact-boundary open is an idealized research proxy; it may be unobtainable in real markets. With availability at 09:55:30, entry is no earlier than 09:56. Future entry/horizon rows label the decision; they never determine its features. Outcome = direction * (last horizon close / assumed entry open - 1) * 100. Every minute in the default three-minute horizon must be unique, valid, completed and available by the split's cutoff. Labels cannot cross session close.

A missing expected entry does not jump to a later convenient price. Greedy planned entry windows, spaced by the horizon per symbol/session, reduce repeated overlapping labels. Selection/cooldown does not depend on the realized outcome or whether it is missing. SPY/QQQ correlation and cross-session dependence remain; observations are not statistically independent.

## Reproducible chronological split
`study(sessions, train_through=..., test_start=..., test_end=..., freeze_id=..., code_revision=...)` requires:
- disjoint ordered date bounds with observed nonempty train AND test sessions;
- unique normalized symbol/date sessions; SPY and QQQ from one date share the split;
- explicit nonempty freeze/code references and fixed Config/horizon before evaluation;
- prior_inspection = UNKNOWN, PREVIOUSLY_VIEWED or DECLARED_NOT_VIEWED.

Dates between train and test are excluded and listed. Training decisions/labels must be available by train_through 23:59:59 ET; test decisions/labels must be available by test_end 23:59:59 ET. Late-published training labels cannot use holdout-period information. There is no optimizer, setup ranking or threshold selection against test results.

The manifest records normalized engine version/config, hypothesis horizon, exact caller revision/freeze IDs, deterministic full-input JSON SHA-256, split dates/exclusions, both availability cutoffs, entry/cooldown assumptions and prior-inspection status. Per-bucket results retain candidate events, feature hashes/observations, missing-label reasons, decision/NO TRADE reason counts, valid/missing outcomes and mean directional ETF movement. No confidence score, predicted probability or headline profitability is produced. The hash covers the supplied dataset representation, not raw database bytes or authenticated source provenance.

Every run remains labeled RETROSPECTIVE_CHRONOLOGICAL. A chronologically later bucket is only a test partition; caller references cannot prove it was untouched. For genuine prospective out-of-sample work, archive signed/published hypothesis/config/code/data-split manifests BEFORE opening test results, record dataset acquisition availability, prohibit retuning on that split, then evaluate a new future block. Previously inspected data must stay marked viewed/unknown. No such real-data evaluation has been performed.

## Synthetic evidence
Thirteen tests written before implementation/corrections cover next-open math, complete horizons, missing/invalid/duplicate future rows, delayed availability, unchanged past classifications under future-price mutation, no skipped entry/overnight label, shared-date splits and excluded dates, manifest reproducibility/input preservation, missing counts, invalid/empty/duplicate metadata entry cooldown and matching symbol normalization for decisions/outcomes. Additional failing-first tests caught training labels leaking past their availability cutoff and replay evaluating beyond its cutoff; both are now blocked.

Local Windows/Python 3.12.14: all 101 tests (69 main + 19 engine + 13 validation), guarded runner and compilation pass. Windows/Linux Python 3.11 CI tests this stacked branch. No actual history, provider, GUI, production DB or trading API is used.

## Decisions before real-data study
Approve canonical completion/availability provenance, proxy VWAP basis, engine conjunctions, all thresholds, entry/horizon/cooldown assumptions, independent unit of analysis and frozen split policy. Define costs/spread/slippage only in a separate reviewed execution-model proposal. Increase session/sample coverage and report uncertainty without converting synthetic examples into unsupported statistical confidence. Provider/calendar semantics and real capture latency still need independent evidence.
