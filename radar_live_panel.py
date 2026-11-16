"""Tk live observation panel. Provider requests run in a bounded child process."""
from datetime import datetime, timezone
import json
from pathlib import Path
from queue import Empty, Queue
import subprocess
import sqlite3
import sys
from threading import Thread

from radar_live import FUTURES_STATUS, SYMBOLS, age_seconds, eastern

POLL_MS = 20_000
WORKER_TIMEOUT = 18


def request_snapshot(port, scan, capture=False):
    argv = [sys.executable, "-B", str(Path(__file__).with_name("radar_live.py")), str(port)]
    if scan:
        argv.append("--scan")
    if capture:
        argv.append("--capture")
    try:
        child = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=WORKER_TIMEOUT,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                               env=_worker_env())
        for line in reversed(child.stdout.splitlines()):
            if line.startswith("RADAR_RESULT ") and child.returncode == 0:
                return json.loads(line.removeprefix("RADAR_RESULT "))
        status = "OpenD SDK worker failed before returning data"
    except subprocess.TimeoutExpired:
        status = "OpenD handshake or request timed out"
    except (OSError, ValueError) as exc:
        status = f"OpenD request unavailable · {exc}"
    return {"status": status, "symbols": {}}


def _worker_env():
    import os

    return {**os.environ, "PYTHONIOENCODING": "utf-8"}


def current_action(row, now):
    action = row.get("action", "WAIT")
    if action == "WAIT":
        return action, row.get("reason", "Missing or unverified data")
    try:
        quote_age = age_seconds(datetime.fromisoformat(row["quote_at"]), now)
        candle_age = age_seconds(datetime.fromisoformat(row["metrics"]["raw_candle"]), now)
    except (ValueError, TypeError, KeyError):
        return "WAIT", "Missing or unverified timestamps"
    if not 0 <= quote_age <= 20 or not 0 <= candle_age <= 150:
        return "WAIT", "Displayed observation expired"
    return action, row["reason"]


def printable(value, suffix=""):
    return f"{value:.2f}{suffix}" if value is not None else "UNAVAILABLE"


def age_label(stamp, now):
    if not stamp:
        return "unavailable"
    return f"{age_seconds(datetime.fromisoformat(stamp), now):,.0f}s"


def dashboard_text(result, last_success, options, now, busy):
    lines = ["OPEND MARKET OBSERVATION · PAPER ONLY",
             result.get("status", "Waiting for first OpenD result"),
             f"Quote authentication {result.get('authenticated', 'unverified')}  ·  "
             f"OpenD {result.get('version', 'unavailable')}  ·  "
             f"Session {result.get('session', 'unverified')} ({result.get('provider_session') or 'provider unavailable'})",
             f"Last successful candle update {last_success or 'unavailable'}",
             FUTURES_STATUS]
    if result.get("recovery"):
        lines.append(result["recovery"])
    if result.get("recorder"):
        lines.append(result["recorder"])
    if busy:
        lines.append("Refreshing read-only observations…")
    for code in SYMBOLS:
        row = result.get("symbols", {}).get(code, {})
        prices = row.get("metrics", {})
        action, reason = current_action(row, now)
        lines += ["", f"{code[3:]}   {action}   |   {reason}",
                  f"Permission  {row.get('permissions', 'Candle entitlement unverified')}",
                  f"Last trade  {printable(row.get('price'))}  ·  age {age_label(row.get('quote_at'), now)}"
                  f"  ·  {row.get('quote_at', 'timestamp unavailable')}",
                  "ETF bid/ask age unavailable · snapshot timestamp refers to last trade",
                  f"Minute bars  {prices.get('bars', 0)}  ·  raw stamp {prices.get('raw_candle', 'unavailable')}"
                  f"  ·  age {age_label(prices.get('raw_candle'), now)}",
                  f"Candles retrieved  {row.get('received_at', 'unavailable')}",
                  f"EMA9 {printable(prices.get('ema9'))}  ·  EMA21 {printable(prices.get('ema21'))}"
                  f"  ·  Turnover VWAP {printable(prices.get('vwap'))}"
                  f"  ·  HLC3 proxy {printable(prices.get('vwap_proxy'))}",
                  f"Relative volume {printable(prices.get('relative_volume'), '×')}"
                  f"  ·  Support {printable(prices.get('support'))}"
                  f"  ·  Resistance {printable(prices.get('resistance'))}"]
        if prices:
            lines.append(f"Five-minute trend {prices.get('five_minute_trend', 'warming up')}"
                         f"  ·  One-minute direction reversals {prices.get('reversals', 'warming up')}")
            for length in (5, 15):
                opening = prices.get(f"opening_{length}m")
                if opening:
                    lines.append(f"Opening {length}m low/high {opening[0]:.2f} / {opening[1]:.2f}"
                                 "  ·  provisional raw-minute window")
        if (prices.get("relative_volume") or 0) >= 2:
            lines.append("  Volume spike · ≥2× the prior 20-minute median")
        scan = options.get(code)
        if scan:
            active = [q for q in scan.get("ranked", []) if all(
                0 <= age_seconds(datetime.fromisoformat(q[key]), now) <= 15
                for key in ("bid_time", "ask_time"))]
            lines.append(f"Options  {scan['status']}  ·  {len(active)} currently fresh")
            for q in active:
                lines.append(f"  {q['code']} {q['side']} {q['strike']:g} {q['expiry']}  "
                             f"{q['bid']:.2f}/{q['ask']:.2f}  entry ${q['premium']:.2f}  "
                             f"cost ${q['round_trip_cost']:.2f}  Δ {q['delta']:.2f}  "
                             f"Vol/OI {q['volume']:g}/{q['interest']:g}")
            for message, count in {**scan.get("rejected", {}), **scan.get("book_errors", {})}.items():
                lines.append(f"  {count} · {message}")
        else:
            lines.append("Options  Not scanned · verified current books required")
    return "\n".join(lines)


