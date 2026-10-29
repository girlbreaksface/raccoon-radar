"""Standalone read-only synthetic replay viewer. No provider/file-loader/order controls."""
import argparse
import sys

from synthetic_replay import replay, ReplayResult
from synthetic_replay_demo import make_demo, SCENARIOS, NOTICE
from pinned_timezone_bridge import consumer_dict


def render_text(result, index):
    """Display-only projection; never exposes unavailable future observation payloads."""
    if type(result) is not ReplayResult:
        raise TypeError("Immutable replay result required")
    if type(index) is not int or not 0 <= index < len(result.points):
        raise ValueError("Choose an existing replay step")
    point = result.points[index]
    lines = [
        "RACCOON RADAR vNext — SYNTHETIC ONLY",
        NOTICE,
        "PR31 profile: first-close EMA seed / 35 bars / FINAL-only; not PR18 study validation.",
        "HLC3 candle-weighted proxy is not trade-level VWAP. No orders or real market data.",
        "",
        f"Step {index+1}/{len(result.points)} | cutoff UTC: {point.step.cutoff}",
        f"Completed-through request: {point.step.watermark} | Pair: {point.pair}",
    ]
    for cell in point.cells:
        canonical = cell.evidence.canonical_report
        lines.extend(("", f"{cell.symbol} | {cell.bias or 'NO TRADE'} | {cell.state} | action {cell.action}",
                      f"Data quality: {cell.data_quality} | Source: FICTIONAL / SYNTHETIC ONLY",
                      "Reasons: " + (", ".join(cell.reasons) if cell.reasons else "none")))
        output = consumer_dict(cell.evidence) if cell.evidence.consumer is not None else {}
        observations = output.get("observations") or {}
        for label, key in (("EMA9", "ema9"), ("EMA21", "ema21"),
                           ("relative volume (prior 20)", "relative_volume"),
                           ("HLC3 volume-weighted candle proxy", "hlc3_volume_weighted_proxy")):
            lines.append(f"  {label}: {observations.get(key, 'UNAVAILABLE')}")
        if canonical.frame is not None and canonical.frame.candles:
            last = canonical.frame.candles[-1]
            lines.extend((f"  Visible bars: {len(canonical.frame.candles)}",
                          f"  Last raw timestamp (unchanged): {last.raw_stamp!r}",
                          f"  Canonical interval: [{last.start}, {last.end})",
                          f"  Known at: {last.available_at}"))
        lines.append(f"  Excluded post-cutoff observations: {len(canonical.exclusions)}")
    lines.extend(("", f"Decision identity: {point.decision_hash}", f"Input identity: {result.input_hash}",
                  f"Run identity: {result.run_hash}",
                  "Hashes are identity checks, not provider authentication or evidence of an edge."))
    return "\n".join(lines)


class ViewerModel:
    """UI state only; replay inputs/results themselves are recursively immutable."""
    def __init__(self, scenario="conflict", minute=35, *, precomputed=()):
        self._precomputed = dict(precomputed)
        self.scenario = scenario
        self.result = self._result(scenario)
        self.index = 0
        self.seek(minute)

    def _result(self, scenario):
        if scenario not in {key for key, _ in SCENARIOS}:
            raise ValueError("Choose a predefined synthetic scenario")
        if scenario in self._precomputed:
            return self._precomputed[scenario]
        return replay(make_demo(scenario), synthetic=True)

    def seek(self, minute):
        if type(minute) is not int or not 1 <= minute <= len(self.result.points):
            raise ValueError("Minute must be within the synthetic session")
        self.index = minute - 1

    def move(self, offset):
        if type(offset) is not int:
            raise ValueError("Integer step required")
        self.index = max(0, min(len(self.result.points)-1, self.index+offset))

    def select(self, scenario):
        result = self._result(scenario)
        self.scenario, self.result = scenario, result
        self.index = min(self.index, len(result.points)-1)

    def text(self):
        return render_text(self.result, self.index)


