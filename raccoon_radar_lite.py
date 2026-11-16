"""Raccoon Radar Lite: isolated, synthetic-only paper replay."""
import argparse
from copy import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
import os
from pathlib import Path
import sqlite3

from futures_spike_radar import MAX_PREMIUM, MAX_TRADES
from historical_radar_replay import SLIP
from pinned_timezone_bridge import consumer_dict
from synthetic_replay import replay
from synthetic_replay_demo import SCENARIOS, make_demo
from radar_lite_journal import JournalError, PaperJournal
from radar_live_panel import AlertState, LivePanel
from radar_observations import ObservationStore
from radar_paper_performance import format_summary, paper_performance
from tools.opend_local_preflight import PORT, port_number


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
        self.events.append(f"{self.now:%H:%M:%S}  OPEN  {contract.symbol} {contract.side} {contract.strike}  ${quote.premium:.2f}")
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
        self.events.append(f"{self.now:%H:%M:%S}  {reason}  {contract.symbol} {contract.side} {contract.strike}"
                           f"  P/L ${quote.proceeds - premium:+.2f}")
        self.open = None


def default_journal_path():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
    directory = Path(base) if base else Path.home() / ".local" / "share"
    return directory / "RaccoonRadarLite" / "paper-journal.sqlite3"


class JournaledReplay:
    def __init__(self, journal, scenario, index, *, new=False):
        self.journal = journal
        points = demo(scenario)
        # Bump the version when fixture quotes or execution semantics change.
        fingerprint = sha256(("paper-v1:" + "".join(p.decision_hash for p in points)).encode()).hexdigest()
        record = journal.open_replay(scenario, index, fingerprint, new=new)
        self.replay_id = record.id
        self.sequence = 0
        if not 0 <= record.initial_index < len(points):
            raise JournalError("Invalid saved replay start.")
        self.run = PaperReplay(points, record.initial_index)
        for sequence, command, contract_index, entry_text in record.commands:
            event_count = len(self.run.events)
            if sequence != self.sequence + 1 or not self.apply(self.run, command, contract_index):
                raise JournalError("Invalid saved replay command.")
            if self.entry_text(self.run, event_count) != entry_text:
                raise JournalError("Saved journal event does not match its replay.")
            self.sequence = sequence

    @staticmethod
    def apply(run, command, contract_index):
        if command == "STEP" and contract_index is None and run.index < len(run.points) - 1:
            run.step()
            return True
        if command == "ENTER" and type(contract_index) is int and 0 <= contract_index < len(CHAIN):
            contract = CHAIN[contract_index]
            cell = next(cell for cell in run.point.cells if cell.symbol == contract.symbol)
            return run.enter(cell, contract)
        return False

    @staticmethod
    def entry_text(run, previous_count):
        if len(run.events) > previous_count:
            return f"{run.now:%Y-%m-%d} UTC   {run.events[-1]}"
        return None

    def record(self, command, contract=None):
        candidate = copy(self.run)
        candidate.events = self.run.events.copy()
        contract_index = None if contract is None else CHAIN.index(contract)
        if not self.apply(candidate, command, contract_index):
            return
        sequence = self.sequence + 1
        self.journal.append(self.replay_id, sequence, command, contract_index,
                            self.entry_text(candidate, len(self.run.events)))
        self.run = candidate
        self.sequence = sequence


