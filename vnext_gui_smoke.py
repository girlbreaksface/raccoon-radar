"""Explicit Tk smoke runner; Windows desktop required, no providers/network/DB."""
from raccoon_radar_vnext_1_1 import create_window, GREEN, RED, AMBER
from synthetic_replay_demo import SCENARIOS


def main():
    root = create_window()
    errors = []
    root.report_callback_exception = lambda *args: errors.append(args)
    try:
        root.update()
        ui = root.replay_ui
        # Reproduce a smaller hosted Windows desktop before opening details.
        root.geometry("980x600")
        root.update()
        assert ui["pair"].cget("text") == "PAIR STATUS  /  CONFLICT"
        assert ui["cards"][0][0].cget("fg") == GREEN
        assert ui["cards"][1][0].cget("fg") == RED
        assert ui["cards"][0][2][0][1].cget("text") == "131.00"
        assert ui["opened"][0] is None
        for name in ("Technical details", "Diagnostics", "Evidence"):
            ui["toggle"](name)
            root.update()
            ui["viewport"].yview_moveto(1)
            root.update()
            assert ui["display"].winfo_ismapped()
            assert ui["display"].cget("state") == "disabled"
            assert len(ui["display"].get("1.0", "end")) > 30
            if name == "Evidence":
                assert "131.002028240960365167" in ui["display"].get("1.0", "end")
            ui["toggle"](name)
            root.update()
            assert not ui["display"].winfo_ismapped()
        for scenario, caption in SCENARIOS:
            ui["choice"].set(caption)
            ui["choice"].event_generate("<<ComboboxSelected>>")
            root.update()
            assert ui["model"].scenario == scenario
            ui["seek"](35)
            if scenario == "provisional":
                assert ui["cards"][1][0].cget("text") == "DATA_BLOCKED"
                assert ui["cards"][1][0].cget("fg") == AMBER
                ui["toggle"]("Diagnostics")
                assert "FINALITY_UNVERIFIED" in ui["display"].get("1.0", "end")
                ui["toggle"]("Diagnostics")
            before = repr(ui["model"].result)
            ui["seek"](1)
            assert str(ui["previous"].cget("state")) == "disabled"
            ui["next"].invoke()
            assert ui["model"].index == 1
            ui["slider"].set(40)
            root.update()
            assert ui["model"].index == 39
            assert str(ui["next"].cget("state")) == "disabled"
            ui["previous"].invoke()
            assert ui["model"].index == 38
            assert repr(ui["model"].result) == before
        for width, height in ((980, 760), (1180, 880)):
            root.geometry(f"{width}x{height}")
            root.update()
            for direction, state, metrics in ui["cards"]:
                assert direction.winfo_width() >= direction.winfo_reqwidth()
        assert not errors, errors
        print("PASS: Windows Tk lifecycle, seven scenarios, conflict/provisional, rounding, details, controls, bounds, resize, immutable results")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
