"""Presentation-only workstation for PR37's immutable synthetic replay results."""
import argparse
from decimal import Decimal, InvalidOperation
import sys

from raccoon_replay_viewer import ViewerModel
from synthetic_replay import replay
from synthetic_replay_demo import make_demo, SCENARIOS, NOTICE
from pinned_timezone_bridge import consumer_dict

BG = "#0e0d17"
PANEL = "#191725"
FG = "#f0edf9"
MUTED = "#b5aec9"
PURPLE = "#b696ff"
GREEN = "#65e6aa"
RED = "#ff8094"
AMBER = "#f3c773"


def indicator(value):
    """Format only the visible label; never round or replace evidence values."""
    if value is None or isinstance(value, bool):
        return "UNAVAILABLE"
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return "UNAVAILABLE"
    if not number.is_finite():
        return "UNAVAILABLE"
    return f"{number:.4f}" if abs(number) < 10 else f"{number:.2f}"


def cell_view(cell):
    output = consumer_dict(cell.evidence) if cell.evidence.consumer is not None else {}
    observations = output.get("observations") or {}
    color = AMBER
    if cell.state == "CANDIDATE":
        color = GREEN if cell.bias == "BULLISH" else RED if cell.bias == "BEARISH" else AMBER
    return (cell.bias or cell.state, color, tuple(
        (label, indicator(observations.get(key))) for label, key in (
            ("EMA 9", "ema9"), ("EMA 21", "ema21"),
            ("Relative volume · prior 20", "relative_volume"),
            ("HLC3 candle-weighted proxy", "hlc3_volume_weighted_proxy"))))


