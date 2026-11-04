"""End-to-end fictional signal -> contract -> option execution regressions."""
from dataclasses import replace
from decimal import Decimal
import unittest
from synthetic_replay_demo import make_demo
from paper_signal_engine import run
from synthetic_contract_selector import Candidate
from synthetic_options_adapter import FixtureObservation
from synthetic_options_pipeline import SelectionInput, execute_fixture_pipeline
from synthetic_options_execution import Config

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo = make_demo("conflict")
        cls.data = replace(demo, steps=(demo.steps[34],))
        cls.event = run(cls.data, synthetic=True).signals[0]

    def candidate(self, **changes):
        e = self.event
        value = Candidate("FICTIONAL1", e.symbol,
                          "CALL" if e.direction == "BULLISH" else "PUT",
                          "2026-10-23", "580", ".19", ".20", 10, 10, e.cutoff)
        return replace(value, **changes)

    def observation(self, second=2, bid=".19", ask=".20", **changes):
        e = self.event
        at = "2026-10-23T10:05:%02d+00:00" % second
        value = FixtureObservation(e.event_id, "FICTIONAL1",
                 "CALL" if e.direction == "BULLISH" else "PUT",
                 at, at, bid, ask)
        return replace(value, **changes)

    def execute(self, candidates, observations, config=Config()):
        item = SelectionInput(self.event.event_id, tuple(candidates), tuple(observations))
        return execute_fixture_pipeline(self.data, (item,), config, synthetic=True)

    def test_end_to_end_target_and_auditable_pnl(self):
        result = self.execute([self.candidate()],
                              [self.observation(), self.observation(3, ".24", ".25")],
                              Config(fee_per_fill=".50"))
        self.assertEqual(result.decisions[0][1].selected, "FICTIONAL1")
        self.assertEqual([row[1] for row in result.execution.ledger[:2]],
                         ["BUY", "SELL_TARGET"])
        self.assertEqual(Decimal(result.execution.realized_net), Decimal("3"))
        self.assertEqual(result.execution.open_positions, ())
        self.assertEqual(result.orders, "DISABLED")

    def test_stop_and_no_eligible_contract(self):
        stopped = self.execute([self.candidate()],
                               [self.observation(), self.observation(3, ".10", ".21")])
        self.assertEqual(stopped.execution.ledger[1][1], "SELL_STOP")
        blocked = self.execute([self.candidate(ask=".31")], [])
        self.assertIsNone(blocked.decisions[0][1].selected)
        self.assertEqual(blocked.execution.ledger[0][1], "UNFILLED")
        self.assertFalse(any(row[1] == "BUY" for row in blocked.execution.ledger))

    def test_rejected_contract_cannot_be_filled(self):
        with self.assertRaises(ValueError):
            self.execute([self.candidate(ask=".31")], [self.observation()])
        with self.assertRaises(ValueError):
            self.execute([self.candidate()], [self.observation(contract="OTHER")])
        with self.assertRaises(ValueError):
            self.execute([self.candidate()], [self.observation(signal_id="WRONG")])

    def test_stale_and_invalid_quotes_still_block(self):
        stale = self.observation(observed_at="2026-10-23T10:04:00+00:00")
        result = self.execute([self.candidate()], [stale])
        self.assertEqual(result.execution.ledger[0][1], "QUOTE_BLOCKED")
        invalid = self.execute([self.candidate()], [self.observation(bid="NaN")])
        self.assertEqual(invalid.execution.ledger[0][1], "QUOTE_BLOCKED")

    def test_fail_closed_inputs(self):
        item = SelectionInput(self.event.event_id, (self.candidate(),), ())
        with self.assertRaises(ValueError):
            execute_fixture_pipeline(self.data, (item,))
        with self.assertRaises(ValueError):
            execute_fixture_pipeline(self.data, (item, item), synthetic=True)
        with self.assertRaises(ValueError):
            execute_fixture_pipeline(self.data,
                (replace(item, signal_id="UNKNOWN"),), synthetic=True)
        with self.assertRaises(ValueError):
            execute_fixture_pipeline(self.data,
                (replace(item, candidates=[self.candidate()]),), synthetic=True)

if __name__ == "__main__":
    unittest.main()
