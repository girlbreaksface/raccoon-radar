"""Synthetic paper-signal events over the existing PR31 replay. No I/O or orders."""
from dataclasses import dataclass

from canonical_candles import FrozenRecord, identity
from synthetic_replay import ReplayInput, replay

VERSION = 'synthetic-paper-signals-v1'
POLICY = 'FIRST_PER_SYMBOL_DIRECTION_SESSION'


@dataclass(frozen=True, slots=True)
class PaperSignal(FrozenRecord):
    event_id: str
    session_date: str
    cutoff: str
    watermark: str
    symbol: str
    direction: str
    pair_state: str
    decision_hash: str
    mode: str = 'SYNTHETIC_PAPER_SIGNAL'
    execution: str = 'DISABLED'


@dataclass(frozen=True, slots=True)
class PaperStep(FrozenRecord):
    cutoff: str
    pair_state: str
    symbols: tuple  # (symbol, replay state, reasons, emission status)


@dataclass(frozen=True, slots=True)
class PaperRun(FrozenRecord):
    version: str
    policy: str
    replay_hash: str
    signals: tuple
    steps: tuple
    run_hash: str
    mode: str = 'SYNTHETIC_ONLY'
    execution: str = 'DISABLED'


def run(data, *, synthetic=False):
    """Replay ONE full session; emit first qualifying symbol/direction only.

    Existing canonicalization, warmup, profile and pair semantics are unchanged.
    Conflict does not veto either independent candidate. A later invalid frame
    cannot erase a prior event. Seen keys survive blocked frames and changes of
    direction. Repeating the same full-session input yields the same event IDs;
    this pure function has no cross-call ledger. No positions, fills or P/L.
    """
    if type(data) is not ReplayInput:
        raise TypeError('Immutable ReplayInput required')
    if len({step.session_date for step in data.steps}) != 1:
        raise ValueError('One explicit session per run required')
    result = replay(data, synthetic=synthetic)
    seen, events, steps = set(), [], []
    for point in result.points:
        symbols = []
        for cell in point.cells:
            status = 'WAIT'
            if cell.state == 'CANDIDATE':
                if cell.bias not in ('BULLISH', 'BEARISH'):
                    raise ValueError('Unsupported candidate direction')
                key = (point.step.session_date, cell.symbol, cell.bias)
                if key in seen:
                    status = 'ALREADY_EMITTED'
                else:
                    seen.add(key)
                    event_id = identity((VERSION, POLICY, result.profile, key,
                                         point.step, point.decision_hash))
                    events.append(PaperSignal(event_id, point.step.session_date,
                        point.step.cutoff, point.step.watermark, cell.symbol,
                        cell.bias, point.pair, point.decision_hash))
                    status = 'PAPER_SIGNAL'
            symbols.append((cell.symbol, cell.state, cell.reasons, status))
        steps.append(PaperStep(point.step.cutoff, point.pair, tuple(symbols)))
    events, steps = tuple(events), tuple(steps)
    return PaperRun(VERSION, POLICY, result.run_hash, events, steps,
                    identity((VERSION, POLICY, result.run_hash, events, steps)))
