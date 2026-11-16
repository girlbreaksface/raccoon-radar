"""Read-only OpenD market observation and fail-closed Radar Lite calculations."""
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import json
from importlib.metadata import version
from hashlib import sha256
from math import isfinite
from statistics import median, fmean
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from futures_spike_radar import MAX_PREMIUM
from historical_radar_replay import FEE, SLIP
from tools.opend_local_preflight import diagnose_opend, port_number

SYMBOLS = ("US.SPY", "US.QQQ")
MINUTE = timedelta(minutes=1)
FUTURES_STATUS = "ES/NQ unavailable · licensed real-time feed and replay provenance unverified"
# Raw 09:31–16:00 coverage supports, but does not independently verify, end labels.
VERIFIED_MINUTE_LABEL = None


def eastern():
    return ZoneInfo("America/New_York")


def market_stamp(value):
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is not None:
        raise ValueError("Expected an Eastern wall-clock timestamp")
    local = stamp.replace(tzinfo=eastern())
    if local.utcoffset() != local.replace(fold=1).utcoffset():
        raise ValueError("Ambiguous or nonexistent Eastern timestamp")
    return local


def session_at(now, calendar):
    local = now.astimezone(eastern())
    day = local.date()
    clock = local.time()
    if day.weekday() >= 5:
        return "WEEKEND", None
    if calendar is None:
        return "CALENDAR UNVERIFIED", None
    if day.isoformat() not in calendar:
        return "HOLIDAY / CLOSED", None
    kind = calendar[day.isoformat()]
    if kind != "WHOLE":
        return "SHORT OR SPECIAL SESSION / WAIT", None
    opening = datetime.combine(day, time(9, 30), eastern())
    if clock < time(4):
        return "CLOSED", opening
    if local < opening:
        return "PREMARKET", opening
    if clock >= time(16):
        return ("AFTER HOURS" if clock < time(20) else "CLOSED"), opening
    return ("OPENING WARMUP" if local < opening + 21 * MINUTE else "REGULAR"), opening


def age_seconds(stamp, now):
    return round((now - stamp).total_seconds(), 1)


def finite(value):
    value = float(value)
    if not isfinite(value):
        raise ValueError("Nonfinite market field")
    return value


def ema(closes, period):
    value = fmean(closes[:period])
    for close in closes[period:]:
        value += (close - value) * 2 / (period + 1)
    return value