def create_window(scenario="conflict", minute=35):
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText

    precomputed = tuple((key, replay(make_demo(key), synthetic=True)) for key, _ in SCENARIOS)
    model = ViewerModel(scenario, minute, precomputed=precomputed)
    root = tk.Tk()
    root.title("Raccoon Radar vNext 1.1 · Synthetic Replay · No Orders")
    root.geometry("1180x880")
    root.minsize(980, 600)
    root.configure(bg=BG)
    # A scrollable page keeps diagnostics reachable on smaller Windows desktops.
    viewport = tk.Canvas(root, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=viewport.yview)
    scrollbar.pack(side="right", fill="y")
    viewport.pack(side="left", fill="both", expand=True)
    viewport.configure(yscrollcommand=scrollbar.set)
    page = tk.Frame(viewport, bg=BG)
    page_id = viewport.create_window((0, 0), window=page, anchor="nw")
    page.bind("<Configure>", lambda _event: viewport.configure(scrollregion=viewport.bbox("all")))
    viewport.bind("<Configure>", lambda event: viewport.itemconfigure(page_id, width=event.width))
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TButton", background="#302445", foreground=FG, padding=(14, 8))
    style.map("TButton", background=[("active", "#513875")], foreground=[("disabled", "#766b88")])
    style.configure("TCombobox", fieldbackground=PANEL, background="#302445", foreground=FG)
    style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", FG)])
    style.configure("Horizontal.TScale", background=PANEL, troughcolor="#332842")

    def label(parent, text="", size=11, color=FG, bg=PANEL, **kwargs):
        return tk.Label(parent, text=text, bg=bg, fg=color, font=("Segoe UI", size), anchor="w", **kwargs)

    header = tk.Frame(page, bg=BG)
    header.pack(fill="x", padx=24, pady=(20, 12))
    label(header, "RACCOON RADAR", 25, bg=BG).pack(side="left")
    label(header, "vNext 1.1  /  REPLAY WORKSTATION", 11, PURPLE, BG).pack(side="right")
    label(page, "SYNTHETIC ONLY   ·   FINAL-only   ·   NO ORDERS   ·   All actions WAIT", 12,
          AMBER, "#30261b", padx=14, pady=10).pack(fill="x", padx=24)
    label(page, "PR31 PROFILE  /  first-close EMA seed  /  35-bar first-close profile", 11,
          PURPLE, BG).pack(fill="x", padx=24, pady=(10, 3))
    label(page, NOTICE, 10, MUTED, BG).pack(fill="x", padx=24)

    toolbar = tk.Frame(page, bg=BG)
    toolbar.pack(fill="x", padx=24, pady=14)
    label(toolbar, "SYNTHETIC SCENARIO", 10, MUTED, BG).pack(side="left", padx=(0, 12))
    choice = ttk.Combobox(toolbar, values=[v for _, v in SCENARIOS], state="readonly", width=36)
    choice.set(dict(SCENARIOS)[scenario])
    choice.pack(side="left")

    cards = tk.Frame(page, bg=BG)
    cards.pack(fill="x", padx=24)
    cards.columnconfigure((0, 1), weight=1, uniform="cards")
    widgets = []
    for column, symbol in enumerate(("SPY", "QQQ")):
        card = tk.Frame(cards, bg=PANEL, highlightthickness=1, highlightbackground="#403250", padx=20, pady=16)
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 8) if column == 0 else (8, 0))
        label(card, symbol, 23).pack(fill="x")
        direction = label(card, size=24, color=AMBER)
        direction.pack(fill="x", pady=(6, 2))
        state = label(card, size=10, color=MUTED)
        state.pack(fill="x", pady=(0, 14))
        metrics = []
        for _ in range(4):
            row = tk.Frame(card, bg=PANEL)
            row.pack(fill="x", pady=3)
            name = label(row, size=10, color=MUTED)
            name.pack(side="left")
            value = label(row, size=12)
            value.pack(side="right")
            metrics.append((name, value))
        widgets.append((direction, state, metrics))

    pair = label(page, size=15, color=AMBER, padx=16, pady=12)
    pair.pack(fill="x", padx=24, pady=(14, 0))
    pair_note = label(page, size=10, color=MUTED, bg=BG)
    pair_note.pack(fill="x", padx=24, pady=(5, 12))
    timeline = tk.Frame(page, bg=PANEL, padx=14, pady=12)
    timeline.pack(fill="x", padx=24)
    progress = label(timeline, size=12, color=PURPLE)
    progress.pack(fill="x", pady=(0, 8))
    controls = tk.Frame(timeline, bg=PANEL)
    controls.pack(fill="x")
    position = tk.DoubleVar(value=minute)
    previous = ttk.Button(controls, text="← Previous", command=lambda: move(-1))
    previous.pack(side="left")
    following = ttk.Button(controls, text="Next →", command=lambda: move(1))
    following.pack(side="right")
    slider = ttk.Scale(controls, from_=1, to=len(model.result.points), variable=position,
                       command=lambda value: seek(int(float(value))))
    slider.pack(side="left", fill="x", expand=True, padx=18)
    timestamp = label(timeline, size=9, color=MUTED)
    timestamp.pack(fill="x", pady=(8, 0))

    details = tk.Frame(page, bg=BG)
    details.pack(fill="both", expand=True, padx=24, pady=(12, 18))
    toggles = tk.Frame(details, bg=BG)
    toggles.pack(fill="x")
    display = ScrolledText(details, height=7, bg=PANEL, fg=FG, insertbackground=FG,
                           font=("Consolas", 10), wrap="word", padx=14, pady=12)
    opened = [None]
    sections = {}
    buttons = {}

    def update_details():
        display.configure(state="normal")
        display.delete("1.0", "end")
        display.insert("1.0", sections.get(opened[0], ""))
        display.configure(state="disabled")

    def toggle(name):
        opened[0] = None if opened[0] == name else name
        for key, button in buttons.items():
            button.configure(text=("▾ " if opened[0] == key else "▸ ") + key)
        if opened[0] is None:
            display.pack_forget()
        else:
            display.pack(fill="both", expand=True, pady=(8, 0))
            update_details()

    for name in ("Technical details", "Diagnostics", "Evidence"):
        button = ttk.Button(toggles, text="▸ " + name, command=lambda name=name: toggle(name))
        button.pack(side="left", padx=(0, 8))
        buttons[name] = button

    def refresh():
        point = model.result.points[model.index]
        for cell, (direction, state, metrics) in zip(point.cells, widgets):
            title, color, values = cell_view(cell)
            direction.configure(text=title, fg=color)
            state.configure(text=f"{cell.state}  ·  SYNTHETIC  ·  {cell.action}")
            for (name, value), (caption, number) in zip(metrics, values):
                name.configure(text=caption)
                value.configure(text=number)
        pair.configure(text="PAIR STATUS  /  " + point.pair, fg=AMBER if "AGREEMENT" not in point.pair else GREEN)
        pair_note.configure(text=("SPY and QQQ disagree. No combined direction inferred." if point.pair == "CONFLICT"
                                  else "Pair state from the unchanged replay engine. Research only; all actions WAIT."))
        position.set(model.index + 1)
        progress.configure(text=f"REPLAY TIMELINE     {model.index + 1:02d} / {len(model.result.points)}")
        timestamp.configure(text=f"Cutoff UTC: {point.step.cutoff}   |   Completed-through request: {point.step.watermark}")
        previous.configure(state="disabled" if model.index == 0 else "normal")
        following.configure(state="disabled" if model.index == len(model.result.points)-1 else "normal")
        sections["Technical details"] = model.text()
        sections["Diagnostics"] = "\n\n".join(
            f"{c.symbol}: {c.state}\nQuality: {c.data_quality}\nReasons: {', '.join(c.reasons) or 'none'}"
            for c in point.cells)
        sections["Evidence"] = model.text() + "\n\nVisible full-precision bridge evidence:\n" + "\n\n".join(
            f"{c.symbol}: {consumer_dict(c.evidence)!r}" if c.evidence.consumer is not None
            else f"{c.symbol}: consumer UNAVAILABLE" for c in point.cells)
        update_details()

    def move(offset):
        model.move(offset)
        refresh()

    def seek(value):
        model.seek(value)
        refresh()

    def select(_event=None):
        model.select(next(key for key, value in SCENARIOS if value == choice.get()))
        refresh()

    choice.bind("<<ComboboxSelected>>", select)
    root.bind("<Left>", lambda _event: move(-1))
    root.bind("<Right>", lambda _event: move(1))
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    # Explicit UI handles for reproducible widget smoke tests; no engine mutation.
    root.replay_ui = dict(model=model, choice=choice, previous=previous, next=following,
                          viewport=viewport, slider=slider, seek=seek, select=select, pair=pair, cards=widgets,
                          toggle=toggle, display=display, opened=opened, refresh=refresh)
    refresh()
    return root


def main(argv=None):
    parser = argparse.ArgumentParser(description="Raccoon Radar vNext 1.1 · synthetic presentation only")
    parser.add_argument("--scenario", choices=[key for key, _ in SCENARIOS], default="conflict")
    parser.add_argument("--minute", type=int, choices=range(1, 41), default=35)
    parser.add_argument("--text", action="store_true")
    args = parser.parse_args(argv)
    if args.text:
        print(ViewerModel(args.scenario, args.minute).text())
        return 0
    try:
        import tkinter as tk
    except ImportError as exc:
        print(f"Viewer unavailable: {exc}. Use --text.", file=sys.stderr)
        return 2
    try:
        root = create_window(args.scenario, args.minute)
    except (tk.TclError, RuntimeError) as exc:
        print(f"Viewer unavailable: {exc}. Use --text.", file=sys.stderr)
        return 2
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
