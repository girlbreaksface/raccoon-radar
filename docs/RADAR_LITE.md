# Raccoon Radar Lite

From this checkout on Windows, run `py -3.12 -B raccoon_radar_lite.py`.
Python 3.11 or newer with Tk is sufficient. No additional packages are required.

The default replay starts at minute 35 with SPY CALL and QQQ PUT. Select
**Paper enter** and then **Next minute** to see a simulated exit. Run with
`--minute 1` to see warmup, `--scenario gap` to see a missing-data WAIT,
or `--scenario mixed` to see a neutral WAIT. The replay is forward-only.
Restarting the app begins a new fictional session with an empty in-memory ledger.

Signals reuse the pinned synthetic ETF candle engine from the earlier
presentation. Options are fictional 100-share contracts. The replay ranks fresh
snapshots by spread, then effective premium, then strike. Entry uses ask plus
0.5% slippage. Exits use bid minus 0.5% slippage. Fees are excluded. Dollar
thresholds on screen are rounded for display. The simulator tests the unrounded
20% target and 15% stop at each subsequent sample, fills at that sample's
effective bid, and closes at replay end if a usable quote is present. Each
replay allows three entries total across the pair and one open contract.

**Live data status** checks localhost:11111 on request. On the tested Windows
machine, moomoo was running and that port was unreachable. A reachable port
alone does not establish quote entitlements, chain identity, or timestamp
semantics. Live SPY/QQQ, options and ES/NQ remain unavailable, and the live status
screen stays WAIT. This MVP neither subscribes to market data nor uses order
endpoints. The existing OpenD minute-bar mapping remains untouched because
the provider's completion and label convention were not verified.

Run the guarded Windows suite with `py -3.12 -B offline_checks.py`.