def candle_metrics(rows, code, now, day):
    """Use only coherent RTH rows whose raw timestamp is at least one minute old."""
    if not rows:
        raise ValueError("No candles returned")
    bars = []
    raw_seen = set()
    previous = None
    for row in rows:
        if row["code"] != code:
            raise ValueError("Wrong symbol in candle response")
        stamp = market_stamp(row["time_key"])
        if stamp.second or stamp.microsecond or stamp > now:
            raise ValueError("Invalid or future minute timestamp")
        if stamp in raw_seen:
            raise ValueError("Duplicate minute timestamp")
        if previous is not None and stamp < previous:
            raise ValueError("Out-of-order minute timestamp")
        raw_seen.add(stamp)
        previous = stamp
        if stamp.date() != day or not time(9, 30) <= stamp.time() <= time(16):
            continue
        if now - stamp < MINUTE:
            continue
        o, h, low, close, volume = (finite(row[key]) for key in ("open", "high", "low", "close", "volume"))
        if not 0 < low <= min(o, close) <= max(o, close) <= h or volume < 0:
            raise ValueError("Inconsistent candle OHLCV")
        turnover = row.get("turnover")
        try:
            turnover = finite(turnover)
        except (ValueError, TypeError):
            turnover = None
        if turnover is not None and (volume == 0 and turnover != 0 or
                                     volume > 0 and not low - .01 <= turnover / volume <= h + .01):
            turnover = None
        bars.append((stamp, h, low, close, volume, turnover))
    if not bars:
        raise ValueError("No aged regular-session minute candles for selected date")
    first_time = bars[0][0].time()
    expected = {"START": (time(9, 30),), "END": (time(9, 31),)}.get(
        VERIFIED_MINUTE_LABEL, (time(9, 30), time(9, 31)))
    if first_time not in expected or any(b[0] - a[0] != MINUTE for a, b in zip(bars, bars[1:])):
        raise ValueError("Missing opening candle or gap in regular-session candles")
    if first_time == time(9, 30) and bars[-1][0].time() == time(16):
        raise ValueError("Contradictory regular-session candle boundaries")
    last = bars[-1]
    values = {"bars": len(bars), "raw_candle": last[0].isoformat(), "close": last[3]}
    for length in (5, 15):
        if len(bars) >= length:
            opening_bars = bars[:length]
            values[f"opening_{length}m"] = [min(bar[2] for bar in opening_bars),
                                           max(bar[1] for bar in opening_bars)]
    if len(bars) < 21:
        return values
    closes = [bar[3] for bar in bars]
    volumes = [bar[4] for bar in bars]
    total_volume = sum(volumes)
    turnover_complete = all(bar[5] is not None for bar in bars)
    prior = bars[-21:-1]
    baseline = median(volumes[-21:-1])
    five_minute_closes = closes[4::5]
    # Four full five-minute groups give a coarse slower trend check.
    recent_groups = five_minute_closes[-4:]
    if all(left < right for left, right in zip(recent_groups, recent_groups[1:])):
        trend = "UP"
    elif all(left > right for left, right in zip(recent_groups, recent_groups[1:])):
        trend = "DOWN"
    else:
        trend = "MIXED"
    changes = [b - a for a, b in zip(closes[-11:-1], closes[-10:])]
    nonzero = [change for change in changes if change]
    reversals = sum(a * b < 0 for a, b in zip(nonzero, nonzero[1:]))
    values.update(
        ema9=ema(closes, 9), ema21=ema(closes, 21),
        vwap=sum(bar[5] for bar in bars) / total_volume if total_volume and turnover_complete else None,
        vwap_proxy=(sum(((bar[1] + bar[2] + bar[3]) / 3) * bar[4] for bar in bars)
                    / total_volume if total_volume else None),
        relative_volume=volumes[-1] / baseline if baseline else None,
        support=min(bar[2] for bar in prior), resistance=max(bar[1] for bar in prior),
        five_minute_trend=trend, reversals=reversals, choppy=reversals >= 5 or trend == "MIXED",
    )
    return values


def directional_view(metrics, reasons):
    if reasons:
        return "WAIT", "; ".join(reasons)
    required = ("vwap", "ema9", "ema21", "relative_volume", "support", "resistance")
    if any(metrics.get(key) is None for key in required):
        return "WAIT", "Indicators or volume baseline unavailable"
    close = metrics["close"]
    if metrics["relative_volume"] < 2:
        return "WAIT", "Volume below 2× prior 20-minute median"
    if metrics.get("choppy", True):
        return "WAIT", "Choppy or contradictory five-minute evidence"
    if close > max(metrics["vwap"], metrics["resistance"]) and metrics["ema9"] > metrics["ema21"]:
        if metrics["five_minute_trend"] == "UP":
            return "CALL", "Close broke prior 20-minute resistance above VWAP; EMA9 > EMA21; five-minute trend UP"
    if close < min(metrics["vwap"], metrics["support"]) and metrics["ema9"] < metrics["ema21"]:
        if metrics["five_minute_trend"] == "DOWN":
            return "PUT", "Close broke prior 20-minute support below VWAP; EMA9 < EMA21; five-minute trend DOWN"
    return "WAIT", "EMA, VWAP, breakout and five-minute evidence do not agree"


def checked_quote(row, code, now):
    if row["code"] != code or row.get("suspension") != False:
        raise ValueError("Quote identity or suspension state invalid")
    quote_time = market_stamp(row["update_time"])
    if quote_time > now or finite(row["last_price"]) <= 0:
        raise ValueError("Future or invalid last trade")
    return quote_time, float(row["last_price"])


