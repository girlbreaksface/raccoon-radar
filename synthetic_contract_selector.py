"""Deterministic fictional 0DTE contract selection. No broker, feed or orders."""
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation, localcontext, Context

VERSION = "synthetic-contract-selector-v1"

@dataclass(frozen=True, slots=True)
class Candidate:
    contract: str
    symbol: str
    right: str
    expiration: str
    strike: str
    bid: str
    ask: str
    bid_size: int
    ask_size: int
    observed_at: str
    synthetic: bool = True

@dataclass(frozen=True, slots=True)
class Decision:
    selected: str | None
    eligible: tuple
    rejected: tuple
    mode: str = "SYNTHETIC_ONLY"
    orders: str = "DISABLED"

def _decimal(raw):
    if type(raw) is not str or not 0 < len(raw) <= 24:
        raise ValueError("bounded decimal string required")
    try:
        n = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError("invalid decimal") from exc
    if not n.is_finite() or n < 0 or n > 1000000 or n.as_tuple().exponent < -8:
        raise ValueError("invalid bounded decimal")
    return n

def _instant(raw):
    if type(raw) is not str:
        raise ValueError("timestamp string required")
    try:
        value = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("offset-aware timestamp required")
    return value

def select_contract(symbol, direction, session_date, at, candidates, *,
                    max_spread_fraction="0.25", max_age_seconds=5,
                    min_bid_size=1, min_ask_size=1):
    """Choose the tightest eligible fictional option; no market-data requests.

    Candidates must all be explicitly synthetic. Bad quotes are rejected per
    contract, while structural ambiguity fails the whole selection.
    """
    if symbol not in ("SPY", "QQQ") or direction not in ("BULLISH", "BEARISH"):
        raise ValueError("SPY/QQQ direction required")
    if type(session_date) is not str or type(candidates) is not tuple or len(candidates) > 10000:
        raise ValueError("bounded immutable candidate tuple required")
    try:
        day = date.fromisoformat(session_date)
    except ValueError as exc:
        raise ValueError("invalid session date") from exc
    if day.isoformat() != session_date:
        raise ValueError("canonical session date required")
    now = _instant(at)
    if now.date() != day:
        raise ValueError("at must be in the declared fictional session date")
    spread_limit = _decimal(max_spread_fraction)
    if spread_limit > 1 or type(max_age_seconds) is not int or not 0 <= max_age_seconds <= 60:
        raise ValueError("invalid spread or freshness policy")
    if (type(min_bid_size) is not int or type(min_ask_size) is not int
            or not 1 <= min_bid_size <= 100000 or not 1 <= min_ask_size <= 100000):
        raise ValueError("invalid liquidity policy")
    expected_right = "CALL" if direction == "BULLISH" else "PUT"
    seen, eligible, rejected = set(), [], []
    with localcontext(Context(prec=50)):
        for c in candidates:
            if type(c) is not Candidate or c.synthetic is not True:
                raise ValueError("only typed fictional candidates accepted")
            if (type(c.contract) is not str or not c.contract.isascii()
                    or not c.contract.isalnum() or not 1 <= len(c.contract) <= 64
                    or c.contract in seen):
                raise ValueError("invalid or duplicate contract identity")
            seen.add(c.contract)
            if c.symbol != symbol or c.right != expected_right:
                rejected.append((c.contract, "WRONG_UNDERLYING_OR_RIGHT"))
                continue
            if c.expiration != session_date:
                rejected.append((c.contract, "NOT_0DTE"))
                continue
            try:
                strike, bid, ask = _decimal(c.strike), _decimal(c.bid), _decimal(c.ask)
                observed = _instant(c.observed_at)
            except (ValueError, TypeError):
                rejected.append((c.contract, "INVALID_QUOTE"))
                continue
            if strike <= 0 or bid <= 0 or ask <= 0 or bid > ask:
                rejected.append((c.contract, "INVALID_QUOTE"))
                continue
            age = (now - observed).total_seconds()
            if not 0 <= age <= max_age_seconds:
                rejected.append((c.contract, "STALE_OR_FUTURE"))
                continue
            if type(c.bid_size) is not int or type(c.ask_size) is not int or c.bid_size < min_bid_size or c.ask_size < min_ask_size:
                rejected.append((c.contract, "INSUFFICIENT_SIZE"))
                continue
            if ask * 100 > 30:
                rejected.append((c.contract, "PREMIUM_LIMIT"))
                continue
            fraction = (ask - bid) / ask
            if fraction > spread_limit:
                rejected.append((c.contract, "SPREAD_TOO_WIDE"))
                continue
            eligible.append((c.contract, fraction, ask))
    eligible.sort(key=lambda item: (item[1], item[2], item[0]))
    return Decision(eligible[0][0] if eligible else None,
                    tuple(item[0] for item in eligible), tuple(sorted(rejected)))
