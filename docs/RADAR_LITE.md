# Raccoon Radar Lite

From this checkout on Windows, run `py -3.12 -B raccoon_radar_lite.py`.
Python 3.11 or newer with Tk is sufficient. No additional packages are required.

The default replay starts at minute 35 with SPY CALL and QQQ PUT. Select
**Paper enter** and then **Next minute** to see a simulated exit. Run with
`--minute 1` to see warmup, `--scenario gap` to see a missing-data WAIT,
or `--scenario mixed` to see a neutral WAIT. The replay is forward-only.
Radar Lite resumes the latest run for the selected scenario, including its
clock, open position and entry count. Click **Paper journal** for entries and
exits across all runs. The Windows default is
`%LOCALAPPDATA%\RaccoonRadarLite\paper-journal.sqlite3`. Use
`--journal PATH` to choose a dedicated file. Use `--new-replay` to begin a
fresh fictional session and retain the old journal. `--minute` specifies
the starting minute for new runs. An earlier version's in-memory trades
cannot be recovered after that version has closed.

The journal records commands and fills in a separate SQLite file. It writes
each accepted command before displaying the updated state and restores by
replaying that command history. A stale second window or a failed write
blocks further paper actions until the app is reopened.

Signals reuse the pinned synthetic ETF candle engine from the earlier
presentation. Options are fictional 100-share contracts. The replay ranks fresh
snapshots by spread, then effective premium, then strike. Entry uses ask plus
0.5% slippage. Exits use bid minus 0.5% slippage. Fees are excluded. Dollar
thresholds on screen are rounded for display. The simulator tests the unrounded
20% target and 15% stop at each subsequent sample, fills at that sample's
effective bid, and closes at replay end if a usable quote is present. Each
replay allows three entries total across the pair and one open contract.

**Live data status → Run OpenD diagnostics** checks IPv4 loopback without
freezing the window. It reports refusal, timeout or other socket failure
separately, plus probe time, elapsed time and the installed Python SDK version
if present. Use `--opend-port PORT` in Radar Lite or
`py -3.12 -B tools/opend_local_preflight.py --port PORT` from PowerShell
for a custom local port. A TCP listener does not establish OpenD identity,
SDK handshake, entitlements or timestamp semantics. Live SPY/QQQ, options
and ES/NQ remain unavailable. The app makes no quote, account or order
requests. The existing OpenD minute-bar mapping is untouched.

Run the guarded Windows suite with `py -3.12 -B offline_checks.py`.
