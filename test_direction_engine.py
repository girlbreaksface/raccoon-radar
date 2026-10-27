"""Synthetic direction hypotheses: no provider, storage, orders or real claims."""
import copy
import math
import unittest
from datetime import datetime, timedelta
from direction_engine import Config, evaluate


EVIDENCE = {"status": "SYNTHETIC", "reference": "synthetic-explicit-intervals-v1"}


def candles(trend="up", count=25, symbol="SPY", day="2026-10-23"):
    start = datetime.fromisoformat(day + " 09:30:00")
    out = []
    for i in range(count):
        price = 100 + i if trend == "up" else 200 - i if trend == "down" else 100
        first = start + timedelta(minutes=i)
        end = first + timedelta(minutes=1)
        out.append(dict(symbol=symbol, raw_timestamp=first.strftime("%Y-%m-%d %H:%M:%S"),
            interval_start_et=first.strftime("%Y-%m-%d %H:%M:%S"),
            interval_end_et=end.strftime("%Y-%m-%d %H:%M:%S"),
            available_at_et=end.strftime("%Y-%m-%d %H:%M:%S"), complete=True,
            open=price - .1 if trend == "up" else price + .1,
            high=price + .25, low=price - .25, close=price,
            volume=200 if i == count - 1 else 100))
    return out


def run(rows, **overrides):
    context = dict(symbol="SPY", session_open_et="2026-10-23 09:30:00",
                   session_close_et="2026-10-23 16:00:00",
                   as_of_et=rows[-1]["available_at_et"] if rows else "2026-10-23 10:00:00",
                   interval_evidence=EVIDENCE)
    context.update(overrides)
    return evaluate(rows, **context)


