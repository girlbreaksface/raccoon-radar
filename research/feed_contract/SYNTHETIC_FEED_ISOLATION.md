# Synthetic stream compatibility prototype

Direct coding-chat approval: isolated offline prototype, regression tests first,
separate draft PR, Windows/Linux validation. Stacked on unchanged PR #52 head
87a9d73edf1e931094dc618570b48b3758fc014e. No existing observer integration.

## Contract

`isolate(tuple[Observation, ...], expected: Identity, synthetic=True)` accepts
only typed frozen synthetic records. Identity contains mode, provider, endpoint,
schema_version, coverage, session, interval, adjustment, adjustment_anchor and
adjustment_version. These fields are exact case-sensitive declared strings.
There is no normalization, alias, endpoint equivalence or adjustment-enum shortcut.
Missing, blank, padded, control-character or UNKNOWN/UNVERIFIED/NOT_ESTABLISHED
identity fields fail closed. Matching unknowns cannot establish compatibility.
All dimensions must match the requested identity for every observation.

Conflicting or malformed evidence blocks the entire batch with empty output and
sorted reason codes. No first/last feed winner, silent filtering or partial output.
Caller retains its immutable original records; this gate never deletes evidence.
Accepted results preserve the exact tuple/order/repeats/labels/bytes. SPY and QQQ
remain separate symbol fields; no cross-symbol revision grouping is performed.

Input bounds: nonempty tuple at most 5000 observations; each has US.SPY/US.QQQ,
a nonblank unpadded source label at most128 characters, positive integer sequence
(bool rejected), and nonempty immutable bytes at most65536. Identity strings are
at most256 characters. These are resource/schema constraints, not provider rules.
Sequence order/uniqueness and timestamp semantics are deliberately not inferred.

`compatibility=COMPATIBLE` means only that caller-declared stream fields match.
Every result still has status DATA_BLOCKED, finality UNKNOWN, completeness
NOT_ESTABLISHED. No candle, timestamp conversion, eligible feature or trade output.
Raw bytes are opaque invented fixture payloads; no SDK/protobuf parsing occurs.

## Evidence and limits

Twelve regression methods cover matching positive control, each mismatching
dimension, malformed/missing expected identity, identically unknown identity,
endpoint/coverage/anchor/version and case differences, permutation-independent
rejection, repeat/order preservation, synthetic opt-in, malformed rows, limits,
deeply immutable accepted values and determinism. Hundreds of subcases are
validation permutations, not independent statistical trials or provider evidence.

Test-first commit a2018c6d8f66bd948cbcab313bb3be7ca32d14f7 preserves the original
test contract before the module exists: inherited102 tests pass, one discovery
error for missing module (103 total discovery entries). This is evidence of an
absent prototype, not a reproduced production defect. Initial implementation
run114 had one harness failure: the helper interpreted explicit None as its default
valid fixture. Changing the helper default to Ellipsis makes explicit None reach
the guard as intended; no assertions or runtime guard were weakened. Final114 pass.

Run `python -I -B research/feed_contract/run_checks.py` (114 methods total),
`python -I -B offline_checks.py`,
`python -I -B research/reconciliation/run_checks.py`,
`python -B research/reconciliation/verify_evidence.py` and compileall.
Existing feed CI discovers the tests on Windows/Linux Python3.11/3.12.
Exact local/CI checkout identities and results are recorded in the PR conversation.

This is not an authenticated provenance boundary, general input-security sandbox,
production adapter or solution for absent historical availability. A caller can
lie in every string. Coverage/session policies and adjustment versions need actual
independent evidence before real use. Opaque bytes are not checked against their
declared identities. Real schemas, corporate-action factors, clocks, availability,
calendar, finality, quote quality and revision lineage remain unverified. Explicit
synthetic opt-in and strings do not authenticate real data as synthetic either.

Existing replay/analyze still groups observations by symbol/source_label and may
report cross-feed observation deltas. That audit behavior and raw archives remain
unchanged. Nothing imports or connects the new gate to ingestion, scanner, GUI or
strategy. A future integration/reconciliation policy requires separate review
and approval; passing these tests does not authorize that step.

No provider, market-data acquisition, private capture, production database,
real-history study, options/execution model, trading, deployment or merge.
All trading remains disabled. Rollback removes only the three added files.

## Boundary coverage amendment — 2026-11-03

The twelve-method/114-total evidence above describes initial head
8d84260baa374638933b43372611741c12cb109a. Four additional regression methods
now make sixteen new methods /118 total feed tests. This test/documentation-only
follow-up checks exact inclusive5000-record/65536-byte/256-character-identity/
128-character-label limits against adjacent rejected values; embedded controls
and padded strings; malformed observed identities with a valid expected identity
in every dimension; and sorted,unique reason codes across all24 mixed-error
permutations. Local118 PASS on unchanged prototype code. These remain bounded
synthetic mechanism checks. The original completion evidence is retained; fresh
Windows/Linux CI and the new exact head are recorded in the PR conversation.
