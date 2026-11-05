"""Synthetic specification regressions; no provider eligibility asserted."""
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext, ROUND_DOWN
import json
from pathlib import Path
import unittest

from production_indicators import Candle, evaluate, causal_quote, session, ET

FIXTURE = Path(__file__).parent / 'fixtures' / 'production_indicator_golden.json'


def bars(day=date(2026, 11, 4), count=120, offset=0, symbol='SPY'):
    start = session(day)[0]
    return [Candle(symbol, start + timedelta(minutes=i), start + timedelta(minutes=i+1),
                   start + timedelta(minutes=i+1, seconds=2), offset+i+1,
                   str(100+(offset+i)%7), str(103+(offset+i)%7),
                   str(98+(offset+i)%7), str(101+(offset+i)%7), str(1+(offset+i)%11),
                   'FINAL', 'VERIFIED_START_END') for i in range(count)]


def run(rows, **kwargs):
    args = dict(symbol='SPY', evaluated_at=rows[-1].available_at,
                evaluation_sequence=rows[-1].sequence+1, required_through=rows[-1].end)
    args.update(kwargs)
    return evaluate(rows, **args)


class IndicatorTests(unittest.TestCase):
    def test_numeric_context_is_independent_of_caller(self):
        expected = run(bars())
        with localcontext() as ctx:
            ctx.prec = 6
            ctx.rounding = ROUND_DOWN
            self.assertEqual(run(bars()), expected)

    def test_evidence_tampering_and_oracle_reproduction(self):
        from production_indicator_checks import evidence, validate_evidence
        report = evidence()
        validate_evidence(report)
        report['numerical']['101']['ema9'] = '100'
        with self.assertRaises(ValueError):
            validate_evidence(report)

    def test_independent_rational_golden(self):
        golden = json.loads(FIXTURE.read_text())
        for count in (101, 120):
            result = run(bars(count=count))
            self.assertEqual(result['status'], 'READY_OFFLINE')
            for field in ('ema9', 'ema21', 'vwap'):
                numerator, denominator = golden[str(count)][field]
                expected = Decimal(numerator) / Decimal(denominator)
                self.assertLess(abs(Decimal(result[field]) - expected), Decimal('1e-24'))

    def test_warmup_means_prior_not_including_current(self):
        for count in (8, 9, 20, 21, 99, 100):
            self.assertEqual(run(bars(count=count))['reason'], 'WARMUP_100_PRIOR')
        self.assertEqual(run(bars(count=101))['prior_candles'], 100)

    def test_cross_session_continuity_and_vwap_reset(self):
        previous = bars(count=390)
        today = bars(date(2026, 11, 5), 15, 390)
        result = run(previous + today)
        golden = json.loads(FIXTURE.read_text())['405']
        self.assertEqual(result['status'], 'READY_OFFLINE')
        for field in ('ema9', 'ema21', 'vwap'):
            a, b = golden[field]
            self.assertLess(abs(Decimal(result[field])-Decimal(a)/Decimal(b)), Decimal('1e-24'))
        self.assertNotEqual(result['ema9'], run(bars())['ema9'])

    def test_no_entries_before_945_or_at_close(self):
        previous = bars(count=390)
        self.assertEqual(run(previous + bars(date(2026, 11, 5), 14, 390))['reason'], 'ENTRY_TIME')
        self.assertEqual(run(previous + bars(date(2026, 11, 5), 15, 390))['status'], 'READY_OFFLINE')
        previous[-1] = replace(previous[-1], available_at=previous[-1].end)
        self.assertEqual(run(previous, evaluated_at=session(date(2026, 11, 4))[1])['reason'], 'ENTRY_TIME')

    def test_calendar_holidays_early_closes_dst_coverage(self):
        for day in (date(2026, 4, 3), date(2026, 7, 3), date(2026, 11, 26), date(2026, 11, 7)):
            self.assertIsNone(session(day))
        for day in (date(2026, 11, 27), date(2026, 12, 24)):
            opening, closing = session(day)
            self.assertEqual(closing.astimezone(ET).hour, 13)
            self.assertEqual(closing-opening, timedelta(minutes=210))
        for day, hour in ((date(2026, 3, 6), 14), (date(2026, 3, 9), 13),
                          (date(2026, 10, 30), 13), (date(2026, 11, 2), 14)):
            self.assertEqual(session(day)[0].hour, hour)
        with self.assertRaises(ValueError):
            session(date(2027, 1, 4))

    def test_holiday_weekend_and_early_close_continuity(self):
        for first, second, count in ((date(2026, 11, 25), date(2026, 11, 27), 390),
                                     (date(2026, 11, 27), date(2026, 11, 30), 210),
                                     (date(2026, 3, 6), date(2026, 3, 9), 390),
                                     (date(2026, 10, 30), date(2026, 11, 2), 390)):
            self.assertEqual(run(bars(first, count) + bars(second, 15, count))['status'], 'READY_OFFLINE')

    def test_missing_duplicate_out_of_order_and_tail(self):
        rows = bars()
        bad = (rows[1:], rows[:20]+rows[21:], rows[:20]+[rows[19]]+rows[20:],
               rows[:20]+[rows[21],rows[20]]+rows[22:])
        for data in bad:
            self.assertEqual(run(data)['status'], 'BLOCKED')
        self.assertEqual(run(rows[:-1], required_through=rows[-1].end)['reason'], 'INCOMPLETE_WATERMARK')
        # A missing prior session tail or a whole session cannot silently reset EMA.
        self.assertEqual(run(rows + bars(date(2026, 11, 5), 15, 120))['status'], 'BLOCKED')
        self.assertEqual(run(bars(count=390) + bars(date(2026, 11, 6), 15, 390))['status'], 'BLOCKED')

    def test_invalidations_anywhere_block_entire_snapshot(self):
        rows = bars()
        for change in (dict(finality='UNKNOWN'), dict(finality='PROVISIONAL'),
                       dict(mapping='UNKNOWN'), dict(revision=1), dict(revision=True),
                       dict(volume='0'), dict(volume='NaN'), dict(close='Infinity'),
                       dict(open='0'), dict(high='99'), dict(volume=True),
                       dict(start=rows[10].start.replace(tzinfo=None)),
                       dict(symbol='QQQ'), dict(sequence=1), dict(sequence=True),
                       dict(available_at=rows[10].start)):
            altered = rows.copy()
            altered[10] = replace(altered[10], **change)
            self.assertEqual(run(altered)['status'], 'BLOCKED', change)
        corrected = rows + [replace(rows[10], revision=1, sequence=121)]
        self.assertEqual(run(corrected)['status'], 'BLOCKED')

    def test_delayed_finality_preserves_knowledge_and_causal_quotes(self):
        rows = bars()
        rows[-1] = replace(rows[-1], available_at=rows[-1].end + timedelta(seconds=20))
        self.assertEqual(run(rows, evaluated_at=rows[-1].end)['status'], 'BLOCKED')
        result = run(rows)
        self.assertEqual(result['available_at'], rows[-1].available_at.isoformat())
        decision = rows[-1].available_at
        for event, receipt, seq, expected in (
                (decision, decision, 122, True), (decision, decision, 121, False),
                (decision-timedelta(seconds=1), decision, 122, False),
                (decision, decision-timedelta(seconds=1), 122, False)):
            self.assertEqual(causal_quote(result, symbol='SPY', event_at=event,
                                         received_at=receipt, sequence=seq), expected)
        self.assertFalse(causal_quote(result, symbol='QQQ', event_at=decision,
                                     received_at=decision, sequence=122))

    def test_symbol_isolation_and_extended_hours(self):
        self.assertEqual(run(bars(symbol='QQQ'), symbol='QQQ')['status'], 'READY_OFFLINE')
        rows = bars()
        rows[0] = replace(rows[0], start=rows[0].start-timedelta(minutes=1), end=rows[0].start)
        self.assertEqual(run(rows)['reason'], 'RTH_INTERVAL')
        self.assertFalse(causal_quote(dict(status='BLOCKED'), symbol='SPY',
                                     event_at=datetime.now(timezone.utc),
                                     received_at=datetime.now(timezone.utc), sequence=1))