class DirectionEngineTests(unittest.TestCase):
    def test_bull_candidate_has_numeric_observations_and_no_confidence(self):
        result = run(candles())
        self.assertEqual(result["signal"], "BULLISH CANDIDATE")
        obs = result["observations"]
        self.assertAlmostEqual(obs["ema9"], 120)
        self.assertAlmostEqual(obs["ema21"], 114)
        self.assertAlmostEqual(obs["vwap_candle_proxy"], (sum(range(100,124))+248)/26)
        self.assertEqual(obs["volume_ratio"], 2)
        self.assertTrue(obs["five_bar_break_above"])
        self.assertEqual(result["data_quality"]["status"], "READY")
        self.assertEqual(result["interval_evidence"]["status"], "SYNTHETIC")
        self.assertEqual(result["timestamp"], candles()[-1]["raw_timestamp"])
        self.assertNotIn("confidence", result)
        self.assertEqual(result["reasons"], [])

    def test_bear_candidate_and_qqq_symbol_partition(self):
        rows = candles("down", symbol="QQQ")
        result = run(rows, symbol="QQQ")
        self.assertEqual(result["signal"], "BEARISH CANDIDATE")
        self.assertTrue(result["observations"]["five_bar_break_below"])

    def test_ema9_rejection_can_support_bear_without_five_bar_breakdown(self):
        rows = candles("down")
        rows[-1].update(open=178, high=181.2, low=176.5, close=176.9)
        result = run(rows)
        self.assertTrue(result["observations"]["ema9_rejection"])
        self.assertFalse(result["observations"]["five_bar_break_below"])
        self.assertEqual(result["signal"], "BEARISH CANDIDATE")

    def test_ema9_support_can_support_bull_without_five_bar_breakout(self):
        rows = candles()
        rows[-1].update(open=122, high=123.5, low=118.8, close=123.1)
        result = run(rows)
        self.assertTrue(result["observations"]["ema9_support"])
        self.assertFalse(result["observations"]["five_bar_break_above"])
        self.assertEqual(result["signal"], "BULLISH CANDIDATE")

    def test_neutral_and_low_volume_have_explicit_no_trade_reasons(self):
        result = run(candles("flat"))
        self.assertEqual(result["signal"], "NO TRADE")
        self.assertIn("NO_ALIGNED_TREND", result["reasons"])
        self.assertIn("INSIDE_OPENING_RANGE", result["reasons"])
        rows = candles()
        rows[-1]["volume"] = 1
        self.assertIn("VOLUME_NOT_CONFIRMED", run(rows)["reasons"])

    def test_unknown_interval_evidence_fails_closed(self):
        for evidence in (None, {"status":"UNVERIFIED","reference":"unknown"}):
            with self.subTest(evidence=evidence):
                result = run(candles(), interval_evidence=evidence)
                self.assertEqual(result["signal"], "NO TRADE")
                self.assertIn("UNVERIFIED_INTERVAL_MAPPING", result["reasons"])

    def test_current_incomplete_bar_is_not_used(self):
        rows = candles()
        rows[-1]["complete"] = False
        result = run(rows)
        self.assertEqual(result["signal"], "NO TRADE")
        self.assertIn("INCOMPLETE_CANDLE", result["reasons"])

    def test_future_rows_and_values_do_not_change_a_past_snapshot(self):
        rows = candles()
        past = run(rows)
        future = candles(count=27)[25:]
        future[-1].update(close=float("nan"), volume=-1)
        result = run(rows + future, as_of_et=rows[-1]["available_at_et"])
        self.assertEqual(result, past)

    def test_delayed_availability_prevents_early_use(self):
        rows = candles()
        rows[-1]["available_at_et"] = "2026-10-23 09:58:00"
        early = run(rows, as_of_et="2026-10-23 09:55:00")
        self.assertEqual(early["timestamp"], rows[-2]["raw_timestamp"])
        self.assertEqual(early["data_quality"]["eligible_bars"], 24)

    def test_gaps_duplicates_and_unsorted_input_fail_closed(self):
        rows = candles()
        for bad, reason in ((rows[1:], "MISSING_MINUTES"),
                            (rows[:8]+rows[9:], "MISSING_MINUTES"),
                            (rows+[rows[-1]], "DUPLICATE_INTERVAL"),
                            ([rows[1],rows[0]]+rows[2:], "OUT_OF_ORDER")):
            with self.subTest(reason=reason):
                result = run(bad)
                self.assertEqual(result["signal"], "NO TRADE")
                self.assertIn(reason, result["reasons"])

    def test_invalid_ohlcv_and_interval_contract_fail_closed(self):
        for fields in ({"low":105}, {"volume":-1}, {"close":math.inf},
                       {"open":0}, {"interval_end_et":"2026-10-23 09:33:00"},
                       {"available_at_et":"2026-10-23 09:29:00"}):
            with self.subTest(fields=fields):
                rows = candles()
                rows[0].update(fields)
                result = run(rows)
                self.assertEqual(result["signal"], "NO TRADE")
                self.assertNotEqual(result["data_quality"]["status"], "READY")

    def test_sessions_and_symbols_are_not_blended(self):
        for fields in ({"symbol":"QQQ"},
                       {"interval_start_et":"2026-10-22 09:30:00"}):
            with self.subTest(fields=fields):
                rows = candles()
                rows[0].update(fields)
                self.assertEqual(run(rows)["signal"], "NO TRADE")

    def test_warmup_zero_volume_empty_and_staleness(self):
        for rows, reason in ((candles(count=10), "INSUFFICIENT_WARMUP"),
                             ([], "NO_COMPLETED_DATA")):
            with self.subTest(reason=reason):
                self.assertIn(reason, run(rows)["reasons"])
        rows = candles()
        for row in rows: row["volume"] = 0
        self.assertIn("ZERO_VOLUME_BASELINE", run(rows)["reasons"])
        self.assertIn("STALE_DATA", run(candles(),as_of_et="2026-10-23 10:00:00")["reasons"])

    def test_input_preserved_and_replay_is_deterministic(self):
        rows = candles()
        before = copy.deepcopy(rows)
        self.assertEqual(run(rows), run(rows))
        self.assertEqual(rows, before)
        self.assertEqual(len(run(rows)["data_hash"]), 64)

    def test_session_end_and_unsupported_symbol_do_not_make_candidates(self):
        self.assertEqual(run(candles(),symbol="IWM")["signal"],"NO TRADE")
        result = run(candles(),session_close_et="2026-10-23 09:45:00")
        self.assertIn("OUTSIDE_SESSION", result["reasons"])

    def test_fixed_ema_labels_cannot_silently_change_periods(self):
        with self.assertRaises(ValueError):
            run(candles(),config=Config(ema_fast=5,ema_slow=10))
        with self.assertRaises(ValueError):
            run(candles(),config=Config(volume_multiplier="invalid"))

    def test_finite_extremes_that_overflow_derived_math_fail_closed(self):
        rows = candles()
        for row in rows:
            row.update(open=1e308,high=1e308,low=1e308,close=1e308,volume=1e308)
        result = run(rows)
        self.assertEqual(result["signal"],"NO TRADE")
        self.assertIn("NUMERIC_OVERFLOW",result["reasons"])

    def test_explicit_1600_interval_end_is_accepted_without_raw_relabeling(self):
        rows = candles(count=390)
        result = run(rows)
        self.assertEqual(result["interval_end_et"],"2026-10-23 16:00:00")
        self.assertNotIn("OUTSIDE_SESSION",result["reasons"])
        after = candles(count=391)[390:]
        self.assertEqual(result,run(rows+after,as_of_et="2026-10-23 16:00:00"))

    def test_invalid_configuration_is_rejected(self):
        for config in (Config(ema_fast=21,ema_slow=9),
                       Config(volume_multiplier=float("nan")),
                       Config(opening_minutes=0)):
            with self.subTest(config=config), self.assertRaises(ValueError):
                run(candles(),config=config)


if __name__ == "__main__":
    unittest.main()
