"""Aggregate fictional paired-target replay metrics."""
from dataclasses import replace
from decimal import Decimal
import unittest
from synthetic_replay_demo import make_demo
from paper_signal_engine import run
from synthetic_options_execution import Quote
from synthetic_target_scorecard import score_replays

class ScorecardTests(unittest.TestCase):
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

    def test_empty_sessions_do_not_claim_a_win_rate(self):
        result = score_replays((), synthetic=True)
        self.assertIsNone(result.five.win_rate)
        self.assertEqual(result.twenty.sessions, 0)
        self.assertEqual(result.trading, "NO-GO")

    def test_same_paths_compare_realized_net_not_just_targets(self):
        reversal = (self.data, (self.quote(2, ".19", ".20"),
                                 self.quote(3, ".21", ".22"),
                                 self.quote(4, ".10", ".21")))
        continuation = (self.data, (self.quote(2, ".19", ".20"),
                                     self.quote(3, ".21", ".22"),
                                     self.quote(4, ".24", ".25")))
        result = score_replays((reversal, continuation), synthetic=True)
        self.assertEqual((result.five.wins, result.five.losses), (2, 0))
        self.assertEqual((result.twenty.wins, result.twenty.losses), (1, 1))
        self.assertEqual(Decimal(result.five.realized_net), Decimal("2"))
        self.assertEqual(Decimal(result.twenty.realized_net), Decimal("-6"))
        self.assertEqual(result.five.win_rate, "1")
        self.assertEqual(result.twenty.win_rate, "0.5")
        self.assertEqual(result.evidence, "FICTIONAL_REPLAY_ONLY")

    def test_open_trades_are_excluded_from_win_rate(self):
        result = score_replays(((self.data, (self.quote(2, ".19", ".20"),)),),
                               synthetic=True)
        self.assertEqual(result.five.unresolved, 1)
        self.assertEqual(result.five.closed, 0)
        self.assertIsNone(result.five.win_rate)

    def test_fees_change_net_wins_to_flat(self):
        result = score_replays(((self.data, (self.quote(2, ".19", ".20"),
                                               self.quote(3, ".21", ".22"))),),
                               fee_per_fill=".50", synthetic=True)
        self.assertEqual((result.five.wins, result.five.flat), (0, 1))
        self.assertEqual(result.five.win_rate, "0")

    def test_fail_closed_nonfictional(self):
        with self.assertRaises(ValueError):
            score_replays(())
        with self.assertRaises(ValueError):
            score_replays(([self.data, ()],), synthetic=True)

if __name__ == "__main__":
    unittest.main()
