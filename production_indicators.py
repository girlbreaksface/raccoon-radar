"""Provisional one-minute RTH indicator profile. Pure, offline, no execution path."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Context, Decimal, localcontext
from zoneinfo import ZoneInfo

ET = ZoneInfo('America/New_York')
UTC = timezone.utc
MINUTE = timedelta(minutes=1)
# Bounded NYSE/Arca published 2026 schedule, reviewed 2026-11-05.
# Unscheduled closures and provider session assignment remain unverified.
HOLIDAYS = frozenset(date.fromisoformat(s) for s in (
    '2026-01-01', '2026-01-19', '2026-02-16', '2026-04-03', '2026-05-25',
    '2026-06-19', '2026-07-03', '2026-09-07', '2026-11-26', '2026-12-25'))
EARLY = frozenset((date(2026, 11, 27), date(2026, 12, 24)))


def session(day):
    """UTC [open, close); unknown calendar years fail closed."""
    if type(day) is not date or day.year != 2026:
        raise ValueError('CALENDAR_COVERAGE')
    if day.weekday() >= 5 or day in HOLIDAYS:
        return None
    return (datetime.combine(day, time(9, 30), ET).astimezone(UTC),
            datetime.combine(day, time(13 if day in EARLY else 16), ET).astimezone(UTC))


def stamp(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('AWARE_TIMESTAMP_REQUIRED')
    return value.astimezone(UTC)


def number(value):
    if type(value) not in (str, int, Decimal):
        raise ValueError('EXACT_NUMERIC_INPUT_REQUIRED')
    result = Decimal(value)
    if not result.is_finite() or result <= 0:
        raise ValueError('POSITIVE_FINITE_REQUIRED')
    return result


@dataclass(frozen=True)
class Candle:
    symbol: str
    start: datetime
    end: datetime
    available_at: datetime  # retained actual knowledge/receipt time, never end time
    sequence: int         # one shared receipt ordering domain with quotes/evaluation
    open: str
    high: str
    low: str
    close: str
    volume: str
    finality: str = 'UNKNOWN'
    mapping: str = 'UNKNOWN'
    revision: int = 0


def next_start(end):
    bounds = session(end.astimezone(ET).date())
    if bounds and end < bounds[1]:
        return end
    day = end.astimezone(ET).date() + timedelta(days=1)
    while True:
        bounds = session(day)
        if bounds:
            return bounds[0]
        day += timedelta(days=1)


def evaluate(candles, *, symbol, evaluated_at, evaluation_sequence, required_through):
    """Recompute a complete immutable snapshot; any invalidation blocks all output.

    required_through is the caller's explicit completeness watermark (interval end),
    not inferred finality. History starts at a session open. RTH-only EMA history
    carries across sessions. First eligible candle has 100 *prior* closes.
    """
    blocked = dict(status='BLOCKED', orders='DISABLED', paper_execution='HOLD',
                   recording='HOLD', live_execution='NO-GO', merge='HOLD', deployment='HOLD')
    try:
        now, through = stamp(evaluated_at), stamp(required_through)
        if symbol not in ('SPY', 'QQQ') or type(evaluation_sequence) is not int or evaluation_sequence < 1:
            raise ValueError('SCOPE_OR_SEQUENCE')
        rows = tuple(candles)
        if not rows:
            raise ValueError('NO_CANDLES')
        previous = available = None
        seq = 0
        closes = []
        e9 = e21 = None
        pv = volume = Decimal(0)
        day = None
        with localcontext(Context(prec=50)):
            for bar in rows:
                start, end, known = stamp(bar.start), stamp(bar.end), stamp(bar.available_at)
                bounds = session(start.astimezone(ET).date())
                if (bar.symbol != symbol or bar.finality != 'FINAL' or
                        bar.mapping != 'VERIFIED_START_END' or type(bar.revision) is not int or bar.revision != 0):
                    raise ValueError('PROVENANCE_OR_CORRECTION')
                if (not bounds or start < bounds[0] or end > bounds[1] or
                        end - start != MINUTE or start.second or start.microsecond):
                    raise ValueError('RTH_INTERVAL')
                if start != (next_start(previous) if previous else bounds[0]):
                    raise ValueError('GAP_DUPLICATE_OR_ORDER')
                if (type(bar.sequence) is not int or not seq < bar.sequence < evaluation_sequence or
                        known < end or known > now or (available is not None and known < available)):
                    raise ValueError('CAUSAL_ORDER')
                o, h, l, c, v = map(number, (bar.open, bar.high, bar.low, bar.close, bar.volume))
                if not l <= min(o, c) <= max(o, c) <= h:
                    raise ValueError('OHLC')
                current_day = start.astimezone(ET).date()
                if current_day != day:
                    pv = volume = Decimal(0)
                    day = current_day
                pv += ((h + l + c) / 3) * v
                volume += v
                closes.append(c)
                if len(closes) == 9:
                    e9 = sum(closes) / 9
                elif len(closes) > 9:
                    e9 += (c - e9) / 5
                if len(closes) == 21:
                    e21 = sum(closes) / 21
                elif len(closes) > 21:
                    e21 += (c - e21) / 11
                previous, available, seq = end, known, bar.sequence
            if previous != through or through > now:
                raise ValueError('INCOMPLETE_WATERMARK')
            if len(closes) <= 100:
                raise ValueError('WARMUP_100_PRIOR')
            opening = datetime.combine(day, time(9, 45), ET).astimezone(UTC)
            bounds = session(day)
            if previous < opening or not opening <= now < bounds[1]:
                raise ValueError('ENTRY_TIME')
            return dict(blocked, status='READY_OFFLINE', reason=None,
                        ema9=str(e9), ema21=str(e21), vwap=str(pv / volume),
                        prior_candles=len(closes) - 1, symbol=symbol,
                        interval_end=previous.isoformat(), available_at=available.isoformat(),
                        evaluated_at=now.isoformat(), evaluation_sequence=evaluation_sequence)
    except (ValueError, TypeError, AttributeError, ArithmeticError) as exc:
        return dict(blocked, reason=str(exc))


def causal_quote(result, *, symbol, event_at, received_at, sequence):
    """Offline timing check only. Strict later receipt sequence resolves equal-time ties."""
    try:
        decision = stamp(datetime.fromisoformat(result['evaluated_at']))
        event, receipt = stamp(event_at), stamp(received_at)
        return (result['status'] == 'READY_OFFLINE' and symbol == result['symbol'] and
                type(sequence) is int and sequence > result['evaluation_sequence'] and
                decision <= event <= receipt and
                session(receipt.astimezone(ET).date()) == session(decision.astimezone(ET).date()) and
                receipt < session(decision.astimezone(ET).date())[1])
    except (KeyError, ValueError, TypeError):
        return False
