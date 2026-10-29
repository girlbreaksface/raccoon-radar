"""Synthetic replay/viewer contracts. No provider, original DB or market data."""
from dataclasses import FrozenInstanceError, replace
from decimal import getcontext
import ast
import contextlib
import copy
import io
from pathlib import Path
import unittest
from unittest.mock import patch


def api():
    import synthetic_replay as replay
    from synthetic_replay_demo import make_demo
    return replay, make_demo


class ReplayTests(unittest.TestCase):
    def test_selected_profile_finality_and_no_actions(self):
        replay, demo = api()
        result = replay.replay(demo("conflict"), synthetic=True)
        self.assertEqual(result.profile, "PR31_FIRST_CLOSE_EMA_35_FINAL_ONLY")
        self.assertEqual(len(result.points), 40)
        self.assertEqual(result.points[34].pair, "CONFLICT")
        self.assertEqual(tuple(c.bias for c in result.points[34].cells), ("BULLISH", "BEARISH"))
        self.assertTrue(all(c.action == "WAIT" for p in result.points for c in p.cells))

    def test_explicit_synthetic_only_typed_input(self):
        replay, demo = api()
        data = demo("conflict")
        for flag in (False, None, 1, "true"):
            with self.assertRaises(ValueError):
                replay.replay(data, synthetic=flag)
        with self.assertRaises(TypeError):
            replay.replay({}, synthetic=True)
        bad = replace(data, series=(replace(data.series[0], bundle=replace(data.series[0].bundle, synthetic=False)), data.series[1]))
        with self.assertRaises(ValueError):
            replay.replay(bad, synthetic=True)

    def test_exact_chronological_bounded_grid(self):
        replay, demo = api()
        data = demo("conflict")
        for steps in ((), data.steps[::-1], (data.steps[0], data.steps[0]), data.steps * 4,
                      (replace(data.steps[0], cutoff="2026-10-23T09:31:01.0000001Z"),)):
            with self.subTest(steps=len(steps)):
                with self.assertRaises(ValueError):
                    replay.replay(replace(data, steps=steps), synthetic=True)

    def test_symbols_must_be_exact_unique_pair(self):
        replay, demo = api()
        data = demo("conflict")
        for series in (data.series[:1], (data.series[0], data.series[0]),
                       (replace(data.series[0], symbol="US.SPY"), data.series[1])):
            with self.assertRaises(ValueError):
                replay.replay(replace(data, series=series), synthetic=True)

    def test_input_series_order_does_not_change_ordered_points(self):
        replay, demo = api()
        data = demo("conflict")
        normal = replay.replay(data, synthetic=True)
        reverse = replay.replay(replace(data, series=data.series[::-1]), synthetic=True)
        self.assertEqual(normal.points, reverse.points)
        self.assertNotEqual(normal.input_hash, reverse.input_hash)

    def test_warmup_is_profile_block_not_valid_no_candidate(self):
        replay, demo = api()
        point = replay.replay(demo("conflict"), synthetic=True).points[33]
        self.assertEqual(point.pair, "PEER_PROFILE_UNAVAILABLE")
        self.assertTrue(all(c.state == "PROFILE_BLOCKED" for c in point.cells))
        self.assertTrue(all("INSUFFICIENT_REFERENCE_WARMUP" in c.reasons for c in point.cells))
        self.assertTrue(all(c.data_quality == "SYNTHETIC_ENGINE_READY" for c in point.cells))

    def test_final_only_blocks_provisional_without_promotion(self):
        replay, demo = api()
        data = demo("provisional")
        result = replay.replay(data, synthetic=True)
        self.assertTrue(result.points[33].cells[1].data_quality == "SYNTHETIC_ENGINE_READY")
        point = result.points[34]
        self.assertEqual(point.cells[1].state, "DATA_BLOCKED")
        self.assertIn("FINALITY_UNVERIFIED", point.cells[1].reasons)
        self.assertEqual(point.pair, "PEER_DATA_UNAVAILABLE")
        self.assertEqual(data.series[1].bundle.observations[34].finality, "PROVISIONAL")

    def test_missing_partial_and_unknown_scenarios_fail_closed(self):
        replay, demo = api()
        for scenario, reason in (("gap", "EXPECTED_GRID_GAP"), ("partial", "PARTIAL_SOURCE"),
                                 ("unknown", "AVAILABILITY_UNKNOWN")):
            with self.subTest(scenario=scenario):
                point = replay.replay(demo(scenario), synthetic=True).points[34]
                self.assertEqual(point.cells[0].state, "CANDIDATE")
                self.assertEqual(point.cells[1].state, "DATA_BLOCKED")
                self.assertIn(reason, point.cells[1].reasons)
                self.assertEqual(point.pair, "PEER_DATA_UNAVAILABLE")

    def test_valid_mixed_is_distinct_from_bad_data(self):
        replay, demo = api()
        point = replay.replay(demo("mixed"), synthetic=True).points[34]
        self.assertEqual(point.pair, "BOTH_NO_TRADE")
        self.assertTrue(all(c.state == "NO_CANDIDATE" for c in point.cells))
        self.assertTrue(all(c.data_quality == "SYNTHETIC_ENGINE_READY" for c in point.cells))

    def test_all_nine_valid_symbol_pairs_keep_both_signals(self):
        replay, demo = api()
        from canonical_candles import identity
        data = demo("conflict")
        for left in ("BULLISH", "BEARISH", None):
            for right in ("BULLISH", "BEARISH", None):
                series = []
                for source, direction in zip(data.series, (left, right)):
                    rows = []
                    for i, row in enumerate(source.bundle.observations):
                        values = ((100+i, 102+i, 99+i, 101+i, 100) if direction == "BULLISH"
                            else (200-i, 202-i, 199-i, 201-i, 100) if direction == "BEARISH"
                            else (100, 101, 99, 100, 100))
                        rows.append(replace(row, values=values, snapshot=repr(values).encode()))
                    rows = tuple(rows)
                    bundle = replace(source.bundle, observations=rows, capture_hash=identity((rows, source.bundle.pages)))
                    series.append(replace(source, bundle=bundle))
                point = replay.replay(replace(data, series=tuple(series), steps=(data.steps[34],)), synthetic=True).points[0]
                expected = ("BOTH_NO_TRADE" if left is None and right is None else
                    "SINGLE_CANDIDATE" if left is None or right is None else
                    "AGREEMENT_" + left if left == right else "CONFLICT")
                self.assertEqual(point.pair, expected)
                self.assertEqual(tuple(c.bias for c in point.cells), (left, right))

    def test_later_invalid_payload_never_changes_earlier_decision(self):
        replay, demo = api()
        from canonical_candles import identity
        data = demo("conflict")
        before = replay.replay(data, synthetic=True)
        source = data.series[0]
        rows = list(source.bundle.observations)
        rows[-1] = replace(rows[-1], values=(float("inf"), None, "bad", True, 0), raw_stamp="INVALID")
        rows = tuple(rows)
        changed = replace(source, bundle=replace(source.bundle, observations=rows,
                          capture_hash=identity((rows, source.bundle.pages))))
        after = replay.replay(replace(data, series=(changed, data.series[1])), synthetic=True)
        for a, b in zip(before.points[:39], after.points[:39]):
            self.assertEqual(a.decision_hash, b.decision_hash)
        self.assertNotEqual(before.run_hash, after.run_hash)
        self.assertEqual(after.points[-1].cells[0].state, "DATA_BLOCKED")

    def test_visibility_exact_fractional_boundary(self):
        replay, demo = api()
        data = demo("conflict")
        step = data.steps[34]
        early = replace(step, cutoff=step.watermark)
        point = replay.replay(replace(data, steps=(early, step)), synthetic=True)
        self.assertEqual(point.points[0].pair, "PEER_DATA_UNAVAILABLE")
        self.assertEqual(point.points[1].pair, "CONFLICT")

    def test_deep_immutability_determinism_and_decimal_context(self):
        replay, demo = api()
        data = demo("conflict")
        before = copy.deepcopy(data)
        decimal = repr(getcontext())
        result = replay.replay(data, synthetic=True)
        self.assertEqual(result, replay.replay(data, synthetic=True))
        self.assertEqual(data, before)
        self.assertEqual(repr(getcontext()), decimal)
        with self.assertRaises(FrozenInstanceError):
            result.points[0].cells[0].bias = "BULLISH"
        self.assertEqual(len(result.run_hash), 64)

    def test_core_has_no_io_provider_or_ui_imports(self):
        replay, demo = api()
        tree = ast.parse(Path(replay.__file__).read_text(encoding="utf-8"))
        imports = {n.names[0].name.split(".")[0] if isinstance(n, ast.Import) else n.module.split(".")[0]
                   for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))}
        self.assertFalse(imports & {"os", "sys", "socket", "sqlite3", "subprocess", "pathlib", "moomoo", "futu", "tkinter"})
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertNotIn("open", calls)

    def test_no_numeric_call_for_blocked_frame(self):
        replay, demo = api()
        data = demo("partial")
        with patch("_pr31_pinned_kernel.assess", wraps=__import__("_pr31_pinned_kernel").assess) as assessor:
            replay.replay(replace(data, series=data.series, steps=(data.steps[34],)), synthetic=True)
        self.assertEqual(assessor.call_count, 1)  # Valid SPY only, never partial QQQ.

    def test_demo_factory_rejects_unknown_and_uses_no_test_imports(self):
        replay, demo = api()
        with self.assertRaises(ValueError):
            demo("real")
        tree = ast.parse(Path(__import__("synthetic_replay_demo").__file__).read_text(encoding="utf-8"))
        self.assertFalse(any(isinstance(n, ast.ImportFrom) and (n.module or "").startswith("test_")
                             for n in ast.walk(tree)))


    def test_real_fractional_receipt_boundary_is_never_rounded_early(self):
        from datetime import datetime, timedelta
        from canonical_candles import identity
        replay, demo = api()
        data = demo("conflict")
        source = data.series[1]
        rows = list(source.bundle.observations)
        receipt = (datetime.fromisoformat(rows[34].available_at) + timedelta(microseconds=1)).isoformat()
        rows[34] = replace(rows[34], available_at=receipt, received_at=receipt, completion_received_at=receipt)
        rows = tuple(rows)
        source = replace(source, bundle=replace(source.bundle, observations=rows,
                         capture_hash=identity((rows, source.bundle.pages))))
        steps = (data.steps[34], replace(data.steps[34], cutoff=receipt))
        result = replay.replay(replace(data, series=(data.series[0], source), steps=steps), synthetic=True)
        self.assertEqual(result.points[0].cells[1].state, "DATA_BLOCKED")
        self.assertEqual(result.points[1].cells[1].state, "CANDIDATE")

    def test_delayed_revision_cannot_rewrite_a_prior_point(self):
        from canonical_candles import identity
        replay, demo = api()
        data = demo("conflict")
        original = replay.replay(data, synthetic=True)
        source = data.series[0]
        late = replace(source.bundle.observations[0], observation_id="LATE", revision_id="REV-2",
                       row_id="LATE", available_at=data.steps[39].cutoff,
                       received_at=data.steps[39].cutoff, completion_received_at=data.steps[39].cutoff,
                       values=(float("inf"), None, True, 0, 0), raw_stamp="BAD")
        rows = source.bundle.observations + (late,)
        pages = (replace(source.bundle.pages[0], observation_ids=tuple(row.observation_id for row in rows)),)
        source = replace(source, bundle=replace(source.bundle, observations=rows, pages=pages,
                         capture_hash=identity((rows, pages))))
        changed = replay.replay(replace(data, series=(source, data.series[1])), synthetic=True)
        for earlier, later in zip(original.points[:39], changed.points[:39]):
            self.assertEqual(earlier.decision_hash, later.decision_hash)
        self.assertNotEqual(original.run_hash, changed.run_hash)
        self.assertEqual(changed.points[-1].cells[0].state, "DATA_BLOCKED")

