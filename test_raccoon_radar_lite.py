from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import unittest

from raccoon_radar_lite import PaperReplay, demo, direction, ranked


class LiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points = demo("conflict")

    def test_signal_and_missing_candle(self):
        self.assertEqual([direction(c) for c in self.points[34].cells], ["CALL", "PUT"])
        run = PaperReplay(demo("gap"))
        qqq = run.point.cells[1]
        self.assertEqual(direction(qqq), "WAIT")
        self.assertEqual(run.candidates(qqq), ())

    def test_quotes_fail_closed(self):
        run = PaperReplay(self.points)
        spy = run.point.cells[0]
        valid = run.candidates(spy)[0]
        invalid = (
            replace(valid, at=run.now - timedelta(seconds=16)),
            replace(valid, at=run.now + timedelta(seconds=1)),
            replace(valid, ask=Decimal(".30")),
            replace(valid, bid=Decimal("NaN")),
            replace(valid, bid=valid.ask + Decimal(".01")),
            replace(valid, contract=replace(valid.contract, strike=999)),
        )
        self.assertEqual(ranked(spy, invalid, run.now), ())
        self.assertEqual(ranked(spy, (valid, *invalid), run.now), (valid,))

    def test_target_stop_and_session_limits(self):
        run = PaperReplay(self.points)
        for expected in ("TARGET", "STOP", "TARGET"):
            spy, qqq = run.point.cells
            self.assertTrue(run.enter(spy, run.candidates(spy)[0].contract))
            self.assertFalse(run.enter(qqq, run.candidates(qqq)[0].contract))
            run.step()
            self.assertIsNone(run.open)
            self.assertIn(expected, run.events[-1])
        spy = run.point.cells[0]
        self.assertFalse(run.enter(spy, run.candidates(spy)[0].contract))

    def test_final_minute_blocks_entry(self):
        run = PaperReplay(self.points, len(self.points) - 1)
        self.assertFalse(run.can_enter)
        run.step()
        self.assertIs(run.point, self.points[-1])
