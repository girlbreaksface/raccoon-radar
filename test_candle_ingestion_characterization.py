"""Characterize CURRENT ingestion; undesirable behavior is not endorsed policy.

Actual worker ASTs run with fake row tables, quote context and ET wall clock.
No Tk, real SDK, persistence event consumer, network or database is executed.
"""
import ast
import copy
import math
import queue
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


def candle(stamp, **overrides):
    return {"time_key": stamp, "open": 100, "high": 102, "low": 99,
            "close": 101, "volume": 10, **overrides}


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def iterrows(self):
        return iter(enumerate(self.rows))


def actual_worker(name):
    path = Path(__file__).with_name("raccoon_dashboard_v1_5_14.py")
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "Dashboard")
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                and n.name == name)
    return path, node


class CandleIngestionCharacterizationTests(unittest.TestCase):
    def run_worker(self, kind, responses, now="2026-10-23 17:00:00",
                   start="2026-10-23", end="2026-10-23", request_error=None):
        wall_clock = datetime.fromisoformat(now)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return wall_clock.replace(tzinfo=tz)

        calls = []
        closed = []

        def request(symbol, **kwargs):
            calls.append((symbol, copy.deepcopy(kwargs)))
            if request_error:
                raise request_error
            ret, data, page = responses.get(
                (symbol, kwargs["start"]), responses.get(symbol, (0, [], None)))
            return ret, Rows(data) if ret == 0 else data, page

        context = types.SimpleNamespace(
            request_history_kline=request, close=lambda: closed.append(True))
        sdk = types.ModuleType("moomoo")
        sdk.OpenQuoteContext = lambda **kwargs: context
        sdk.RET_OK = 0
        sdk.KLType = types.SimpleNamespace(K_1M="SYNTHETIC_1M")
        zones = types.ModuleType("zoneinfo")
        zones.ZoneInfo = lambda name: timezone.utc  # ET WALL clock, no DST claim.
        name = "_fetch_candles_worker" if kind == "single" else "_fetch_range_worker"
        path, node = actual_worker(name)
        namespace = {"datetime": Clock, "timedelta": timedelta,
                     "analyze": lambda rows: [{"synthetic_analysis": True}]}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"),
             namespace)
        dashboard = types.SimpleNamespace(candle_queue=queue.Queue())
        with patch.dict("sys.modules", {"moomoo": sdk, "zoneinfo": zones}):
            args = () if kind == "single" else (
                datetime.fromisoformat(start).date(), datetime.fromisoformat(end).date())
            namespace[name](dashboard, *args)
        event = dashboard.candle_queue.get_nowait()
        self.assertTrue(dashboard.candle_queue.empty())
        self.assertEqual(closed, [True])
        return event, calls

    def both(self, rows, page=None):
        return {s: (0, rows, page) for s in ("US.SPY", "US.QQQ")}

    def raw(self, event):
        self.assertIn(event[0], ("success", "range_success"))
        return event[5] if event[0] == "success" else event[2]

    def spy_times(self, event):
        return [r["time"] for r in self.raw(event) if r["symbol"] == "US.SPY"]

    def test_current_both_paths_exclude_1600_without_shifting_raw_stamps(self):
        stamps = ["2026-10-23 " + t for t in
                  ("09:29:00", "09:30:00", "15:59:00", "16:00:00", "16:01:00")]
        rows = [candle(t) for t in stamps]
        original = copy.deepcopy(rows)
        for kind in ("single", "range"):
            with self.subTest(kind=kind):
                event, _ = self.run_worker(kind, self.both(rows))
                self.assertEqual(self.spy_times(event), [stamps[1], stamps[2]])
        self.assertEqual(rows, original)

    def test_current_range_keeps_current_and_future_minutes_single_does_not(self):
        rows = [candle("2026-10-23 " + t) for t in
                ("12:33:00", "12:34:00", "12:35:00")]
        single, _ = self.run_worker("single", self.both(rows), now="2026-10-23 12:34:45")
        ranged, _ = self.run_worker("range", self.both(rows), now="2026-10-23 12:34:45")
        self.assertEqual(self.spy_times(single), ["2026-10-23 12:33:00"])
        self.assertEqual(self.spy_times(ranged), [r["time_key"] for r in rows])

    def test_single_cutoff_is_current_minute_even_at_exact_boundary(self):
        rows = [candle("2026-10-23 " + t) for t in ("12:33:00", "12:34:00")]
        for seconds in ("00", "59"):
            with self.subTest(seconds=seconds):
                event, _ = self.run_worker("single", self.both(rows),
                                          now="2026-10-23 12:34:" + seconds)
                self.assertEqual(self.spy_times(event), ["2026-10-23 12:33:00"])

    def test_current_single_does_not_filter_wrong_session_date_range_does(self):
        rows = [candle("2026-10-22 09:30:00"), candle("2026-10-23 09:30:00")]
        single, _ = self.run_worker("single", self.both(rows))
        ranged, _ = self.run_worker("range", self.both(rows))
        self.assertEqual(self.spy_times(single), [r["time_key"] for r in rows])
        self.assertEqual(self.spy_times(ranged), ["2026-10-23 09:30:00"])

    def test_gaps_and_duplicate_rows_are_retained_not_repaired(self):
        rows = [candle("2026-10-23 09:32:00"), candle("2026-10-23 09:30:00"),
                candle("2026-10-23 09:32:00", close=100)]
        for kind in ("single", "range"):
            with self.subTest(kind=kind):
                event, _ = self.run_worker(kind, self.both(rows))
                self.assertEqual(self.spy_times(event), [
                    "2026-10-23 09:30:00", "2026-10-23 09:32:00", "2026-10-23 09:32:00"])
                values = [r["close"] for r in self.raw(event) if r["symbol"] == "US.SPY"]
                self.assertEqual(values, [101, 101, 100])

    def test_current_pagination_key_is_discarded_by_both_paths(self):
        for kind in ("single", "range"):
            with self.subTest(kind=kind):
                event, calls = self.run_worker(
                    kind, self.both([candle("2026-10-23 09:30:00")], page="MORE_PAGES"))
                self.assertEqual(len(calls), 2)
                self.assertTrue(all("page_req_key" not in kwargs for _, kwargs in calls))
                self.assertEqual(self.spy_times(event), ["2026-10-23 09:30:00"])

    def test_partial_session_with_empty_qqq_is_reported_as_success(self):
        responses = self.both([candle("2026-10-23 09:30:00")])
        responses["US.QQQ"] = (0, [], None)
        for kind in ("single", "range"):
            with self.subTest(kind=kind):
                event, _ = self.run_worker(kind, responses)
                self.assertEqual(len(self.raw(event)), 1)
                if kind == "range":
                    self.assertEqual(event[3], ["2026-10-23"])
                    self.assertEqual(event[4], [])

    def test_single_provider_failure_drops_partial_result_and_reports_error(self):
        responses = self.both([candle("2026-10-23 09:30:00")])
        responses["US.QQQ"] = (1, "SYNTHETIC QQQ ERROR", None)
        event, _ = self.run_worker("single", responses)
        self.assertEqual(event[0], "error")
        self.assertIn("SYNTHETIC QQQ ERROR", event[1])

    def test_range_failure_discards_that_day_but_keeps_later_day(self):
        responses = {}
        for day in ("2026-10-22", "2026-10-23"):
            for symbol in ("US.SPY", "US.QQQ"):
                responses[(symbol, day)] = (0, [candle(day + " 09:30:00")], None)
        responses[("US.QQQ", "2026-10-22")] = (1, "SYNTHETIC FIRST DAY ERROR", None)
        event, calls = self.run_worker("range", responses, start="2026-10-22")
        self.assertEqual(event[3], ["2026-10-23"])
        self.assertEqual(len(event[4]), 1)
        self.assertTrue(all(r["time"].startswith("2026-10-23") for r in self.raw(event)))
        self.assertEqual(len(calls), 4)

    def test_ingestion_only_float_converts_not_ohlcv_validates(self):
        rows = [candle("2026-10-23 09:30:00", low=105),
                candle("2026-10-23 09:31:00", volume=float("nan")),
                candle("2026-10-23 09:32:00", volume="invalid")]
        for kind in ("single", "range"):
            with self.subTest(kind=kind):
                event, _ = self.run_worker(kind, self.both(rows))
                spy = [r for r in self.raw(event) if r["symbol"] == "US.SPY"]
                self.assertEqual(len(spy), 2)
                self.assertEqual(spy[0]["low"], 105)
                self.assertTrue(math.isnan(spy[1]["volume"]))

    def test_weekend_single_uses_friday_range_skips_weekend(self):
        event, calls = self.run_worker("single", self.both(
            [candle("2026-10-23 09:30:00")]), now="2026-10-24 12:00:00")
        self.assertEqual(event[3], "2026-10-23")
        self.assertTrue(all(k["start"] == "2026-10-23" for _, k in calls))
        ranged, calls = self.run_worker("range", {}, start="2026-10-24", end="2026-10-25")
        self.assertEqual(ranged[0], "error")
        self.assertEqual(calls, [])

    def test_declared_early_close_is_not_a_calendar_rule_in_workers(self):
        rows = [candle("2026-11-27 13:00:00"), candle("2026-11-27 13:01:00")]
        for kind in ("single", "range"):
            with self.subTest(kind=kind):
                event, _ = self.run_worker(kind, self.both(rows),
                    now="2026-11-27 17:00:00", start="2026-11-27", end="2026-11-27")
                self.assertEqual(self.spy_times(event), [r["time_key"] for r in rows])

    def test_request_exception_reports_error_and_closes_context(self):
        for kind in ("single", "range"):
            with self.subTest(kind=kind):
                event, _ = self.run_worker(kind, {}, request_error=RuntimeError("SYNTHETIC"))
                self.assertEqual(event, ("error", "SYNTHETIC"))


if __name__ == "__main__":
    unittest.main()