class ViewerTests(unittest.TestCase):
    def test_text_displays_selected_time_profile_quality_and_calculations(self):
        replay, demo = api()
        from raccoon_replay_viewer import render_text
        result = replay.replay(demo("conflict"), synthetic=True)
        text = render_text(result, 34)
        for required in ("SYNTHETIC ONLY", "FINAL-only", "35", "CONFLICT", "SPY", "QQQ",
                         "EMA9", "EMA21", "relative volume", "HLC3", "WAIT", "UTC", "not PR18"):
            self.assertIn(required, text)

    def test_blocked_view_explains_provisional_and_no_action(self):
        replay, demo = api()
        from raccoon_replay_viewer import render_text
        text = render_text(replay.replay(demo("provisional"), synthetic=True), 34)
        self.assertIn("FINALITY_UNVERIFIED", text)
        self.assertIn("DATA_BLOCKED", text)
        self.assertIn("No orders", text)

    def test_early_view_does_not_display_future_values(self):
        replay, demo = api()
        from raccoon_replay_viewer import render_text
        result = replay.replay(demo("conflict"), synthetic=True)
        text = render_text(result, 0)
        self.assertNotIn("140", text)  # Last SPY close is 140, not visible at minute1.
        self.assertIn("INSUFFICIENT_REFERENCE_WARMUP", text)

    def test_text_cli_uses_no_tk_and_rejects_external_paths(self):
        api()
        import raccoon_replay_viewer as viewer
        with patch.object(viewer, "create_window", side_effect=AssertionError("GUI forbidden")):
            with contextlib.redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(viewer.main(["--text", "--scenario", "conflict", "--minute", "35"]), 0)
            self.assertIn("CONFLICT", stream.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                viewer.main(["--file", "research.sqlite3"])

    def test_view_index_validation(self):
        replay, demo = api()
        from raccoon_replay_viewer import render_text
        result = replay.replay(demo("mixed"), synthetic=True)
        for index in (-1, 40, True, "1"):
            with self.assertRaises(ValueError):
                render_text(result, index)

    def test_viewer_model_step_and_scenario_controls(self):
        api()
        from raccoon_replay_viewer import ViewerModel
        model = ViewerModel("conflict", 35)
        self.assertEqual(model.index, 34)
        model.move(100)
        self.assertEqual(model.index, 39)
        model.move(-100)
        self.assertEqual(model.index, 0)
        model.select("provisional")
        self.assertEqual(model.index, 0)
        model.seek(35)
        self.assertIn("FINALITY_UNVERIFIED", model.text())

    def test_headless_gui_error_is_reported_without_a_traceback(self):
        api()
        import types
        import raccoon_replay_viewer as viewer
        class HeadlessError(Exception):
            pass
        fake_tk = types.SimpleNamespace(TclError=HeadlessError)
        with patch.dict("sys.modules", {"tkinter": fake_tk}):
            with patch.object(viewer, "create_window", side_effect=HeadlessError("No display")):
                with contextlib.redirect_stderr(io.StringIO()) as stream:
                    self.assertEqual(viewer.main([]), 2)
                self.assertIn("--text", stream.getvalue())

    def test_precomputed_ui_scenario_change_never_runs_calculations(self):
        replay, demo = api()
        import raccoon_replay_viewer as viewer
        conflict = replay.replay(demo("conflict"), synthetic=True)
        provisional = replay.replay(demo("provisional"), synthetic=True)
        cache = (("conflict", conflict), ("provisional", provisional))
        with patch.object(viewer, "replay", side_effect=AssertionError("Calculation in UI callback")):
            model = viewer.ViewerModel("conflict", 35, precomputed=cache)
            model.select("provisional")
            self.assertIn("FINALITY_UNVERIFIED", model.text())
