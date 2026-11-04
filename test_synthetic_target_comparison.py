"""Paired-target comparisons with identical fictional inputs."""
from dataclasses import replace
from decimal import Decimal
import unittest
from synthetic_replay_demo import make_demo
from paper_signal_engine import run
from synthetic_options_execution import Quote, Config, simulate
from synthetic_target_comparison import compare_targets

class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo = make_demo("conflict")
        cls.data = replace(demo, steps=(demo.steps[34],))
        cls.event = run(cls.data, synthetic=True).signals[0]

    def quote(self, second, bid, ask):
        e = self.event
        at = "2026-10-23T10:05:%02d+00:00" % second
        return Quote(e.event_id, "FICTIONAL1",
                     "CALL" if e.direction == "BULLISH" else "PUT",
                     at, at, bid, ask)

    def test_five_exits_earlier_than_twenty_on_identical_path(self):
        quotes = (self.quote(2, ".19", ".20"),
                  self.quote(3, ".21", ".22"),
                  self.quote(4, ".24", ".25"))
        paired = compare_targets(self.data, quotes, synthetic=True)
        self.assertEqual(paired.five.target_exits, 1)
        self.assertEqual(paired.twenty.target_exits, 1)
        self.assertEqual(Decimal(paired.five.realized_net), Decimal("1"))
        self.assertEqual(Decimal(paired.twenty.realized_net), Decimal("4"))
        self.assertNotEqual(paired.five.run_hash, paired.twenty.run_hash)
        self.assertEqual(paired.evidence, "FICTIONAL_REPLAY_ONLY")

    def test_five_exits_before_reversal_twenty_stops(self):
        quotes = (self.quote(2, ".19", ".20"),
                  self.quote(3, ".21", ".22"),
                  self.quote(4, ".10", ".21"))
        paired = compare_targets(self.data, quotes, synthetic=True)
        self.assertEqual((paired.five.target_exits, paired.five.stop_exits), (1, 0))
        self.assertEqual((paired.twenty.target_exits, paired.twenty.stop_exits), (0, 1))
        self.assertEqual(Decimal(paired.five.realized_net), Decimal("1"))
        self.assertEqual(Decimal(paired.twenty.realized_net), Decimal("-10"))

    def test_costs_can_erase_five_percent_gain(self):
        quotes = (self.quote(2, ".19", ".20"), self.quote(3, ".21", ".22"))
        paired = compare_targets(self.data, quotes, fee_per_fill=".50", synthetic=True)
        self.assertEqual(Decimal(paired.five.realized_net), Decimal("0"))
        self.assertEqual(paired.twenty.target_exits, 0)
        self.assertEqual(paired.twenty.open_positions, 1)

    def test_unsupported_target_and_nonfictional_rejected(self):
        with self.assertRaises(ValueError):
            simulate(self.data, (), Config(profit_target_fraction=".10"), synthetic=True)
        with self.assertRaises(ValueError):
            compare_targets(self.data, (), synthetic=False)

if __name__ == "__main__":
    unittest.main()