def option_candidate(chain, snap, book, underlying, now):
    """Validate each book side independently of the snapshot's last-trade timestamp."""
    code = chain["code"]
    side = chain["option_type"]
    expiry = date.fromisoformat(chain["strike_time"])
    local = now.astimezone(eastern())
    strike = finite(chain["strike_price"])
    if (not code.startswith("US.") or code != snap["code"] or code != book["code"]
            or chain["stock_owner"] != underlying or snap["stock_owner"] != underlying
            or chain["option_standard_type"] != "STANDARD" or chain["suspension"] != False
            or snap["suspension"] != False or snap["option_valid"] != True
            or side not in ("CALL", "PUT") or side != snap["option_type"]
            or chain["strike_time"] != snap["strike_time"] or expiry < local.date()
            or strike <= 0 or strike != finite(snap["option_strike_price"])
            or chain["lot_size"] != 100 or snap["option_contract_size"] != 100):
        raise ValueError("Unverified option chain/snapshot identity")
    times = []
    for key in ("bid_epoch", "ask_epoch"):
        try:
            epoch = finite(book[key])
            if epoch <= 0:
                raise ValueError("Nonpositive epoch")
            times.append(datetime.fromtimestamp(epoch, timezone.utc))
        except (KeyError, ValueError, TypeError, OverflowError, OSError) as exc:
            raise ValueError("Verified per-side US order-book timestamps unavailable") from exc
    meta_at = market_stamp(snap["update_time"])
    if (any(not timedelta(0) <= now - at <= timedelta(seconds=15) for at in times)
            or not timedelta(0) <= now - meta_at <= timedelta(seconds=60)):
        raise ValueError("Stale option book or Greek snapshot")
    bid, bid_size = map(finite, book["Bid"][0][:2])
    ask, ask_size = map(finite, book["Ask"][0][:2])
    volume, interest = (finite(snap[key]) for key in ("volume", "option_open_interest"))
    delta, gamma, theta, vega = (finite(snap[f"option_{key}"])
                                for key in ("delta", "gamma", "theta", "vega"))
    if (not 0 < bid <= ask or (ask - bid) / ask > .25000001 or min(bid_size, ask_size) < 1
            or volume < 10 or interest < 50 or not 0 < (delta if side == "CALL" else -delta) <= 1
            or gamma < 0 or theta > 0 or vega < 0):
        raise ValueError("Liquidity, spread or Greeks outside limits")
    ask_dec, bid_dec = Decimal(str(ask)), Decimal(str(bid))
    premium = ask_dec * (1 + SLIP) * 100
    if premium > MAX_PREMIUM:
        raise ValueError("Entry premium exceeds cap")
    cost = premium - bid_dec * (1 - SLIP) * 100 + 2 * FEE
    return dict(code=code, side=side, strike=strike, expiry=expiry.isoformat(), bid=bid, ask=ask,
                premium=float(premium), round_trip_cost=float(cost), volume=volume, interest=interest,
                delta=delta, gamma=gamma, theta=theta, vega=vega,
                bid_time=times[0].isoformat(), ask_time=times[1].isoformat())


