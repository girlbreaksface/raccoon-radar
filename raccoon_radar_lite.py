"""Raccoon Radar Lite: isolated, synthetic-only paper replay."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from functools import lru_cache

from futures_spike_radar import MAX_PREMIUM, MAX_TRADES
from historical_radar_replay import SLIP
from pinned_timezone_bridge import consumer_dict
from synthetic_replay import replay
from synthetic_replay_demo import SCENARIOS, make_demo
from tools.opend_local_preflight import check_local_opend


@dataclass(frozen=True)
class Contract:
    symbol: str
    side: str
    strike: int
    expiry: str


@dataclass(frozen=True)
class Quote:
    contract: Contract
    at: datetime
    bid: Decimal
    ask: Decimal

    @property
    def premium(self):
        return self.ask * (1 + SLIP) * 100

    @property
    def proceeds(self):
        return self.bid * (1 - SLIP) * 100


CHAIN = tuple(Contract(symbol, side, strike, "2026-10-30")
              for symbol, base in (("SPY", 140), ("QQQ", 165))
              for side, strikes in (("CALL", (base, base + 1)), ("PUT", (base, base - 1)))
              for strike in strikes)


def stamp(value):
    return datetime.fromisoformat(value)


@lru_cache(maxsize=len(SCENARIOS))
def demo(scenario):
    return replay(make_demo(scenario), synthetic=True).points


def direction(cell):
    return {"BULLISH": "CALL", "BEARISH": "PUT"}.get(cell.bias, "WAIT")


def fixture_quotes(point, index):
    """Explicit fictional chain snapshots on the replay clock."""
    now = stamp(point.step.cutoff)
    for contract in CHAIN:
        # Alternating tape lets the replay exercise both target and stop.
        bid = Decimal("0.18" if index % 2 == 0 else "0.25")
        better = contract.strike in (140, 165)
        if not better:
            bid -= Decimal("0.01")
        quote_time = now - timedelta(seconds=30 if index == 35 and not better else 1)
        yield Quote(contract, quote_time, bid, bid + Decimal("0.02" if better else "0.03"))


def usable(quote, now):
    return (quote.contract in CHAIN and quote.at.tzinfo is not None
            and timedelta(0) <= now - quote.at <= timedelta(seconds=15)
            and now.date() < datetime.fromisoformat(quote.contract.expiry).date()
            and quote.bid.is_finite() and quote.ask.is_finite()
            and 0 < quote.bid <= quote.ask)


def ranked(cell, quotes, now):
    side = direction(cell)
    if cell.state != "CANDIDATE":
        return ()
    eligible = (q for q in quotes if q.contract.symbol == cell.symbol
                and q.contract.side == side and usable(q, now)
                and q.premium <= MAX_PREMIUM)
    return tuple(sorted(eligible, key=lambda q: (q.ask - q.bid, q.premium, q.contract.strike)))


class PaperReplay:
    def __init__(self, points, index=34):
        self.points = points
        self.index = index
        self.open = None
        self.entries = 0
        self.events = []

    @property
    def point(self):
        return self.points[self.index]

    @property
    def now(self):
        return stamp(self.point.step.cutoff)

    @property
    def quotes(self):
        return tuple(fixture_quotes(self.point, self.index))

    def candidates(self, cell):
        return ranked(cell, self.quotes, self.now)

    @property
    def can_enter(self):
        return (self.open is None and self.entries < MAX_TRADES
                and self.index < len(self.points) - 1)

    def enter(self, cell, contract):
        if not self.can_enter or cell not in self.point.cells:
            return False
        quote = next((q for q in self.candidates(cell) if q.contract == contract), None)
        if quote is None:
            return False
        self.open = quote
        self.entries += 1
        self.events.append(f"{self.now:%H:%M:%S}  OPEN  {contract.symbol} {contract.side}  ${quote.premium:.2f}")
        return True

    def step(self):
        if self.index == len(self.points) - 1:
            return
        self.index += 1
        if self.open is None:
            return
        quote = next((q for q in self.quotes
                      if q.contract == self.open.contract and usable(q, self.now)), None)
        if quote is None:
            return
        premium = self.open.premium
        if quote.proceeds >= premium * Decimal("1.20"):
            reason = "TARGET"
        elif quote.proceeds <= premium * Decimal(".85"):
            reason = "STOP"
        elif self.index == len(self.points) - 1:
            reason = "REPLAY END"
        else:
            return
        contract = quote.contract
        self.events.append(f"{self.now:%H:%M:%S}  {reason}  {contract.symbol} {contract.side}"
                           f"  P/L ${quote.proceeds - premium:+.2f}")
        self.open = None


class RadarWindow:
    def __init__(self, root, *, live=False, scenario="conflict", minute=35):
        from tkinter import ttk

        self.ttk = ttk
        self.root = root
        self.scenario = scenario
        self.minute = minute
        self.live = live
        self.session = None if live else PaperReplay(demo(scenario), minute - 1)
        root.title("Raccoon Radar Lite")
        root.geometry("880x600")
        root.minsize(780, 560)
        root.configure(bg="#101521")
        self.style()
        self.body = self.ttk.Frame(root, padding=24)
        self.body.pack(fill="both", expand=True)
        self.render()

    def style(self):
        style = self.ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#101521")
        style.configure("Card.TFrame", background="#1c2537")
        style.configure("TLabel", background="#101521", foreground="#ecf0f7",
                        font=("Segoe UI", 11))
        style.configure("Card.TLabel", background="#1c2537", foreground="#ecf0f7")
        style.configure("Title.TLabel", font=("Segoe UI", 26, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(12, 6))

    def label(self, parent, value, **kwargs):
        self.ttk.Label(parent, text=value, **kwargs).pack(anchor="w", pady=(0, 4))

    def render(self):
        for child in self.body.winfo_children():
            child.destroy()
        self.label(self.body, "Raccoon Radar Lite", style="Title.TLabel")
        mode = "LIVE DATA STATUS" if self.live else "SYNTHETIC REPLAY"
        self.label(self.body, mode + "   /   PAPER ONLY   /   ES · NQ UNAVAILABLE")
        if self.live:
            self.label(self.body, "SPY  WAIT   ·   QQQ  WAIT")
            self.label(self.body, "Market candles, option chain and current bid/ask unavailable.")
            self.live_status = self.ttk.Label(self.body, text="OpenD reachability unchecked.")
            self.live_status.pack(anchor="w", pady=8)
            self.ttk.Button(self.body, text="Check local OpenD port", command=self.check_port).pack(anchor="w")
            self.ttk.Button(self.body, text="Open synthetic replay", command=self.toggle).pack(anchor="w", pady=10)
            return

        run = self.session
        toolbar = self.ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=10)
        self.label(toolbar, f"Replay clock  {run.now:%Y-%m-%d %H:%M:%S} UTC"
                   f"   ·   Minute {run.index + 1}/{len(run.points)}   ·   {self.scenario.title()}")
        self.next_button = self.ttk.Button(toolbar, text="Next minute", command=self.advance,
                                      state="normal" if run.index < len(run.points) - 1 else "disabled")
        self.next_button.pack(side="left")
        self.ttk.Button(toolbar, text="Live data status", command=self.toggle).pack(side="left", padx=8)
        description = ("Synthetic quotes · $30 premium cap incl. slippage · "
                       f"{run.entries}/{MAX_TRADES} entries · 1 contract max")
        self.label(self.body, description)
        cards = self.ttk.Frame(self.body)
        cards.pack(fill="x", pady=8)
        self.entry_buttons = []
        for column, cell in enumerate(run.point.cells):
            cards.columnconfigure(column, weight=1, uniform="cards")
            self.card(cards, column, cell)
        if run.open:
            premium = run.open.premium
            position = (f"Open  {run.open.contract.symbol} {run.open.contract.side}  ·  "
                        f"Entry ${premium:.2f}   Target ${premium * Decimal('1.20'):.2f}   "
                        f"Stop ${premium * Decimal('.85'):.2f}")
        else:
            position = "No open paper position"
        self.label(self.body, position)
        self.label(self.body, "Paper ledger · last 3 events")
        for item in run.events[-3:]:
            self.label(self.body, item)

    def card(self, parent, column, cell):
        run = self.session
        card = self.ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 8) if column == 0 else (8, 0))
        action = direction(cell)
        ink = {"CALL": "#79e6bd", "PUT": "#ffa4ae", "WAIT": "#ffd48a"}[action]
        self.label(card, f"{cell.symbol}   {action}", style="Card.TLabel",
                   font=("Segoe UI", 17, "bold"), foreground=ink)
        if cell.evidence.consumer is not None:
            obs = consumer_dict(cell.evidence)["observations"]
            if obs.get("interval_end") and obs.get("ema9") and obs.get("ema21"):
                end = stamp(obs["interval_end"])
                age = (run.now - end).total_seconds()
                self.label(card, f"Bar end  {end:%H:%M:%S} UTC  ·  {age:.0f}s old", style="Card.TLabel")
                self.label(card, f"EMA 9  {Decimal(obs['ema9']):.2f}   EMA 21  {Decimal(obs['ema21']):.2f}",
                           style="Card.TLabel")
        if cell.reasons:
            self.label(card, " · ".join(r.replace("_", " ").lower() for r in cell.reasons),
                       style="Card.TLabel", wraplength=330)
        quotes = run.candidates(cell)
        if not quotes:
            self.label(card, "No eligible synthetic contracts", style="Card.TLabel")
        for index, q in enumerate(quotes, start=1):
            age = (run.now - q.at).total_seconds()
            self.label(card, f"{index}. {q.contract.strike}  {q.contract.expiry}  ·  "
                       f"{q.bid:.2f}/{q.ask:.2f} bid/ask  ·  {age:.0f}s old", style="Card.TLabel")
            button = self.ttk.Button(card, text=f"Paper enter · ${q.premium:.2f}",
                                state="normal" if run.can_enter else "disabled",
                                command=lambda contract=q.contract: self.enter(cell, contract))
            button.pack(anchor="w", pady=(0, 5))
            self.entry_buttons.append(button)

    def advance(self):
        self.session.step()
        self.render()

    def enter(self, cell, contract):
        self.session.enter(cell, contract)
        self.render()

    def toggle(self):
        self.live = not self.live
        if not self.live and self.session is None:
            self.session = PaperReplay(demo(self.scenario), self.minute - 1)
        self.render()

    def check_port(self):
        message = ("OpenD port reachable. Market data unverified." if check_local_opend()
                   else "OpenD unavailable at 127.0.0.1:11111.")
        self.live_status.configure(text=message)


def main():
    import tkinter as tk

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-status", action="store_true")
    parser.add_argument("--scenario", choices=[key for key, _ in SCENARIOS], default="conflict")
    parser.add_argument("--minute", type=int, choices=range(1, 41), default=35, metavar="1-40")
    args = parser.parse_args()
    root = tk.Tk()
    RadarWindow(root, live=args.live_status, scenario=args.scenario, minute=args.minute)
    root.mainloop()


if __name__ == "__main__":
    main()

