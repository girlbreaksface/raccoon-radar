# OpenD candle contract review — November 2, 2026

Status: PROVISIONAL / UNKNOWN / DATA_BLOCKED. Documentation review only;
no provider requests, new capture, strategy integration or finality promotion.

## Scope and dependency chain

Reviewed draft #43 `fb38c328c57cb2d819adaaa706d6eaf8ceb082bb`, draft #44
`99ed196ae60b5894816fefe8c414f0007bea6e43`, and draft #45
`ed38c2812f39047e4b9ccc78c3344944634e167d`. Each child's base SHA equals
its parent's head. #43 itself depends on the unmerged reconciliation branch
`838851a3cfd248b19bd0a2a590a7bf55756eaed2`; this stack is not main.

#44 retains exact labels, receipt/row order, repeats and revisions, verifies and
decodes the full capture before selecting intersecting inclusive cutoffs, and
never promotes later-label observations to FINAL. #45 adds descriptive receipt
metrics and seal safety checks. Neither is a completed-candle adapter.

## Provider-supported facts and unresolved behavior

The official pages currently identify themselves as API documentation v10.12.
The captured SDK/OpenD version is 10.11.7108; current documentation is useful
contract evidence, not proof of identical behavior in that pinned build.

| Subject | Supported by the inspected provider documentation | Still unresolved for this capture |
| --- | --- | --- |
| Label timezone | US stock `time_key` is US Eastern, formatted `yyyy-MM-dd HH:mm:ss`. | Exact interval start/end meaning, boundary inclusivity, DST edge behavior and auction assignment. Keep the source string untouched. |
| Revisions | Callback example sends the same label twice with changed close, volume and turnover. | No inspected statement bounds late corrections, guarantees order, or prohibits open/low revisions. Example updates do not establish an after-boundary correction policy. |
| Finality | Published UpdateKL and KLine structures expose no explicit final/closed flag. `isBlank` denotes empty content. | No inspected finality watermark, immutable-after rule, correction horizon or completeness guarantee. Blank, quiet, later-label and sealed do not imply final. |
| Adjustment | `RehabType_Forward = 1`; `AuType.QFQ` means forward adjustment. The decoder accepts flag 1. | Flag identity does not certify the factors, anchor date, historical stability or adjustment correctness of SPY/QQQ observations. |
| Factor mathematics | `get_rehab` documents forward price transformation as original price multiplied by factor A, plus factor B. | Actual factors and their effective/as-of versions were not fetched. Volume/turnover transformation and push/history consistency are not established by that price formula. |

Sources inspected November 2, 2026:

- [Real-time candle callback](https://openapi.moomoo.com/moomoo-api-doc/en/quote/update-kl.html): Python return fields, UpdateKL schema, Java example with repeated label.
- [Quotation definitions](https://openapi.moomoo.com/moomoo-api-doc/en/quote/quote.html): Candlestick Adjustment Type / RehabType and Candlestick data / KLine.
- [Adjustment factors](https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-rehab.html): factor fields and price transformation.
- [Current candles](https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-kl.html) and [historical candles](https://openapi.moomoo.com/moomoo-api-doc/en/quote/request-history-kline.html): timestamps and adjustment parameters; historical request start/end dates do not define a candle label's boundary.

These are bounded findings from the listed pages, not a claim that no provider
statement exists anywhere. Do not substitute the newer REST/WebSocket API's
semantics for OpenD. No undocumented timestamp shift, factor calculation or
waiting period has been introduced.

## Engineering finding and fix

P2: `capture.verify` checked hash consistency but accepted impossible receipt
chronology and boolean sequence values. A re-sealed synthetic journal could pass
an empty cutoff despite these contradictions. Hashes do not establish schema
validity. Replay rejected some receipt-order cases, but the shared verifier did
not enforce the writer's receipt/journal timing invariants.

The verifier now rejects invalid cutoff/origin types, noninteger or negative
clock fields, noninteger sequence values, receipt/journal rollback, receipts
after their journal time, and wall/monotonic divergence over 250 ms. Checks run
before selection. Equal receipt times remain valid. Regression cases deliberately
recompute hashes and seal sizes to exercise semantic validation rather than
ordinary tamper detection. This remains consistency checking, not authentication,
UTC accuracy, latency certification or provider truth.

Validation of the fix on Windows/Python 3.12.10: 65 guarded feed tests, 158 broader
project tests and 54 reconciliation tests passed; all 88 inherited synthetic evidence variants
reproduced exactly. Full local capture replay and quality reporting ran under
OfflineGuard without importing moomoo: 1,143 receipts, six groups, QQQ sequence
386/388 open values 696.88/696.9054, and all three evidence file hashes unchanged.
Feed source syntax and whitespace checks passed. Private evidence was not uploaded.

At the reviewed original heads, GitHub reports all four workflows successful for
each PR. For #45, [feed run 41479960367](https://github.com/girlbreaksface/raccoon-radar/actions/runs/41479960367)
has four successful Ubuntu/Windows Python 3.11/3.12 jobs; broader Python run
41479960049, presentation run 41479960182 and reconciliation run 41479960407
also succeeded. Those results precede this follow-up fix and must not be credited
to a new head until its own checks finish.

Residual limitations: the capture runner is an explicitly invoked prototype,
not an expiring authorization system; SDK source hashes are recorded, not an
allowlist for all installed dependencies. Journal seals are not signatures.
Production-import isolation tests inspect direct root imports, not every possible
dynamic dependency. CI's tzdata install is unpinned; passing CI does not certify
exchange calendars. These do not justify enabling live use or strategy input.

## Required provider clarification

The SDK's [provider-maintained PyPI page](https://pypi.org/project/moomoo-api/)
lists `openapi@moomoo.com`. No authenticated provider support conversation was
available in the inspected sources; no message was sent. Suggested questions:

1. For OpenD/SDK 10.11.7108, US.SPY/US.QQQ, K_1M, RTH, does label 10:52:00
   denote the start or end? Specify inclusive/exclusive endpoints and opening,
   closing auction, early-close and DST treatment.
2. Can an older label be revised after a later label is pushed, including open,
   high, low, close, volume and turnover? What ordering, replay and maximum
   correction delay guarantees exist, if any?
3. Is there an authoritative completion/finality flag, watermark or documented
   immutable-after rule? If none, explicitly confirm that no finite quiet period
   establishes permanent finality.
4. For rehabType 1, which factor version/anchor and corporate actions apply?
   How do factors compose, affect volume/turnover, and change historical values?
   Are pushed and historical candles guaranteed to agree for the same as-of basis?

Next step: obtain and retain a version/endpoint-scoped written provider answer.
Until then retain UNKNOWN mapping/finality and DATA_BLOCKED strategy eligibility.
