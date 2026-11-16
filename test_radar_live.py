"""Synthetic provider fixtures exercise market data without an SDK connection."""
from base64 import b64decode
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from radar_live import (candle_metrics, collect, directional_view, eastern, option_candidate,
                        rank_options, session_at)
from radar_live_panel import AlertState, current_action, finalize_decisions, request_snapshot
from radar_paper_performance import paper_performance


def local(hour, minute, second=0, day=16):
    return datetime(2026, 11, day, hour, minute, second, tzinfo=eastern())


def candles(code, count=31):
    rows = []
    for i in range(count):
        close = 100 + i * .1
        volume = 250 if i == 29 else 100
        rows.append(dict(code=code, time_key=(local(9, 30) + timedelta(minutes=i)).
                         strftime("%Y-%m-%d %H:%M:%S"), open=close, close=close,
                         high=close + .05, low=close - .05, volume=volume,
                         turnover=close * volume))
    return rows


class Records(list):
    def to_dict(self, orient):
        assert orient == "records"
        return list(self)


class MockOpenD:
    def __init__(self, now, authenticated=True, deny=None):
        self.now = now
        self.authenticated = authenticated
        self.deny = deny
        self.subscribed = []

    def get_global_state(self):
        return 0, dict(qot_logined=self.authenticated, program_status_type="READY",
                       server_ver="1012", timestamp=self.now.timestamp(), market_us="MORNING")

    def request_trading_days(self, market, *, start, end):
        return 0, [dict(time=end, trade_date_type="WHOLE")]

    def get_market_snapshot(self, codes):
        return 0, Records(dict(code=code, suspension=False, last_price=103,
                               update_time=self.now.strftime("%Y-%m-%d %H:%M:%S"))
                          for code in codes)

    def subscribe(self, codes, types, **kwargs):
        self.subscribed.extend(codes)
        return (-1, "No entitlement") if self.deny in codes else (0, None)

    def get_cur_kline(self, code, *args):
        return 0, Records(candles(code))


