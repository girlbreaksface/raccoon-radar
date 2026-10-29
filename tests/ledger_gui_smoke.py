"""Own-window synthetic Tk smoke; requires desktop or Xvfb. No market connections."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from manual_ledger_ui import LedgerWindow, prepare_display


def main():
    prepare_display()
    root = tk.Tk()
    app = LedgerWindow(root)
    with tempfile.TemporaryDirectory(prefix="synthetic-ledger-ui-") as temp:
        path = Path(temp)
        def wait():
            deadline = time.monotonic() + 15
            while app.work.busy:
                root.update()
                if time.monotonic() > deadline:
                    raise AssertionError("UI operation timeout")
                time.sleep(.01)
            root.update()
        assert app.controller.repository is None
        assert str(app.buttons["save"]["state"]) == "disabled"
        app.run(lambda: app.controller.create_store(path / "journal"), app.clear_form)
        wait()
        app.variables["quantity"].set("3")
        app.variables["fees"].set("0.01")
        app.variables["reason"].set("synthetic GUI entry")
        app.buttons["save"].invoke()
        wait()
        assert app.controller.snapshot["snapshot_sequence"] == 1, app.status.get()
        position = app.positions.get_children()[0]
        app.positions.selection_set(position)
        app.buttons["select"].invoke()
        wait()
        assert str(app.entries["strike"]["state"]) == "disabled"
        for key, value in dict(quantity="1", premium="1.20", fees="0.01",
                               effective_at="2026-10-23T11:00:00-04:00",
                               reason="synthetic GUI partial exit").items():
            app.variables[key].set(value)
        app.buttons["save"].invoke()
        wait()
        assert app.controller.snapshot["positions"][0]["remaining"] == 2
        assert app.controller.snapshot["positions"][0]["realized_usd"] == "19.99000000"
        revision = app.history.get_children()[-1]
        app.history.selection_set(revision)
        app.buttons["correct"].invoke()
        wait()
        assert "correction" in app.mode.get()
        app.variables["premium"].set("1.10")
        app.variables["reason"].set("synthetic GUI correction")
        app.buttons["save"].invoke()
        wait()
        assert len(app.controller.snapshot["revisions"]) == 3
        app.sequence.set("1")
        app.buttons["view"].invoke()
        wait()
        assert str(app.buttons["save"]["state"]) == "disabled"
        assert app.controller.snapshot["positions"][0]["remaining"] == 3
        app.run(lambda: app.controller.export(path / "export"))
        wait()
        assert json.loads((path / "export" / "report.json").read_text())["snapshot_sequence"] == 1
        app.sequence.set("Latest")
        app.buttons["view"].invoke()
        wait()
        app.run(lambda: app.controller.backup(path / "backup"))
        wait()
        assert "sequence" in app.status.get(), app.status.get()
        # Invalid entry creates no commit and shows the deferred exception text.
        app.variables["quantity"].set("1.5")
        app.variables["reason"].set("synthetic invalid integer")
        app.buttons["save"].invoke()
        wait()
        assert "integer" in app.status.get()
        assert app.controller.snapshot["snapshot_sequence"] == 3
        app.clear_form()
        screenshot = os.environ.get("LEDGER_SCREENSHOT")
        if screenshot:
            from PIL import ImageGrab
            root.lift()
            root.update()
            image = ImageGrab.grab(bbox=(root.winfo_rootx(), root.winfo_rooty(),
                                         root.winfo_rootx()+root.winfo_width(),
                                         root.winfo_rooty()+root.winfo_height()))
            image.save(screenshot)
            print("screenshot_sha256=" + hashlib.sha256(Path(screenshot).read_bytes()).hexdigest())
        app.close()
    print("Tk smoke PASS: startup, queued entry/partial exit/correction, historical controls, export, backup, visible error, close")


if __name__ == "__main__":
    main()
