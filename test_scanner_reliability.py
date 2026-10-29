"""Synthetic evidence contracts and actual dashboard method regressions; no GUI/SDK/DB."""
import ast
import copy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock


def method(name, namespace):
    path = Path(__file__).with_name("raccoon_dashboard_v1_5_14.py")
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Dashboard")
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name]


class DashboardBiasRegressions(unittest.TestCase):
    def dashboard(self, rows):
        dashboard = types.SimpleNamespace(last_mtimes={}, csv_path=None, trade_path=None,
            signal_rows=[], spy_label=Mock(), qqq_label=Mock(), note=Mock(), status=Mock(),
            fill=Mock(), rows_label=Mock(), signal_tree=Mock(), trade_tree=Mock(),
            tabs=Mock(), signals_frame=Mock(), read_csv=Mock(return_value=(rows, ["symbol", "bias"])))
        # Bind only when implemented; the old methods do not call this helper.
        try:
            fn = method("_refresh_signal_labels", {"datetime": datetime})
            dashboard._refresh_signal_labels = types.MethodType(fn, dashboard)
        except StopIteration:
            pass
        return dashboard

    def load(self, rows):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"synthetic.csv"
            path.write_text("synthetic fixture", encoding="utf-8")
            dashboard = self.dashboard(rows)
            fn = method("load_csv", dict(Path=Path, filedialog=types.SimpleNamespace(
                askopenfilename=lambda **_: str(path)), messagebox=Mock()))
            fn(dashboard)
            return dashboard

    def test_substring_symbol_cannot_become_spy_bias(self):
        dashboard = self.load([dict(symbol="NOTSPY", bias="BULLISH")])
        self.assertEqual(dashboard.spy_label.config.call_args.kwargs["text"], "UNAVAILABLE")

    def test_unknown_csv_bias_cannot_become_current_bias(self):
        dashboard = self.load([dict(symbol="SPY", bias="GUARANTEED WIN")])
        self.assertEqual(dashboard.spy_label.config.call_args.kwargs["text"], "UNAVAILABLE")

    def test_unverified_timestamp_and_source_are_explicit(self):
        dashboard = self.load([dict(symbol="SPY", bias="BULLISH", bar_time_et="2026-10-23 10:00:00")])
        self.assertEqual(dashboard.spy_label.config.call_args.kwargs["text"], "UNVERIFIED")

    def test_csv_error_clears_both_previous_bias_labels(self):
        dashboard = self.dashboard([])
        dashboard.csv_path = "synthetic-missing.csv"
        method("poll_files", dict(Path=Path))(dashboard)
        for label in (dashboard.spy_label, dashboard.qqq_label):
            self.assertEqual(label.config.call_args.kwargs["text"], "UNAVAILABLE")

    def test_unchanged_csv_is_rechecked_without_rereading(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"synthetic.csv"
            path.write_text("synthetic", encoding="utf-8")
            dashboard = self.dashboard([])
            dashboard.csv_path = str(path)
            dashboard.last_mtimes[str(path)] = path.stat().st_mtime_ns
            dashboard._refresh_signal_labels = Mock()
            method("poll_files", dict(Path=Path))(dashboard)
            dashboard._refresh_signal_labels.assert_called_once_with()
            dashboard.read_csv.assert_not_called()

    def test_even_empty_exception_message_clears_previous_snapshot(self):
        dashboard = self.dashboard([dict(symbol="SPY", bias="BULLISH")])
        dashboard.signal_rows = [dict(symbol="SPY", bias="BULLISH")]
        dashboard._refresh_signal_labels(error="")
        self.assertEqual(dashboard.signal_rows, [])
        self.assertEqual(dashboard.spy_label.config.call_args.kwargs["text"], "UNAVAILABLE")


class SignalEvidenceTests(unittest.TestCase):
    now = datetime(2026, 10, 23, 14, 0, tzinfo=timezone.utc)

    def evaluate(self, rows, **changes):
        from scanner_reliability import evaluate_signals
        options = dict(now=self.now, max_age_seconds=120,
            evidence=dict(source_sha256="a"*64, authority="SYNTHETIC TEST CONTRACT",
                          availability_verified=True))
        options.update(changes)
        return evaluate_signals(rows, **options)

    def row(self, **changes):
        return dict(symbol="US.SPY", bias="BULLISH", source_sha256="a"*64,
                    event_at="2026-10-23T13:59:00+00:00",
                    available_at="2026-10-23T13:59:01+00:00", **changes)

    def test_each_symbol_has_independent_age_and_missing_state(self):
        spy = self.row()
        qqq = {**spy, "symbol":"QQQ", "event_at":"2026-10-23T13:00:00+00:00",
               "available_at":"2026-10-23T13:00:01+00:00"}
        result = self.evaluate([spy, qqq])
        self.assertTrue(result["SPY"]["eligible"])
        self.assertFalse(result["QQQ"]["eligible"])
        self.assertIn("STALE_EVENT", result["QQQ"]["reasons"])
        self.assertIn("NO_ROWS", self.evaluate([spy])["QQQ"]["reasons"])

    def test_latest_event_selected_not_file_order_inputs_unchanged(self):
        old = {**self.row(), "bias":"BEARISH", "event_at":"2026-10-23T13:58:30+00:00"}
        rows = [self.row(), old]
        before = copy.deepcopy(rows)
        self.assertEqual(self.evaluate(rows)["SPY"]["bias"], "BULLISH")
        self.assertEqual(rows, before)

    def test_default_missing_authority_or_policy_never_eligible(self):
        for changes in (dict(evidence=None), dict(max_age_seconds=None)):
            self.assertFalse(self.evaluate([self.row()], **changes)["SPY"]["eligible"])

    def test_unknown_and_malformed_signal_fail_closed(self):
        for bias in (None, [], "UNKNOWN", "bullish", " BULLISH "):
            row = {**self.row(), "bias":bias}
            self.assertFalse(self.evaluate([row])["SPY"]["eligible"])

    def test_future_delayed_naive_or_mismatched_source_fail_closed(self):
        cases = [dict(event_at="2026-10-23T14:01:00+00:00"),
                 dict(available_at="2026-10-23T14:01:00+00:00"),
                 dict(event_at="2026-10-23 13:59:00"), dict(source_sha256="b"*64)]
        for changes in cases:
            self.assertFalse(self.evaluate([{**self.row(), **changes}])["SPY"]["eligible"])

    def test_conflicting_same_event_and_malformed_latest_do_not_fallback(self):
        conflict = {**self.row(), "bias":"BEARISH"}
        self.assertFalse(self.evaluate([self.row(), conflict])["SPY"]["eligible"])
        self.assertFalse(self.evaluate([self.row(), {**self.row(), "bias":None}])["SPY"]["eligible"])

    def test_policy_and_clock_must_be_finite_positive_and_aware(self):
        for value in (float("nan"), float("inf"), -1, 0, True, 10**1000):
            self.assertFalse(self.evaluate([self.row()], max_age_seconds=value)["SPY"]["eligible"])
        with self.assertRaises(ValueError):
            self.evaluate([], now=self.now.replace(tzinfo=None))

    def test_no_trade_is_not_a_candidate_and_known_availability_not_inferred(self):
        result = self.evaluate([{**self.row(), "bias":"NO TRADE"}])["SPY"]
        self.assertFalse(result["eligible"])
        self.assertEqual(result["display"], "NO TRADE")
        self.assertIn("NO_TRADE", result["reasons"])
        result = self.evaluate([{**self.row(), "available_at":None}])["SPY"]
        self.assertFalse(result["eligible"])
        self.assertIn("TIMESTAMP_UNVERIFIED", result["reasons"])

    def test_generator_input_preserves_both_symbols_and_spy_qqq_conflict(self):
        rows = [self.row(), {**self.row(), "symbol":"QQQ", "bias":"BEARISH"}]
        result = self.evaluate(iter(rows))
        self.assertEqual(result["SPY"]["bias"],"BULLISH")
        self.assertEqual(result["QQQ"]["bias"],"BEARISH")

    def test_availability_before_event_and_empty_authority_are_rejected(self):
        self.assertFalse(self.evaluate([{**self.row(), "available_at":"2026-10-23T13:58:00Z"}])["SPY"]["eligible"])
        self.assertFalse(self.evaluate([self.row()], evidence=dict(source_sha256="a"*64,
            authority="", availability_verified=True))["SPY"]["eligible"])


class CandleAndPaginationTests(unittest.TestCase):
    def candle(self, stamp="2026-10-23 09:30:00", **changes):
        return dict(time_key=stamp, symbol="US.SPY", open=100, high=102, low=99,
                    close=101, volume=10, **changes)

    def test_quality_preserves_raw_gaps_duplicates_invalid_and_partial(self):
        from scanner_reliability import assess_candles
        rows = [self.candle(), self.candle(), self.candle("2026-10-23 09:32:00")]
        before = copy.deepcopy(rows)
        result = assess_candles(rows, symbol="SPY", session="2026-10-23", pagination_complete=False)
        self.assertEqual(result["duplicates"], ["2026-10-23 09:30:00"])
        self.assertEqual(result["raw_stamp_gaps"], [["2026-10-23 09:30:00", "2026-10-23 09:32:00"]])
        self.assertFalse(result["eligible"])
        self.assertIn("PAGINATION_INCOMPLETE", result["reasons"])
        self.assertEqual(rows, before)

    def test_nonfinite_nonpositive_inconsistent_ohlcv_rejected(self):
        from scanner_reliability import assess_candles
        for changes in (dict(volume=float("nan")), dict(close=0),dict(open=float("inf")),
                        dict(low=105), dict(volume=-1)):
            result = assess_candles([{**self.candle(), **changes}], symbol="SPY", session="2026-10-23", pagination_complete=True)
            self.assertEqual(result["invalid_rows"], [0])

    def test_boundary_no_shift_no_assumed_calendar_or_finality(self):
        from scanner_reliability import assess_candles
        rows = [self.candle("2026-10-23 16:00:00")]
        result = assess_candles(rows, symbol="SPY", session="2026-10-23", pagination_complete=True)
        self.assertEqual(result["raw_stamps"], ["2026-10-23 16:00:00"])
        self.assertIn("INTERVAL_COMPLETION_AVAILABILITY_UNVERIFIED", result["reasons"])
        self.assertFalse(result["eligible"])

    def test_pagination_keeps_all_raw_pages_and_no_inputs_mutated(self):
        from scanner_reliability import collect_pages
        pages = [(0, [self.candle()], "next"),(0,[self.candle("2026-10-23 16:00:00")],None)]
        before = copy.deepcopy(pages)
        request = Mock(side_effect=pages)
        result = collect_pages(request, "US.SPY", dict(start="2026-10-23",end="2026-10-23"))
        self.assertTrue(result["pagination_complete"])
        self.assertEqual(len(result["rows"]),2)
        self.assertEqual(request.call_args.kwargs["page_req_key"],"next")
        self.assertEqual(pages,before)

    def test_partial_failure_repeated_key_page_limit_and_exception_fail_closed(self):
        from scanner_reliability import collect_pages
        for responses, limit in [([(0,[self.candle()],"x"),(1,"synthetic error",None)],10),
                                 ([(0,[self.candle()],"x"),(0,[],"x")],10),
                                 ([(0,[self.candle()],"x")],1),
                                 ([(0,[self.candle()],"x"),OSError("synthetic")],10)]:
            result = collect_pages(Mock(side_effect=responses), "US.SPY", {}, max_pages=limit)
            self.assertFalse(result["pagination_complete"])
            self.assertEqual(result["rows"][0]["time_key"],"2026-10-23 09:30:00")
            self.assertTrue(result["reasons"])


if __name__ == "__main__":
    unittest.main()
