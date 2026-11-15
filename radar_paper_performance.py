"""Summaries of closed synthetic fills at the recorded cent precision."""
from collections import defaultdict
from decimal import Decimal
import re

EXIT = re.compile(r"\b(?:TARGET|STOP|REPLAY END)\s+(SPY|QQQ)\s+(CALL|PUT)\s+\d+\s+P/L \$([+-]\d+\.\d{2})$")


def summarize(profits):
    equity = peak = drawdown = Decimal(0)
    wins = 0
    for profit in profits:
        wins += profit > 0
        equity += profit
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    count = len(profits)
    return {"closed": count, "wins": wins, "total": equity, "drawdown": drawdown,
            "win_rate": Decimal(100) * wins / count if count else None,
            "expectancy": equity / count if count else None}


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
