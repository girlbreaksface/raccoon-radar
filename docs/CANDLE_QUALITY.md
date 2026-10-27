# Synthetic candle-quality diagnostics
New API: `candle_quality.audit_candles(rows, expected_start="09:30", expected_end="15:59")`. Bounds are inclusive raw-stamp hypotheses, explicitly supplied by the caller. Use 09:31–16:00 only as a separately labeled candidate; use a verified early-close schedule when applicable. This module does not choose a timestamp convention or query an exchange calendar.

The function is pure and accepts candle dictionaries in memory; no database/file/network API or automatic repair is used. It reports invalid row indexes/reasons, duplicate timestamp counts, out-of-order transitions, outside-bound rows, missing valid minutes, expected counts, valid unique counts and per-symbol/date coverage. Symbols are normalized only in diagnostic grouping, never written back. Zero volume is permitted; prices must be finite and positive, volume finite and nonnegative, and OHLC ordered. Unparseable symbol/timestamp records are global invalid rows and cannot be attributed to a session. Entirely absent symbol-days require a caller-supplied schedule outside this API.

Coverage means each declared minute has at least one valid row. It does not establish uniqueness, absence of bad duplicates, trading-day identity, completed candles, correct provider interval semantics or predictive value. The separate quality_ok flag additionally requires no invalid OHLCV, duplicate, ordering or outside-bound issues in that session. Global invalid rows must always be reviewed. Raw timestamps and inputs remain unchanged.

## Synthetic verification
Ten new tests written before implementation cover full/partial coverage, an interior gap, conflicting duplicates replacing a minute, NaN/infinity/nonpositive prices/negative or malformed volume/invalid bounds, zero volume, malformed input, ordering, outside rows, symbols/dates, explicit early-close bounds, deterministic reports, input preservation and empty input. Initial run failed because the new API did not exist. After implementation the initial 20-test audit snapshot against main 342c7389 and compilation pass on Windows/Python 3.12.14. CI results are recorded in the PR. This is new diagnostic behavior, not a change to market calculations or provider ingestion.

Run: `python -B -m unittest discover -v -p "test_*.py"` and `python -m compileall -q .`. No production research data is needed. The existing five persistence tests use only disposable temporary fixtures. Draft PR #1 remains separate review work. PRs #5/#8/#10 are now merged; do not count other unmerged tests as part of main.

No real research store was opened, migrated, modified or deleted. No provider semantics, live feed, GUI or trading execution was tested.

## Standalone CSV report (no GUI/SQLite integration)
Run:
```text
python -B candle_quality_report.py --input synthetic.csv --expected-start 09:30 --expected-end 15:59
python -B candle_quality_report.py --input synthetic.csv --expected-start 09:31 --expected-end 16:00 --output new-report.json
```
The second example declares an alternate raw-stamp hypothesis; it does not endorse Moomoo end labels. For a known early-close session, supply independently verified expected bounds instead. Input requires symbol, time or bar_time_et, and open/high/low/close/volume CSV columns. No default user path or database support is provided.

The report includes the source filename and exact-byte SHA-256, all audit findings and a status: COVERAGE_MATCH (exit 0), REVIEW (exit 2), or NO_DATA (exit 2). Input/schema/output errors return 1. Coverage match applies only to the caller's declared interval and observed symbol-days. It is never a vendor confirmation, exchange calendar check, completeness proof for absent symbol-days, executable signal or trading edge. Input/source authenticity and a fetched response's completeness remain unknown.

Without --output JSON goes to stdout. An output file is created using exclusive mode; existing evidence or the input cannot be overwritten. Source bytes remain unchanged. Exclusive creation is not a crash-safe archival protocol; an interrupted new output may be incomplete. Source hashes preserve identity, not provider provenance.

Five additional synthetic report tests were written before the CLI existed. They verify gap/duplicate/invalid review findings, explicit unverified labeling, input byte/hash preservation, no SQLite call, refusal to replace source/existing output, creation of a new report, malformed/non-CSV input rejection and header-only NO_DATA. Local Windows/Python 3.12.14: all 32 tests (17 main at 0d9015cc + 10 audit + 5 report) and compilation pass. Refreshed Windows/Linux Python 3.11 CI results are recorded in this PR. The CLI remains standalone and changes no calculation, ingestion path or research database.
