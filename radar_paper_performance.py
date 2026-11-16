"""Summaries of closed synthetic fills at the recorded cent precision."""
from collections import defaultdict
from decimal import Decimal
import re

EXIT = re.compile(r"\b(?:TARGET|STOP|REPLAY END)\s+(SPY|QQQ)\s+(CALL|PUT)\s+\d+\s+P/L \$([+-]\d+\.\d{2})$")


def summarize(profits):
    profits = tuple(profits)
    equity = peak = drawdown = Decimal(0)
    winning = [profit for profit in profits if profit > 0]
    losing = [profit for profit in profits if profit < 0]
    gross_win, gross_loss = sum(winning, Decimal(0)), -sum(losing, Decimal(0))
    loss_streak = max_loss_streak = 0
    for profit in profits:
        loss_streak = loss_streak + 1 if profit < 0 else 0
        max_loss_streak = max(max_loss_streak, loss_streak)
        equity += profit
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    count = len(profits)
    return {"closed": count, "wins": len(winning), "losses": len(losing),
            "breakeven": count - len(winning) - len(losing), "total": equity, "drawdown": drawdown,
            "win_rate": Decimal(100) * len(winning) / count if count else None,
            "expectancy": equity / count if count else None,
            "average_win": gross_win / len(winning) if winning else None,
            "average_loss": gross_loss / len(losing) if losing else None,
            "profit_factor": gross_win / gross_loss if gross_loss else None,
            "max_loss_streak": max_loss_streak}


def paper_performance(history):
    profits = []
    setups = defaultdict(list)
    # Journal is newest run first and chronological within each run.
    for _, scenario, text in sorted(history, key=lambda row: row[0]):
        match = EXIT.search(text)
        if match:
            symbol, side, amount = match.groups()
            profit = Decimal(amount)
            profits.append(profit)
            setups[(scenario, symbol, side)].append(profit)
    return summarize(profits), {key: summarize(values) for key, values in sorted(setups.items())}


def format_summary(summary):
    if not summary["closed"]:
        return "No closed simulated trades."
    return (f"{summary['closed']} closed · {summary['win_rate']:.1f}% wins · "
            f"P/L ${summary['total']:+.2f} · Expectancy ${summary['expectancy']:+.2f} per trade · "
            f"Max drawdown ${summary['drawdown']:.2f}")


def format_trade_distribution(summary):
    def number(key, prefix=""):
        value = summary[key]
        return f"{prefix}{value:.2f}" if value is not None else "unavailable"

    return (f"{summary['wins']} wins · {summary['losses']} losses · {summary['breakeven']} flat"
            f" · Avg win {number('average_win', '$')} · Avg loss {number('average_loss', '$')}"
            f" · Profit factor {number('profit_factor')} · Loss streak {summary['max_loss_streak']}")