def create_window(scenario="conflict", minute=35):
    # Lazy import: headless text mode and tests do not require Tk or a display.
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText

    # Complete all bounded calculations BEFORE creating Tk widgets. Callbacks only
    # select immutable results and render text; there are no worker/UI thread races.
    precomputed = tuple((key, replay(make_demo(key), synthetic=True)) for key, _ in SCENARIOS)
    model = ViewerModel(scenario, minute, precomputed=precomputed)
    root = tk.Tk()
    root.title("Raccoon Radar vNext — Synthetic Replay")
    root.geometry("1120x820")
    root.minsize(820, 600)
    root.configure(bg="#101820")
    tk.Label(root, text="RACCOON RADAR  /  vNext Replay", bg="#101820", fg="#efefef",
             font=("Segoe UI", 20, "bold"), anchor="w").pack(fill="x", padx=22, pady=(18, 8))
    tk.Label(root, text="SYNTHETIC ONLY  •  FINAL-only  •  No orders or provider connections",
             bg="#453b18", fg="#ffe49a", font=("Segoe UI", 11, "bold"), anchor="w",
             padx=12, pady=10).pack(fill="x", padx=22)
    controls = tk.Frame(root, bg="#101820")
    controls.pack(fill="x", padx=22, pady=12)
    tk.Label(controls, text="Scenario", bg="#101820", fg="white").pack(side="left", padx=(0, 8))
    labels = dict(SCENARIOS)
    choice = ttk.Combobox(controls, values=[label for _, label in SCENARIOS], state="readonly", width=35)
    choice.set(labels[scenario])
    choice.pack(side="left")
    position = tk.StringVar(value=str(minute))
    status = tk.StringVar()
    display = ScrolledText(root, bg="#15232e", fg="#e6edf3", insertbackground="white",
                           font=("Consolas", 10), wrap="word", padx=16, pady=12)
    display.pack(fill="both", expand=True, padx=22, pady=(0, 12))

    def refresh():
        position.set(str(model.index+1))
        status.set(f"Step {model.index+1}/40  |  {model.result.points[model.index].pair}")
        display.configure(state="normal")
        display.delete("1.0", "end")
        display.insert("1.0", model.text())
        display.configure(state="disabled")

    def move(offset):
        model.move(offset)
        refresh()

    def select(_event):
        selected = next(key for key, label in SCENARIOS if label == choice.get())
        model.select(selected)
        refresh()

    def seek(value):
        model.seek(int(float(value)))
        refresh()

    choice.bind("<<ComboboxSelected>>", select)
    ttk.Button(controls, text="Previous", command=lambda: move(-1)).pack(side="left", padx=(18, 6))
    ttk.Button(controls, text="Next", command=lambda: move(1)).pack(side="left")
    ttk.Scale(controls, from_=1, to=40, variable=position, command=seek).pack(side="left", fill="x", expand=True, padx=18)
    tk.Label(root, textvariable=status, bg="#101820", fg="#a7d4df",
             anchor="w", font=("Segoe UI", 11)).pack(fill="x", padx=22, pady=(0, 12))
    root.bind("<Left>", lambda _event: move(-1))
    root.bind("<Right>", lambda _event: move(1))
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    refresh()
    return root


def main(argv=None):
    parser = argparse.ArgumentParser(description="Standalone synthetic-only PR31 replay viewer")
    parser.add_argument("--text", action="store_true", help="Print one synthetic step without a GUI")
    parser.add_argument("--scenario", choices=[key for key, _ in SCENARIOS], default="conflict")
    parser.add_argument("--minute", type=int, choices=range(1, 41), default=35)
    args = parser.parse_args(argv)
    if args.text:
        print(ViewerModel(args.scenario, args.minute).text())
        return 0
    try:
        import tkinter as tk
    except ImportError as exc:
        print(f"Viewer unavailable: {exc}. Use --text for offline preview.", file=sys.stderr)
        return 2
    try:
        root = create_window(args.scenario, args.minute)
    except (tk.TclError, RuntimeError) as exc:
        print(f"Viewer unavailable: {exc}. Use --text for offline preview.", file=sys.stderr)
        return 2
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
