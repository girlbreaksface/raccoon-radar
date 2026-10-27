"""Synthetic-only candle quality contracts; no storage, network or repair."""
import copy
import unittest
from datetime import datetime, timedelta
from candle_quality import audit_candles


def candles(count=5, start="2026-10-23 09:30:00", symbol="SPY"):
    first = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    return [dict(symbol=symbol, time=(first + timedelta(minutes=i)).strftime(
        "%Y-%m-%d %H:%M:%S"), open=100, high=101, low=99, close=100, volume=10)
        for i in range(count)]


class CandleQualityTests(unittest.TestCase):
    def audit(self, rows, start="09:30", end="09:34"):
        return audit_candles(rows, expected_start=start, expected_end=end)

    def test_full_coverage_is_not_timestamp_verification(self):
        report = self.audit(candles())
        session = report["sessions"][0]
        self.assertTrue(session["coverage_complete"])
        self.assertTrue(session["quality_ok"])
        self.assertEqual(session["valid_unique_minutes"], 5)
        self.assertEqual(report["timestamp_semantics"], "UNVERIFIED")

    def test_gap_and_partial_session_are_explicit(self):
        rows = candles()
        for subset, missing in ((rows[:2], ["09:32", "09:33", "09:34"]),
                                (rows[:2] + rows[3:], ["09:32"])):
            with self.subTest(missing=missing):
                session = self.audit(subset)["sessions"][0]
                self.assertFalse(session["coverage_complete"])
                self.assertEqual(session["missing_minutes"], missing)
                self.assertFalse(session["quality_ok"])

    def test_duplicate_does_not_fill_gap_and_is_not_silently_removed(self):
        rows = candles()
        rows[2] = dict(rows[1], high=102)
        session = self.audit(rows)["sessions"][0]
        self.assertEqual(session["row_count"], 5)
        self.assertEqual(session["valid_unique_minutes"], 4)
        self.assertEqual(session["duplicates"],
                         [{"timestamp": "2026-10-23 09:31:00", "count": 2}])
        self.assertEqual(session["missing_minutes"], ["09:32"])

    def test_invalid_ohlcv_is_counted_and_cannot_fill_coverage(self):
        for field, value in (("low", 105), ("open", 0), ("close", float("nan")),
                             ("high", float("inf")), ("volume", -1),
                             ("volume", "bad")):
            with self.subTest(field=field, value=value):
                rows = candles()
                rows[2][field] = value
                report = self.audit(rows)
                self.assertEqual(report["invalid_rows"][0]["index"], 2)
                self.assertEqual(report["sessions"][0]["missing_minutes"], ["09:32"])
        rows = candles()
        rows[0]["volume"] = 0
        self.assertTrue(self.audit(rows)["sessions"][0]["quality_ok"])

    def test_bad_shape_symbol_and_timestamp_are_reported(self):
        report = self.audit([None, {}, dict(candles()[0], symbol=" "),
                             dict(candles()[0], time="bad"),
                             dict(candles()[0], time="2026-10-23 09:30:01")])
        self.assertEqual(len(report["invalid_rows"]), 5)
        self.assertEqual(report["row_count"], 5)

    def test_order_and_outside_bounds_are_reported(self):
        rows = candles()
        report = self.audit([rows[1], rows[0]] + rows[2:] +
                            candles(1, "2026-10-23 09:35:00"))
        session = report["sessions"][0]
        self.assertEqual(session["out_of_order_count"], 1)
        self.assertEqual(session["outside_expected_count"], 1)
        self.assertTrue(session["coverage_complete"])
        self.assertFalse(session["quality_ok"])

    def test_symbols_and_dates_do_not_bridge_coverage(self):
        rows = candles(2) + candles(2, symbol="QQQ") + candles(
            2, "2026-10-26 09:30:00")
        sessions = self.audit(rows)["sessions"]
        self.assertEqual(len(sessions), 3)
        self.assertTrue(all(s["missing_minutes"] == ["09:32", "09:33", "09:34"]
                            for s in sessions))

    def test_caller_can_declare_early_close_or_end_label_hypothesis(self):
        rows = candles(210, "2026-11-27 09:31:00")
        report = self.audit(rows, "09:31", "13:00")
        self.assertTrue(report["sessions"][0]["coverage_complete"])
        self.assertEqual(report["timestamp_semantics"], "UNVERIFIED")

    def test_inputs_are_unchanged_and_results_deterministic(self):
        rows = candles()
        original = copy.deepcopy(rows)
        self.assertEqual(self.audit(rows), self.audit(rows))
        self.assertEqual(rows, original)
        self.assertEqual(self.audit([])["sessions"], [])

    def test_reversed_or_off_minute_bounds_are_rejected(self):
        for start, end in (("16:00", "09:30"), ("bad", "16:00"),
                           ("09:30:01", "16:00")):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                self.audit([], start, end)


if __name__ == "__main__":
    unittest.main()