class AlertState:
    def __init__(self):
        self.health = None
        self.active = frozenset()

    def update(self, health, signals):
        signals = frozenset(signals)
        changed = (self.health is not None and health != self.health) or bool(signals - self.active)
        self.health, self.active = health, signals
        return changed


class FeedRecovery:
    """A fresh request supplies a full recent window after an interruption."""
    def __init__(self):
        self.failures = 0
        self.recovering = False
        self.state = None

    def apply(self, result):
        rows = result.get("symbols", {})
        failed = (result.get("authenticated") is not True or any(
            not rows.get(code, {}).get("metrics") for code in SYMBOLS))
        if result.get("session") == "REGULAR":
            failed |= any(rows.get(code, {}).get("candle_health") == "STALE" for code in SYMBOLS)
        previous = self.state
        if failed:
            self.failures += 1
            self.recovering = True
            self.state = "INTERRUPTED"
            delay = min(60_000, 5_000 * 2 ** min(self.failures - 1, 4))
            result["recovery"] = f"Feed interrupted · retries in {delay // 1000}s"
        elif self.recovering and previous != "CONFIRMING":
            self.failures = 0
            self.state = "CONFIRMING"
            delay = 5_000
            result["recovery"] = "Feed returned · confirming a second complete response"
        else:
            self.failures = 0
            self.recovering = False
            self.state = "OBSERVING"
            delay = POLL_MS
            result["recovery"] = "Two-symbol observation available"
        if previous != self.state:
            result["transition"] = f"{previous or 'STARTUP'} → {self.state}"
        if self.state != "OBSERVING":
            for row in rows.values():
                row["action"] = "WAIT"
                row["reason"] = "; ".join(filter(None, (row.get("reason"), result["recovery"])))
                row["volume_alert_eligible"] = False
                if "options" in row:
                    row["options"] = {"status": "WAIT · feed recovery"}
        return delay


