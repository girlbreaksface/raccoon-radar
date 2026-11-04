"""Offline fictional 0DTE selection tests."""
from dataclasses import replace
import unittest
from synthetic_contract_selector import Candidate, select_contract

AT = "2026-10-23T14:05:02+00:00"
DAY = "2026-10-23"

def c(contract="A", **kw):
    obj = Candidate(contract, "SPY", "CALL", DAY, "580", ".20", ".25",
                    10, 10, AT)
    return replace(obj, **kw)

def pick(items, **kw):
    return select_contract("SPY", "BULLISH", DAY, AT, tuple(items), **kw)

class SelectionTests(unittest.TestCase):
    def test_tightest_then_cheapest_then_id(self):
        result = pick([c("B", bid=".22", ask=".25"), c("A", bid=".22", ask=".25"),
                       c("C", bid=".19", ask=".25")])
        self.assertEqual(result.selected, "A")
        self.assertEqual(result.eligible, ("A", "B", "C"))
        self.assertEqual(result.orders, "DISABLED")

    def test_premium_spread_and_size(self):
        result = pick([c("P", ask=".31"), c("S", bid=".01"),
                       c("L", ask_size=0), c("OK", bid=".24", ask=".30")])
        self.assertEqual(result.selected, "OK")
        self.assertEqual(dict(result.rejected), {
            "P":"PREMIUM_LIMIT", "S":"SPREAD_TOO_WIDE",
            "L":"INSUFFICIENT_SIZE"})

    def test_right_expiration_and_symbol(self):
        result = pick([c("PUT", right="PUT"), c("NEXT", expiration="2026-10-24"),
                       c("QQQ", symbol="QQQ")])
        self.assertIsNone(result.selected)
        self.assertEqual(len(result.rejected), 3)

    def test_bad_or_stale_quotes(self):
        result = pick([c("NAN", bid="NaN"), c("CROSS", bid=".26"),
                       c("OLD", observed_at="2026-10-23T14:04:55+00:00"),
                       c("FUTURE", observed_at="2026-10-23T14:05:03+00:00")])
        self.assertIsNone(result.selected)
        self.assertEqual(dict(result.rejected)["OLD"], "STALE_OR_FUTURE")

    def test_inclusive_boundaries(self):
        result = pick([c("LIMIT", bid=".225", ask=".30",
                         observed_at="2026-10-23T14:04:57+00:00")])
        self.assertEqual(result.selected, "LIMIT")

    def test_fail_closed_structure(self):
        with self.assertRaises(ValueError):
            pick([c(), c()])
        with self.assertRaises(ValueError):
            pick([replace(c(), synthetic=False)])
        with self.assertRaises(ValueError):
            pick([{"contract":"A"}])
        with self.assertRaises(ValueError):
            pick([], max_age_seconds=True)
        with self.assertRaises(ValueError):
            pick([], max_spread_fraction="NaN")

    def test_put_direction(self):
        result = select_contract("SPY", "BEARISH", DAY, AT,
                                 (c(right="PUT"),))
        self.assertEqual(result.selected, "A")

if __name__ == "__main__":
    unittest.main()
