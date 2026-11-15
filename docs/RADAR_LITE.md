# Raccoon Radar Lite

Launch from the repository checkout on Windows with Python 3.12 and Tk.

```powershell
py -3.12 -B raccoon_radar_lite.py
```

The default starts synthetic replay. Click **Live data status** or launch
with `--live-status` to open OpenD observation directly. The replay and
journal work without OpenD or any Python packages beyond the standard
library. OpenD observation needs the installed moomoo Python SDK and IANA
New York time-zone data in that environment. Use `--opend-port PORT`
for a configured local port, and `--sound` or the **Sound** checkbox
for audible alerts. Sound starts off by default.

## Read-only OpenD observation

Start and authenticate the local OpenD quote service. Radar's background
worker opens only `OpenQuoteContext`. The UI can refresh the observation
every 20 seconds while the panel is open. Worker timeout is 18 seconds.
The dashboard shows quote authentication, SDK handshake status, provider
market state, per-symbol subscription result, last successful retrieval,
raw candle timestamps and ages, and last-trade timestamps and ages. An
ETF snapshot's last-trade time establishes age for the trade only.

The OpenD US calendar distinguishes full days, weekends and holidays.
Premarket and after-hours observations display with WAIT. Short and
special sessions display WAIT. Opening warmup is at least 21 minutes
and valid indicators require 21 contiguous aged regular-session bars.
Exactly one minute or more must elapse after a raw candle stamp before
the bar is used. The program rejects gaps, duplicates, future stamps,
identity mismatches, and inconsistent OHLCV. It retains raw Eastern
timestamps and does not rewrite any historical data. Last trades older
than 20 seconds and raw candles older than 150 seconds block signals.

EMA9 and EMA21 use simple-average seeds and update from validated closes.
Turnover VWAP uses summed dollar turnover divided by summed volume when
each bar is internally consistent. The separately labeled HLC3-volume
proxy is available when turnover VWAP cannot be verified. Relative
volume compares the latest retained bar to the prior 20-minute median;
the dashboard flags 2× and above. Support and resistance are the prior
20-minute low and high. Direction requires a breakout with EMA, verified
VWAP and relative-volume agreement, plus SPY/QQQ agreement. The provider's
minute boundary convention remains unverified, so live directional
signals stay at WAIT. Close-to-open coverage alone cannot resolve the
convention.

**Scan options** requests a bounded sample of standard contracts near the
ETF price with expiries through seven days. A scan needs a regular market
window and a recent ETF last trade. Ranking requires matching chain and
snapshot identity, standard 100-share size, independently timestamped
current bid and ask, valid Greeks, and minimum liquidity. Estimated
round-trip cost includes spread, slippage and two estimated fees. The
entry premium cap includes slippage. The tested US book omitted both
timestamps, so it produced no verified candidate. The live panel has
no entry controls. ES/NQ stays unavailable pending a licensed data source
with verified instrument, timestamp, and volume provenance.

## Synthetic paper journal

A fresh default replay starts at minute 35 with SPY CALL and QQQ PUT.
Choose **Paper enter**, then **Next minute**. Use `--scenario gap`
for a missing-data example, or `--new-replay --minute 1` for
opening warmup. The replay is forward-only. The journal restores the
selected scenario's last run, replay cursor, position and entry count.
It stores accepted commands before updating the UI. A stale second
window or failed write blocks further changes until the app is reopened.

The journal lives at `%LOCALAPPDATA%\RaccoonRadarLite\paper-journal.sqlite3`
or an explicit `--journal PATH`. `--new-replay` starts a new run
and retains history. **Paper performance** shows closed-trade win rate,
P/L, expectancy and dollar max drawdown, grouped results by scenario,
symbol and side, and the complete journal. Analytics use recorded cents,
exclude open positions, and reflect artificial fills only.

Each simulation permits one open contract total, no averaging down, and
three entries per session. Entry uses ask plus 0.5% slippage with a $30
premium cap. Replay exits use bid minus 0.5% slippage and test the 20%
target and 15% stop at each subsequent sample. The simulator records the
available effective bid on exit. Replay fees are excluded. The live
scanner includes illustrative fees in its separate cost estimate.

## Verification

Run `py -3.12 -B offline_checks.py`. On Sunday, November 15, 2026,
OpenD 10.12 authenticated and supplied 390 Friday RTH candles each for
SPY and QQQ, along with Monday's calendar entry and SPY chain metadata.
Friday candles were stale for signal purposes. Sample turnover failed
consistency checks, so HLC3 proxies remained available alongside missing
turnover VWAP. A tested SPY option book subscription and read succeeded,
with both side timestamps blank. Regular-session Monday freshness,
minute label semantics, and verified current US option books remain open.

Provider references are the moomoo [global state](https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-global-state.html),
[minute candles](https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-kl.html),
[trading calendar](https://openapi.moomoo.com/moomoo-api-doc/en/quote/request-trading-days.html),
and [order book](https://openapi.moomoo.com/moomoo-api-doc/en/quote/get-order-book.html)
documentation.