SDK = SimpleNamespace(SubType=SimpleNamespace(K_1M="K_1M"), Session=SimpleNamespace(RTH="RTH"),
                      KLType=SimpleNamespace(K_1M="K_1M"), AuType=SimpleNamespace(NONE="NONE"),
                      TradeDateMarket=SimpleNamespace(US="US"))


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            eastern()
        except ZoneInfoNotFoundError:
            fixture = Path(__file__).parent / "tests/canonicalizer_fixtures/new_york_tzdata_2026_5.b64.txt"
            zone = ZoneInfo.from_file(BytesIO(b64decode(fixture.read_bytes())), key="America/New_York")
            cls.enterClassContext(patch("radar_live.eastern", return_value=zone))
            cls.enterClassContext(patch(f"{__name__}.eastern", return_value=zone))

    def test_market_session(self):
        calendar = {"2026-11-16": "WHOLE", "2026-11-18": "MORNING"}
        for instant, state in ((local(10, 0, day=15), "WEEKEND"),
                               (local(10, 0, day=17), "HOLIDAY / CLOSED"),
                               (local(10, 0, day=18), "SHORT OR SPECIAL SESSION / WAIT"),
                               (local(8, 0), "PREMARKET"), (local(9, 30), "OPENING WARMUP"),
                               (local(10, 0), "REGULAR"), (local(16, 0), "AFTER HOURS")):
            self.assertEqual(session_at(instant, calendar)[0], state)
        self.assertEqual(session_at(local(10, 0), None)[0], "CALENDAR UNVERIFIED")

    def test_indicators_and_no_lookahead(self):
        now = local(10, 0, 10)
        metrics = candle_metrics(candles("US.SPY"), "US.SPY", now, now.date())
        self.assertEqual(metrics["bars"], 30)
        self.assertAlmostEqual(metrics["ema9"], 102.5)
        self.assertAlmostEqual(metrics["ema21"], 101.9)
        self.assertAlmostEqual(metrics["vwap"], metrics["vwap_proxy"])
        self.assertEqual(metrics["relative_volume"], 2.5)
        self.assertEqual(directional_view(metrics, ())[0], "CALL")
        self.assertEqual(directional_view(metrics, ("stale",))[0], "WAIT")

    def test_bad_timestamps_and_turnover(self):
        now = local(10, 0, 10)
        rows = candles("US.SPY")
        for invalid in (rows[2:], rows[:5] + rows[6:], [*rows, rows[0]],
                        rows[:4] + [rows[5], rows[4]] + rows[6:],
                        [*rows, dict(rows[-1], time_key="2026-11-16 10:02:00")]):
            with self.assertRaises(ValueError):
                candle_metrics(invalid, "US.SPY", now, now.date())

    def test_forming_end_label_excluded_in_eastern_or_utc(self):
        from datetime import timezone

        rows = candles("US.SPY", 32)
        rows[-1]["close"] = 9999  # The incomplete row cannot enter validation or metrics.
        for second in (0, 59):
            now = local(10, 0, second)
            for retrieved in (now, now.astimezone(timezone.utc)):
                result = candle_metrics(rows, "US.SPY", retrieved, now.date())
                self.assertEqual(result["bars"], 30)
                self.assertEqual(result["raw_candle"], "2026-11-16T09:59:00-05:00")
        at_boundary = local(10, 1)
        self.assertEqual(candle_metrics(rows, "US.SPY", at_boundary, at_boundary.date())["bars"], 31)

    def test_delayed_or_suspicious_future_tail(self):
        now = local(10, 0, 10)
        rows = candles("US.SPY", 32)
        delayed = candle_metrics(rows[:27], "US.SPY", now, now.date())
        self.assertEqual(delayed["raw_candle"], "2026-11-16T09:56:00-05:00")
        later = local(10, 5, 10)
        result = collect(MockOpenD(later), SDK, clock=lambda: later)
        for row in result["symbols"].values():
            self.assertEqual(row["candle_health"], "STALE")
            self.assertEqual(row["action"], "WAIT")
        for invalid in (rows[:-2] + rows[-1:], rows + [rows[-1]], rows[:-1] + [
                dict(rows[-1], time_key="2026-11-17 10:01:00")]):
            with self.assertRaisesRegex(ValueError, "future minute timestamp"):
                candle_metrics(invalid, "US.SPY", now, now.date())
        rows[2]["turnover"] = 10
        metrics = candle_metrics(rows, "US.SPY", now, now.date())
        self.assertIsNone(metrics["vwap"])
        self.assertIsNotNone(metrics["vwap_proxy"])
        self.assertEqual(directional_view(metrics, ())[0], "WAIT")

    def test_provisional_opening_range_and_chop(self):
        now = local(10, 0, 10)
        rows = candles("US.SPY")
        metrics = candle_metrics(rows, "US.SPY", now, now.date())
        self.assertEqual(metrics["five_minute_trend"], "UP")
        self.assertEqual(metrics["opening_5m"], [rows[0]["low"], rows[4]["high"]])
        for index in range(18, 29):
            row = rows[index]
            close = 101 if index % 2 else 102
            row.update(open=close, close=close, high=close + .05, low=close - .05,
                       turnover=close * row["volume"])
        metrics = candle_metrics(rows, "US.SPY", now, now.date())
        self.assertTrue(metrics["choppy"])
        self.assertIn("Choppy", directional_view(metrics, ())[1])

    def test_observation_fail_closed_and_partial_permission(self):
        now = local(10, 0, 10)
        result = collect(MockOpenD(now, deny="US.QQQ"), SDK, clock=lambda: now)
        self.assertEqual(result["symbols"]["US.SPY"]["metrics"]["bars"], 30)
        self.assertIn("convention unverified", result["symbols"]["US.SPY"]["reason"])
        self.assertEqual(result["symbols"]["US.QQQ"]["permissions"], "No entitlement")
        self.assertEqual({r["action"] for r in result["symbols"].values()}, {"WAIT"})
        with patch("radar_live.VERIFIED_MINUTE_LABEL", "START"):
            result = collect(MockOpenD(now, deny="US.QQQ"), SDK, clock=lambda: now)
        self.assertIn("confirmation missing", result["symbols"]["US.SPY"]["reason"])
        provider = MockOpenD(now, authenticated=False)
        self.assertEqual(collect(provider, SDK, clock=lambda: now)["symbols"], {})
        self.assertEqual(provider.subscribed, [])

    def test_rendered_signal_expires(self):
        now = local(10, 0, 10)
        row = dict(action="CALL", reason="breakout", quote_at=now.isoformat(),
                   metrics=dict(raw_candle=(now - timedelta(minutes=1)).isoformat()))
        self.assertEqual(current_action(row, now)[0], "CALL")
        self.assertEqual(current_action(row, now + timedelta(seconds=21))[0], "WAIT")
        result = {"symbols": {"US.SPY": dict(row), "US.QQQ": dict(
            row, quote_at=(now - timedelta(seconds=21)).isoformat())}}
        finalize_decisions(result, now)
        self.assertEqual({row["action"] for row in result["symbols"].values()}, {"WAIT"})

    def test_option_identity_freshness_greeks_and_cap(self):
        now = local(10, 0, 10)
        chain = dict(code="US.TEST", stock_owner="US.SPY", lot_size=100, suspension=False,
                     option_standard_type="STANDARD", option_type="CALL", strike_time="2026-11-16",
                     strike_price=104)
        snap = dict(code="US.TEST", stock_owner="US.SPY", suspension=False, option_valid=True,
                    option_type="CALL", strike_time="2026-11-16", option_strike_price=104,
                    option_contract_size=100, update_time="2026-11-16 10:00:05",
                    volume=20, option_open_interest=100, option_delta=.2, option_gamma=.1,
                    option_theta=-.1, option_vega=.1)
        book = dict(code="US.TEST", Bid=[(.23, 10)], Ask=[(.25, 10)],
                    bid_epoch=(now - timedelta(seconds=3)).timestamp(),
                    ask_epoch=(now - timedelta(seconds=4)).timestamp())
        valid = option_candidate(chain, snap, book, "US.SPY", now)
        self.assertAlmostEqual(valid["premium"], 25.125)
        self.assertGreater(valid["round_trip_cost"], 2)
        for bad_book in (dict(book, bid_epoch=None), dict(book, ask_epoch=0),
                         dict(book, Ask=[(.30, 10)]), dict(book, Ask=[(.20, 10)])):
            with self.assertRaises(ValueError):
                option_candidate(chain, snap, bad_book, "US.SPY", now)
        with self.assertRaises(ValueError):
            option_candidate(chain, dict(snap, option_delta=-.2), book, "US.SPY", now)
        ranks, reasons = rank_options([chain, chain], [snap], {"US.TEST": book}, "US.SPY", now)
        self.assertEqual((ranks, reasons), ([], {"Duplicate contract": 2}))
        ranks, reasons = rank_options([chain], [snap], {"US.TEST": dict(book, bid_epoch=None)},
                                      "US.SPY", now)
        self.assertEqual((ranks, reasons), ([], {"Verified per-side US order-book timestamps unavailable": 1}))

    def test_scan_off_session_does_not_request_options(self):
        now = local(10, 0, 10, day=15)
        result = collect(MockOpenD(now), SDK, scan=True, clock=lambda: now)
        for row in result["symbols"].values():
            self.assertIn("regular session", row["options"]["status"])


