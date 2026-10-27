"""Independent decimal oracles and synthetic rule-boundary review evidence.

No threshold optimization or claim that excluded examples are useful trades.
"""
import copy
import json
import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext

from direction_engine import Config
from test_direction_engine import candles, run


def decimal_ema(values, period):
    # Separate high-precision recurrence; not imported from the engine.
    with localcontext() as ctx:
        ctx.prec = 50
        value = sum(values[:period]) / Decimal(period)
        alpha = Decimal(2) / Decimal(period + 1)
        for close in values[period:]:
            value = value + alpha * (close - value)
        return value


class DirectionMathReviewTests(unittest.TestCase):
    def test_irregular_prices_and_volumes_match_independent_decimal_oracles(self):
        rows = candles(count=40)
        for i,row in enumerate(rows):
            price = Decimal("100") + Decimal(i % 7)*Decimal(".3") + Decimal(i)*Decimal(".11")
            row.update(open=float(price-Decimal(".1")),high=float(price+Decimal(".4")),
                       low=float(price-Decimal(".2")),close=float(price),volume=100+13*i)
        rows[3]["volume"] = 0
        obs = run(rows)["observations"]
        d = lambda value: Decimal(str(value))
        closes = [d(row["close"]) for row in rows]
        with localcontext() as ctx:
            ctx.prec = 50
            numerator = sum(((d(r["high"])+d(r["low"])+d(r["close"]))/3)*d(r["volume"]) for r in rows)
            denominator = sum(d(r["volume"]) for r in rows)
            prior_mean = sum(d(r["volume"]) for r in rows[-21:-1])/20
            self.assertAlmostEqual(obs["ema9"],float(decimal_ema(closes,9)),places=10)
            self.assertAlmostEqual(obs["ema21"],float(decimal_ema(closes,21)),places=10)
            self.assertAlmostEqual(obs["vwap_candle_proxy"],float(numerator/denominator),places=10)
            self.assertAlmostEqual(obs["volume_baseline"],float(prior_mean),places=10)
            self.assertAlmostEqual(obs["volume_ratio"],float(d(rows[-1]["volume"])/prior_mean),places=10)

    def test_opening_range_half_open_window_excludes_event_bar(self):
        rows = candles("flat",count=31)
        rows[-1].update(open=102,high=104,low=102,close=103,volume=200)
        config = Config(opening_minutes=30)
        result = run(rows,config=config)
        self.assertEqual(result["observations"]["opening_range_high"],100.25)
        self.assertEqual(result["observations"]["opening_range_low"],99.75)
        self.assertIn("INSUFFICIENT_WARMUP",run(rows[:-1],config=config)["reasons"])
        self.assertEqual(result["signal"],"BULLISH CANDIDATE")

    def test_volume_equality_is_inclusive_but_opening_price_equality_is_not(self):
        rows = candles()
        rows[-1]["volume"] = 120
        self.assertEqual(run(rows)["signal"],"BULLISH CANDIDATE")
        rows[-1]["volume"] = 119.999
        self.assertIn("VOLUME_NOT_CONFIRMED",run(rows)["reasons"])
        rows = candles()
        rows[0]["high"] = rows[-1]["close"]
        result = run(rows)
        self.assertFalse(result["observations"]["above_opening_range"])
        self.assertIn("INSIDE_OPENING_RANGE",result["reasons"])

    def test_synthetic_ablation_shows_strict_or_and_volume_suppression(self):
        rows = candles()
        for row in rows[:15]: row["high"] = 130
        blocked = run(rows)
        self.assertTrue(blocked["observations"]["bullish_trend"])
        self.assertTrue(blocked["observations"]["volume_confirmed"])
        self.assertTrue(blocked["observations"]["five_bar_break_above"])
        self.assertEqual(blocked["signal"],"NO TRADE")
        self.assertIn("INSIDE_OPENING_RANGE",blocked["reasons"])
        rows = candles()
        rows[-1]["volume"] = 100
        self.assertEqual(run(rows)["signal"],"NO TRADE")
        self.assertEqual(run(rows,config=Config(volume_multiplier=1.0))["signal"],
                         "BULLISH CANDIDATE")

    def test_price_reflection_and_positive_scaling_preserve_direction_symmetry(self):
        up = candles()
        reflected = copy.deepcopy(up)
        for old,new in zip(up,reflected):
            new.update(open=1000-old["open"],high=1000-old["low"],
                       low=1000-old["high"],close=1000-old["close"])
        self.assertEqual(run(up)["signal"],"BULLISH CANDIDATE")
        self.assertEqual(run(reflected)["signal"],"BEARISH CANDIDATE")
        scaled = copy.deepcopy(up)
        for row in scaled:
            for key in ("open","high","low","close"): row[key] *= 3
        result = run(scaled)
        self.assertEqual(result["signal"],run(up)["signal"])
        self.assertAlmostEqual(result["observations"]["ema9"],run(up)["observations"]["ema9"]*3)

    def test_warmup_and_early_gap_suppress_even_later_clean_trend(self):
        rows = candles(count=50)
        self.assertIn("INSUFFICIENT_WARMUP",run(rows[:21])["reasons"])
        self.assertEqual(run(rows)["signal"],"BULLISH CANDIDATE")
        damaged = rows[:1]+rows[2:]
        self.assertIn("MISSING_MINUTES",run(damaged)["reasons"])
        self.assertEqual(run(damaged)["signal"],"NO TRADE")

    def test_repeated_candidates_are_locations_not_fresh_crossings(self):
        rows = candles(count=35)
        for row in rows[21:]: row["volume"] = 1000
        first = run(rows[:25])
        second = run(rows[:28])
        self.assertEqual(first["signal"],"BULLISH CANDIDATE")
        self.assertEqual(second["signal"],"BULLISH CANDIDATE")
        self.assertTrue(first["observations"]["above_opening_range"])
        self.assertTrue(second["observations"]["above_opening_range"])

    def test_unknown_or_non_string_raw_stamp_cannot_become_a_candidate(self):
        for raw in (None,0,[],""," "):
            with self.subTest(raw=raw):
                rows = candles()
                rows[-1]["raw_timestamp"] = raw
                result = run(rows)
                self.assertEqual(result["signal"],"NO TRADE")
                self.assertIn("INVALID_RAW_TIMESTAMP",result["reasons"])

    def test_result_mutation_does_not_mutate_inputs_or_later_snapshots(self):
        rows = candles()
        before = copy.deepcopy(rows)
        config = Config()
        expected = run(rows,config=config)
        changed = run(rows,config=config)
        changed["observations"]["ema9"] = -1
        changed["interval_evidence"]["reference"] = "mutated output"
        self.assertEqual(run(rows,config=config),expected)
        self.assertEqual(rows,before)
        self.assertEqual(json.loads(json.dumps(expected,allow_nan=False)),expected)
        with self.assertRaises(FrozenInstanceError):
            config.volume_multiplier = 7


if __name__ == "__main__":
    unittest.main()
