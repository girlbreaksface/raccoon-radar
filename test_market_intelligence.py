"""Regression checks for read-only opening-range research and timestamp ambiguity."""
import unittest
from datetime import datetime, timedelta
from market_intelligence import calculate


def candles(first_minute=30, count=30, symbol="SPY"):
    start = datetime(2026, 10, 23, 9, first_minute)
    return [
        dict(symbol=symbol, time=(start + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"),
             # Cap synthetic excursions so a 390-minute fixture stays positive.
             open=100, high=101 + min(i, 90), low=99 - min(i, 90), close=100, volume=100)
        for i in range(count)
    ]


class OpeningRangeTests(unittest.TestCase):
    def test_complete_start_labeled_opening_ranges(self):
        r = calculate(candles())["SPY"]
        self.assertEqual(r["or5"], {"high": 105, "low": 95})
        self.assertEqual(r["or15"], {"high": 115, "low": 85})
        self.assertEqual(r["or30"], {"high": 130, "low": 70})
        self.assertEqual(r["or5_missing"], [])

    def test_missing_0930_does_not_become_verified_range(self):
        r = calculate(candles(first_minute=31))["SPY"]
        for n in (5, 15, 30):
            self.assertIsNone(r[f"or{n}"])
            self.assertIn("09:30", r[f"or{n}_missing"])
        self.assertIsNotNone(r["candidate_or5"])
        self.assertFalse(r["end_labeled_full_session_evidence"])

    def test_full_390_end_labeled_session_is_evidence_not_confirmation(self):
        rows = candles(first_minute=31, count=390)
        self.assertTrue(all(row["low"] > 0 for row in rows))
        r = calculate(rows)["SPY"]
        self.assertTrue(r["end_labeled_full_session_evidence"])
        self.assertIsNone(r["or5"])
        self.assertIsNotNone(r["candidate_or30"])

    def test_missing_minute_prevents_complete_range(self):
        rows = [r for r in candles() if not r["time"].endswith("09:32:00")]
        r = calculate(rows)["SPY"]
        self.assertIsNone(r["or5"])
        self.assertEqual(r["or5_missing"], ["09:32"])

    def test_bad_ohlc_is_discarded(self):
        rows = candles(count=5)
        rows[0]["low"] = 105
        r = calculate(rows)["SPY"]
        self.assertIsNone(r["or5"])
        self.assertIn("09:30", r["or5_missing"])


if __name__ == "__main__":
    unittest.main()
