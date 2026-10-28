"""Standalone H-011 calculator component; no dashboard, persistence or market IO."""
import tkinter as tk
from tkinter import ttk

from raccoon_ledger import calculator_view, NOTICE


class LedgerPanel(ttk.Frame):
    """Manual reference component. It can be mounted later after integration review."""
    def __init__(self, master):
        super().__init__(master, padding=24, style="Ledger.TFrame")
        style = ttk.Style(self)
        style.configure("Ledger.TFrame", background="#151724")
        style.configure("Ledger.TLabel", background="#151724", foreground="#f2f1fb")
        style.configure("LedgerNotice.TLabel", background="#23263a", foreground="#e8c579", padding=12)
        style.configure("LedgerValue.TLabel", background="#23263a", foreground="#f2f1fb",
                        padding=12, font=("Segoe UI", 12, "bold"))
        style.configure("LedgerError.TLabel", background="#151724", foreground="#f1b8aa")
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text="Raccoon Ledger", style="Ledger.TLabel",
                  font=("Segoe UI", 20, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(self, text="Manual long-option premium calculator",
                  style="Ledger.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0,12))
        ttk.Label(self, text=NOTICE, wraplength=720, style="LedgerNotice.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(0,16))
        defaults = dict(premium="", contracts="1", stop_percent="15", target_percent="20",
                        tick="0.01", entry_fees="0.00", exit_fees="0.00")
        labels = dict(premium="Entry premium ($ per share)", contracts="Contracts (whole number)",
                      stop_percent="Stop reference (%)", target_percent="Target reference (%)",
                      tick="Manual tick ($; verify contract rules)",
                      entry_fees="Entry fees ($ total position)", exit_fees="Estimated exit fees ($ total position)")
        self.inputs = {key:tk.StringVar(master=self, value=value) for key,value in defaults.items()}
        for row, (key, variable) in enumerate(self.inputs.items(), 3):
            ttk.Label(self, text=labels[key], style="Ledger.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0,16), pady=3)
            if key == "tick":
                widget = ttk.Combobox(self, textvariable=variable,
                                     values=("0.01","0.05","0.10"), state="readonly", width=16)
            else:
                widget = ttk.Entry(self, textvariable=variable, width=20)
            widget.grid(row=row, column=1, sticky="ew", pady=3)
        self.outputs = {key:tk.StringVar(master=self) for key in ("stop","target","entry_cost","error")}
        for row, (key, label) in enumerate(
                (("stop","Stop reference"),("target","Target reference"),("entry_cost","Estimated entry cost")), 10):
            ttk.Label(self, text=label, style="Ledger.TLabel").grid(row=row, column=0, sticky="w", pady=6)
            ttk.Label(self, textvariable=self.outputs[key], style="LedgerValue.TLabel").grid(
                row=row, column=1, sticky="ew", pady=6)
        ttk.Label(self, textvariable=self.outputs["error"], style="LedgerError.TLabel",
                  wraplength=720).grid(row=13,column=0,columnspan=2,sticky="w",pady=(8,0))
        ttk.Label(self, text="Levels rounded toward entry. P&L subtracts both fee fields. "
                  "Inputs are not saved; this milestone has no journal or feed.",
                  style="Ledger.TLabel",wraplength=720).grid(
                      row=14,column=0,columnspan=2,sticky="w",pady=(8,0))
        for variable in self.inputs.values():
            variable.trace_add("write", self._refresh)
        self._refresh()

    def _refresh(self, *_):
        view = calculator_view({key:variable.get() for key,variable in self.inputs.items()})
        for key, variable in self.outputs.items():
            variable.set(view[key])


def main():
    root = tk.Tk()
    root.title("Raccoon Ledger | Manual reference calculator")
    root.configure(bg="#151724")
    root.minsize(760, 650)
    LedgerPanel(root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
