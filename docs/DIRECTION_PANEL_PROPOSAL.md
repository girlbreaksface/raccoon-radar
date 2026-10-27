# Compact directional-panel proposal — not integrated
Baseline: main b0ad02dc996b00406e7da08fb33b6382f658ea40. Proposed engine: #13. Proposed chronological validation: #14. Ingestion contract/proposals: #15.

## Reviewable artifact
Open docs/mockups/direction_panel.html locally. It is static, contains no script, remote font, service call or data import, and changes no Tkinter code. It follows existing dashboard colors (#151724 background, purple/lavender controls, restrained amber data caveats), compact cards and monospaced timestamps. Two cards fit a desktop desk view and stack at narrow widths.

SPY shows a SYNTHETIC bullish example using the engine test's numeric observations; QQQ shows an illustrative blocked state with indicators unavailable. They are not real market data or generated trading recommendations. Do not label this file a working scanner.

## Proposed fields and behavior
Each SPY/QQQ card displays the three engine labels verbatim; quality/evidence status; raw timestamp, interval end, actual availability and as-of time separately; EMA9/21, explicitly labeled candle VWAP proxy, prior-volume comparison; opening/five-bar observations; and explicit NO TRADE reasons. Expanded details show hypothesis parameters and evidence/source IDs. No confidence percentage, options selector, buy/sell control or order path.

Invalid, missing, incomplete, stale or unverified input must force NO TRADE and show which gate failed. READY data is not a claim of statistical validity. SYNTHETIC or caller-asserted VERIFIED evidence must remain visible. Absent values use an em dash rather than a cached prior-session signal. Text labels/reasons convey state independently of color.

## Future integration boundary — separate approval required
1. Approve #13's canonical completed-interval/availability contract and every hypothesis/threshold; review #14 before real-history assessment.
2. Approve a separately evidenced read-only adapter. Legacy raw stamps alone cannot populate canonical fields or verified evidence; missing metadata means NO TRADE.
3. Run the pure engine in a worker on immutable input snapshots. Route result/error envelopes through the existing queue; render widgets only on Tk's main thread. Include a request/session ID so stale responses cannot overwrite a newer snapshot.
4. Keep computation and SQLite/provider access outside the renderer. The panel never calls source-store initialization, upserts, or external services.
5. Add renderer/state tests for all labels, missing/stale fields, out-of-order request completion, session changes, error/shutdown and accessibility. Windows visual QA on disposable data is required; this HTML is not a Tk runtime test.
6. Review a NEW GUI integration PR only after the engine, adapter and tests are approved. This proposal does not authorize wiring, automatic refresh or a rollout.

## Verification and limits
Documentation/static HTML only; main's 69 guarded tests and source compilation pass locally on Windows/Python 3.12.14. Windows/Linux Python 3.11 CI validates the unchanged runtime baseline. No screenshot/live-GUI compatibility or real provider state is verified. The mockup's disclosures/field values were reviewed against the engine synthetic contract, not a live chart.

Moomoo timestamp semantics, source availability/latency, exchange calendars and empirical directional utility remain unresolved. No production database, calculation, ingestion, trading action or merge is included.
