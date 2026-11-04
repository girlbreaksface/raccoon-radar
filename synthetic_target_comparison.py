"""Paired, deterministic fictional target comparison; not an empirical win rate."""
from dataclasses import dataclass
from synthetic_options_execution import Config, simulate

@dataclass(frozen=True, slots=True)
class Arm:
    target: str
    realized_net: str
    net_pnl: str | None
    buys: int
    target_exits: int
    stop_exits: int
    open_positions: int
    run_hash: str

@dataclass(frozen=True, slots=True)
class Comparison:
    five: Arm
    twenty: Arm
    evidence: str = "FICTIONAL_REPLAY_ONLY"
    trading: str = "NO-GO"

def compare_targets(data, quotes, *, slippage_bps="0", fee_per_fill="0",
                    max_quote_age_seconds=5, synthetic=False):
    if synthetic is not True or type(quotes) is not tuple:
        raise ValueError("Explicit immutable synthetic inputs required")
    arms = []
    for target in ("0.05", "0.20"):
        config = Config(slippage_bps=slippage_bps, fee_per_fill=fee_per_fill,
                        max_quote_age_seconds=max_quote_age_seconds,
                        profit_target_fraction=target)
        result = simulate(data, quotes, config, synthetic=True)
        kinds = tuple(row[1] for row in result.ledger)
        arms.append(Arm(target, result.realized_net, result.net_pnl,
                        kinds.count("BUY"), kinds.count("SELL_TARGET"),
                        kinds.count("SELL_STOP"), len(result.open_positions),
                        result.run_hash))
    return Comparison(*arms)
