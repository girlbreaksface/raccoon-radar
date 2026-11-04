"""Pure fictional bid/ask execution model over PR58 signals. No broker or I/O."""
from dataclasses import dataclass
from datetime import timedelta
from decimal import Context, Decimal, localcontext

from canonical_candles import FrozenRecord, identity, _time
from paper_signal_engine import run

VERSION = 'synthetic-paper-execution-v1'


@dataclass(frozen=True, slots=True)
class Quote(FrozenRecord):
    session_date: str
    at: str
    symbol: str
    bid: str
    ask: str
    synthetic: bool = True


@dataclass(frozen=True, slots=True)
class Config(FrozenRecord):
    initial_cash: str = '10000'
    quantity: int = 1
    fee_per_fill: str = '0'
    slippage_bps: str = '0'
    latency_seconds: int = 0
    entry_timeout_seconds: int = 30
    hold_seconds: int = 60


@dataclass(frozen=True, slots=True)
class Fill(FrozenRecord):
    signal_id: str
    symbol: str
    at: str
    side: str
    purpose: str
    quantity: int
    price: str
    fee: str


@dataclass(frozen=True, slots=True)
class Position(FrozenRecord):
    signal_id: str
    symbol: str
    direction: str
    opened_at: str
    entry_price: str
    quantity: int
    last_quote_at: str
    liquidation_mark: str
    unrealized_net: str


@dataclass(frozen=True, slots=True)
class Simulation(FrozenRecord):
    version: str
    as_of: str
    signal_run_hash: str
    config: Config
    fills: tuple
    signal_statuses: tuple
    open_positions: tuple
    cash: str
    short_collateral: str
    available_cash: str
    realized_net: str
    unrealized_net: str
    equity: str
    input_hash: str
    run_hash: str
    mode: str = 'SYNTHETIC_ONLY'
    broker_execution: str = 'DISABLED'


def _number(value, *, positive=False):
    # Bound precision/magnitude so local Decimal arithmetic is reproducible.
    if type(value) is not str or len(value) > 24:
        raise ValueError('Decimal strings of at most 24 characters required')
    try:
        number = Decimal(value)
    except Exception as exc:
        raise ValueError('Invalid decimal') from exc
    if (not number.is_finite() or number < 0 or number > Decimal('1000000000')
            or number.as_tuple().exponent < -8 or (positive and number == 0)):
        raise ValueError('Nonnegative bounded values with at most 8 decimals required')
    return number


def simulate(data, quotes, config=Config(), *, synthetic=False):
    """ONE synthetic session. No ambient time, persistence, or automatic liquidation.

    Next quote strictly after decision; entry deadline inclusive; hold starts at
    fill. Signals arriving while open/pending are ignored, never deferred/reversed.
    Quotes are fictional immediately executable bid/ask with unlimited size.
    Short proceeds are locked with an additional 100% entry-notional collateral.
    """
    if synthetic is not True or type(config) is not Config or type(quotes) is not tuple:
        raise ValueError('Explicit synthetic mode, Config and immutable quotes required')
    initial = _number(config.initial_cash, positive=True)
    fee, bps = _number(config.fee_per_fill), _number(config.slippage_bps)
    if bps >= 10000:
        raise ValueError('Slippage must be below 10000 bps')
    for value, lower, upper in ((config.quantity, 1, 1000000),
            (config.latency_seconds, 0, 3600), (config.entry_timeout_seconds, 1, 3600),
            (config.hold_seconds, 1, 86400)):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError('Invalid integer simulation parameter')
    if config.latency_seconds > config.entry_timeout_seconds:
        raise ValueError('Latency exceeds entry timeout')
    signals = run(data, synthetic=True)
    session = data.steps[0].session_date
    openings = [_time(s.context.calendar.open_at) for s in data.series]
    closings = [_time(s.context.calendar.close_at) for s in data.series]
    if len(quotes) > 10000:
        raise ValueError('At most 10000 fictional quotes per run')
    prepared, previous = [], None
    for q in quotes:
        if type(q) is not Quote or q.synthetic is not True or q.symbol not in ('SPY', 'QQQ'):
            raise ValueError('Typed fictional SPY/QQQ quotes required')
        at = _time(q.at)
        key = (at, q.symbol)
        if previous is not None and key <= previous:
            raise ValueError('Strict (time, symbol) quote order required; no duplicates')
        if q.session_date != session or not max(openings) <= at < min(closings):
            raise ValueError('Quote outside declared common session')
        bid, ask = _number(q.bid, positive=True), _number(q.ask, positive=True)
        if bid > ask:
            raise ValueError('Crossed synthetic quote')
        prepared.append((q, at, bid, ask))
        previous = key
    with localcontext(Context(prec=50, rounding='ROUND_HALF_EVEN')):
        horizon = max([_time(data.steps[-1].cutoff)] + [p[1] for p in prepared])
        return _execute(signals, tuple(prepared), quotes, config, initial, fee, bps, horizon)


