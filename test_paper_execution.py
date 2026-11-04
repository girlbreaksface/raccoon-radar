"""Fictional executable quotes only; no market history, broker, or user stores."""
from dataclasses import replace
from decimal import Decimal, getcontext
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from paper_execution import Config, Quote, simulate
from paper_signal_engine import run
from synthetic_replay_demo import make_demo


def data(scenario='conflict', full=False):
    d = make_demo(scenario)
    return d if full else replace(d, steps=(d.steps[34],))


def quote(symbol, at, bid='100', ask='101'):
    return Quote('2026-10-23', '2026-10-23T' + at + '+00:00', symbol, bid, ask)


def roundtrip():
    return (quote('QQQ', '10:05:02'), quote('SPY', '10:05:02', '99', '100'),
            quote('QQQ', '10:06:02', '89', '90'), quote('SPY', '10:06:02', '110', '111'))


class ExecutionTests(unittest.TestCase):
    def test_long_short_cash_fees_and_collateral_reconcile(self):
        r = simulate(data(), roundtrip(), Config(fee_per_fill='1'), synthetic=True)
        self.assertEqual([f.side for f in r.fills], ['SELL', 'BUY', 'BUY', 'SELL'])
        self.assertEqual(Decimal(r.realized_net), Decimal('16'))
        self.assertEqual(Decimal(r.cash), Decimal('10016'))
        self.assertEqual(Decimal(r.equity), Decimal('10016'))
        self.assertEqual(Decimal(r.short_collateral), 0)
        self.assertEqual(r.open_positions, ())
        self.assertTrue(all(status == 'CLOSED' for _, status in r.signal_statuses))
        self.assertEqual(r.broker_execution, 'DISABLED')

    def test_no_same_time_or_predecision_fill(self):
        quotes = (quote('SPY', '10:05:00', '9', '10'),
                  quote('SPY', '10:05:01', '19', '20'),
                  quote('SPY', '10:05:02', '29', '30'))
        r = simulate(data(), quotes, synthetic=True)
        self.assertEqual(len(r.fills), 1)
        self.assertEqual(Decimal(r.fills[0].price), 30)
        self.assertEqual(r.fills[0].at, quotes[-1].at)

    def test_latency_and_entry_deadline_inclusive(self):
        quotes = (quote('SPY', '10:05:02'), quote('SPY', '10:05:04'))
        r = simulate(data(), quotes, Config(latency_seconds=3), synthetic=True)
        self.assertEqual(r.fills[0].at, quotes[-1].at)
        r = simulate(data(), (quote('SPY', '10:05:31'),), synthetic=True)
        self.assertEqual(len(r.fills), 1)
        r = simulate(data(), (quote('SPY', '10:05:32'),), synthetic=True)
        self.assertEqual(r.fills, ())
        self.assertTrue(all(s == 'ENTRY_EXPIRED' for _, s in r.signal_statuses))

    def test_missing_entry_quotes_pending_or_expired_at_horizon(self):
        pending = simulate(data(), (), synthetic=True)
        self.assertTrue(all(s == 'PENDING_ENTRY' for _, s in pending.signal_statuses))
        expired = simulate(data(full=True), (), synthetic=True)
        self.assertTrue(all(s == 'ENTRY_EXPIRED' for _, s in expired.signal_statuses))
        self.assertEqual(Decimal(expired.equity), 10000)

    def test_missing_exit_stays_open_with_last_known_marks(self):
        r = simulate(data(full=True), roundtrip()[:2], Config(fee_per_fill='1'), synthetic=True)
        self.assertEqual(len(r.fills), 2)
        self.assertEqual(len(r.open_positions), 2)
        self.assertEqual(Decimal(r.short_collateral), 200)
        self.assertEqual(Decimal(r.unrealized_net), -4)
        self.assertEqual(Decimal(r.equity), 9996)
        self.assertTrue(all(p.last_quote_at.endswith('10:05:02+00:00') for p in r.open_positions))
        self.assertGreater(r.as_of, r.open_positions[0].last_quote_at)

    def test_slippage_applies_adversely_and_quantity_scales(self):
        r = simulate(data(), roundtrip(), Config(quantity=2, slippage_bps='100', fee_per_fill='1'), synthetic=True)
        self.assertEqual([Decimal(f.price) for f in r.fills],
                         [Decimal('99'), Decimal('101'), Decimal('90.9'), Decimal('108.9')])
        self.assertEqual(Decimal(r.realized_net), Decimal('28'))
        self.assertEqual(Decimal(r.cash), Decimal('10028'))

    def test_funding_rejects_and_short_proceeds_are_not_free_cash(self):
        r = simulate(data(), roundtrip()[:2], Config(initial_cash='100', fee_per_fill='1'), synthetic=True)
        self.assertEqual(r.fills, ())
        self.assertTrue(all(s == 'REJECTED_CAPITAL' for _, s in r.signal_statuses))
        r = simulate(data(), roundtrip()[:2], Config(initial_cash='150'), synthetic=True)
        self.assertEqual([f.symbol for f in r.fills], ['QQQ'])
        self.assertEqual(Decimal(r.cash), 250)
        self.assertEqual(Decimal(r.available_cash), 50)
        self.assertEqual(Decimal(r.short_collateral), 200)

    def test_future_quote_does_not_rewrite_prior_fill(self):
        quotes = roundtrip()
        a = simulate(data(), quotes[:2], synthetic=True)
        b = simulate(data(), quotes, synthetic=True)
        self.assertEqual(a.fills, b.fills[:2])
        self.assertNotEqual(a.input_hash, b.input_hash)

    def test_determinism_and_decimal_context_isolation(self):
        before = getcontext().copy()
        try:
            getcontext().prec = 6
            getcontext().rounding = 'ROUND_DOWN'
            a = simulate(data(), roundtrip(), synthetic=True)
            getcontext().prec = 28
            b = simulate(data(), roundtrip(), synthetic=True)
            self.assertEqual(a, b)
            self.assertEqual(getcontext().prec, 28)
        finally:
            from decimal import setcontext
            setcontext(before)

    def test_invalid_quotes_fail_before_any_result(self):
        q = quote('SPY', '10:05:02')
        bads = (replace(q, synthetic=False), replace(q, symbol='AAPL'),
                replace(q, session_date='2026-10-24'), replace(q, at='2026-10-23T10:10:00Z'),
                replace(q, bid='NaN'), replace(q, ask='Infinity'), replace(q, bid='0'),
                replace(q, bid='102'), replace(q, ask='1e-9'), replace(q, bid=True))
        for bad in bads:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    simulate(data(), (bad,), synthetic=True)
        for quotes in ((q, q), (quote('SPY', '10:05:03'), q)):
            with self.assertRaises(ValueError):
                simulate(data(), quotes, synthetic=True)

    def test_invalid_config_and_non_synthetic_inputs_rejected(self):
        for config in (Config(quantity=True), Config(quantity=0), Config(initial_cash='0'),
                       Config(slippage_bps='10000'), Config(fee_per_fill='-1'),
                       Config(hold_seconds=0), Config(latency_seconds=31)):
            with self.assertRaises(ValueError):
                simulate(data(), (), config, synthetic=True)
        for flag in (False, None, 1, 'true'):
            with self.assertRaises(ValueError):
                simulate(data(), (), synthetic=flag)
        d = data()
        bad = replace(d.series[0], bundle=replace(d.series[0].bundle, synthetic=False))
        with self.assertRaises(ValueError):
            simulate(replace(d, series=(bad, d.series[1])), (), synthetic=True)

    def test_blocked_symbol_never_fills(self):
        r = simulate(data('provisional'), roundtrip(), synthetic=True)
        self.assertTrue(r.fills)
        self.assertTrue(all(f.symbol == 'SPY' for f in r.fills))

    def test_no_broker_storage_or_transport_dependencies(self):
        import paper_execution
        tree = ast.parse(Path(paper_execution.__file__).read_text())
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {'dataclasses', 'datetime', 'decimal',
                                   'canonical_candles', 'paper_signal_engine'})
        self.assertFalse(any(isinstance(n, ast.Import) for n in ast.walk(tree)))

    def test_open_and_pending_signals_not_reversed_or_deferred(self):
        d = data()
        result = run(d, synthetic=True)
        first = result.signals[0]
        second = replace(first, event_id='fictional-opposite', direction='BEARISH',
                         cutoff='2026-10-23T10:05:03+00:00')
        fixture = replace(result, signals=(first, second))
        with patch('paper_execution.run', return_value=fixture):
            r = simulate(d, (quote('SPY', '10:05:02'), quote('SPY', '10:06:02')), synthetic=True)
            self.assertEqual(r.signal_statuses[1][1], 'IGNORED_POSITION_OPEN')
            self.assertEqual(len(r.fills), 2)
            pending = simulate(d, (quote('SPY', '10:05:04'),), synthetic=True)
            self.assertEqual(pending.signal_statuses[1][1], 'IGNORED_ENTRY_PENDING')

    def test_expired_pending_does_not_suppress_new_direction(self):
        d = data()
        result = run(d, synthetic=True)
        first = result.signals[0]
        second = replace(first, event_id='fictional-opposite', direction='BEARISH',
                         cutoff='2026-10-23T10:06:03+00:00')
        with patch('paper_execution.run', return_value=replace(result, signals=(first, second))):
            r = simulate(d, (quote('SPY', '10:06:04'),), synthetic=True)
        self.assertEqual([status for _, status in r.signal_statuses], ['ENTRY_EXPIRED', 'OPEN'])
        self.assertEqual(r.fills[0].side, 'SELL')

    def test_later_data_block_cancels_pending_but_not_exit(self):
        from paper_signal_engine import PaperStep
        d = data()
        result = run(d, synthetic=True)
        block = PaperStep('2026-10-23T10:05:03+00:00', 'PEER_DATA_UNAVAILABLE',
            (('SPY', 'DATA_BLOCKED', ('SYNTHETIC_FAULT',), 'WAIT'),))
        fixture = replace(result, steps=result.steps + (block,))
        with patch('paper_execution.run', return_value=fixture):
            canceled = simulate(d, (quote('SPY', '10:05:04'),), synthetic=True)
            self.assertEqual(canceled.fills, ())
            self.assertEqual(canceled.signal_statuses[0][1], 'CANCELED_DATA_BLOCKED')
            closed = simulate(d, (quote('SPY', '10:05:02'), quote('SPY', '10:06:02')), synthetic=True)
            self.assertEqual([f.purpose for f in closed.fills], ['ENTRY', 'EXIT_HOLD'])

    def test_exit_waits_for_holding_boundary_and_later_quote(self):
        quotes = (quote('SPY', '10:05:02'), quote('SPY', '10:06:01', '200', '201'),
                  quote('SPY', '10:06:03', '90', '91'))
        r = simulate(data(), quotes, synthetic=True)
        self.assertEqual(r.fills[-1].at, quotes[-1].at)
        self.assertEqual(Decimal(r.realized_net), -11)


if __name__ == '__main__':
    unittest.main()