class RadarWindow:
    def __init__(self, root, *, live=False, scenario="conflict", minute=35,
                 journal=None, new_replay=False, opend_port=PORT, sound=False, observation_store=None):
        from tkinter import BooleanVar, ttk

        self.ttk = ttk
        self.root = root
        self.scenario = scenario
        self.minute = minute
        self.live = live
        self.journal = journal if journal is not None else PaperJournal(default_journal_path())
        self.journaled = None
        self.session = None
        self.journal_error = None
        self.new_replay = new_replay
        self.opend_port = opend_port
        self.observation_store = observation_store
        self.sound = BooleanVar(root, value=sound)
        self.replay_alerts = AlertState()
        if not live:
            self.open_replay()
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
            self.live_panel = LivePanel(self)
            return

        if self.journal_error:
            self.label(self.body, self.journal_error, wraplength=690)
        if self.session is None:
            self.ttk.Button(self.body, text="Paper journal", command=self.show_journal).pack(anchor="w")
            self.ttk.Button(self.body, text="Live data status", command=self.toggle).pack(anchor="w")
            return
        run = self.session
        toolbar = self.ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=10)
        self.label(toolbar, f"Replay clock  {run.now:%Y-%m-%d %H:%M:%S} UTC"
                   f"   ·   Minute {run.index + 1}/{len(run.points)}   ·   {self.scenario.title()}")
        self.next_button = self.ttk.Button(toolbar, text="Next minute", command=self.advance,
                                      state="normal" if not self.journal_error and run.index < len(run.points) - 1 else "disabled")
        self.next_button.pack(side="left")
        self.ttk.Button(toolbar, text="Live data status", command=self.toggle).pack(side="left", padx=8)
        self.ttk.Button(toolbar, text="Paper performance", command=self.show_journal).pack(side="left")
        self.ttk.Checkbutton(toolbar, text="Sound", variable=self.sound).pack(side="left", padx=8)
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
                                state="normal" if run.can_enter and not self.journal_error else "disabled",
                                command=lambda contract=q.contract: self.enter(contract))
            button.pack(anchor="w", pady=(0, 5))
            self.entry_buttons.append(button)

    def open_replay(self):
        try:
            self.journaled = JournaledReplay(self.journal, self.scenario, self.minute - 1,
                                             new=self.new_replay)
        except (sqlite3.Error, OSError, JournalError) as exc:
            self.journal_error = f"Paper journal unavailable. {exc}"
            return
        self.new_replay = False
        self.journal_error = None
        self.session = self.journaled.run

    def record(self, command, contract=None):
        if self.journal_error:
            return
        try:
            self.journaled.record(command, contract)
        except (sqlite3.Error, OSError, JournalError) as exc:
            self.journal_error = f"Paper journal could not save. {exc}"
        self.session = self.journaled.run
        self.render()

    def advance(self):
        self.record("STEP")
        cells = self.session.point.cells
        health = tuple((cell.symbol, cell.state) for cell in cells)
        signals = {(cell.symbol, direction(cell)) for cell in cells
                   if direction(cell) != "WAIT" and self.session.can_enter}
        if self.replay_alerts.update(health, signals) and self.sound.get():
            self.root.bell()

    def enter(self, contract):
        self.record("ENTER", contract)

    def show_journal(self):
        import tkinter as tk
        from tkinter import messagebox

        try:
            history = self.journal.history()
        except (sqlite3.Error, OSError, JournalError) as exc:
            messagebox.showerror("Paper journal unavailable", str(exc), parent=self.root)
            return
        window = tk.Toplevel(self.root)
        window.title("Synthetic paper journal")
        window.geometry("730x380")
        scroll = self.ttk.Scrollbar(window)
        scroll.pack(side="right", fill="y")
        text = tk.Text(window, wrap="word", padx=12, pady=12, yscrollcommand=scroll.set)
        text.pack(fill="both", expand=True)
        scroll.configure(command=text.yview)
        overall, setups = paper_performance(history)
        lines = ["SYNTHETIC PAPER PERFORMANCE · CLOSED TRADES ONLY",
                 format_summary(overall), "", "SETUPS"]
        lines.extend(f"{scenario} / {symbol} {side}  ·  {format_summary(summary)}"
                     for (scenario, symbol, side), summary in setups.items())
        lines += ["", "TRADE HISTORY"]
        lines.extend(f"Replay {run_id} ({scenario})   {entry}" for run_id, scenario, entry in history)
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")

    def toggle(self):
        self.live = not self.live
        if not self.live and self.session is None:
            self.open_replay()
        self.render()


def main():
    import tkinter as tk

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-status", action="store_true")
    parser.add_argument("--scenario", choices=[key for key, _ in SCENARIOS], default="conflict")
    parser.add_argument("--minute", type=int, choices=range(1, 41), default=35, metavar="1-40")
    parser.add_argument("--journal", type=Path, default=default_journal_path())
    parser.add_argument("--new-replay", action="store_true", help="Start a new run and retain prior journal entries")
    parser.add_argument("--opend-port", type=port_number, default=PORT)
    parser.add_argument("--record-observations", type=Path, metavar="FILE",
                        help="Store OpenD observations in a dedicated SQLite file")
    parser.add_argument("--sound", action="store_true", help="Enable audible signal and health alerts")
    args = parser.parse_args()
    root = tk.Tk()
    RadarWindow(root, live=args.live_status, scenario=args.scenario, minute=args.minute,
                journal=PaperJournal(args.journal), new_replay=args.new_replay,
                opend_port=args.opend_port, sound=args.sound,
                observation_store=ObservationStore(args.record_observations) if args.record_observations else None)
    root.mainloop()


if __name__ == "__main__":
    main()
