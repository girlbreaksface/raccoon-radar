"""Pure synthetic long-option simulation over PR58; no I/O or order adapter."""
from dataclasses import dataclass
from decimal import Decimal, Context, localcontext
from canonical_candles import FrozenRecord, identity, _time
from paper_signal_engine import run

VERSION = 'synthetic-options-execution-v2'


@dataclass(frozen=True, slots=True)
class Config(FrozenRecord):
    slippage_bps: str = '0'
    fee_per_fill: str = '0'
    profit_target_fraction: str = '0.05'
    max_quote_age_seconds: int = 5


@dataclass(frozen=True, slots=True)
class Quote(FrozenRecord):
    signal_id: str
    contract: str
    right: str
    at: str  # availability time
    observed_at: str
    bid: str
    ask: str
    synthetic: bool = True


@dataclass(frozen=True, slots=True)
class Result(FrozenRecord):
    version: str
    signal_run_hash: str
    config: Config
    ledger: tuple
    open_positions: tuple
    realized_net: str
    unrealized_net: str | None
    net_pnl: str | None
    input_hash: str
    run_hash: str
    mode: str = 'SYNTHETIC_ONLY'
    trading: str = 'NO-GO'
    orders: str = 'DISABLED'


def number(value):
    if type(value) is not str or len(value) > 24:
        raise ValueError('Bounded decimal strings required')
    try:
        n = Decimal(value)
    except Exception as exc:
        raise ValueError('Invalid decimal') from exc
    if not n.is_finite() or n < 0 or n > 1000000 or n.as_tuple().exponent < -8:
        raise ValueError('Invalid bounded nonnegative decimal')
    return n


def simulate(data, quotes, config=Config(), *, synthetic=False):
    """One session, one contract per trade, $30 entry premium including slippage.

    Bullish buys a fictional call; bearish buys a fictional put. Both exit by
    selling. Targets/stops compare executable liquidation premium to entry premium
    (configurable 5% or 20% / -15%, fees excluded from trigger, included in P/L). Three entries/day.
    """
    if synthetic is not True or type(quotes) is not tuple or type(config) is not Config:
        raise ValueError('Explicit synthetic mode and immutable typed inputs required')
    bps, fee = number(config.slippage_bps), number(config.fee_per_fill)
    target = number(config.profit_target_fraction)
    if target not in (Decimal('0.05'), Decimal('0.20')):
        raise ValueError('Only 5% and 20% synthetic target arms supported')
    if bps >= 10000 or type(config.max_quote_age_seconds) is not int or not 0 <= config.max_quote_age_seconds <= 60:
        raise ValueError('Invalid slippage or freshness policy')
    signals = run(data, synthetic=True)
    events = {e.event_id: e for e in signals.signals}
    if len(quotes) > 10000:
        raise ValueError('Too many quotes')
    opening = max(_time(s.context.calendar.open_at) for s in data.series)
    closing = min(_time(s.context.calendar.close_at) for s in data.series)
    # Structural ambiguity aborts the entire pure run before any result is returned.
    previous = None
    for q in quotes:
        if type(q) is not Quote or q.synthetic is not True or q.signal_id not in events:
            raise ValueError('Typed fictional quotes bound to emitted signals required')
        if type(q.contract) is not str or not q.contract.isascii() or not q.contract.isalnum() or len(q.contract) > 64 or not q.contract:
            raise ValueError('Fictional contract identifier required')
        if q.right != ('CALL' if events[q.signal_id].direction == 'BULLISH' else 'PUT'):
            raise ValueError('Option right conflicts with signal')
        at = _time(q.at)
        key = (at, q.signal_id)
        if previous is not None and key <= previous:
            raise ValueError('Strict availability time / signal ID order required')
        if not opening <= at < closing:
            raise ValueError('Quote outside common session')
        previous = key
    with localcontext(Context(prec=50, rounding='ROUND_HALF_EVEN')):
        return _execute(data, signals, quotes, config, bps / 10000, fee, target)


