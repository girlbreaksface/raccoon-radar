"""Offline ES/NQ spike detection and long-option paper research."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import isfinite, log1p
from statistics import median

PAIRS = {"ES": "SPY", "NQ": "QQQ"}
MINUTE = timedelta(minutes=1)
MAX_PREMIUM = Decimal("30")
MAX_TRADES = 3


@dataclass(frozen=True, slots=True)
class Bar:
    symbol: str
    instrument: str
    end: datetime
    received: datetime
    high: float
    low: float
    close: float
    volume: int
    complete: bool = True
    delayed: bool = False


@dataclass(frozen=True, slots=True)
class Session:
    """Caller-verified common cash session, including early closes."""

    opening: datetime
    closing: datetime


@dataclass(frozen=True, slots=True)
class Spike:
    session: Session
    at: datetime
    etf: str
    direction: int = 0
    flags: tuple[str, ...] = ()
    volume_ratio: float | None = None
    displacement_ratio: float | None = None
    broken_level: float | None = None
    etf_return: float | None = None
    estimated_move: float | None = None
    source_lag_seconds: float | None = None


def _utc(value):
    return isinstance(value, datetime) and value.tzinfo is timezone.utc


def _bar_flags(bars, symbol, session, as_of):
    flags = set()
    if len(bars) != 21:
        return {f"{symbol}_INSUFFICIENT_BARS"}
    if any(not _utc(b.end) or not _utc(b.received) for b in bars):
        return {f"{symbol}_INVALID_TIMESTAMP"}
    if any(new.end - old.end != MINUTE for old, new in zip(bars, bars[1:])):
        flags.add(f"{symbol}_BAR_GAP_OR_DUPLICATE")
    if any(not session.opening < b.end <= session.closing for b in bars):
        flags.add(f"{symbol}_OUTSIDE_SESSION")
    if len({b.instrument for b in bars}) != 1 or not bars[0].instrument:
        flags.add(f"{symbol}_INSTRUMENT_CHANGE")
    for b in bars:
        if b.symbol != symbol or not b.complete or b.delayed:
            flags.add(f"{symbol}_UNVERIFIED_BAR")
        if (not all(isfinite(v) for v in (b.low, b.close, b.high))
                or not 0 < b.low <= b.close <= b.high
                or type(b.volume) is not int or b.volume <= 0):
            flags.add(f"{symbol}_INVALID_BAR")
        if not b.end <= b.received <= as_of:
            flags.add(f"{symbol}_NOT_AVAILABLE")
        elif b.received - b.end > timedelta(seconds=5):
            flags.add(f"{symbol}_FEED_LATENCY")
    if as_of - bars[-1].end > timedelta(seconds=10):
        flags.add(f"{symbol}_STALE")
    return flags


def detect(root, futures, etf, session, as_of):
    """Evaluate 20 preceding completed minutes and one common event minute."""
    symbol = PAIRS[root]
    if (not all(_utc(t) for t in (session.opening, session.closing, as_of))
            or not session.opening <= as_of < session.closing):
        raise ValueError("Decision must be inside a verified UTC cash session")
    flags = _bar_flags(futures, root, session, as_of)
    flags.update(_bar_flags(etf, symbol, session, as_of))
    if not flags and any(f.end != e.end for f, e in zip(futures, etf)):
        flags.add("BAR_TIME_MISMATCH")
    if flags:
        return Spike(session, as_of, symbol, flags=tuple(sorted(flags)))

    history, event = futures[:-1], futures[-1]
    previous = history[-1].close
    move = event.close - previous
    direction = 1 if move > 0 else -1
    level = max(b.high for b in history) if direction > 0 else min(b.low for b in history)
    volume_ratio = event.volume / median(b.volume for b in history)
    typical_range = max(0.25, median(b.high - b.low for b in history))
    displacement = abs(move) / typical_range
    etf_return = (etf[-1].close - etf[-2].close) / etf[-2].close
    if volume_ratio < 2.5:
        flags.add("VOLUME_BELOW_THRESHOLD")
    if displacement < 2:
        flags.add("DISPLACEMENT_BELOW_THRESHOLD")
    if direction * (event.close - level) <= 0:
        flags.add("NO_RANGE_BREAK")
    if direction * etf_return < 0.0003:
        flags.add("ETF_UNCONFIRMED")
    # A repeat-of-move scenario from the current ETF price, in dollars.
    estimate = etf[-1].close * min(abs(move / previous), abs(etf_return))
    lag = max((b.received - b.end).total_seconds() for b in (event, etf[-1]))
    return Spike(session, as_of, symbol, direction if not flags else 0,
                 tuple(sorted(flags)), volume_ratio, displacement,
                 level if "NO_RANGE_BREAK" not in flags else None,
                 etf_return, estimate, lag)


@dataclass(frozen=True, slots=True)
class Option:
    symbol: str
    contract: str
    right: str
    expires: datetime
    observed: datetime
    received: datetime
    bid: Decimal
    ask: Decimal
    bid_size: int
    ask_size: int
    volume: int
    open_interest: int
    delta: float
    gamma: float
    theta_per_day: float
    vega_per_point: float
    multiplier: int = 100
    delayed: bool = False


@dataclass(frozen=True, slots=True)
class Candidate:
    contract: str
    bid: Decimal
    ask: Decimal
    entry_premium: Decimal
    immediate_loss: Decimal
    favorable_pnl: float
    adverse_pnl: float
    max_loss: Decimal
    score: float


@dataclass(frozen=True, slots=True)
class PaperEntry:
    session: Session
    at: datetime
    symbol: str
    contract: str
    closed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Ranking:
    candidates: tuple[Candidate, ...] = ()
    rejected: tuple[tuple[str, str], ...] = ()
    flags: tuple[str, ...] = ()


def _quote_reason(q, spike, as_of, horizon):
    right = "CALL" if spike.direction > 0 else "PUT"
    if not q.contract or q.symbol != spike.etf or q.right != right or q.multiplier != 100:
        return "CONTRACT_MISMATCH"
    if (not all(_utc(t) for t in (q.expires, q.observed, q.received))
            or q.expires <= as_of + horizon):
        return "EXPIRY_OR_TIMESTAMP"
    if q.delayed or not spike.at <= q.observed <= q.received <= as_of:
        return "QUOTE_UNAVAILABLE"
    if as_of - q.observed > timedelta(seconds=5):
        return "QUOTE_STALE"
    if (not all(isinstance(p, Decimal) and p.is_finite() for p in (q.bid, q.ask))
            or not 0 < q.bid <= q.ask <= 1000000):
        return "INVALID_MARKET"
    sizes = (q.bid_size, q.ask_size, q.volume, q.open_interest)
    if (any(type(n) is not int for n in sizes)
            or min(q.bid_size, q.ask_size) < 1 or q.volume < 10 or q.open_interest < 50
            or (q.ask - q.bid) / q.ask > Decimal(".25")):
        return "INSUFFICIENT_LIQUIDITY"
    if (not all(isfinite(v) for v in (q.delta, q.gamma, q.theta_per_day, q.vega_per_point))
            or not 0 < spike.direction * q.delta <= 1
            or q.gamma < 0 or q.theta_per_day > 0 or q.vega_per_point < 0):
        return "INVALID_GREEKS"
    return None


def _paper_flags(spike, as_of, entries):
    if not spike.direction or spike.flags:
        return ("NO_CONFIRMED_SPIKE",)
    if (not _utc(as_of) or not spike.at <= as_of < spike.session.closing
            or as_of - spike.at > timedelta(seconds=15)):
        return ("SIGNAL_EXPIRED",)
    today = tuple(e for e in entries if e.session == spike.session)
    if any(not _utc(e.at) or not spike.session.opening <= e.at <= as_of
           or (e.closed_at is not None
               and (not _utc(e.closed_at) or not e.at <= e.closed_at <= as_of))
           for e in today):
        return ("INVALID_PAPER_HISTORY",)
    if len(today) >= MAX_TRADES:
        return ("DAILY_LIMIT",)
    if any(e.symbol == spike.etf and e.closed_at is None for e in today):
        return ("EXPOSURE_OPEN",)
    return ()


def rank(spike, quotes, as_of, *, entries=()):
    """Rank a snapshot using the complete as-of paper entry history."""
    flags = _paper_flags(spike, as_of, entries)
    if flags:
        return Ranking(flags=flags)
    horizon = timedelta(minutes=5)
    if as_of + horizon >= spike.session.closing:
        return Ranking(flags=("INSUFFICIENT_SESSION_TIME",))
    quotes = tuple(quotes)
    if len({q.contract for q in quotes}) != len(quotes):
        return Ranking(flags=("DUPLICATE_CONTRACT",))
    if not quotes:
        return Ranking(flags=("NO_OPTION_QUOTES",))
    candidates, rejected = [], []
    slip, fee = Decimal(".005"), Decimal(".65")
    for q in quotes:
        reason = _quote_reason(q, spike, as_of, horizon)
        if reason:
            rejected.append((q.contract, reason))
            continue
        premium = q.ask * (1 + slip) * 100
        if premium > MAX_PREMIUM:
            rejected.append((q.contract, "PREMIUM_LIMIT"))
            continue
        max_loss = premium + fee
        immediate_loss = premium - q.bid * (1 - slip) * 100 + 2 * fee

        def scenario_pnl(move, iv_points):
            change = (q.delta * move + 0.5 * q.gamma * move ** 2
                      + q.theta_per_day * (horizon / timedelta(days=1))
                      + q.vega_per_point * iv_points)
            proceeds = max(0, float(q.bid) + change) * float(1 - slip) * 100
            return proceeds - float(premium + (2 if proceeds > 0 else 1) * fee)

        move = spike.direction * spike.estimated_move
        favorable = scenario_pnl(move, 0)
        adverse = scenario_pnl(-move, -1)
        if favorable <= 0:
            rejected.append((q.contract, "NO_MODELED_UPSIDE_AFTER_COSTS"))
            continue
        liquidity = min(1, log1p(min(q.bid_size, q.ask_size, q.volume, q.open_interest)) / log1p(20))
        score = liquidity * favorable / (float(max_loss + immediate_loss) + max(0, -adverse))
        candidates.append(Candidate(q.contract, q.bid, q.ask, premium,
                                    immediate_loss, favorable, adverse, max_loss, score))
    candidates.sort(key=lambda c: (-c.score, c.contract))
    return Ranking(tuple(candidates), tuple(sorted(rejected)))


def record_paper_entry(spike, quotes, as_of, entries=()):
    """Return an updated immutable paper history and its ranking.

    Replay callers carry the returned history into the next decision.
    """
    ranking = rank(spike, quotes, as_of, entries=entries)
    if not ranking.candidates:
        return entries, ranking
    selected = ranking.candidates[0]
    entry = PaperEntry(spike.session, as_of, spike.etf, selected.contract)
    return (*entries, entry), ranking