def _execute(signals, prepared, quotes, config, initial, fee, bps, horizon):
    cash, realized = initial, Decimal(0)
    pending, positions, last, statuses, fills = {}, {}, {}, {}, []
    index, quantity = 0, Decimal(config.quantity)
    slip = bps / Decimal(10000)
    timeline = sorted(
        [(_time(s.cutoff), 0, i, s) for i, s in enumerate(signals.steps)] +
        [(_time(e.cutoff), 1, i, e) for i, e in enumerate(signals.signals)],
        key=lambda item: item[:3])

    def reserve():
        return sum((2 * p['price'] * quantity for p in positions.values()
                    if p['sign'] == -1), Decimal(0))

    def fill(event, q, price, sign, purpose):
        nonlocal cash
        cash -= sign * price * quantity + fee
        fills.append(Fill(event.event_id, event.symbol, q.at,
                          'BUY' if sign == 1 else 'SELL', purpose,
                          config.quantity, str(price), str(fee)))

    def expire(at):
        for symbol, event in tuple(pending.items()):
            if at > _time(event.cutoff) + timedelta(seconds=config.entry_timeout_seconds):
                statuses[event.event_id] = 'ENTRY_EXPIRED'
                del pending[symbol]

    def decide(event):
        expire(_time(event.cutoff))
        if event.symbol in positions:
            statuses[event.event_id] = 'IGNORED_POSITION_OPEN'
        elif event.symbol in pending:
            statuses[event.event_id] = 'IGNORED_ENTRY_PENDING'
        else:
            pending[event.symbol] = event
            statuses[event.event_id] = 'PENDING_ENTRY'

    def advance(at):
        nonlocal index
        while index < len(timeline) and timeline[index][0] <= at:
            when, kind, _, event = timeline[index]
            index += 1
            expire(when)
            if kind == 1:
                decide(event)
            else:
                for symbol, state, _, _ in event.symbols:
                    if state in ('DATA_BLOCKED', 'PROFILE_BLOCKED') and symbol in pending:
                        statuses[pending[symbol].event_id] = 'CANCELED_' + state
                        del pending[symbol]
        expire(at)

    for q, at, bid, ask in prepared:
        # Decisions at exactly this quote time are visible, but cannot fill on it.
        advance(at)
        last[q.symbol] = (q, bid, ask)
        position = positions.get(q.symbol)
        if position is not None and at >= position['due']:
            sign = -position['sign']
            price = ask * (1 + slip) if sign == 1 else bid * (1 - slip)
            fill(position['event'], q, price, sign, 'EXIT_HOLD')
            realized += position['sign'] * (price - position['price']) * quantity - 2 * fee
            statuses[position['event'].event_id] = 'CLOSED'
            del positions[q.symbol]
        event = pending.get(q.symbol)
        if event is None:
            continue
        decision = _time(event.cutoff)
        if at <= decision or at < decision + timedelta(seconds=config.latency_seconds):
            continue
        sign = 1 if event.direction == 'BULLISH' else -1
        price = ask * (1 + slip) if sign == 1 else bid * (1 - slip)
        if cash - reserve() < price * quantity + fee:
            statuses[event.event_id] = 'REJECTED_CAPITAL'
            del pending[q.symbol]
            continue
        fill(event, q, price, sign, 'ENTRY')
        positions[q.symbol] = dict(event=event, price=price, sign=sign, opened=q.at,
                                   due=at + timedelta(seconds=config.hold_seconds))
        statuses[event.event_id] = 'OPEN'
        del pending[q.symbol]

    advance(horizon)
    opened, market_value, unrealized = [], Decimal(0), Decimal(0)
    for symbol in sorted(positions):
        p = positions[symbol]
        q, bid, ask = last[symbol]
        mark = bid * (1 - slip) if p['sign'] == 1 else ask * (1 + slip)
        # Mark includes slippage but no hypothetical exit fee; entry fee is paid.
        net = p['sign'] * (mark - p['price']) * quantity - fee
        unrealized += net
        market_value += p['sign'] * mark * quantity
        opened.append(Position(p['event'].event_id, symbol, p['event'].direction,
            p['opened'], str(p['price']), config.quantity, q.at, str(mark), str(net)))
    equity = cash + market_value
    assert equity - initial == realized + unrealized
    input_hash = identity((VERSION, signals.run_hash, quotes, config))
    values = (VERSION, horizon.isoformat(), signals.run_hash, config, tuple(fills),
              tuple((e.event_id, statuses[e.event_id]) for e in signals.signals),
              tuple(opened), str(cash), str(reserve()), str(cash - reserve()),
              str(realized), str(unrealized), str(equity), input_hash)
    return Simulation(*values, identity(values))
