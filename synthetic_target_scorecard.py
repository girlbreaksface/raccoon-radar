"""Aggregate paired fictional replay sessions without inventing win rates."""
from dataclasses import dataclass
from decimal import Decimal, localcontext, Context
from synthetic_options_execution import Config, simulate

@dataclass(frozen=True, slots=True)
class Score:
    target: str
    sessions: int
    entries: int
    closed: int
    wins: int
    losses: int
    flat: int
    targets: int
    stops: int
    unresolved: int
    realized_net: str
    win_rate: str | None
    mean_closed_net: str | None

@dataclass(frozen=True, slots=True)
class Scorecard:
    five: Score
    twenty: Score
    evidence: str = "FICTIONAL_REPLAY_ONLY"
    trading: str = "NO-GO"

def _score(target, runs):
    entries = closed = wins = losses = flat = targets = stops = unresolved = 0
    total = Decimal(0)
    for result in runs:
        entries += sum(row[1] == "BUY" for row in result.ledger)
        unresolved += len(result.open_positions)
        total += Decimal(result.realized_net)
        for row in result.ledger:
            if row[1] not in ("SELL_TARGET", "SELL_STOP"):
                continue
            closed += 1
            targets += row[1] == "SELL_TARGET"
            stops += row[1] == "SELL_STOP"
            pnl = Decimal(row[4][3])
            wins += pnl > 0
            losses += pnl < 0
            flat += pnl == 0
    with localcontext(Context(prec=50)):
        rate = str(Decimal(wins) / Decimal(closed)) if closed else None
        average = str(total / Decimal(closed)) if closed else None
    return Score(target, len(runs), entries, closed, wins, losses, flat,
                 targets, stops, unresolved, str(total), rate, average)

def score_replays(sessions, *, slippage_bps="0", fee_per_fill="0",
                  max_quote_age_seconds=5, synthetic=False):
    """Each session is (immutable replay_input, immutable quote tuple).

    Counts only closed trades in win rate; does not mark unresolved positions as
    wins or losses. Requires both arms to see the same fictional sessions.
    """
    if synthetic is not True or type(sessions) is not tuple or len(sessions) > 1000:
        raise ValueError("Bounded immutable fictional sessions required")
    five, twenty = [], []
    for session in sessions:
        if type(session) is not tuple or len(session) != 2 or type(session[1]) is not tuple:
            raise ValueError("Each session must contain replay and immutable quotes")
        data, quotes = session
        for target, output in (("0.05", five), ("0.20", twenty)):
            config = Config(slippage_bps=slippage_bps, fee_per_fill=fee_per_fill,
                            max_quote_age_seconds=max_quote_age_seconds,
                            profit_target_fraction=target)
            output.append(simulate(data, quotes, config, synthetic=True))
    return Scorecard(_score("0.05", five), _score("0.20", twenty))