class LivePanel:
    def __init__(self, owner):
        import tkinter as tk

        self.owner = owner
        self.root = owner.root
        self.results = None
        self.result = {}
        self.last_success = None
        self.options = {}
        self.next_poll = None
        self.alerts = AlertState()
        self.recovery = FeedRecovery()
        toolbar = owner.ttk.Frame(owner.body)
        toolbar.pack(fill="x", pady=7)
        self.refresh = owner.ttk.Button(toolbar, text="Refresh OpenD", command=self.start)
        self.refresh.pack(side="left")
        self.scan = owner.ttk.Button(toolbar, text="Scan options", command=lambda: self.start(True))
        self.scan.pack(side="left", padx=6)
        owner.ttk.Button(toolbar, text="Synthetic replay", command=owner.toggle).pack(side="left")
        owner.ttk.Checkbutton(toolbar, text="Sound", variable=owner.sound).pack(side="left", padx=8)
        scroll = owner.ttk.Scrollbar(owner.body)
        scroll.pack(side="right", fill="y")
        self.view = tk.Text(owner.body, wrap="word", padx=12, pady=10, background="#1c2537",
                            foreground="#ecf0f7", font=("Segoe UI", 10), yscrollcommand=scroll.set)
        self.view.pack(fill="both", expand=True)
        scroll.configure(command=self.view.yview)
        self.start()
        self.tick()

    def start(self, scan=False):
        if self.results is not None:
            return
        if self.next_poll is not None:
            self.root.after_cancel(self.next_poll)
            self.next_poll = None
        if scan:
            self.options = {}
        self.results = queue = Queue()
        port = self.owner.opend_port

        def run():
            store = self.owner.observation_store
            result = request_snapshot(port, scan, capture=store is not None)
            delay = self.recovery.apply(result)
            if store is not None:
                try:
                    store.append(result, datetime.now(eastern()))
                    result["recorder"] = "OpenD poll recorded · separate observation database"
                except (OSError, sqlite3.Error, ValueError, KeyError) as exc:
                    result["recorder"] = f"Observation write failed · {exc}"
                for row in result.get("symbols", {}).values():
                    row.pop("raw_candles", None)
            queue.put((scan, result, delay))

        Thread(target=run, daemon=True).start()
        self.refresh.configure(state="disabled")
        self.scan.configure(state="disabled")

    def auto_poll(self):
        self.next_poll = None
        if self.view.winfo_exists():
            self.start()

    def tick(self):
        if not self.view.winfo_exists():
            if self.next_poll is not None:
                self.root.after_cancel(self.next_poll)
            return
        if self.results is not None:
            try:
                scan, self.result, delay = self.results.get_nowait()
            except Empty:
                pass
            else:
                self.results = None
                rows = self.result.get("symbols", {})
                stamps = [r["received_at"] for r in rows.values() if r.get("metrics") and r.get("received_at")]
                if stamps:
                    self.last_success = max(stamps)
                if scan:
                    self.options = {code: r["options"] for code, r in rows.items() if "options" in r}
                elif (self.recovery.state != "OBSERVING"
                      or self.result.get("session") not in ("REGULAR", "OPENING WARMUP")):
                    self.options = {}
                self.refresh.configure(state="normal")
                self.scan.configure(state="normal")
                self.next_poll = self.root.after(delay, self.auto_poll)
        now = datetime.now(timezone.utc)
        rows = self.result.get("symbols", {})
        decisions = {code: current_action(row, now) for code, row in rows.items()}
        health = (self.result.get("status", "").splitlines()[0:1], self.result.get("session"),
                  tuple((code, row.get("permissions"), decisions[code]) for code, row in rows.items()))
        signals = {(code, action) for code, (action, _) in decisions.items() if action != "WAIT"}
        for code, row in rows.items():
            metrics = row.get("metrics", {})
            raw = metrics.get("raw_candle")
            if (row.get("volume_alert_eligible") and raw and (metrics.get("relative_volume") or 0) >= 2
                    and 0 <= age_seconds(datetime.fromisoformat(raw), now) <= 150):
                signals.add((code, "VOLUME"))
        if self.result and self.alerts.update(health, signals) and self.owner.sound.get():
            self.root.bell()
        text = dashboard_text(self.result, self.last_success, self.options, now, self.results is not None)
        if text != self.view.get("1.0", "end-1c"):
            top, _ = self.view.yview()
            self.view.configure(state="normal")
            self.view.delete("1.0", "end")
            self.view.insert("1.0", text)
            self.view.configure(state="disabled")
            self.view.yview_moveto(top)
        self.root.after(250 if self.results is not None else 1000, self.tick)
