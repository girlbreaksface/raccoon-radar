# Opening-range integration review
Reviewed against main 342c7389b735188ddf75867c1f62aca4f8176bb0, which includes PR #4 (migration fixture closure and Windows/Linux CI) and PR #5 (conditional timestamp wording). The five tests in this PR remain unchanged.

Current main has ten tests: five volume-discovery tests and five timestamp-evidence wording tests. This PR adds five opening-range tests, for 15 combined tests. Local Windows/Python 3.12.14: all 15 pass; compileall passes. This branch now uses main's Windows/Linux Python 3.11 workflow so PR CI checks the actual merged source view on both platforms. Results are recorded in the PR.

The opening-range tests check raw-stamp range extrema/completeness, absent 09:30, full 09:31–16:00 candidate coverage remaining unconfirmed, an interior gap and rejected invalid OHLC. Main's wording tests add evidence-conditional language, per-symbol/latest-session scoping, no-data behavior, input preservation and provisional report labels. These are complementary synthetic contracts, not independent provider confirmation.

Review decision: ready for merge as synthetic test coverage once the current Windows/Linux jobs pass, subject to explicit approval. No raw OpenD evidence is required to merge tests whose expected outputs explicitly remain provisional. Actual provider timestamp semantics, calendar completeness, ingestion filtering/pagination and trading validity remain unverified. No runtime source or research store is changed. Do not merge automatically.
