# Unsent provider-support inquiry

Draft only. Separate user confirmation is required before sending. Intended address from issue #46: openapi@moomoo.com; confirm the support destination when sending. No raw capture, account identifiers or private reports are attached.

Subject: Written K_1M contract clarification for moomoo SDK/OpenD 10.11.7108 (US.SPY / US.QQQ, RTH, rehabType=1)

Hello moomoo OpenAPI Support,

We are documenting the data contract for offline market-data research using moomoo SDK/OpenD 10.11.7108, US.SPY and US.QQQ, K_1M during regular trading hours, with observed protobuf `rehabType=1`. Please confirm the following specifically for that version, distinguishing Qot_UpdateKL pushes, get_cur_kline / Qot_GetKL snapshots, and historical-kline retrieval. If a guarantee differs by endpoint, market, entitlement, session setting or version, please identify the difference. Please distinguish guaranteed behavior from typical behavior and explicitly state when no guarantee exists.

1. **Exact minute boundaries.** For `time_key=2026-11-02 10:52:00` in US Eastern time, what exact event-time interval does the label represent? Is it the interval start or end, and which endpoint is inclusive? Which candle receives an event timestamped exactly 10:52:00? Please give corresponding first/last RTH labels for a normal session and an early close, explain opening/closing auction assignment and any extended-hours interaction, and specify timezone/DST rules and how the UTC offset can be recovered. Does protobuf time/timestamp carry the same semantics as Python time_key? Please do not assume that shifting labels by 60 seconds is valid.

2. **Late revisions and ordering.** Can a minute's open, high, low, close, volume or turnover change after a later minute label has already been delivered? Can corrections occur after the session, on a later day, after reconnect or through backfill? Are pushes complete replacements or incremental deltas, and can repeat or out-of-order messages occur within/across callbacks? Is there a sequence/revision identifier or ordering guarantee? What is the guaranteed maximum correction delay, measured from which event/clock? If there is no finite bound, please say so. How are corrections exposed to a continuously subscribed client versus snapshot/history clients?

3. **Authoritative finality.** Is there a closed/final marker, immutable-after watermark, revision generation or other authoritative criterion for a K_1M candle in 10.11.7108? Please identify its exact endpoint, field, units and scope. Does a subsequent label, session close, successful historical response or any quiet waiting period guarantee permanent immutability? If none does, please confirm that no finite observed stability period establishes permanent finality. Distinguish a closed interval from a candle that can no longer be corrected, and distinguish both from complete session coverage.

4. **Adjustment contract.** Please confirm the exact meaning of protobuf rehabType=1 and its mapping to SDK AuType.QFQ for each endpoint above. What formula, corporate-action set, factor anchor/as-of date and factor version apply to OHLC? How can a client retrieve and pin the factors used at capture time? Are volume, turnover and last_close adjusted, and how? Can a later corporate action or factor correction rewrite earlier results? Under identical session/adjustment options, should real-time callbacks, current snapshots and history agree; if not, what reconciliation rules and timing apply? Can a client reproduce an earlier adjusted result after factor updates?

For context only, our internal issue records repeated updates and a previously reported QQQ open/low change from 696.88 to 696.9054 under one label at receipt sequences 386/388. These are local receipt positions, not provider sequence IDs. We are not asserting this establishes interval boundaries, a provider defect or a correction-delay bound, and the private capture was not reverified in the current audit. We can discuss a separately approved minimal redacted example if needed; no private raw capture is supplied with this inquiry.

Tracking: https://github.com/girlbreaksface/raccoon-radar/issues/46 and its documentation review https://github.com/girlbreaksface/raccoon-radar/issues/46#issuecomment-6584081282. Frozen offline audit: draft PR https://github.com/girlbreaksface/raccoon-radar/pull/48 at 6c3acba2f22d582cbe9102d9e9aea3f12b31b62d.

We reviewed these official documentation pages, currently labeled v10.12; please provide the applicable 10.11.7108 contract or archived version and identify relevant changes:
- https://openapi.moomoo.com/moomoo-api-doc/en/quote/update-kl.html
- https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-kl.html
- https://openapi.moomoo.com/moomoo-api-doc/en/quote/quote.html

Please answer each numbered item in writing, with the applicable version/endpoint, authoritative reference, exceptions and any unsupported guarantee. A support case identifier and response date would help us preserve the scope accurately.

Until these points are resolved, our observations remain PROVISIONAL, finality UNKNOWN, strategy use DATA_BLOCKED and completeness NOT_ESTABLISHED. This request concerns documentation and offline research, not order execution.

Thank you.