def rank_options(chain, snapshots, books, underlying, now):
    codes = Counter(row["code"] for row in chain)
    snapshot_counts = Counter(row["code"] for row in snapshots)
    lookup = {row["code"]: row for row in snapshots if snapshot_counts[row["code"]] == 1}
    ranked = []
    rejected = Counter()
    for row in chain:
        code = row["code"]
        if codes[code] != 1:
            rejected["Duplicate contract"] += 1
            continue
        try:
            ranked.append(option_candidate(row, lookup[code], books[code], underlying, now))
        except (ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
            reason = str(exc) if isinstance(exc, ValueError) else "Missing or invalid option fields"
            rejected[reason] += 1
    ranked.sort(key=lambda q: (q["round_trip_cost"], -q["volume"], -q["interest"], -abs(q["delta"]), q["code"]))
    return ranked, dict(rejected)


class FeedError(RuntimeError):
    pass


def call(method, *args, **kwargs):
    result, data = method(*args, **kwargs)
    if result != 0:
        raise FeedError(str(data)[:220])
    return data


def scan_options(sdk, ctx, code, price, day, clock):
    start, end = day.isoformat(), (day + timedelta(days=7)).isoformat()
    chain = call(ctx.get_option_chain, code, start=start, end=end).to_dict("records")
    selected = []
    for side in ("CALL", "PUT"):
        eligible = [row for row in chain if row.get("option_type") == side
                    and row.get("option_standard_type") == "STANDARD"
                    and row.get("suspension") == False]
        selected.extend(sorted(eligible, key=lambda r: (abs(finite(r["strike_price"]) - price),
                                                        r["strike_time"], r["code"]))[:4])
    if not selected:
        return {"status": "No standard contracts in scan window"}
    codes = list(dict.fromkeys(row["code"] for row in selected))
    call(ctx.subscribe, codes, [sdk.SubType.ORDER_BOOK], is_first_push=False, subscribe_push=False)
    snaps = call(ctx.get_market_snapshot, codes).to_dict("records")
    books = {}
    issues = Counter()
    for contract in codes:
        try:
            raw_book = call(ctx.get_order_book, contract, num=1)
            # The US SDK can return both display strings blank. Receipt time
            # and last-trade time cannot establish freshness of either side.
            books[contract] = {**raw_book, "bid_epoch": raw_book.get("svr_recv_time_bid_timestamp"),
                               "ask_epoch": raw_book.get("svr_recv_time_ask_timestamp")}
        except FeedError as exc:
            issues[str(exc)] += 1
    ranked, rejected = rank_options(selected, snaps, books, code, clock())
    return {"status": f"Scanned {len(codes)} contracts · {len(ranked)} eligible",
            "ranked": ranked, "rejected": rejected, "book_errors": dict(issues)}


def collect(ctx, sdk, *, scan=False, capture=False, clock=lambda: datetime.now(timezone.utc)):
    global_state = call(ctx.get_global_state)
    result = {"status": "SDK handshake OK", "authenticated": global_state.get("qot_logined") is True,
              "version": str(global_state.get("server_ver", "?")), "symbols": {}}
    if not result["authenticated"] or global_state.get("program_status_type") != "READY":
        result["status"] += (" · sign in to OpenD quotes" if not result["authenticated"]
                             else f" · quote service {global_state.get('program_status_type', 'unknown')}")
        return result
    local_day = clock().astimezone(eastern()).date()
    calendar = None
    try:
        rows = call(ctx.request_trading_days, sdk.TradeDateMarket.US,
                    start=(local_day - timedelta(days=10)).isoformat(), end=local_day.isoformat())
        calendar = {row["time"]: row["trade_date_type"] for row in rows}
    except (FeedError, KeyError, TypeError) as exc:
        result["calendar_error"] = str(exc)
    now = clock()
    regime, _ = session_at(now, calendar)
    result["session"] = regime
    result["provider_session"] = global_state.get("market_us")
    result["checked_at"] = now.isoformat()
    provider_clock_ok = False
    try:
        provider_clock_ok = abs(now.timestamp() - finite(global_state["timestamp"])) <= 30
    except (KeyError, ValueError, TypeError):
        pass
    try:
        snapshots = call(ctx.get_market_snapshot, list(SYMBOLS)).to_dict("records")
    except FeedError as exc:
        snapshots = []
        result["snapshot_error"] = str(exc)
    subscriptions = {}
    # Subscribe individually so a denial for one ETF does not erase the other.
    for code in SYMBOLS:
        try:
            call(ctx.subscribe, [code], [sdk.SubType.K_1M], session=sdk.Session.RTH,
                 is_first_push=False, subscribe_push=False)
            subscriptions[code] = "RTH minute subscription accepted"
        except FeedError as exc:
            subscriptions[code] = str(exc)
    for code in SYMBOLS:
        data = {"permissions": subscriptions[code], "metrics": {}}
        result["symbols"][code] = data
        reasons = []
        quote_fresh = False
        try:
            row, = [row for row in snapshots if row.get("code") == code]
            quote_time, price = checked_quote(row, code, clock())
            data.update(quote_at=quote_time.isoformat(), price=price)
            quote_fresh = age_seconds(quote_time, clock()) <= 20
            if not quote_fresh:
                reasons.append("Last trade stale")
        except (ValueError, KeyError, TypeError, OverflowError):
            reasons.append("Last trade missing or invalid")
        if not provider_clock_ok:
            reasons.append("Provider clock unavailable or inconsistent")
        if regime != "REGULAR":
            reasons.append(regime)
        elif result["provider_session"] not in ("MORNING", "AFTERNOON"):
            reasons.append("Provider status disagrees with regular session")
        if VERIFIED_MINUTE_LABEL is None:
            reasons.append("Minute-bar timestamp convention unverified")
        try:
            if subscriptions[code] != "RTH minute subscription accepted":
                raise FeedError(subscriptions[code])
            rows = call(ctx.get_cur_kline, code, 390, sdk.KLType.K_1M, sdk.AuType.NONE).to_dict("records")
            retrieved = clock()
            if capture:
                # Preserve values from the SDK, including invalid nonfinite markers.
                fields = ("code", "time_key", "open", "high", "low", "close", "volume", "turnover")
                data["raw_candles"] = [
                    {key: (repr(row[key]) if isinstance(row[key], float) and not isfinite(row[key])
                           else row[key]) for key in fields if key in row} for row in rows]
                data["capture_at"] = retrieved.isoformat()
            data["received_at"] = retrieved.isoformat()
            day = local_day
            if regime not in ("REGULAR", "OPENING WARMUP"):
                past_close = retrieved.astimezone(eastern()).time() >= time(16)
                eligible_days = [date.fromisoformat(key) for key, kind in (calendar or {}).items()
                                 if kind == "WHOLE" and (key < local_day.isoformat()
                                     or key == local_day.isoformat() and past_close)]
                if eligible_days:
                    day = max(eligible_days)
            data["metrics"] = candle_metrics(rows, code, retrieved, day)
            data["observed_date"] = day.isoformat()
            candle_fresh = age_seconds(datetime.fromisoformat(data["metrics"]["raw_candle"]), retrieved) <= 150
            if not candle_fresh:
                reasons.append("Minute candle stale")
            data["candle_health"] = "CURRENT" if candle_fresh else "STALE"
            data["volume_alert_eligible"] = (candle_fresh and quote_fresh and provider_clock_ok
                                             and regime == "REGULAR"
                                             and result["provider_session"] in ("MORNING", "AFTERNOON"))
        except (FeedError, ValueError, TypeError, KeyError, OverflowError) as exc:
            data["candle_error"] = str(exc)
            reasons.append(str(exc))
        data["action"], data["reason"] = directional_view(data["metrics"], reasons)
        if scan:
            scan_regime, _ = session_at(clock(), calendar)
            if (scan_regime not in ("REGULAR", "OPENING WARMUP") or not quote_fresh
                    or not provider_clock_ok or result["provider_session"] not in ("MORNING", "AFTERNOON")
                    or age_seconds(quote_time, clock()) > 20):
                data["options"] = {"status": "WAIT · regular session and fresh verified ETF quote required"}
            else:
                try:
                    data["options"] = scan_options(sdk, ctx, code, price, local_day, clock)
                except (FeedError, ValueError, KeyError, TypeError, OverflowError) as exc:
                    data["options"] = {"status": f"Unavailable · {exc}"}
    actions = {row["action"] for row in result["symbols"].values()}
    if "WAIT" in actions or len(actions) > 1:
        for row in result["symbols"].values():
            if row["action"] != "WAIT":
                row.update(action="WAIT", reason="SPY/QQQ confirmation missing or contradictory")
    return result


def fetch_opend(port, *, scan=False, capture=False):
    diagnostic = diagnose_opend(port)
    if diagnostic.status != "REACHABLE":
        return {"status": diagnostic.describe(), "symbols": {}}
    try:
        import moomoo as sdk
    except ImportError as exc:
        return {"status": f"OpenD SDK unavailable · {exc}", "symbols": {}}
    ctx = sdk.OpenQuoteContext(host="127.0.0.1", port=port)
    try:
        result = collect(ctx, sdk, scan=scan, capture=capture)
        if capture:
            result["provenance"] = {
                "source": "MOOMOO_OPEND", "sdk": version("moomoo-api"), "port": port,
                "endpoint": "get_cur_kline", "interval": "1m", "session": "RTH",
                "adjustment": "NONE", "timezone": "America/New_York", "requested_count": 390,
                "coverage": "bounded latest response; no pagination",
                "minute_label": VERIFIED_MINUTE_LABEL,
                "worker_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            }
        return result
    finally:
        ctx.close()


if __name__ == "__main__":
    try:
        value = fetch_opend(port_number(sys.argv[1]), scan="--scan" in sys.argv[2:],
                            capture="--capture" in sys.argv[2:])
    except Exception as exc:
        value = {"status": f"OpenD handshake or request failed · {exc}", "symbols": {}}
    # SDK logs can precede this line. Emit a tagged JSON record for the UI.
    print("RADAR_RESULT " + json.dumps(value, allow_nan=False), flush=True)
