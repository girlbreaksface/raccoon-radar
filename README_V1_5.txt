RACCOON RADAR v1.5 — SEC Fundamental & Catalyst Intelligence

Install in a NEW versioned folder; do not overwrite v1.4.1.
Close old app, make dated backups of raccoon_history.sqlite3, raccoon_swing.sqlite3, raccoon_discovery.sqlite3, then COPY those three into this new folder. Never move the originals. Launch: py raccoon_dashboard_v1_2.py

New SEC fundamentals tab: enter ticker and SEC contact User-Agent (example RaccoonRadar/1.5 you@example.com); fetch official SEC submissions and companyfacts, or load saved snapshot offline. Internet required for fetch; no live market news, options, or order APIs. Values are reported periods, not normalized or automatically audited. SEC endpoints may reject requests, rate limit, or omit facts for certain issuers.

New raccoon_fundamentals.sqlite3 stores snapshots and user-written source-linked notes. BACK THIS UP TOO after first use. Research cases remain in raccoon_swing.sqlite3. Notes are ticker-linked and NOT automatically copied into the Swing Desk fields. Manual verification required before interpreting financing, cash runway, dilution, or catalysts.

Testing: Python syntax and offline persistence unit checks only. SEC network and Windows GUI require testing on user's machine.
Rollback: close app and launch old v1.4.1 folder; old DBs untouched. No migration modifies existing schemas.
