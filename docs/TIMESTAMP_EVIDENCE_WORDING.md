# Timestamp-evidence wording regression

## Scope and behavior
Only the timestamp_convention text selection in market_intelligence.calculate changes. It now uses the existing full_end_labeled predicate: exactly 390 unique consecutive one-minute bars in the selected symbol/session, starting 09:31 and ending 16:00.

When the predicate is true, the existing "STRONGLY SUGGESTED ... not independently verified" text remains. Otherwise the text explicitly says the timestamp convention is UNVERIFIED and that the selected session lacks that specific coverage. Lack of this pattern does not disprove end labeling; early closes and partial sessions may legitimately lack it. The predicate itself, raw-stamp ranges, provisional shifted ranges, all other calculations and provider ingestion are unchanged.

## Synthetic regression evidence
Five new tests in test_timestamp_evidence_wording.py cover:
- One candle, a partial opening window, a missing interior minute, a duplicate replacing a minute, and 390 start-labeled bars must not claim end-label full-session support.
- Exact 09:31–16:00 coverage retains the qualified claim and evidence flags, without independent confirmation.
- Evidence is scoped to each symbol and latest selected session; a full QQQ session or an earlier full SPY session cannot justify a partial current SPY session.
- Input rows remain identical; raw and provisional 5/15/30-minute range values and provisional/non-trading report labels are preserved for synthetic start/end-stamp examples.
- Empty data reports no data and no full-session evidence claim.

Before the fix, these tests produced eight assertion failures (including subtests) caused by the unconditional wording. After the fix, all five pass.

Draft PR #1 was reviewed at a18b3e63c3c34025177985ebb196b831cfd4cca6. Its five tests separately guard complete raw-stamp ranges, missing 09:30, provisional end-label coverage, missing interior minutes and invalid OHLC; they do not assert conditional timestamp wording. Those tests remain on their own branch and are compatible with this change.

## Validation
On Windows/Python 3.12.14:
```text
python -B -m unittest -v test_timestamp_evidence_wording
python -B -m unittest discover -v -p "test_*.py"
python -m compileall -q .
```
All ten branch tests pass and compilation succeeds. Running the exact PR #1 file in an in-memory unittest module alongside discovery yields 15/15 passing tests. The combined-test loading approach is documented in docs/ISSUE_3_VALIDATION.md; use it with this branch's discovery. A separate in-memory comparison against the unchanged main source across eight synthetic scenarios found every output other than timestamp_convention identical and no raw-input mutation.

Existing CI runs compilation and the ten branch tests on Windows and Linux/Python 3.11. Run links and observed CI results are recorded in the PR. PR #1's additional five tests are included in local combined validation, not copied into this branch.

## What remains unverified
These tests establish consistency between application wording and its existing synthetic coverage predicate. They do not prove that Moomoo timestamps identify interval starts or ends, establish real-data completeness, validate exchange calendars/early closes, or independently confirm any opening range for trading. The retained positive wording is an existing research hypothesis, not a newly validated provider claim.

Independent opening/closing OHLCV comparison or explicit vendor confirmation remains necessary, along with endpoint/SDK/OpenD versions, entitlement state, request/session/adjustment settings, complete pagination and immutable evidence provenance. No provider connection, GUI, SEC service, production research database, timestamp rewrite or trading path was exercised. Existing volume tests use disposable temporary databases only.
