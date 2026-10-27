"""Synthetic regression tests for evidence wording; no provider or database access."""
import copy
import unittest
from datetime import datetime, timedelta

from market_intelligence import calculate, format_report


def synthetic_candles(count=390, start="2026-10-23 09:31:00", symbol="SPY"):
    first = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    return [
        dict(symbol=symbol, time=(first + timedelta(minutes=i)).strftime(
            "%Y-%m-%d %H:%M:%S"),
             open=100, high=101, low=99, close=100, volume=100)
        for i in range(count)
    ]


class TimestampEvidenceWordingTests(unittest.TestCase):
    def assert_no_full_session_claim(self, result):
        self.assertFalse(result["end_labeled_full_session_evidence"])
        self.assertFalse(result["session_complete_390"])
        self.assertNotIn("STRONGLY SUGGESTED", result["timestamp_convention"])
        self.assertIn("UNVERIFIED", result["timestamp_convention"])

    def test_insufficient_or_wrong_coverage_does_not_claim_full_session(self):
        full = synthetic_candles()
        cases = {
            "one candle": full[:1],
            "opening window only": full[:30],
            "missing interior minute": full[:100] + full[101:],
            "390 rows but duplicate replaces minute": full[:100] + [full[99]] + full[101:],
            "390 start-labeled bars": synthetic_candles(start="2026-10-23 09:30:00"),
        }
        for name, rows in cases.items():
            with self.subTest(name=name):
                self.assert_no_full_session_claim(calculate(rows)["SPY"])

    def test_full_end_labeled_coverage_retains_support_without_confirmation(self):
        result = calculate(synthetic_candles())["SPY"]
        self.assertTrue(result["end_labeled_full_session_evidence"])
        self.assertTrue(result["session_complete_390"])
        self.assertIn("STRONGLY SUGGESTED", result["timestamp_convention"])
        self.assertIn("not independently verified", result["timestamp_convention"])

    def test_evidence_is_scoped_to_each_symbol_and_selected_session(self):
        rows = synthetic_candles(symbol="QQQ") + synthetic_candles(count=1)
        results = calculate(rows)
        self.assertIn("STRONGLY SUGGESTED", results["QQQ"]["timestamp_convention"])
        self.assert_no_full_session_claim(results["SPY"])
        rows = synthetic_candles() + synthetic_candles(
            count=1, start="2026-10-26 09:31:00")
        result = calculate(rows)["SPY"]
        self.assertEqual(result["session"], "2026-10-26")
        self.assert_no_full_session_claim(result)

    def test_raw_rows_ranges_and_provisional_report_are_preserved(self):
        for start in ("2026-10-23 09:30:00", "2026-10-23 09:31:00"):
            with self.subTest(start=start):
                rows = synthetic_candles(count=31, start=start)
                original = copy.deepcopy(rows)
                results = calculate(rows)
                self.assertEqual(rows, original)
                result = results["SPY"]
                for minutes in (5, 15, 30):
                    expected_raw = {"high": 101.0, "low": 99.0} if start.endswith(
                        "09:30:00") else None
                    self.assertEqual(result[f"or{minutes}"], expected_raw)
                    self.assertEqual(result[f"candidate_or{minutes}"],
                                     {"high": 101.0, "low": 99.0})
                report = format_report(results)
                self.assertNotIn("STRONGLY SUGGESTED", report)
                self.assertIn(result["timestamp_convention"], report)
                self.assertIn("PROVISIONAL end-labeled", report)
                self.assertIn("NOT VERIFIED FOR TRADING", report)

    def test_empty_input_report_does_not_claim_timestamp_evidence(self):
        results = calculate([])
        self.assertEqual(results, {"SPY": {"status": "NO DATA"},
                                   "QQQ": {"status": "NO DATA"}})
        self.assertNotIn("STRONGLY SUGGESTED", format_report(results))


if __name__ == "__main__":
    unittest.main()
