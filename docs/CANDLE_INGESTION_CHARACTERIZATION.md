# Candle ingestion characterization (no behavior change)
Baseline: main 342c7389b735188ddf75867c1f62aca4f8176bb0. This PR adds tests and documentation only. The tests execute the actual _fetch_candles_worker and _fetch_range_worker ASTs with fake quote responses, a fixed ET wall clock, fake timezone dependency and a stub analyzer. They stop at the emitted queue event: the persistence consumer, Tk, SDK, databases and provider are never run.

## Observed behavior, not approved ingestion policy
| Scenario | Single-day worker | Range worker |
|---|---|---|
| 09:29, 09:30, 15:59, 16:00, 16:01 | Keeps 09:30 and 15:59; excludes 16:00 | Same |
| Now 12:34:45, raw 12:33/12:34/12:35 | Keeps only 12:33 | Keeps all three |
| Exact current minute boundary | Drops timestamps >= current minute for today's rows | No equivalent guard |
| Wrong session date in provider response | Can keep another date's regular-hours rows | Requires row date == requested day |
| Missing minute, unsorted rows, conflicting duplicate | Sorts emitted rows; retains duplicates; does not fill gaps | Same |
| Provider returns a pagination key | Discards key; only one request per symbol/day | Same |
| Success with SPY row and empty QQQ response | Emits success with partial coverage | Marks day successful without warning |
| QQQ errors after successful SPY response | Emits error and no partial data payload | Discards that symbol-day batch; can retain later fully successful days |
| Invalid numeric string versus invalid OHLC/NaN | Skips conversion errors; float-convertible invalid OHLC and NaN can reach raw payload | Same |
| Weekend request | Falls back to Friday; no holiday calendar | Skips weekend days |
| Hypothetical 13:00 early close with 13:01 response | No early-close calendar rule | Same |
| Request raises exception | Error event; closes context | Same |

Raw timestamps that survive filtering are copied unchanged. The tests also preserve the fake response input. "Discard" here describes the worker's output filtering, not any change to provider responses or a user database.

## Why the boundaries differ
The 16:00 exclusion is explicit in both predicates: single-day rejects hours outside 9..15; range accepts 09:30 onward in hour 9 or hours 10..15. No end-label rationale is encoded there.

Only the single-day loop compares today's timestamp to now rounded down to a minute. The range loop separately repeats parsing/filtering and has no clock comparison. Source inspection shows this asymmetry across the supplied versioned dashboards; it is consistent with duplicated implementation paths, not a shared completed-candle policy.

GitHub file history on main contains the original upload (4840bd0fc7cf5330f1aa85a97c1584147f588a1e, "Add files via upload") rather than a design discussion. Author intent and any provider rationale therefore cannot be established from the available history. The hypothesis that range fetching was intended only for prior completed days does not excuse the omission: the date-selection handler allows today. No causal claim about the original author is made.

## Verified, provisional, unresolved
Verified by 13 synthetic characterization tests: the table above, context cleanup, emitted event structure and accepted timestamp preservation. These tests intentionally record current undesirable behavior and must be updated with independently justified regression expectations when fixing that behavior. They are not endorsements or permanently frozen rules.

Provisional: 09:30–15:59 and 09:31–16:00 are candidate raw-stamp conventions. A single-day timestamp cutoff alone does not prove its bars are completed: at a boundary, start/end labeling changes the interpretation.

Unresolved: Moomoo interval semantics, SDK/OpenD flags/versions, adjustment/session settings, pagination completeness in real responses, exchange calendars/holidays/early closes, DST conversion and valid live completion times. No provider connection or independent OHLCV comparison was performed. The fake zone preserves the controlled ET wall clock and deliberately does not test IANA timezone rules.

## Test results and next decision
Local Windows/Python 3.12.14: 23 tests (10 main + 13 new) and compilation pass. Windows/Linux Python 3.11 CI runs the same branch suite; results are recorded in the PR. Opening-range integration is separately validated in PR #1; no duplicate tests are copied here.

Recommended follow-up: define and review a raw-retention/derived-session policy and a convention-aware completed-bar contract; add desired-behavior failing tests before changing ingestion. Pagination and partial-response metadata need explicit completeness states. Never silently shift timestamps, fill missing candles or rewrite history. A standalone diagnostic should flag these findings rather than infer provider semantics or trading validity.
