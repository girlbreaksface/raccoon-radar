"""Fictional options only; no provider or execution evidence."""
from dataclasses import replace
from decimal import Decimal, localcontext
import unittest
from unittest.mock import patch
from canonical_candles import identity
from paper_signal_engine import run
from synthetic_replay_demo import make_demo
from synthetic_options_execution import Config, Quote, simulate, VERSION


class OptionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = make_demo('conflict')
        cls.data = replace(d, steps=(d.steps[34],))
        cls.signals = run(cls.data, synthetic=True)
        cls.e = cls.signals.signals[0]

    def q(self, second=2, bid='.19', ask='.20', **changes):
        at = '2026-10-23T10:05:%02d+00:00' % second
        q = Quote(self.e.event_id, 'FICTIONAL1', 'CALL' if self.e.direction == 'BULLISH' else 'PUT', at, at, bid, ask)
        return replace(q, **changes)

    def sim(self, quotes, config=Config()):
        return simulate(self.data, quotes, config, synthetic=True)

    def test_target_accounting_and_hash_chain(self):
        r = self.sim((self.q(), self.q(3, '.24', '.25')), Config(fee_per_fill='.50'))
        self.assertEqual(Decimal(r.realized_net), 3)
        self.assertEqual(r.open_positions, ())
        self.assertEqual(r.net_pnl, r.realized_net)
        self.assertEqual([x[1] for x in r.ledger[:2]], ['BUY', 'SELL_TARGET'])
        for row in r.ledger:
            self.assertEqual(row[-1], identity((VERSION, row[:-1])))
        self.assertEqual(r.ledger[1][-2], r.ledger[0][-1])
        self.assertEqual(r.trading, 'NO-GO')

    def test_stop_boundary_and_gap_fills_at_bid(self):
        for bid, pnl in (('.17', '-3'), ('.10', '-10')):
            r = self.sim((self.q(), self.q(3, bid, '.21')))
            self.assertEqual(r.ledger[1][1], 'SELL_STOP')
            self.assertEqual(Decimal(r.realized_net), Decimal(pnl))

    def test_slippage_and_fees(self):
        r = self.sim((self.q(), self.q(3, '.30', '.31')), Config(slippage_bps='100', fee_per_fill='1'))
        self.assertEqual(Decimal(r.realized_net), Decimal('7.5'))

    def test_premium_limit_inclusive_and_slippage(self):
        self.assertEqual(self.sim((self.q(ask='.30'),)).ledger[0][1], 'BUY')
        self.assertEqual(self.sim((self.q(ask='.30'),), Config(slippage_bps='1')).ledger[0][1], 'REJECT_PREMIUM_LIMIT')
        self.assertEqual(self.sim((self.q(ask='.31'),)).ledger[0][1], 'REJECT_PREMIUM_LIMIT')

    def test_missing_and_stale_marks_are_unknown(self):
        self.assertEqual(self.sim(()).ledger[0][1], 'UNFILLED')
        r = self.sim((self.q(), self.q(10, observed_at=self.q().at)))
        self.assertEqual(r.ledger[1][1], 'QUOTE_BLOCKED')
        self.assertIsNone(r.net_pnl)
        self.assertIsNone(r.open_positions[0][-1])

    def test_invalid_quotes_cannot_fill_or_exit(self):
        for changes in ({'bid':'NaN'}, {'bid':'0'}, {'ask':'Infinity'}, {'bid':'.3'}, {'observed_at':'bad'}, {'observed_at':self.q(3).at}):
            with self.subTest(changes=changes):
                r = self.sim((self.q(**changes),))
                self.assertEqual(r.ledger[0][1], 'QUOTE_BLOCKED')
                self.assertEqual(r.open_positions, ())
        r = self.sim((self.q(), self.q(3, bid='NaN')))
        self.assertIsNone(r.net_pnl)
        self.assertEqual(Decimal(r.realized_net), 0)

    def test_freshness_boundary(self):
        self.assertEqual(self.sim((self.q(7, observed_at=self.q().at),)).ledger[0][1], 'BUY')
        self.assertEqual(self.sim((self.q(8, observed_at=self.q().at),)).ledger[0][1], 'QUOTE_BLOCKED')

    def test_no_same_time_or_future_leakage(self):
        same = self.q(1)
        self.assertEqual(self.sim((same,)).ledger[0][1], 'UNFILLED')
        a = self.sim((self.q(),))
        b = self.sim((self.q(), self.q(3, '.24', '.25')))
        self.assertEqual(a.ledger[0], b.ledger[0])

    def test_structural_invalidity_aborts(self):
        for quotes in ((self.q(), self.q()), (self.q(3), self.q()),
                       (self.q(synthetic=False),), (self.q(right='INVALID'),),
                       (self.q(), self.q(3, contract='OTHER'))):
            with self.assertRaises(ValueError):
                self.sim(quotes)
        for config in (Config(slippage_bps='10000'), Config(fee_per_fill='-1'), Config(max_quote_age_seconds=True)):
            with self.assertRaises(ValueError):
                self.sim((), config)
        with self.assertRaises(ValueError):
            simulate(self.data, ())
        bad = replace(self.data.series[0], bundle=replace(self.data.series[0].bundle, synthetic=False))
        with self.assertRaises(ValueError):
            simulate(replace(self.data, series=(bad, self.data.series[1])), (), synthetic=True)

    def test_determinism_context_and_put_is_also_long(self):
        quotes = (self.q(), self.q(3, '.24', '.25'))
        a = self.sim(quotes)
        with localcontext() as ctx:
            ctx.prec = 6
            ctx.rounding = 'ROUND_DOWN'
            self.assertEqual(a, self.sim(quotes))
        e = replace(self.e, direction='BEARISH')
        with patch('synthetic_options_execution.run', return_value=replace(self.signals, signals=(e,))):
            r = self.sim(tuple(replace(q, right='PUT') for q in quotes))
            self.assertEqual(r.ledger[0][1], 'BUY')
            self.assertEqual(Decimal(r.realized_net), 4)

    def test_three_entries_per_session(self):
        events, quotes = [], []
        for i in range(4):
            e = replace(self.e, event_id='fixture%d' % i, cutoff='2026-10-23T10:05:%02d+00:00' % (i * 3 + 1))
            events.append(e)
            quotes.extend((replace(self.q(i * 3 + 2), signal_id=e.event_id),
                           replace(self.q(i * 3 + 3, '.24', '.25'), signal_id=e.event_id)))
        with patch('synthetic_options_execution.run', return_value=replace(self.signals, signals=tuple(events))):
            r = self.sim(tuple(quotes))
        self.assertEqual(sum(row[1] == 'BUY' for row in r.ledger), 3)
        self.assertTrue(any(row[1] == 'REJECT_DAILY_LIMIT' for row in r.ledger))

    def test_full_session_warmup_does_not_cancel_later_signal(self):
        full = make_demo('conflict')
        quotes = (self.q(), self.q(3, '.24', '.25'))
        result = simulate(full, quotes, synthetic=True)
        shortened = self.sim(quotes)
        self.assertEqual(tuple(row[:5] for row in result.ledger[:2]),
                         tuple(row[:5] for row in shortened.ledger[:2]))
        self.assertEqual([row[1] for row in result.ledger[:2]], ['BUY', 'SELL_TARGET'])
        self.assertEqual(result.realized_net, shortened.realized_net)

    def test_block_before_signal_does_not_cancel_recovered_signal(self):
        from paper_signal_engine import PaperStep
        for state in ('DATA_BLOCKED', 'PROFILE_BLOCKED'):
            block = PaperStep('2026-10-23T10:05:00+00:00', 'BLOCKED',
                             ((self.e.symbol, state, (), 'WAIT'),))
            fixture = replace(self.signals, steps=(block,) + self.signals.steps)
            with self.subTest(state=state), patch('synthetic_options_execution.run', return_value=fixture):
                self.assertEqual(self.sim((self.q(),)).ledger[0][1], 'BUY')

    def test_block_at_signal_cutoff_remains_fail_closed(self):
        from paper_signal_engine import PaperStep
        block = PaperStep(self.e.cutoff, 'BLOCKED',
                         ((self.e.symbol, 'DATA_BLOCKED', (), 'WAIT'),))
        fixture = replace(self.signals, steps=self.signals.steps + (block,))
        with patch('synthetic_options_execution.run', return_value=fixture):
            self.assertEqual(self.sim((self.q(),)).ledger[0][1], 'REJECT_DATA_BLOCKED')

    def test_block_cancels_entry_but_allows_valid_exit(self):
        from paper_signal_engine import PaperStep
        block = PaperStep(self.q(3).at, 'BLOCKED', ((self.e.symbol, 'DATA_BLOCKED', (), 'WAIT'),))
        with patch('synthetic_options_execution.run', return_value=replace(self.signals, steps=self.signals.steps + (block,))):
            self.assertEqual(self.sim((self.q(4),)).ledger[0][1], 'REJECT_DATA_BLOCKED')
            self.assertEqual(self.sim((self.q(), self.q(4, '.24', '.25'))).ledger[1][1], 'SELL_TARGET')


if __name__ == '__main__':
    unittest.main()
