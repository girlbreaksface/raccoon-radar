# Provider response and Windows observer — November 5, 2026

## Evidence and decisions

Read the original OpenAPI Support email in Gmail, message 1a1aa73a312be556,
subject `回复: *EXTERNAL*OpenAPI technical clarification — K_1M candle timestamps,
revisions and finality (10.11.7108)`. Sender openapi@moomoo.com; Date header
November 5 at 14:44:17 +0800 (01:44:17 Eastern). Preserved the complete raw RFC2822
message privately, 61,159 bytes, SHA256
`0a0876d3bfcf934b79c9128c032cf4b043fd8e13715cdf1f6a7b882d47a40a22`.
Mailbox authentication headers report DKIM/SPF/DMARC pass; this work does not
independently revalidate the mail signatures or treat a hash as a signature.
Private correspondence, account identifiers and raw market data are not committed.

| Previous blocker | New evidence and remaining status |
| --- | --- |
| Cost/entitlement for underlying SPY/QQQ K_1M | Support confirms promotional US LV3 coverage without purchase; promotion expiry and future level unknown. Current local get_user_info reports us_qot_right LV3. Subscription success, latency and callback delivery remain unverified. This does not verify options entitlement. |
| Permission to retain API callbacks | Support explicitly permits private noncommercial storage, private backups and derived results without retention limit/deletion obligation or additional API fee. No resale/redistribution. Exact agreement version/clauses not supplied. Provider-permission question resolved within stated personal scope; user recording authorization remains HOLD. |
| Interval labels and inclusivity | End labels, exchange-local time/DST, [start,end) intervals, actual early close confirmed for matching OpenD/SDK 10.11.7108. Current SDK 10.12.7208 and abbreviated OpenD server_ver 1011 do not establish that exact build pair. No raw timestamp rewritten. |
| Coverage comparability | Live Nasdaq-only versus post-close consolidated history clarified. No payload coverage identifier or exact switch watermark. Provenance must be external; never splice or equate them. Underlying bars are not historical option bid/ask data. |
| Finality and revisions | Support confirms no authoritative flag, deadline, version or ordered updates. One second is not a guarantee. This blocker is a known provider limitation, not awaiting discovery of a FINAL field. |
| Adjustment factor lineage | No versions/as-of/revision history. Future use must preserve exact retrieved factor sets and receipt time; no factor requests or adjustment application in this observer. |
| Read-only switch | No official switch. Quote context only; no trade context/unlock/order path. Simulated trading also requires exclusion because real-account unlock does not protect it. |
| Version precision | 10.11.7108 may truncate fractional high-precision volume; snapshot update times can carry milliseconds. Keep serialized payload/SDK-decoded values and precise receipts; do not reconstruct lost precision. |

## Conservative policy

Every provider observation remains UNKNOWN finality and BLOCKED for signals,
regardless of elapsed time, later labels, duplicate payloads, historical agreement
or closed sessions. The FINAL-only production indicator calculator stays isolated;
its numerical fixtures establish software correctness, not provider finality.
Any future provisional analytical display must have a separately reviewed causal
revision/revocation policy and cannot pass the production entry gate.

`RevisionBook` retains bounded volatile immutable arrival records, serialized SDK
protobuf bytes, original decoded row/label, UTC receipt with fractional seconds,
monotonic clock, local sequence, repeated/changed observations, prior-arrival link,
SDK/OpenD versions and source-context claims. Local revision numbers are not
provider versions or correction order. Invalid intervals stay blocked; historical
contexts cannot enter this live book. Capacity stops ingestion rather than
evicting old evidence. No real callback persistence/export path is enabled.
Transport loss, delivery completeness, durable custody, clock accuracy and
independent interval OHLCV comparisons remain unverified.

## Current Windows verification

At 15:03:53 UTC (10:03:53 Eastern), the local quote-only observer queried only
get_user_info, get_global_state and query_subscription, installed a quote callback
handler and waited five seconds. It observed LV3, quote login, SDK 10.12.7208 and
OpenD server_ver 1011. No existing SPY/QQQ K_1M subscriptions; zero callbacks.
Context close confirmed. No subscribe/unsubscribe, history, trade context, unlock,
order or account mutation occurred. SDK package initialization may load shared SDK
class definitions; observer application imports only quote-specific classes and
never project execution paths or trade-context symbols.

Run locally from this checkout with `python -B quote_observer.py` for a new
metadata-only check; it does not write callback files or activate subscriptions.
Use `python -B -m unittest test_quote_observer -v` for synthetic offline tests.
SDK is lazy-imported only by the explicit local preflight; ordinary tests require
no installed SDK or OpenD. Existing local research databases are untouched.

Restriction on new subscriptions prevents testing subscription success/delivery.
No confirmation is being requested now: the code and remaining blocker are
reviewable. Recording additionally needs successful local verification and the
user's separate explicit authorization. No paid product/trial activated.

## Other engineering and coordination

PR #77 fixes missing foundation evidence references; its local ten-suite foundation
passed (282 root, 120 feed, 54 reconciliation), and hash-bound certification held
all gates. Independently downloaded #76 Windows/Python3.12 foundation archive
13394646123 matches published SHA256 a765ef2378eeb3bfaafe0480df424dce9e59aedfb8bf0e5f4a77400f4b678573.
All ten logs/five artifacts and certification self-hash verified. Its 114 source
hashes match the pinned Git tree, accounting explicitly for Windows CRLF checkout
conversion on 105 files. This is archive integrity verification, not an external
reviewer or authentic-data certification.

Concurrent `Build Raccoon Radar contract picker` chat uses an isolated local clone,
offline fixture/UI scope, no pushes or Actions; its files were not incorporated.
Existing #73–#76 branches and historical research proposals remain preserved.
Licensed historical options bid/ask, point-in-time universe/fees, contamination
audit and frozen chronological holdout are still absent. Broker fill lineage,
terminal-order baseline and production risk durability remain unresolved.

Local observer verification adds ten synthetic tests to the already verified
stack. To minimize Actions consumption under the latest instruction, publish this
observer draft with a skip-ci commit marker and validate the full foundation
locally. #77 already has all 26 hosted checks passing at
0461612e7df4ed4613c1d16ff3b69a2c9e61143b; do not attribute those hosted checks to
the new observer head. No new workflow or dependency is added.

Paper HOLD; recording HOLD; live NO-GO; orders DISABLED; merge/deployment HOLD.