def _execute(data, signals, quotes, config, slip, fee, target):
    events = {e.event_id: e for e in signals.signals}
    positions, done, blocked, latest, bindings = {}, set(), set(), {}, {}
    ledger, realized, entries = [], Decimal(0), 0
    gates = sorted(signals.steps, key=lambda s: _time(s.cutoff))
    gate_index = 0
    horizon = max([_time(data.steps[-1].cutoff)] + [_time(q.at) for q in quotes])

    def log(kind, event_id, at, details):
        parent = ledger[-1][-1] if ledger else signals.run_hash
        row = (len(ledger) + 1, kind, event_id, at, details, parent)
        ledger.append(row + (identity((VERSION, row)),))

    for q in quotes:
        e, at = events[q.signal_id], _time(q.at)
        while gate_index < len(gates) and _time(gates[gate_index].cutoff) <= at:
            for symbol, state, _, _ in gates[gate_index].symbols:
                if state in ('DATA_BLOCKED', 'PROFILE_BLOCKED'):
                    blocked.add(symbol)  # conservative latch for rest of session
            gate_index += 1
        if q.signal_id in bindings and bindings[q.signal_id] != q.contract:
            raise ValueError('Contract cannot change during a signal lifecycle')
        bindings[q.signal_id] = q.contract
        try:
            observed = _time(q.observed_at)
            bid, ask = number(q.bid), number(q.ask)
            if bid == 0 or ask == 0 or bid > ask or not 0 <= (at - observed).total_seconds() <= config.max_quote_age_seconds:
                raise ValueError('Invalid or stale quote')
        except (ValueError, TypeError):
            latest.pop(q.signal_id, None)
            log('QUOTE_BLOCKED', q.signal_id, q.at, ())
            continue
        latest[q.signal_id] = (at, observed, bid)
        if q.signal_id in positions:
            entry, opened = positions[q.signal_id]
            exit_price = bid * (1 - slip)
            reason = 'TARGET' if exit_price >= entry * (1 + target) else 'STOP' if exit_price <= entry * Decimal('.85') else None
            if reason:
                pnl = (exit_price - entry) * 100 - 2 * fee
                realized += pnl
                log('SELL_' + reason, q.signal_id, q.at,
                    (q.contract, str(exit_price), str(fee), str(pnl), q.observed_at))
                del positions[q.signal_id]
                done.add(q.signal_id)
        elif q.signal_id not in done and at > _time(e.cutoff):
            entry = ask * (1 + slip)
            reason = ('DATA_BLOCKED' if e.symbol in blocked else
                      'DAILY_LIMIT' if entries >= 3 else
                      'EXPOSURE' if any(events[k].symbol == e.symbol for k in positions) else
                      'PREMIUM_LIMIT' if entry * 100 > 30 else None)
            if reason:
                log('REJECT_' + reason, q.signal_id, q.at, ())
                done.add(q.signal_id)
                continue
            entries += 1
            positions[q.signal_id] = (entry, q.at)
            log('BUY', q.signal_id, q.at, (q.contract, str(entry), str(fee), q.observed_at))
    opened, unrealized = [], Decimal(0)
    for event_id, (entry, at) in sorted(positions.items()):
        mark = latest.get(event_id)
        valid = mark is not None and (horizon - mark[1]).total_seconds() <= config.max_quote_age_seconds
        net = (mark[2] * (1 - slip) - entry) * 100 - 2 * fee if valid else None
        if net is None:
            unrealized = None
        elif unrealized is not None:
            unrealized += net
        opened.append((event_id, bindings[event_id], at, str(entry), str(net) if net is not None else None))
    for e in signals.signals:
        if e.event_id not in done and e.event_id not in positions:
            log('UNFILLED', e.event_id, horizon.isoformat(), ())
    input_hash = identity((VERSION, signals.run_hash, quotes, config))
    values = (VERSION, signals.run_hash, config, tuple(ledger), tuple(opened),
              str(realized), str(unrealized) if unrealized is not None else None,
              str(realized + unrealized) if unrealized is not None else None, input_hash)
    return Result(*values, identity(values))
