"""Synthetic safety regressions; no bid/ask adapter or real-feed certification."""
from datetime import datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import unittest

from adapter import Health, select
from test_adapter import bar, context
from research.reconciliation.vendor.canonical_candles import _raw_time


class FailClosedTests(unittest.TestCase):
    def blocked(self, result, reason):
        self.assertEqual(result.status, 'DATA_BLOCKED')
        self.assertEqual(result.ids, ())
        self.assertIn(reason, result.reasons)

    def test_invalid_price_observations_never_fall_back_to_prior_final(self):
        cases = [('bad',) * 5, ('100',) * 4, (None,) * 5]
        for invalid in ('NaN', 'sNaN', 'Infinity', '-Infinity', '0', '-1'):
            for slot in range(4):
                values = ['100', '102', '99', '101', '10']
                values[slot] = invalid
                cases.append(tuple(values))
        cases += [('100','102','99','101',v) for v in ('NaN','Infinity','-1')]
        cases += [('100','98','99','101','10'), ('100','102','101','100','10')]
        for values in cases:
            with self.subTest(values=values):
                replacement = bar(id='bad', parent='a', values=values,
                                  received=70, receipt_seq=3, committed=71,
                                  commit_seq=4, authority_time=71, authority_seq=4)
                self.blocked(select((bar(), replacement), context()), 'OHLCV')
                self.assertEqual(select((bar(), replacement), context(cutoff=65)).ids, ('a',))

    def test_halt_resume_needs_explicit_revalidation_as_of_both_cutoffs(self):
        history = (Health(1,1,'VALIDATED'), Health(70,5,'HALTED'),
                   Health(80,6,'RESUMED'), Health(90,7,'RECOVERING'),
                   Health(95,8,'VALIDATED'))
        for cutoff, sequence in ((70,5),(80,6),(90,7),(94,20),(100,7)):
            with self.subTest(cutoff=cutoff, sequence=sequence):
                self.blocked(select((bar(),), context(health=history, cutoff=cutoff,
                                                     sequence=sequence)), 'HEALTH')
        self.assertEqual(select((bar(),), context(health=history, cutoff=69)).ids, ('a',))
        self.assertEqual(select((bar(),), context(health=history, cutoff=95,sequence=8)).ids, ('a',))
        # Health recovery cannot repair absent interval coverage.
        self.blocked(select((bar(),), context(health=history, expected=(0,60),cutoff=200)), 'COVERAGE')

    def test_et_to_utc_frozen_dates_and_both_dst_boundaries(self):
        zone = ZoneInfo('America/New_York')
        mapping = SimpleNamespace(raw_format='ISO')
        dates = {'2024-01-19':15, '2024-03-08':15, '2024-03-11':14,
                 '2024-03-15':14, '2024-06-03':14, '2024-07-03':14,
                 '2024-11-01':14, '2024-11-04':15}
        for date, hour in dates.items():
            raw = date + 'T10:00:00'
            self.assertEqual(_raw_time(raw,mapping,zone),
                             datetime.fromisoformat(date).replace(hour=hour,tzinfo=timezone.utc))
            self.assertEqual(raw, date + 'T10:00:00')
        for raw in ('2024-03-10T02:30:00','2024-11-03T01:30:00',
                    '2024-03-11T10:00:00-05:00'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                _raw_time(raw,mapping,zone)
        self.assertEqual(_raw_time('2024-11-03T01:30:00-04:00',mapping,zone).hour,5)
        self.assertEqual(_raw_time('2024-11-03T01:30:00-05:00',mapping,zone).hour,6)

    def test_live_and_historical_modes_never_enter_synthetic_consumer(self):
        for mode in ('LIVE','HISTORICAL','live','historical','MIXED',''):
            with self.subTest(mode=mode):
                self.blocked(select((bar(),),context(mode=mode)), 'CONTEXT')
        self.assertEqual(select((bar(),),context()).status,'MOCK_READY')
        # No per-row origin exists: a synthetic envelope cannot certify isolation.
        self.assertNotIn('feed', bar().__dataclass_fields__)
