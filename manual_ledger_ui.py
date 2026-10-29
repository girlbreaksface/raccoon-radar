"""Standalone H-014 synthetic-only journal window. No Radar/dashboard imports."""
import json
from decimal import Decimal
import sys
from pathlib import Path
from queue import Empty
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from ledger_ui_controller import LedgerController, WorkQueue, example_form
from manual_ledger import NOTICE


class LedgerWindow:
    def __init__(self, root):
        self.root = root
        self.controller = LedgerController()
        self.work = WorkQueue()
        self.closing = False
        self.after_success = None
        root.title("Raccoon Ledger | Practice Mode | SYNTHETIC DRAFT")
        root.geometry("1280x1000")
        root.minsize(1100, 940)
        root.configure(bg="#132126")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#132126")
        style.configure("TLabel", background="#132126", foreground="#edf4ee")
        style.configure("TButton", padding=5)
        style.configure("Treeview", rowheight=26)
        outer = ttk.Frame(root, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="RACCOON LEDGER · Practice Mode", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(outer, text=NOTICE, foreground="#ffd180", wraplength=1150).pack(anchor="w", pady=(3, 8))
        ttk.Label(outer, text="Fictional manual records only • Local plaintext • No quote, order or alert connections",
                  foreground="#a9c5bc").pack(anchor="w")
        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=10)
        self.buttons = {}
        for name, label, action in (
            ("new", "New Journal", self.new_store),
            ("open", "Open Journal", self.open_store),
            ("reload", "Reload / reconcile", lambda: self.run(self.controller.reload)),
            ("export", "Export displayed snapshot", lambda: self.destination("export")),
            ("backup", "New backup", lambda: self.destination("backup")),
            ("recover", "Recovery…", self.recover)):
            self.button(toolbar, name, label, action).pack(side="left", padx=(0, 6))
        self.location = tk.StringVar(value="No store selected. Nothing opens automatically.")
        ttk.Label(outer, textvariable=self.location, wraplength=1150).pack(anchor="w")
        viewbar = ttk.Frame(outer)
        viewbar.pack(fill="x", pady=8)
        ttk.Label(viewbar, text="Snapshot: ").pack(side="left")
        self.sequence = tk.StringVar(value="Latest")
        self.sequence_box = ttk.Combobox(viewbar, textvariable=self.sequence, state="readonly", width=12)
        self.sequence_box.pack(side="left")
        self.button(viewbar, "view", "View", self.view).pack(side="left", padx=6)
        ttk.Label(viewbar, text="Numbered snapshots are read-only. Latest shows corrections.",
                  foreground="#a9c5bc").pack(side="left")
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        form_frame = ttk.Frame(body, padding=(0, 0, 16, 0))
        form_frame.pack(side="left", fill="y")
        self.mode = tk.StringVar(value="New fictional position")
        ttk.Label(form_frame, textvariable=self.mode, wraplength=350,
                  font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=6)
        self.variables, self.entries = {}, {}
        labels = dict(underlying="Underlying", right="Right", expiration="Expiration (YYYY-MM-DD)",
                      strike="Strike (USD)", side="Simulated fill type", quantity="Whole contracts",
                      premium="Premium per share (USD)", fees="Total fill fees (USD)",
                      effective_at="Time (ISO + UTC offset)", timezone="Time zone", tie="Time tie order",
                      reason="Required reason", tick="Unverified reference tick")
        choices = dict(underlying=("SPY", "QQQ"), right=("CALL", "PUT"),
                       side=("BUY_TO_OPEN", "SELL_TO_CLOSE", "MANUAL_ZERO_CLOSE"),
                       timezone=("America/New_York", "UTC"))
        for row, (key, default) in enumerate(example_form().items(), 1):
            ttk.Label(form_frame, text=labels[key]).grid(row=row, column=0, sticky="w", pady=2)
            var = tk.StringVar(value=default)
            widget = (ttk.Combobox(form_frame, textvariable=var, values=choices[key], width=24,
                                   state="readonly") if key in choices else
                      ttk.Entry(form_frame, textvariable=var, width=27))
            widget.grid(row=row, column=1, sticky="ew", pady=2, padx=(8, 0))
            self.variables[key], self.entries[key] = var, widget
        row = len(self.variables) + 1
        self.button(form_frame, "save", "Record simulated fill", self.save).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(12, 4))
        self.button(form_frame, "clear", "New fictional position", self.clear_form).grid(
            row=row+1, column=0, columnspan=2, sticky="ew")
        ttk.Label(form_frame, text="Sample dates and prices are fictional. Edit them explicitly.\n"
                  "Fees are per fill; tick is a user assertion, never verified.\n"
                  "Dependent multi-fill corrections and restore use the CLI.",
                  wraplength=370, foreground="#a9c5bc").grid(
                      row=row+2, column=0, columnspan=2, sticky="w", pady=10)
        notebook = ttk.Notebook(body)
        notebook.pack(side="left", fill="both", expand=True)
        positions = ttk.Frame(notebook, padding=8)
        history = ttk.Frame(notebook, padding=8)
        summaries = ttk.Frame(notebook, padding=8)
        notebook.add(positions, text="Positions")
        notebook.add(history, text="Trade Corrections")
        notebook.add(summaries, text="Daily, Weekly & Monthly Results")
        self.positions = self.tree(positions, ("Contract", "Status", "Remaining", "Realized USD (exact)"))
        self.button(positions, "select", "Use selected position for next fill", self.select_position).pack(fill="x", pady=6)
        self.history = self.tree(history, ("Sequence", "Side", "Qty", "Voided", "Reason"))
        self.button(history, "correct", "Correct selected current revision", self.correct).pack(fill="x", pady=4)
        self.button(history, "void", "Void selected current revision…", self.void).pack(fill="x")
        self.summary = tk.Text(summaries, wrap="none", width=55, height=12,
                               bg="#eef3ef", font=("Consolas", 10))
        self.summary.pack(fill="both", expand=True)
        self.details = tk.Text(history, height=8, width=50, wrap="word")
        self.details.pack(fill="x", pady=8)
        self.history.bind("<<TreeviewSelect>>", self.show_revision)
        pendingbar = ttk.Frame(outer)
        pendingbar.pack(fill="x", pady=8, before=body)
        self.button(pendingbar, "retry", "Retry SAME pending command", lambda: self.run(
            self.controller.retry_pending, self.clear_form)).pack(side="left")
        self.button(pendingbar, "abandon", "Resolve / abandon pending intent…", self.abandon).pack(side="left", padx=6)
        self.status = tk.StringVar(value="Practice Mode. Fictional records only; synthetic development preview.")
        ttk.Label(outer, textvariable=self.status, wraplength=1150, foreground="#ffd180").pack(anchor="w", before=body, pady=(0, 8))
        self.render()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(50, self.poll)

    def button(self, parent, name, text, command):
        widget = ttk.Button(parent, text=text, command=command)
        self.buttons[name] = widget
        return widget

    def tree(self, parent, columns):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=8)
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=120, minwidth=75)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return tree

    def run(self, operation, success=None):
        if self.work.busy or self.closing:
            return
        self.after_success = success
        self.work.start(operation)
        self.status.set("Working locally… Do not close or move store files.")
        self.controls()

    def poll(self):
        try:
            event = self.work.take()
        except Empty:
            pass
        else:
            self.render()
            if event["ok"]:
                if self.after_success:
                    self.after_success(event["result"])
                result = event["result"]
                self.status.set("Completed. " + (str(result) if not isinstance(result, dict) else
                    str({k: v for k, v in result.items() if k in ("sequence", "path", "command_id")})))
            else:
                pending = self.controller.pending
                self.status.set(event["error"] + (f" | Pending command {pending['command_id']}; retry/reconcile before editing."
                                                  if pending else ""))
            self.after_success = None
            self.controls()
        if self.closing and not self.work.busy:
            self.closing = False
            self.close()
            return
        self.root.after(50, self.poll)

    def controls(self):
        c = self.controller
        busy = self.work.busy or self.closing
        pending = bool(c.pending)
        opened = c.repository is not None
        latest = c.view_sequence is None
        for name, widget in self.buttons.items():
            enabled = not busy and not pending
            if name in ("reload", "retry", "abandon"):
                enabled = not busy and opened and (pending or name == "reload")
            elif name not in ("new", "open", "recover"):
                enabled = enabled and opened
                if name not in ("export", "view"):
                    enabled = enabled and latest
            widget.configure(state="normal" if enabled else "disabled")
        self.sequence_box.configure(state="readonly" if opened and not busy and not pending else "disabled")
        for key, widget in self.entries.items():
            enabled = opened and latest and not busy and not pending
            if c.selection and key in ("underlying", "right", "expiration", "strike"):
                enabled = False
            widget.configure(state=("readonly" if isinstance(widget, ttk.Combobox) else "normal")
                             if enabled else "disabled")

    def render(self):
        c = self.controller
        snapshot = c.snapshot
        for tree in (self.positions, self.history):
            tree.delete(*tree.get_children())
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.configure(state="disabled")
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        if snapshot:
            sequence = snapshot["snapshot_sequence"]
            label = "Latest (restated)" if c.view_sequence is None else "Historical / read-only"
            self.location.set(f"{c.repository.path} | {label} | committed sequence {sequence}")
            self.sequence_box.configure(values=["Latest"] + [str(n) for n in range(sequence+1)])
            self.sequence.set("Latest" if c.view_sequence is None else str(c.view_sequence))
            for position in snapshot["positions"]:
                contract = position["contract"]
                self.positions.insert("", "end", iid=position["position_id"], values=(
                    f"{contract['underlying']} {contract['right']} {Decimal(contract['strike']).scaleb(-8):f} {contract['expiration']}",
                    position["status"], position["remaining"], position["realized_usd"]))
            for revision in snapshot["revisions"]:
                self.history.insert("", "end", iid=revision["revision_id"], values=(
                    revision["recorded_sequence"], revision["side"], revision["quantity"],
                    revision["voided"], revision["reason"]))
            self.summary.insert("end", "Repository-calculated Eastern summaries (synthetic)\n\n" +
                                json.dumps(snapshot["summaries"], indent=2))
        else:
            self.location.set("No active store. Open failures never create a new store.")
        self.summary.configure(state="disabled")
        self.controls()

    def fill_form(self, values):
        for key, var in self.variables.items():
            var.set(values[key])
        self.mode.set("Auditable correction — original retained" if self.controller.correction else
                      "Existing fictional position" if self.controller.selection else "New fictional position")
        self.controls()

    def clear_form(self, _result=None):
        self.fill_form(self.controller.new_position())

    def new_destination(self, title):
        parent = filedialog.askdirectory(parent=self.root, title=f"{title}: choose parent directory")
        if not parent:
            return None
        name = simpledialog.askstring(title, "NEW subdirectory name (must not exist):", parent=self.root)
        if not name:
            return None
        if Path(name).name != name or name in (".", "..") or any(c in name for c in '/\\:'):
            messagebox.showerror(title, "Use a single new directory name.", parent=self.root)
            return None
        return Path(parent) / name

    def new_store(self):
        path = self.new_destination("New Journal — Practice Mode, plaintext")
        if path and messagebox.askyesno("Synthetic only", f"Create a fictional-only PLAINTEXT store at\n{path}?",
                                        parent=self.root):
            self.run(lambda: self.controller.create_store(path), self.clear_form)

    def open_store(self):
        path = filedialog.askdirectory(parent=self.root, title="Open Journal — existing synthetic journal only")
        if path:
            self.run(lambda: self.controller.open_store(path), self.clear_form)

    def save(self):
        values = {key: var.get() for key, var in self.variables.items()}
        self.run(lambda: self.controller.submit_form(values), self.clear_form)

    def view(self):
        selected = self.sequence.get()
        sequence = None if selected == "Latest" else int(selected)
        self.run(lambda: self.controller.set_sequence(sequence), self.clear_form)

    def select_position(self):
        selected = self.positions.selection()
        if selected:
            self.run(lambda: self.controller.select_position(selected[0]), self.fill_form)

    def correct(self):
        selected = self.history.selection()
        if selected:
            self.run(lambda: self.controller.load_correction(selected[0]), self.fill_form)

    def void(self):
        selected = self.history.selection()
        if not selected:
            return
        reason = simpledialog.askstring("Auditable void", "Required reason (original history remains):", parent=self.root)
        if reason and messagebox.askyesno("Confirm void", "Append a void revision? This can be rejected if dependent fills become invalid.",
                                         parent=self.root):
            self.run(lambda: self.controller.void_revision(selected[0], reason, confirmed=True), self.clear_form)

    def show_revision(self, _event=None):
        selected = self.history.selection()
        if not selected or not self.controller.snapshot or self.work.busy:
            return
        revision = next(r for r in self.controller.snapshot["revisions"] if r["revision_id"] == selected[0])
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("end", json.dumps(revision, indent=2))
        self.details.configure(state="disabled")

    def destination(self, kind):
        path = self.new_destination(f"New plaintext {kind}")
        if path:
            self.run(lambda: getattr(self.controller, kind)(path))

    def abandon(self):
        if messagebox.askyesno("Resolve pending request", "Reload to reconcile a committed receipt, then abandon only uncommitted intent? No saved history is deleted.",
                               parent=self.root):
            self.run(lambda: self.controller.abandon_pending(confirmed=True), self.clear_form)

    def recover(self):
        path = filedialog.askdirectory(parent=self.root, title="Select known synthetic store needing recovery")
        if path and messagebox.askyesno("Exclusive recovery — caution", "Stop every other Ledger process first.\n"
                "Confirm you alone own this synthetic store. This is an assertion, not a lock guarantee.\n"
                "Raw recovery capture is NOT a verified backup. No automatic recovery or Open fallback.\nProceed?",
                parent=self.root):
            self.run(lambda: self.controller.recover_store(path, confirmed=True), self.clear_form)

    def close(self):
        if self.work.busy:
            self.closing = True
            self.status.set("Waiting for local operation to finish before closing…")
            self.controls()
            return
        if self.controller.pending and not messagebox.askyesno("Unresolved command", "Pending request exists only in memory.\n"
                "Record its command ID and inspect history before any manual retry after restart.\n"
                f"{self.controller.pending['command_id']}\nClose without automatic resubmission?", parent=self.root):
            self.root.after(50, self.poll)
            return
        self.work.close()
        self.root.destroy()


def prepare_display():
    """Use physical Windows coordinates so the initial window fits the display."""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()


def main():
    prepare_display()
    root = tk.Tk()
    LedgerWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