class PresentationTests(unittest.TestCase):
    def test_alert_state_and_timeout(self):
        alerts = AlertState()
        self.assertFalse(alerts.update("ready", []))
        self.assertTrue(alerts.update("ready", ["SPY"]))
        self.assertFalse(alerts.update("ready", ["SPY"]))
        self.assertTrue(alerts.update("stale", []))
        with patch("radar_live_panel.subprocess.run", side_effect=subprocess.TimeoutExpired([], 18)):
            self.assertIn("timed out", request_snapshot(11111, False)["status"])

    def test_performance_restores_realized_synthetic_results(self):
        history = [(2, "gap", "10:05:01 TARGET QQQ PUT 165 P/L $+4.00"),
                   (1, "conflict", "10:05:01 STOP SPY CALL 140 P/L $-5.00"),
                   (1, "conflict", "10:06:01 TARGET SPY CALL 140 P/L $+7.00"),
                   (1, "conflict", "10:07:01 OPEN SPY CALL 140 $20.10")]
        overall, setups = paper_performance(history)
        self.assertEqual(overall["closed"], 3)
        self.assertEqual(overall["wins"], 2)
        self.assertEqual(overall["total"], Decimal("6"))
        self.assertEqual(overall["expectancy"], Decimal("2"))
        self.assertEqual(overall["drawdown"], Decimal("5"))
        self.assertEqual(overall["profit_factor"], Decimal("2.2"))
        self.assertEqual(overall["average_loss"], Decimal("5"))
        self.assertEqual(overall["max_loss_streak"], 1)
        self.assertEqual(setups[("conflict", "SPY", "CALL")]["closed"], 2)
