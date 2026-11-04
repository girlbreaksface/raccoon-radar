"""Offline regression checks for the fixture-to-simulator adapter."""
from dataclasses import replace
import unittest
from synthetic_replay_demo import make_demo
from paper_signal_engine import run
from synthetic_options_execution import Config, Quote, simulate
from synthetic_options_adapter import FixtureObservation, run_fixture_adapter

class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo = make_demo('conflict')
        cls.data = replace(demo, steps=(demo.steps[34],))
        cls.event = run(cls.data, synthetic=True).signals[0]

    def fixture(self, at='2026-10-23T10:05:02+00:00', bid='.19', ask='.20'):
        e = self.event
        return FixtureObservation(e.event_id, 'FICTIONAL1',
            'CALL' if e.direction == 'BULLISH' else 'PUT', at, at, bid, ask)

    def test_adapter_matches_direct_simulation(self):
        obs = (self.fixture(), self.fixture('2026-10-23T10:05:03+00:00', '.24', '.25'))
        converted = tuple(Quote(o.signal_id, o.contract, o.right,
            o.available_at, o.observed_at, o.bid, o.ask) for o in obs)
        self.assertEqual(run_fixture_adapter(self.data, obs, synthetic=True),
                         simulate(self.data, converted, synthetic=True))

    def test_rejects_untrusted_or_mutable_input(self):
        for observations in ([self.fixture()], (replace(self.fixture(), synthetic=False),),
                             ({'bid':'.20'},)):
            with self.subTest(observations=observations):
                with self.assertRaises(ValueError):
                    run_fixture_adapter(self.data, observations, synthetic=True)
        with self.assertRaises(ValueError):
            run_fixture_adapter(self.data, (self.fixture(),))
        with self.assertRaises(ValueError):
            run_fixture_adapter(self.data, (), config=None, synthetic=True)

    def test_bad_price_remains_blocked(self):
        result = run_fixture_adapter(self.data, (self.fixture(bid='NaN'),), synthetic=True)
        self.assertEqual(result.ledger[0][1], 'QUOTE_BLOCKED')
        self.assertEqual(result.orders, 'DISABLED')
        self.assertEqual(result.trading, 'NO-GO')

    def test_stale_quote_cannot_fill(self):
        obs = replace(self.fixture(), observed_at='2026-10-23T10:04:00+00:00')
        result = run_fixture_adapter(self.data, (obs,), synthetic=True)
        self.assertEqual(result.ledger[0][1], 'QUOTE_BLOCKED')
        self.assertEqual(result.open_positions, ())

if __name__ == '__main__':
    unittest.main()
