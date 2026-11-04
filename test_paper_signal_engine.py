"""Fictional fixtures only. No market access or user databases."""
from dataclasses import replace
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from paper_signal_engine import run
from synthetic_replay_demo import make_demo


class PaperSignalTests(unittest.TestCase):
    def test_conflict_keeps_independent_directions_and_deduplicates(self):
        result = run(make_demo('conflict'), synthetic=True)
        self.assertEqual([(e.symbol, e.direction) for e in result.signals],
                         [('SPY', 'BULLISH'), ('QQQ', 'BEARISH')])
        self.assertTrue(all(e.pair_state == 'CONFLICT' for e in result.signals))
        self.assertTrue(all(e.execution == 'DISABLED' for e in result.signals))
        self.assertTrue(all(s[3] == 'ALREADY_EMITTED' for s in result.steps[-1].symbols))

    def test_aligned_and_no_direction(self):
        aligned = run(make_demo('aligned'), synthetic=True)
        self.assertEqual(len(aligned.signals), 2)
        self.assertTrue(all(e.pair_state == 'AGREEMENT_BULLISH' for e in aligned.signals))
        self.assertEqual(run(make_demo('mixed'), synthetic=True).signals, ())

    def test_warmup_and_bad_data_never_emit_for_blocked_symbol(self):
        data = make_demo('aligned')
        self.assertEqual(run(replace(data, steps=data.steps[:34]), synthetic=True).signals, ())
        for scenario in ('provisional', 'gap', 'partial', 'unknown'):
            with self.subTest(scenario=scenario):
                result = run(make_demo(scenario), synthetic=True)
                self.assertEqual([e.symbol for e in result.signals], ['SPY'])
                self.assertTrue(all(s.symbols[1][3] == 'WAIT' for s in result.steps))

    def test_repeated_run_and_prefix_have_stable_events(self):
        data = make_demo('conflict')
        full = run(data, synthetic=True)
        self.assertEqual(full, run(data, synthetic=True))
        prefix = run(replace(data, steps=data.steps[:35]), synthetic=True)
        self.assertEqual(full.signals, prefix.signals)
        self.assertEqual(full.steps[:35], prefix.steps)
        self.assertNotEqual(full.run_hash, prefix.run_hash)

    def test_future_invalid_values_cannot_change_prior_signal(self):
        from canonical_candles import identity
        data = make_demo('aligned')
        source = data.series[0]
        rows = source.bundle.observations[:-1] + (replace(
            source.bundle.observations[-1], values=(float('nan'), 1, 1, 1, 1)),)
        changed = replace(source, bundle=replace(source.bundle, observations=rows,
                          capture_hash=identity((rows, source.bundle.pages))))
        revised = run(replace(data, series=(changed, data.series[1])), synthetic=True)
        self.assertEqual(run(data, synthetic=True).signals, revised.signals)
        self.assertEqual(revised.steps[-1].symbols[0][1], 'DATA_BLOCKED')

    def test_real_inputs_and_multi_session_are_rejected(self):
        data = make_demo()
        for flag in (False, None, 1, 'true'):
            with self.assertRaises(ValueError):
                run(data, synthetic=flag)
        bad = replace(data.series[0], bundle=replace(data.series[0].bundle, synthetic=False))
        with self.assertRaises(ValueError):
            run(replace(data, series=(bad, data.series[1])), synthetic=True)
        with self.assertRaises(ValueError):
            run(replace(data, steps=(data.steps[0], replace(data.steps[1],
                session_date='2026-10-24'))), synthetic=True)

    def test_no_transport_storage_or_order_dependencies(self):
        import paper_signal_engine
        tree = ast.parse(Path(paper_signal_engine.__file__).read_text())
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(modules, {'dataclasses', 'canonical_candles', 'synthetic_replay'})
        self.assertFalse(any(isinstance(n, ast.Import) for n in ast.walk(tree)))

    def test_block_and_direction_change_do_not_reset_seen_keys(self):
        from synthetic_replay import replay
        data = make_demo('aligned')
        data = replace(data, steps=data.steps[34:38])
        baseline = replay(data, synthetic=True)
        points = list(baseline.points)
        points[1] = replace(points[1], cells=tuple(replace(c, state='DATA_BLOCKED',
            bias=None, reasons=('SYNTHETIC_FAULT',)) for c in points[1].cells))
        points[2] = replace(points[2], cells=tuple(replace(c, bias='BEARISH')
            for c in points[2].cells))
        # Trusted synthetic fixture exercises the event reducer's own transitions.
        with patch('paper_signal_engine.replay', return_value=replace(baseline, points=tuple(points))):
            result = run(data, synthetic=True)
        self.assertEqual([(e.symbol, e.direction) for e in result.signals],
            [('SPY', 'BULLISH'), ('QQQ', 'BULLISH'), ('SPY', 'BEARISH'), ('QQQ', 'BEARISH')])
        self.assertTrue(all(s[3] == 'WAIT' for s in result.steps[1].symbols))
        self.assertTrue(all(s[3] == 'ALREADY_EMITTED' for s in result.steps[3].symbols))


if __name__ == '__main__':
    unittest.main()
